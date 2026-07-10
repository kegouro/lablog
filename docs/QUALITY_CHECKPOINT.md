# Quality checkpoint — lablog (post v0.2.1 + diagram presets)

**Fecha:** 2026-07-10
**Rama de trabajo:** `kegouro/feat/diagram-presets-and-polish` (PR #12)
**Tag en main:** `v0.2.1`

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
| Diagram presets → Jupyter | 🟡 MVP | 4 presets, API, UI Insert/+Sim, sliders+rango+L# |
| Dual highlight TikZ canvas | 🔜 | Solo gutter/line por ahora |
| PySpice / netlist mágico | 🔜 | docs only |
| Multi-tab always-on version | 🟡 | UI envía version; clientes CLI no |
| E2E browser | 🔜 | sin Playwright en CI |
| PyPI trusted publish | ⚠️ | config usuario |

## Comandos de verificación

```bash
pytest -q                 # ≥196 passed, cov ≥80%
ruff check src tests
mypy -p lablog
cd ui && npm test && npm run build
lablog diagrams
lablog diagrams --expand rc_series_charge
lablog diagrams --sim rc_series_charge
```

## Punto claro de parada

Con **PR #12 mergeado** se considera un checkpoint de calidad **sólido para uso local/lab**:

- No hay bugs críticos abiertos en `bugs.md` de la caza previa.
- El camino “dibujar circuito parametrizado → celda de simulación” existe de punta a punta.
- Preview y PDF están alineados con un stack de física real.

Siguiente nivel premium (no bloqueante): highlight en canvas TikZ, más presets, e2e Playwright, PyPI verde.
