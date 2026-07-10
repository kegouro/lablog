# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] - 2026-07-10

### Fixed

- Figure isolation: each cell run writes unique `{token}_fig_N.png` files (no shared `fig_0` overwrite or stale glob).
- Autosave races: flush awaits in-flight PUT; debounce cancelled + draft flushed on unmount/page change; lab mode switch flushes editor first.
- Ghost `"vault"` page no longer appears in page lists (vault audit stream excluded).
- Lab `markdown` / `latex` cells survive editor autosave round-trip (`CODE_ENVIRONMENTS`).
- Cells panel no longer offers Julia (engine is Python-only).
- Export/PDF compile flush the editor buffer before reading the event log.
- Static HTML export: `\href`/`\url` only allow `http(s)`/`mailto` and escape attributes (XSS).
- Voice dictation uses `/voice` intent pipeline instead of raw latex append.
- Lab canvas awaits `insertCell` so failed inserts do not leave phantom cells.
- Post-v0.2.0 critical client/data fixes (204 empty body, cell runtime merge, figures path, Canva escape, cells latex sync).

## [0.2.0] - 2026-07-10

### Added

- CQRS-lite backend: `commands` (writes) and `projections` (reads); HTTP adapter thinner.
- Domain events for cell failures (`execution_failed`) with cell `status` on the AST.
- Atomic JSONL append (`fsync`) and tolerance for truncated last lines.
- Dedicated single-worker compute pool for Jupyter execution off the event loop.
- PDF line-aware errors: FSM log parser, `editor_line` mapping, gutter highlight on jump.
- LaTeX autocomplete overlay (commands, environments, symbols via `/api/v1/suggest`).
- Physics/lab templates SSOT (`src/lablog/templates.py`) + `lablog new --template=...`.
- Multi-page includes at compile time: `\input{page:<uuid>}` with cycle/depth guards.
- Error boundaries keyed by page version; speech dictation FSM; structured `ApiError`.
- Smoke script `scripts/smoke_install.sh` and `docs/QUICKSTART.md`.

### Changed

- Frontend no longer parses LaTeX; preview uses backend AST + `AstRenderer`.
- Kernel failures return `error_code: KERNEL_DEAD` for actionable UI.
- Renamed PyPI distribution from `lablog` to `jose-labarca-lablog` (0.1.x unreleased note).

### Fixed

- Broken restore/export helpers after command extraction (missing projector imports).
- XSS sinks in parameter overlay and lab markdown preview (React nodes / no raw user HTML).

## [0.1.0] - 2026-07-05

### Added

- Initial public release of lablog: a live LaTeX laboratory notebook.
- Event-sourced JSONL persistence with deterministic projection.
- Structural LaTeX editor with parameter overlay, find & replace, and undo/redo.
- Live KaTeX preview with support for common display environments.
- Executable Python cells backed by Jupyter kernels, with figure capture and timeouts.
- Voice dictation via browser SpeechRecognition.
- Vault for attachments with preview and time-locked deletion.
- Static site export and GitHub Pages deployment.
- Native desktop app via pywebview and PyInstaller packaging.
- Production-ready health endpoint that reports Jupyter kernel readiness.
- GitHub Actions release workflow that publishes `jose-labarca-lablog` to PyPI on tags.
- Regression tests for voice dictation, mixed-option code cells, AST preview, and cell error display.

### Fixed

- Voice dictation no longer enters an infinite append loop after stopping.
- LaTeX parser now handles cells with and without `[options]` in the same document.
- Code engine is now thread-safe and surfaces kernel startup failures as actionable 503 errors.
- Frontend Zustand subscriptions use selectors, eliminating mount-time re-fetch loops.
- Markdown preview in lab mode escapes HTML before rendering inline math.

### Changed

- Improved live preview: renders AST directly where possible and shows per-block KaTeX errors.
- Raised backend test coverage threshold to 80%.

[Unreleased]: https://github.com/kegouro/lablog/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/kegouro/lablog/releases/tag/v0.2.1
[0.2.0]: https://github.com/kegouro/lablog/releases/tag/v0.2.0
[0.1.0]: https://github.com/kegouro/lablog/releases/tag/v0.1.0
