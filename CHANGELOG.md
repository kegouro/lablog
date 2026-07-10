# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-07-10

### Added

- **Diagram catalog (12 presets)**: RC, voltage divider, RLC, Wheatstone, half-wave rectifier, RC low-pass, noninverting op-amp, mass-spring-damper, second-order plant, PI controller, thin lens, Feynman Møller.
- **Re-apply diagrams** from Parameters (`POST /diagrams/apply`, `% lablog-param` markers).
- **Dual highlight**: editor line jump + TikZ/Circuitikz `color=` on focused `name=` components.
- **Optional PySpice** extra (`jose-labarca-lablog[pyspice]`) with RC / RLC / half-wave cells and numpy fallback.
- **Personalization**: density, editor font, Nord palette, reduced motion, lab/paper/teaching profiles, export/import JSON.
- **Configurable shortcuts** (mod+s save, panel toggles, lab mode, new page).
- **Export Jupyter notebook** (`GET …/export/ipynb`).
- Playwright smoke e2e in CI; quality checkpoint docs.

### Changed

- Diagram presets expand/simulate API accepts `highlight_param` and `prefer_pyspice`.
- Command palette opens panels, preference profiles, and preference export.

### Fixed

- Templates menu no longer crashes when `/templates` returns a non-array payload.

## [0.2.1] - 2026-07-10

### Fixed

- Soft-delete: all write routes reject deleted pages (`409`); `list_cells` 404s.
- Autosave: in-flight flush, unmount draft save, discardPending for parameter freeze, re-queue on failure, optional `version` → `409 VERSION_CONFLICT`.
- Page-switch races: ignore stale `getPage` / `listCells` responses.
- LaTeX parse: code envs only (no `document` swallow); balanced cell matching; escape `\end{` in sources on serialize.
- Vault: random deletion tokens, force-delete only when pending, unique upload temps, meta lock.
- Event store per-page lock; restore keeps error cell status; safe download filenames; 5MB latex cap; safe cell_id.
- Live preview: memoized AST renderer, inline math in prose text nodes, lazy figures.
- Figure isolation per run; ghost vault page excluded; markdown/latex cell round-trip; Julia UI removed; export/PDF flush; href XSS; voice `/voice`; lab await insert.
- Post-v0.2.0 client fixes (204 body, cell runtime merge, figures path, Canva escape, cells latex sync).

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

[Unreleased]: https://github.com/kegouro/lablog/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/kegouro/lablog/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/kegouro/lablog/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/kegouro/lablog/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/kegouro/lablog/releases/tag/v0.1.0
