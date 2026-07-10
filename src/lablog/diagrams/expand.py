"""Expande plantillas de diagramas y celdas de simulación."""

from __future__ import annotations

import math
import re
from typing import Any

from lablog.diagrams.models import DiagramPreset, ParamSpec

_PLACEHOLDER = re.compile(r"\{\{(\w+)\}\}")


def clamp_params(preset: DiagramPreset, values: dict[str, Any] | None) -> dict[str, float]:
    """Mezcla defaults con values y aplica min/max."""
    out = preset.defaults()
    if not values:
        return out
    specs = preset.param_map()
    for key, raw in values.items():
        if key not in specs:
            continue
        spec = specs[key]
        try:
            num = float(raw)
        except (TypeError, ValueError):
            continue
        if math.isnan(num) or math.isinf(num):
            continue
        if spec.min is not None:
            num = max(spec.min, num)
        if spec.max is not None:
            num = min(spec.max, num)
        if spec.scale == "log" and num <= 0:
            num = spec.min if spec.min and spec.min > 0 else 1e-12
        out[key] = num
    return out


def _format_value(spec: ParamSpec, value: float) -> str:
    """Formato estable para LaTeX/Python (sin notación basura)."""
    if abs(value) != 0 and (abs(value) < 1e-3 or abs(value) >= 1e4):
        return f"{value:.{max(spec.precision, 3)}e}"
    # Enteros limpios
    if abs(value - round(value)) < 1e-12 and abs(value) < 1e12:
        return str(int(round(value)))
    return f"{value:.{spec.precision}g}"


def expand_template(template: str, preset: DiagramPreset, values: dict[str, float]) -> str:
    specs = preset.param_map()

    def repl(m: re.Match[str]) -> str:
        key = m.group(1)
        if key not in values:
            return m.group(0)
        spec = specs.get(key)
        if spec is None:
            return str(values[key])
        return _format_value(spec, values[key])

    return _PLACEHOLDER.sub(repl, template)


def resolve_highlight_lines(
    full_latex: str,
    param_specs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Rellena ``highlight.line`` con la línea real en el LaTeX generado.

    Orden de búsqueda por parámetro:
    1. comentario ``% lablog-param: id=``
    2. ``name=<tikz>`` del highlight
    3. fragmento ``highlight.latex``
    """
    lines = full_latex.splitlines()
    resolved: list[dict[str, Any]] = []
    for raw in param_specs:
        p = dict(raw)
        hl = dict(p.get("highlight") or {})
        pid = str(p.get("id", ""))
        line_no: int | None = None
        if pid:
            pat = re.compile(rf"%\s*lablog-param:\s*{re.escape(pid)}\s*=")
            for i, line in enumerate(lines, start=1):
                if pat.search(line):
                    line_no = i
                    break
        tikz_name = hl.get("tikz")
        if line_no is None and tikz_name:
            needle = f"name={tikz_name}"
            for i, line in enumerate(lines, start=1):
                if needle in line.replace(" ", ""):
                    # también acepta name = R1
                    line_no = i
                    break
            if line_no is None:
                loose = re.compile(rf"name\s*=\s*{re.escape(str(tikz_name))}\b")
                for i, line in enumerate(lines, start=1):
                    if loose.search(line):
                        line_no = i
                        break
        frag = hl.get("latex")
        if line_no is None and frag:
            for i, line in enumerate(lines, start=1):
                if str(frag) in line:
                    line_no = i
                    break
        if line_no is not None:
            hl["line"] = line_no
        p["highlight"] = hl
        resolved.append(p)
    return resolved


def augment_derived_params(preset: DiagramPreset, values: dict[str, float]) -> dict[str, float]:
    """Añade magnitudes derivadas usadas en plantillas (no son sliders)."""
    out = dict(values)
    if preset.preset_id == "thin_lens":
        f = out.get("f", 0.1)
        do = out.get("do", 0.3)
        # 1/f = 1/do + 1/di  →  di = 1/(1/f - 1/do)
        if abs(do) < 1e-15 or abs(f) < 1e-15:
            di = 1e6
        else:
            denom = 1.0 / f - 1.0 / do
            di = 1.0 / denom if abs(denom) > 1e-15 else 1e6
        m = (-di / do) if abs(do) > 1e-15 else 0.0
        out["di"] = di
        out["m"] = m
        # Altura del rayo en el esquema (evita flechas enormes si |m|≫1)
        out["m_draw"] = max(-1.5, min(1.5, m)) if abs(m) < 1e5 else 0.0
    return out


# Colores semánticos UI → nombres xcolor/TikZ seguros.
_HIGHLIGHT_LATEX_COLORS: dict[str, str] = {
    "amber": "orange",
    "sky": "cyan",
    "rose": "red",
    "emerald": "green!70!black",
    "violet": "violet",
}

# Presets con celda PySpice opcional (sin dependencia hard).
_PYSPICE_PRESETS = frozenset({"rc_series_charge", "rlc_series_step", "half_wave_rectifier"})


def colorize_named_component(latex: str, tikz_name: str, latex_color: str) -> str:
    """Inyecta ``color=...`` junto a ``name=<tikz_name>`` (Circuitikz/TikZ)."""
    if not tikz_name or not latex_color:
        return latex
    # Evita re-inyectar si ya hay color en el mismo token name=
    name_pat = re.compile(
        rf"(?P<pre>[\[,;\s])name\s*=\s*{re.escape(tikz_name)}\b",
    )

    def repl(m: re.Match[str]) -> str:
        # Busca hacia atrás en el mismo [...] si ya hay color=
        start = max(0, m.start() - 80)
        window = latex[start : m.end()]
        if re.search(r"\bcolor\s*=", window):
            return m.group(0)
        return f"{m.group('pre')}color={latex_color},name={tikz_name}"

    return name_pat.sub(repl, latex, count=1)


def apply_param_highlight(
    latex: str,
    preset: DiagramPreset,
    highlight_param: str | None,
) -> str:
    """Colorea el componente TikZ del parámetro activo (si tiene highlight.tikz)."""
    if not highlight_param:
        return latex
    spec = preset.param_map().get(highlight_param)
    if spec is None or not spec.highlight.tikz:
        return latex
    color = _HIGHLIGHT_LATEX_COLORS.get(spec.highlight.color, "orange")
    return colorize_named_component(latex, spec.highlight.tikz, color)


def expand_preset(
    preset: DiagramPreset,
    values: dict[str, Any] | None = None,
    *,
    highlight_param: str | None = None,
) -> dict[str, Any]:
    """Devuelve latex (tikz) + params efectivos + metadatos de highlight."""
    clamped = augment_derived_params(preset, clamp_params(preset, values))
    latex = expand_template(preset.tikz_template, preset, clamped)
    latex = apply_param_highlight(latex, preset, highlight_param)
    header = (
        f"% lablog-diagram: preset={preset.preset_id} version={preset.version}\n"
        + "".join(f"% lablog-param: {k}={v}\n" for k, v in sorted(clamped.items()))
    )
    if highlight_param:
        header += f"% lablog-highlight: {highlight_param}\n"
    full = header + latex
    specs = resolve_highlight_lines(full, [p.model_dump() for p in preset.params])
    return {
        "preset_id": preset.preset_id,
        "version": preset.version,
        "kind": preset.kind,
        "title": preset.title,
        "latex": full,
        "params": clamped,
        "param_specs": specs,
        "has_simulation": bool(preset.sim_template and preset.sim_backend != "none"),
        "highlight_param": highlight_param,
        "supports_pyspice": preset.preset_id in _PYSPICE_PRESETS,
    }


def _pyspice_source(preset_id: str, params: dict[str, float]) -> str | None:
    """Fuente Jupyter que intenta PySpice y cae a numpy analítico."""
    if preset_id == "rc_series_charge":
        r = params.get("R", 1000.0)
        c = params.get("C", 1e-6)
        v0 = params.get("V0", 5.0)
        return f'''# lablog-sim: preset=rc_series_charge backend=pyspice
# LABLOG_PARAMS_START
R = {r}  # ohm
C = {c}  # F
V0 = {v0}  # V
# LABLOG_PARAMS_END

import numpy as np
import matplotlib.pyplot as plt

def _numpy_rc(R, C, V0):
    tau = R * C
    t = np.linspace(0, 5 * tau, 400)
    v_c = V0 * (1.0 - np.exp(-t / tau))
    return t, v_c, tau

try:
    from PySpice.Spice.Netlist import Circuit
    from PySpice.Unit import u_Ohm, u_F, u_V, u_s  # type: ignore

    circuit = Circuit("RC charge")
    circuit.V("in", "n_in", circuit.gnd, V0 @ u_V)
    circuit.R(1, "n_in", "n_out", R @ u_Ohm)
    circuit.C(1, "n_out", circuit.gnd, C @ u_F)
    simulator = circuit.simulator(temperature=25, nominal_temperature=25)
    tau = R * C
    analysis = simulator.transient(step_time=tau / 80, end_time=5 * tau)
    t = np.array(analysis.time)
    v_c = np.array(analysis["n_out"])
    backend = "pyspice"
except Exception as exc:  # noqa: BLE001 — fallback pedagógico
    print(f"PySpice no disponible ({{type(exc).__name__}}: {{exc}})")
    print("Instala: pip install 'jose-labarca-lablog[pyspice]'  (requiere ngspice)")
    t, v_c, tau = _numpy_rc(R, C, V0)
    backend = "numpy_fallback"

plt.figure(figsize=(6, 3))
plt.plot(t * 1e3, v_c)
plt.xlabel("t [ms]")
plt.ylabel("v_C [V]")
plt.title(f"RC carga · {{backend}} · τ={{tau * 1e3:.3g}} ms")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
print(f"backend={{backend}}  τ={{tau:.6e}} s")
'''
    return None


def expand_simulation(
    preset: DiagramPreset,
    values: dict[str, Any] | None = None,
    *,
    prefer_pyspice: bool = False,
) -> dict[str, Any]:
    """Genera source de celda Python a partir del preset."""
    if not preset.sim_template or preset.sim_backend == "none":
        raise ValueError(f"Preset sin simulación: {preset.preset_id}")
    clamped = clamp_params(preset, values)
    backend = preset.sim_backend
    if prefer_pyspice and preset.preset_id in _PYSPICE_PRESETS:
        pys = _pyspice_source(preset.preset_id, clamped)
        if pys is not None:
            return {
                "preset_id": preset.preset_id,
                "backend": "pyspice",
                "source": pys,
                "params": clamped,
                "language": "python",
            }
    source = expand_template(preset.sim_template, preset, clamped)
    return {
        "preset_id": preset.preset_id,
        "backend": backend,
        "source": source,
        "params": clamped,
        "language": "python",
    }


def parse_lablog_params(latex: str) -> dict[str, float]:
    """Extrae ``% lablog-param: name=value`` del documento."""
    out: dict[str, float] = {}
    for m in re.finditer(r"%\s*lablog-param:\s*(\w+)\s*=\s*([^\s%]+)", latex):
        try:
            out[m.group(1)] = float(m.group(2))
        except ValueError:
            continue
    return out


def parse_lablog_preset_id(latex: str) -> str | None:
    """Extrae ``% lablog-diagram: preset=ID`` del documento."""
    m = re.search(r"%\s*lablog-diagram:\s*preset=([A-Za-z0-9_-]+)", latex)
    return m.group(1) if m else None


def _find_env_end(text: str, begin_pos: int) -> int | None:
    """Devuelve el índice justo tras el ``\\end{env}`` que cierra el ``\\begin`` en begin_pos."""
    m = re.match(r"\\begin\{([a-zA-Z*]+)\}", text[begin_pos:])
    if not m:
        return None
    env = m.group(1)
    depth = 0
    pos = begin_pos
    begin_re = re.compile(rf"\\begin\{{{re.escape(env)}\}}")
    end_re = re.compile(rf"\\end\{{{re.escape(env)}\}}")
    while pos < len(text):
        b = begin_re.search(text, pos)
        e = end_re.search(text, pos)
        if e is None:
            return None
        if b is not None and b.start() < e.start():
            depth += 1
            pos = b.end()
            continue
        depth -= 1
        pos = e.end()
        if depth == 0:
            return pos
    return None


def _diagram_span(doc_latex: str) -> tuple[int, int] | None:
    """Rango [start, end) del primer bloque lablog-diagram + entorno TikZ asociado."""
    header = re.search(r"%\s*lablog-diagram:", doc_latex)
    if not header:
        return None
    start = header.start()
    rest = doc_latex[start:]
    begin = re.search(r"\\begin\{([a-zA-Z*]+)\}", rest)
    if not begin:
        # Solo cabecera de comentarios hasta la siguiente línea no-comentario o EOF.
        end_rel = len(rest)
        for i, line in enumerate(rest.splitlines(keepends=True)):
            if i == 0:
                continue
            if not line.lstrip().startswith("%"):
                # fin de comentarios (sin contar el salto previo ya incluido)
                end_rel = sum(len(x) for x in rest.splitlines(keepends=True)[:i])
                break
        return start, start + end_rel

    env_start = start + begin.start()
    env_end = _find_env_end(doc_latex, env_start)
    if env_end is None:
        # Fallback conservador: no devorar el resto del documento.
        line_end = doc_latex.find("\n", env_start)
        env_end = len(doc_latex) if line_end < 0 else line_end
    # Incluye newline final del bloque si existe.
    if env_end < len(doc_latex) and doc_latex[env_end] == "\n":
        env_end += 1
    return start, env_end


def replace_or_append_diagram(doc_latex: str, new_block: str) -> str:
    """Sustituye el bloque lablog-diagram existente o lo añade al final.

    Preserva el texto del documento fuera del bloque (no reemplaza hasta EOF).
    """
    new_block = new_block.strip() + "\n"
    span = _diagram_span(doc_latex)
    if span is None:
        base = doc_latex.rstrip()
        if base:
            return base + "\n\n" + new_block
        return new_block
    start, end = span
    return doc_latex[:start] + new_block + doc_latex[end:]
