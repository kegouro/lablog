# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- GitHub Actions release workflow that publishes `lablog` to PyPI on tags.
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

[Unreleased]: https://github.com/kegouro/lablog/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/kegouro/lablog/releases/tag/v0.1.0
