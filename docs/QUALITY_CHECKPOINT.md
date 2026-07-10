# Quality checkpoint — lablog v0.3.0

**Fecha:** 2026-07-10
**Release:** `v0.3.0` (`jose-labarca-lablog`)

## Barra “obra maestra OSS”

| Área | Estado |
|------|--------|
| Event sourcing + soft-delete | ✅ |
| Autosave / version conflicts | ✅ |
| Vault path safety | ✅ |
| Scientific LaTeX live + PDF | ✅ |
| Diagram workbench (12 presets) | ✅ |
| Re-apply + dual highlight | ✅ |
| Optional PySpice + numpy fallback | ✅ |
| Personalization + profiles + shortcuts | ✅ |
| Export tex/pdf/docx/site/**ipynb** | ✅ |
| Playwright e2e smoke in CI | ✅ |
| CONTRIBUTING / SECURITY / CoC | ✅ |
| CITATION.cff + Keep a Changelog | ✅ |
| PyPI trusted publish | ⚠️ maintainer PyPI config |

## Verification

```bash
pytest -q
ruff check src tests
mypy -p lablog
cd ui && npm run build && npm test && npm run test:e2e
lablog diagrams
python -c "import lablog; print(lablog.__version__)"
```
