# Quality checkpoint — lablog

**Fecha:** 2026-07-10
**Tag estable:** `v0.2.1`
**Main:** PRs #12–#16 (diagramas, personalización, e2e, PySpice)

## Barra “premium senior” (estado)

| Área | Estado | Evidencia |
|------|--------|-----------|
| Event sourcing / soft-delete | ✅ | Writes guardan `409` si deleted |
| Autosave / races | ✅ | flush + inflight + discardPending + version PUT |
| Vault safety | ✅ | tokens aleatorios, force solo pending |
| Live preview + PDF científico | ✅ | KaTeX + circuitikz/tikz/physics |
| Diagram presets (12) | ✅ | expand / apply / re-sim / SPICE opcional |
| Highlight editor + TikZ color | ✅ | gutter + `color=` en `name=` |
| Personalización | ✅ | densidad, fuente editor, Nord, perfiles lab/paper/teaching, export JSON |
| Export notebook | ✅ | `GET …/export/ipynb` (markdown + code cells) |
| E2E Playwright | ✅ | smoke preferencias en CI |
| PySpice | 🟡 | extra opcional + fallback numpy |
| PyPI trusted publish | ⚠️ | config usuario |

## Perfiles de UI

| Perfil | Uso |
|--------|-----|
| Laboratorio | compacto, mono, lab mode, acento esmeralda |
| Paper | serif, moka, menos motion |
| Docencia | sans grande, Nord, azul |

Atajo: **⌘/Ctrl+K** → «Perfil: …»

## Export

| Formato | Ruta |
|--------|------|
| tex / txt / pdf / docx / canva / site | menú Exportar |
| **ipynb** | menú Exportar → Notebook Jupyter |

## Comandos

```bash
pytest -q
ruff check src tests
mypy -p lablog
cd ui && npm run build && npm test && npm run test:e2e
lablog diagrams
```

## Siguiente nivel (no bloqueante)

- Más backends PySpice (RLC, half-wave netlist real)
- Perfiles de layout de paneles
- Atajos de teclado configurables
- PyPI OIDC verde
