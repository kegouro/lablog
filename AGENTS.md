# Agent Instructions — lablog

## Stack
- Backend: Python 3.11+, FastAPI, Pydantic, event sourcing (JSONL), Jupyter client.
- Frontend: Vite 8, React 19, TypeScript, Tailwind CSS v4, shadcn/ui, Zustand.
- Voice: browser SpeechRecognition + faster-whisper local pipeline.

## Package Manager
- Python: `uv` (`uv sync --extra dev`, `uv lock`).
- Node: `npm` (`npm install`, `npm run dev`, `npm run build`).

## Dev Commands
```bash
# Backend
source .venv/bin/activate
uvicorn lablog.api:app --host 127.0.0.1 --port 8000 --reload

# Frontend
cd ui
npm run dev

# Full validation
pytest -q
ruff check src tests
mypy -p lablog
cd ui && npm run build && npm run lint
```

## Environment
Copy `.env.example` to `.env`. Key vars:
- `LABLOG_DATA_DIR` — defaults to `~/.lablog`.
- `LABLOG_HOST` / `LABLOG_PORT` — API bind address.
- `LABLOG_CORS_ORIGINS` — comma-separated origins.

Never commit secrets or local data paths.

## File-Scoped Commands
| Task | Command |
|------|---------|
| Python lint | `ruff check src/lablog/<file>.py` |
| Python typecheck | `mypy -p lablog` (module-level) |
| Python test file | `pytest tests/test_<name>.py -q` |
| TS typecheck | `cd ui && npx tsc --noEmit` |
| TS lint | `cd ui && npx eslint src/<file>.tsx` |

## Key Conventions
- Backend uses event sourcing: append-only events in `src/lablog/events.py`, projection in `src/lablog/projector.py`.
- Never mutate projected AST directly from the API; create an event and re-project.
- All configurable paths go through `src/lablog/config.py`.
- Frontend API layer lives in `ui/src/lib/api.ts`; mirror backend response shapes there.
- UI state uses `ui/src/stores/app-store.ts`; keep API calls out of components when possible.

## Commit Attribution
AI commits MUST include:
```
Co-Authored-By: Kimi Code <noreply@example.com>
```
