# Contributing to lablog

Thanks for helping improve a research-grade lab notebook. This document keeps
contributions small, reviewable, and aligned with the architecture.

## Development setup

```bash
# Python
uv sync --extra dev
source .venv/bin/activate

# UI
cd ui && npm install
```

Run backend: `uvicorn lablog.api:app --host 127.0.0.1 --port 8000 --reload`
Run frontend: `cd ui && npm run dev`

## Quality bar (required before PR)

```bash
pytest -q
ruff check src tests
mypy -p lablog
cd ui && npm run build && npm run lint && npm test
# optional local e2e
cd ui && npm run test:e2e:install && npm run test:e2e
```

Coverage floor is **≥80%** (enforced by pytest).

## Architecture rules

1. **Event sourcing**: never mutate projected AST from the API. Append an event and re-project.
2. **Config paths**: go through `src/lablog/config.py` only.
3. **API shapes**: mirror backend responses in `ui/src/lib/api.ts`.
4. **UI state**: Zustand store; keep network I/O out of leaf components when possible.
5. **Diagrams**: add presets in `src/lablog/diagrams/catalog.py`; expand/clamp in `expand.py`; optional SPICE in `pyspice_sim.py`.

## Commit style

Use conventional commits (`feat`, `fix`, `docs`, `test`, `chore`, …).
AI-assisted commits must include:

```
Co-Authored-By: Kimi Code <noreply@example.com>
```

(or your tool’s equivalent attribution).

## Pull requests

- Prefer **small, focused PRs** with a short test plan.
- Update `CHANGELOG.md` under `[Unreleased]` for user-visible changes.
- Do not commit secrets, local data under `~/.lablog`, or `ui/test-results/`.

## Diagram presets

When adding a preset:

1. TikZ/Circuitikz template that compiles with the PDF preamble.
2. Param specs with min/max, scale, description, and highlight.
3. Optional sim template with `LABLOG_PARAMS_START/END`.
4. Tests in `tests/test_diagrams.py`.

## Security reports

See [SECURITY.md](SECURITY.md). Please do not open public issues for unfixed vulns.

## License

By contributing you agree that your contributions are licensed under the MIT License.
