"""Catálogo de presets de diagramas (MVP embebido)."""

from __future__ import annotations

from lablog.diagrams.models import DiagramPreset, HighlightSpec, ParamSpec

_RC_TIKZ = r"""\begin{circuitikz}
  \draw (0,0) node[left]{$+$}
    to[V, v=$V_0$, name=V1] (0,2)
    to[short] (2.5,2)
    to[R, R=${{R}}$, l_=$R$, name=R1] (2.5,0)
    to[C, C=${{C}}$, l_=$C$, name=C1] (0,0);
  \node[right] at (2.9,1) {$v_C$};
\end{circuitikz}
"""

_RC_SIM = r'''# lablog-sim: preset=rc_series_charge version=1
# LABLOG_PARAMS_START
R = {{R}}  # ohm  range [1, 1e6]
C = {{C}}  # F    range [1e-12, 1e-3]
V0 = {{V0}}  # V  range [0.1, 100]
# LABLOG_PARAMS_END

import numpy as np
import matplotlib.pyplot as plt

tau = R * C
t = np.linspace(0, 5 * tau, 400)
v_c = V0 * (1.0 - np.exp(-t / tau))
i = (V0 / R) * np.exp(-t / tau)

fig, ax = plt.subplots(1, 2, figsize=(8, 3))
ax[0].plot(t * 1e3, v_c)
ax[0].set_xlabel("t [ms]")
ax[0].set_ylabel("v_C [V]")
ax[0].set_title(f"Carga RC · τ={tau * 1e3:.3g} ms")
ax[0].grid(True, alpha=0.3)
ax[1].plot(t * 1e3, i * 1e3)
ax[1].set_xlabel("t [ms]")
ax[1].set_ylabel("i [mA]")
ax[1].set_title("Corriente")
ax[1].grid(True, alpha=0.3)
fig.tight_layout()
plt.show()
print(f"τ = RC = {tau:.6e} s")
'''

_DIV_TIKZ = r"""\begin{circuitikz}
  \draw (0,0) node[left]{$V_{in}$}
    to[V, v=$V_{in}$, name=Vin] (0,3)
    to[short] (2,3)
    to[R, R=${{R1}}$, l_=$R_1$, name=R1] (2,1.5)
    to[R, R=${{R2}}$, l_=$R_2$, name=R2] (2,0)
    to[short] (0,0);
  \draw (2,1.5) to[short, *-o] (3.2,1.5) node[right]{$V_{out}$};
\end{circuitikz}
"""

_DIV_SIM = r'''# lablog-sim: preset=voltage_divider version=1
# LABLOG_PARAMS_START
R1 = {{R1}}  # ohm
R2 = {{R2}}  # ohm
Vin = {{Vin}}  # V
# LABLOG_PARAMS_END

Vout = Vin * R2 / (R1 + R2)
print(f"Vout = {Vout:.6g} V  (ratio R2/(R1+R2) = {R2/(R1+R2):.4f})")
'''

_MSD_TIKZ = r"""\begin{tikzpicture}[scale=1.1]
  \draw[thick] (0,0) -- (0,1.2);
  \draw[thick, decoration={aspect=0.3, segment length=2mm, amplitude=2mm, coil},
        decorate] (0,0.6) -- (2.2,0.6) node[midway, above=2pt] {$k$};
  \draw[thick, fill=black!10] (2.2,0.2) rectangle (3.2,1.0);
  \node at (2.7,0.6) {$m$};
  \draw[thick] (3.2,0.6) -- (4.0,0.6);
  \draw[thick] (4.0,0.2) -- (4.0,1.0);
  \foreach \y in {0.3,0.5,0.7,0.9}
    \draw (4.0,\y) -- (4.25,\y+0.1);
  \node[below] at (4.1,0.15) {$b$};
  \draw[<->] (2.7,-0.15) -- node[below] {$x$} (2.7,0.15);
\end{tikzpicture}
"""

_MSD_SIM = r'''# lablog-sim: preset=mass_spring_damper version=1
# LABLOG_PARAMS_START
m = {{m}}  # kg
k = {{k}}  # N/m
b = {{b}}  # N·s/m
x0 = {{x0}}  # m
v0 = {{v0}}  # m/s
# LABLOG_PARAMS_END

import numpy as np
import matplotlib.pyplot as plt

wn = np.sqrt(k / m)
zeta = b / (2 * np.sqrt(max(k * m, 1e-30)))
t_end = max(5.0, 8 * np.pi / max(wn, 1e-6))
n = 600
dt = t_end / n
t = np.linspace(0, t_end, n + 1)
x = np.empty(n + 1)
v = np.empty(n + 1)
x[0], v[0] = x0, v0
for i in range(n):
    a = (-k * x[i] - b * v[i]) / m
    v[i + 1] = v[i] + a * dt
    x[i + 1] = x[i] + v[i + 1] * dt

plt.figure(figsize=(6, 3))
plt.plot(t, x)
plt.xlabel("t [s]")
plt.ylabel("x [m]")
plt.title(f"Masa-resorte-amortiguador  ωn={wn:.3g}  ζ={zeta:.3g}")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
print(f"ωn={wn:.4g} rad/s  ζ={zeta:.4g}")
'''

_FEYNMAN_TIKZ = r"""\begin{center}
\begin{tikzpicture}[
  fermion/.style={thick, postaction={decorate},
    decoration={markings, mark=at position 0.55 with {\arrow{stealth}}}},
  photon/.style={decorate, decoration={snake, amplitude=1.1pt, segment length=5pt}, thick},
  every node/.style={font=\small}
]
  \draw[fermion] (-{{spread}},0.9) -- (-0.5,0.2);
  \draw[fermion] (-{{spread}},-0.9) -- (-0.5,-0.2);
  \draw[photon] (-0.5,0.2) -- (0.5,-0.2);
  \draw[fermion] (0.5,-0.2) -- ({{spread}},-0.9);
  \draw[fermion] (0.5,0.2) -- ({{spread}},0.9);
  \fill (-0.5,0.2) circle (1.5pt);
  \fill (0.5,-0.2) circle (1.5pt);
  \node[left] at (-{{spread}},0.9) {$e^-$};
  \node[left] at (-{{spread}},-0.9) {$e^-$};
  \node[right] at ({{spread}},0.9) {$e^-$};
  \node[right] at ({{spread}},-0.9) {$e^-$};
\end{tikzpicture}
\end{center}
"""


def _p(
    pid: str,
    label: str,
    description: str,
    value: float,
    *,
    unit: str = "",
    min_v: float | None = None,
    max_v: float | None = None,
    scale: str = "linear",
    tikz: str | None = None,
    latex: str | None = None,
    line: int | None = None,
    color: str = "amber",
) -> ParamSpec:
    return ParamSpec(
        id=pid,
        label=label,
        description=description,
        value=value,
        unit=unit,
        min=min_v,
        max=max_v,
        scale=scale,  # type: ignore[arg-type]
        highlight=HighlightSpec(tikz=tikz, latex=latex, line=line, color=color),  # type: ignore[arg-type]
    )


_CATALOG: list[DiagramPreset] = [
    DiagramPreset(
        preset_id="rc_series_charge",
        kind="circuitikz",
        title="RC serie — carga",
        summary="Carga de condensador a través de R. Ideal para medir τ = RC.",
        category="circuitos",
        tags=["rc", "transitorio", "lab"],
        params=[
            _p(
                "R",
                "Resistencia",
                "Limita la corriente de carga. Mayor R → mayor τ = RC.",
                1000,
                unit="ohm",
                min_v=1,
                max_v=1e6,
                scale="log",
                tikz="R1",
                latex="R=",
                line=5,
                color="amber",
            ),
            _p(
                "C",
                "Capacitancia",
                "Almacena carga. Mayor C → mayor τ y más energía ½CV².",
                1e-6,
                unit="F",
                min_v=1e-12,
                max_v=1e-3,
                scale="log",
                tikz="C1",
                latex="C=",
                line=6,
                color="sky",
            ),
            _p(
                "V0",
                "Tensión fuente",
                "Escala la asíntota v_C(∞) = V0.",
                5.0,
                unit="V",
                min_v=0.1,
                max_v=100,
                tikz="V1",
                latex="V0",
                line=3,
                color="rose",
            ),
        ],
        tikz_template=_RC_TIKZ,
        sim_backend="numpy_ode",
        sim_template=_RC_SIM,
    ),
    DiagramPreset(
        preset_id="voltage_divider",
        kind="circuitikz",
        title="Divisor de tensión",
        summary="Dos resistencias en serie: Vout = Vin · R2/(R1+R2).",
        category="circuitos",
        tags=["dc", "resistivo"],
        params=[
            _p(
                "R1",
                "R1 (superior)",
                "Rama superior del divisor.",
                10_000,
                unit="ohm",
                min_v=1,
                max_v=1e7,
                scale="log",
                tikz="R1",
                color="amber",
            ),
            _p(
                "R2",
                "R2 (inferior)",
                "Rama inferior; mayor R2 → mayor Vout.",
                10_000,
                unit="ohm",
                min_v=1,
                max_v=1e7,
                scale="log",
                tikz="R2",
                color="sky",
            ),
            _p(
                "Vin",
                "Vin",
                "Tensión de entrada.",
                5.0,
                unit="V",
                min_v=0.1,
                max_v=100,
                tikz="Vin",
                color="rose",
            ),
        ],
        tikz_template=_DIV_TIKZ,
        sim_backend="numpy_ode",
        sim_template=_DIV_SIM,
    ),
    DiagramPreset(
        preset_id="mass_spring_damper",
        kind="mechanics",
        title="Masa-resorte-amortiguador",
        summary="Oscilador 1D con amortiguamiento viscoso.",
        category="mecanica",
        tags=["ode", "oscilador"],
        params=[
            _p(
                "m",
                "Masa",
                "Inercia del bloque.",
                1.0,
                unit="kg",
                min_v=0.01,
                max_v=100,
                scale="log",
            ),
            _p(
                "k",
                "Resorte k",
                "Rigidez. Mayor k → mayor ωn.",
                10.0,
                unit="N/m",
                min_v=0.1,
                max_v=1e5,
                scale="log",
            ),
            _p(
                "b",
                "Amortiguamiento",
                "Fuerza −b v.",
                0.5,
                unit="N·s/m",
                min_v=0,
                max_v=1e3,
            ),
            _p("x0", "x(0)", "Posición inicial.", 1.0, unit="m", min_v=-2, max_v=2),
            _p("v0", "v(0)", "Velocidad inicial.", 0.0, unit="m/s", min_v=-10, max_v=10),
        ],
        tikz_template=_MSD_TIKZ,
        sim_backend="numpy_ode",
        sim_template=_MSD_SIM,
    ),
    DiagramPreset(
        preset_id="qed_moller",
        kind="feynman_tikz",
        title="QED e⁻e⁻ (árbol)",
        summary="Diagrama de Møller estilo Feynman (solo visual; sin simulación).",
        category="particulas",
        tags=["feynman", "tikz"],
        params=[
            _p(
                "spread",
                "Apertura",
                "Separación horizontal de las legs del diagrama.",
                1.8,
                unit="",
                min_v=1.0,
                max_v=3.5,
                scale="linear",
            ),
        ],
        tikz_template=_FEYNMAN_TIKZ,
        sim_backend="none",
        sim_template=None,
    ),
]


def list_presets() -> list[DiagramPreset]:
    return list(_CATALOG)


def get_preset(preset_id: str) -> DiagramPreset | None:
    return next((p for p in _CATALOG if p.preset_id == preset_id), None)
