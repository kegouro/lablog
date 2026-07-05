# lablog v0.1.0 Release Notes

**Release date:** 2026-07-03
**Tag:** [`v0.1.0`](https://github.com/kegouro/lablog/releases/tag/v0.1.0)

## Highlights

lablog is a live LaTeX laboratory notebook for working scientists. v0.1.0 ships the core local-first experience: a real-time editor, PDF compilation, executable code cells, time-travel history, and a secure vault.

## What's new

- **Live LaTeX editor** with syntax-aware overlays, find/replace, undo/redo, and keyboard shortcuts.
- **Real PDF compilation** via Tectonic (XeTeX), with source-mapped errors and jump-to-line.
- **Executable cells** for Python, Sage, Julia, R, Octave, Bash and more.
- **Time-travel** over the append-only event log, with a version diff view.
- **Templates menu** for articles, lab reports, problem sets, Beamer decks and letters.
- **Secure vault** for file uploads with deletion phrases, preview and download.
- **Voice dictation** support (browser API + optional local Whisper).
- **Native desktop app** via `lablog app` using pywebview.
- **GitHub Pages** static-site export.

## Quality & automation

- 73 backend tests (pytest) with **71% coverage** and a 60% threshold.
- 11 frontend tests with Vitest, React Testing Library and jsdom.
- GitHub Actions CI runs `ruff`, `mypy`, `pytest`, `oxlint`, build and frontend tests.
- Pre-commit hooks for `ruff`, `mypy`, `oxlint` and frontend tests.

## Install

```bash
pip install lablog
lablog --help
```

Or run locally with `uv`:

```bash
uv sync --extra dev
uv run lablog serve
```

## Known limitations

- Single-user, local-first by design.
- PDF compilation requires the Tectonic engine to be installed via the in-app banner.
- The PDF endpoint must not be exposed publicly without rate limiting and isolation.
