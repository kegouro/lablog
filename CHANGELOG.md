# Changelog

All notable changes to lablog are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/) and the project aims to follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-07-03

### Added
- **Full LaTeX mode**: pages containing `\documentclass` compile exactly as
  written (raw XeTeX via Tectonic — no injected preamble). The live preview
  hides the preamble, renders `\maketitle` as a title block and the `abstract`
  environment as a styled summary; a "LaTeX completo" badge marks the mode.
  Compile errors map 1:1 to editor lines and are clickable (jump-to-line).
- **Templates menu** in the toolbar: five XeTeX-ready starting points
  (scientific article, lab report, problem set, Beamer presentation, formal
  letter), each a complete compilable document.
- **Version diff** in the time-travel panel: a Diff toggle shows added/removed
  lines between any historical version and the present document.
- **Time-travel**: a "Historia" panel over the preview exposes the append-only
  event log — scrub any page through its entire history with a slider or event
  list, see the document rendered at that instant, and restore any version.
  Restore never deletes: it appends a new `document_replaced` (plus re-emitted
  `cell_executed` events so cell outputs survive the round-trip). Design was
  hardened by an adversarial review panel (index clamping, 409 on deleted pages,
  autosave flush before restore, out-of-order scrub guard).
- **Real PDF compilation** with Tectonic (XeTeX). The preview stays fast and is
  labelled "Aproximada"; a **Compilar PDF** button produces a faithful PDF.
  Executable cells render as code + output + figure. Compilation is async with a
  hard timeout, runs in an isolated temp directory, and caches output by document
  hash.
- **In-app engine install/update banner**: downloads a pinned, checksum-verified
  Tectonic binary once (then fully offline) and warms the common LaTeX packages.
  "Update" re-installs the pinned version — never a runtime fetch-latest.
- **Source-mapped compile errors**: TeX errors map back to the originating cell
  ("Celda N · línea M") via injected `% lablog-src` markers.
- **Native desktop app** (`lablog app`): a real OS window via pywebview, fully
  offline; the engine binds to `127.0.0.1` on an ephemeral port. Portable bundle
  via `scripts/package_desktop.sh` + `lablog.spec`.
- **Editor**: in-editor find & replace (Ctrl+F), undo/redo that survives
  programmatic insertions, bold/italic/inline-math shortcuts, Tab indent, and
  cursor-aware symbol/snippet insertion.
- **Structural LaTeX renderer**: sections, emphasis, lists, links and inline
  mathematics now render in the live preview (previously only `$math$`).
- Static-site export themed to the brand kit, deployed to GitHub Pages.
- `httpx` declared as an explicit test dependency; `hatchling` build backend so
  the package installs cleanly.

### Fixed
- Parser treated every `\begin{...}` as an executable cell, so `align`,
  `equation`, `itemize`, etc. rendered as code blocks. Now only a whitelist of
  languages are cells; all other environments are real LaTeX.
- `projector._move_cell` reordered the whole document; cells without a label
  collapsed onto a shared id. Both fixed with regression tests.
- Security: path-traversal validation for page ids and vault uploads, enforced
  Jupyter-kernel timeout, LaTeX-injection-safe export title, upload size limit,
  atomic vault metadata writes, contained cell-figure paths.
- Frontend: favorites persistence, attribute-context XSS in the editor overlay,
  vault upload/deletion recovery, dictation safety timeout, persisted lab/panel
  state, robust localStorage handling.
- Replaced `fancyvrb` with `fvextra` in the PDF preamble (`breaklines` is an
  `fvextra` option) and made the Tectonic cache-dir check platform-correct.

### Notes
- lablog is local-first and single-user. The PDF endpoint runs Tectonic without
  `--shell-escape` (no OS command execution) and must not be exposed publicly
  without rate limiting and isolation.

[Unreleased]: https://github.com/kegouro/lablog/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/kegouro/lablog/releases/tag/v0.1.0
