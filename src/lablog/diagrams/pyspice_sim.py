"""Generadores de celdas Jupyter con PySpice + fallback numpy.

Sin dependencia hard: el código generado hace try/import y cae a ODE/analítico.
"""

from __future__ import annotations

# Presets con backend SPICE opcional.
PYSPICE_PRESETS = frozenset(
    {
        "rc_series_charge",
        "rlc_series_step",
        "half_wave_rectifier",
    }
)


def build_pyspice_source(preset_id: str, params: dict[str, float]) -> str | None:
    """Devuelve source Python o None si el preset no tiene plantilla SPICE."""
    if preset_id == "rc_series_charge":
        return _rc_charge(params)
    if preset_id == "rlc_series_step":
        return _rlc_step(params)
    if preset_id == "half_wave_rectifier":
        return _half_wave(params)
    return None


def _rc_charge(params: dict[str, float]) -> str:
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
    from PySpice.Unit import u_Ohm, u_F, u_V  # type: ignore

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


def _rlc_step(params: dict[str, float]) -> str:
    r = params.get("R", 10.0)
    inductance = params.get("L", 1e-3)
    c = params.get("C", 1e-6)
    v0 = params.get("V0", 5.0)
    return f'''# lablog-sim: preset=rlc_series_step backend=pyspice
# LABLOG_PARAMS_START
R = {r}  # ohm
L = {inductance}  # H
C = {c}  # F
V0 = {v0}  # V
# LABLOG_PARAMS_END

import numpy as np
import matplotlib.pyplot as plt

def _numpy_rlc(R, L, C, V0):
    wn = 1.0 / np.sqrt(L * C)
    zeta = R / 2.0 * np.sqrt(C / L)
    t_end = max(5e-3, 12 * np.pi / max(wn, 1.0))
    n = 800
    dt = t_end / n
    t = np.linspace(0, t_end, n + 1)
    q = np.zeros(n + 1)
    i = np.zeros(n + 1)
    for k in range(n):
        di = (V0 - R * i[k] - q[k] / C) / L
        i[k + 1] = i[k] + di * dt
        q[k + 1] = q[k] + i[k + 1] * dt
    return t, q / C, i, wn, zeta

try:
    from PySpice.Spice.Netlist import Circuit
    from PySpice.Unit import u_Ohm, u_H, u_F, u_V  # type: ignore

    circuit = Circuit("RLC series step")
    circuit.V("in", "n1", circuit.gnd, V0 @ u_V)
    circuit.R(1, "n1", "n2", R @ u_Ohm)
    circuit.L(1, "n2", "n3", L @ u_H)
    circuit.C(1, "n3", circuit.gnd, C @ u_F)
    simulator = circuit.simulator(temperature=25, nominal_temperature=25)
    wn = 1.0 / np.sqrt(L * C)
    t_end = max(5e-3, 12 * np.pi / max(wn, 1.0))
    analysis = simulator.transient(step_time=t_end / 800, end_time=t_end)
    t = np.array(analysis.time)
    v_c = np.array(analysis["n3"])
    # Corriente por la C: i ≈ C dv/dt (robusto entre versiones PySpice)
    i = C * np.gradient(v_c, t, edge_order=1)
    zeta = R / 2.0 * np.sqrt(C / L)
    backend = "pyspice"
except Exception as exc:  # noqa: BLE001
    print(f"PySpice no disponible ({{type(exc).__name__}}: {{exc}})")
    print("Instala: pip install 'jose-labarca-lablog[pyspice]'  (requiere ngspice)")
    t, v_c, i, wn, zeta = _numpy_rlc(R, L, C, V0)
    backend = "numpy_fallback"

fig, ax = plt.subplots(1, 2, figsize=(8, 3))
ax[0].plot(t * 1e3, v_c)
ax[0].set_xlabel("t [ms]")
ax[0].set_ylabel("v_C [V]")
ax[0].set_title(f"RLC · {{backend}}  ωn={{wn:.3g}}  ζ={{zeta:.3g}}")
ax[0].grid(True, alpha=0.3)
ax[1].plot(t * 1e3, i * 1e3)
ax[1].set_xlabel("t [ms]")
ax[1].set_ylabel("i [mA]")
ax[1].grid(True, alpha=0.3)
fig.tight_layout()
plt.show()
print(f"backend={{backend}}  ωn={{wn:.4g}}  ζ={{zeta:.4g}}")
'''


def _half_wave(params: dict[str, float]) -> str:
    vpeak = params.get("Vpeak", 10.0)
    f = params.get("f", 50.0)
    rload = params.get("Rload", 1000.0)
    c = params.get("C", 100e-6)
    return f'''# lablog-sim: preset=half_wave_rectifier backend=pyspice
# LABLOG_PARAMS_START
Vpeak = {vpeak}  # V
f = {f}  # Hz
Rload = {rload}  # ohm
C = {c}  # F
# LABLOG_PARAMS_END

import numpy as np
import matplotlib.pyplot as plt

def _numpy_hwr(Vpeak, f, Rload, C):
    periods = 4
    n = 1200
    t = np.linspace(0, periods / max(f, 1e-6), n)
    dt = t[1] - t[0]
    vs = Vpeak * np.sin(2 * np.pi * f * t)
    vo = np.zeros(n)
    for i in range(1, n):
        if vs[i] >= vo[i - 1]:
            vo[i] = vs[i]
        else:
            vo[i] = vo[i - 1] * np.exp(-dt / max(Rload * C, 1e-15))
    return t, vs, vo

try:
    from PySpice.Spice.Netlist import Circuit
    from PySpice.Unit import u_V, u_Hz, u_Ohm, u_F  # type: ignore

    # Fuente senoidal + diodo primitivo (D) + RC paralelo.
    # Evita subcircuitos externos que fallan sin librerías ngspice.
    circuit = Circuit("half-wave rectifier")
    circuit.SinusoidalVoltageSource(
        "in", "n_ac", circuit.gnd, amplitude=Vpeak @ u_V, frequency=f @ u_Hz
    )
    circuit.D(1, "n_ac", "n_out", model="IdealDiode")
    circuit.model("IdealDiode", "D", IS=1e-14, N=1)
    circuit.R("load", "n_out", circuit.gnd, Rload @ u_Ohm)
    circuit.C(1, "n_out", circuit.gnd, C @ u_F)
    simulator = circuit.simulator(temperature=25, nominal_temperature=25)
    t_end = 4.0 / max(f, 1e-6)
    analysis = simulator.transient(step_time=t_end / 1200, end_time=t_end)
    t = np.array(analysis.time)
    vs = np.array(analysis["n_ac"])
    vo = np.array(analysis["n_out"])
    backend = "pyspice"
except Exception as exc:  # noqa: BLE001
    print(f"PySpice no disponible ({{type(exc).__name__}}: {{exc}})")
    print("Instala: pip install 'jose-labarca-lablog[pyspice]'  (requiere ngspice)")
    t, vs, vo = _numpy_hwr(Vpeak, f, Rload, C)
    backend = "numpy_fallback"

vripple = float(np.max(vo[len(vo) // 2 :]) - np.min(vo[len(vo) // 2 :]))
plt.figure(figsize=(7, 3))
plt.plot(t * 1e3, vs, alpha=0.45, label="v_s")
plt.plot(t * 1e3, vo, label="v_o")
plt.xlabel("t [ms]")
plt.ylabel("V")
plt.title(f"Media onda · {{backend}}  ΔV≈{{vripple:.3g}} V")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.show()
print(f"backend={{backend}}  ripple p-p ≈ {{vripple:.4g}} V")
'''
