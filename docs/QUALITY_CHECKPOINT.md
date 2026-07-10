# Quality checkpoint — lablog (diagram catalog maturity)

**Fecha:** 2026-07-10
**Tag estable:** `v0.2.1`
**Main:** incluye PRs #12–#14 (presets + re-apply + highlight + catálogo)

## Barra “premium senior” (estado)

| Área | Estado | Evidencia |
|------|--------|-----------|
| Event sourcing / soft-delete | ✅ | Writes guardan `409` si deleted; tests prod hardening |
| Autosave / races | ✅ | flush + inflight + discardPending + version PUT |
| Vault safety | ✅ | tokens aleatorios, force solo pending |
| LaTeX parse cells | ✅ | CODE_ENV only + balanced + escape `\end` |
| Live preview math | ✅ | ~190 símbolos, matrices/align, macros physics |
| PDF scientific packages | ✅ | ams, booktabs, siunitx, physics, braket, tikz, **circuitikz** |
| Stress fixtures | ✅ | `tests/fixtures/latex/*` |
| Diagram presets → Jupyter | ✅ | **12 presets**, expand/apply API, Insert/+Sim, re-apply sliders |
| Re-apply sin `{{}}` | ✅ | `% lablog-param` + `POST /diagrams/apply` |
| Dual highlight (editor) | ✅ | `resolve_highlight_lines` + focus gutter + leyenda nodo |
| Dual highlight (canvas TikZ PDF) | 🔜 | recolor `name=` en recompilación |
| Catálogo UI | ✅ | categorías + búsqueda |
| PySpice / netlist mágico | 🔜 | docs only |
| E2E browser | 🔜 | sin Playwright en CI |
| PyPI trusted publish | ⚠️ | config usuario |

## Catálogo de presets (12)

| ID | Categoría | Sim |
|----|-----------|-----|
| `rc_series_charge` | circuitos | ODE carga |
| `voltage_divider` | circuitos | DC |
| `rlc_series_step` | circuitos | ODE 2º |
| `wheatstone` | circuitos | DC puente |
| `half_wave_rectifier` | circuitos | diodo+RC |
| `rc_lowpass` | circuitos | Bode |
| `noninverting_opamp` | circuitos | G ideal |
| `mass_spring_damper` | mecanica | ODE |
| `second_order_step` | control | ODE |
| `pi_controller` | control | lazo cerrado |
| `thin_lens` | optica | 1/f, m |
| `qed_moller` | particulas | viz |

## Comandos de verificación

```bash
pytest tests/test_diagrams.py -q --no-cov
pytest -q
ruff check src tests
mypy -p lablog
cd ui && npm run build && npm run lint
lablog diagrams
lablog diagrams --expand rc_lowpass
lablog diagrams --sim noninverting_opamp
```

## Punto claro de parada

El camino **preset → parámetros → re-sim Jupyter** está maduro para uso de lab local.
Siguiente nivel no bloqueante: color en PDF TikZ, PySpice, e2e Playwright, PyPI verde.
