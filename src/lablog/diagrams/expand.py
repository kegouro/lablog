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


def expand_preset(
    preset: DiagramPreset,
    values: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Devuelve latex (tikz) + params efectivos + metadatos de highlight."""
    clamped = clamp_params(preset, values)
    latex = expand_template(preset.tikz_template, preset, clamped)
    header = (
        f"% lablog-diagram: preset={preset.preset_id} version={preset.version}\n"
        + "".join(f"% lablog-param: {k}={v}\n" for k, v in sorted(clamped.items()))
    )
    return {
        "preset_id": preset.preset_id,
        "version": preset.version,
        "kind": preset.kind,
        "title": preset.title,
        "latex": header + latex,
        "params": clamped,
        "param_specs": [p.model_dump() for p in preset.params],
        "has_simulation": bool(preset.sim_template and preset.sim_backend != "none"),
    }


def expand_simulation(
    preset: DiagramPreset,
    values: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Genera source de celda Python a partir del preset."""
    if not preset.sim_template or preset.sim_backend == "none":
        raise ValueError(f"Preset sin simulación: {preset.preset_id}")
    clamped = clamp_params(preset, values)
    source = expand_template(preset.sim_template, preset, clamped)
    return {
        "preset_id": preset.preset_id,
        "backend": preset.sim_backend,
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
