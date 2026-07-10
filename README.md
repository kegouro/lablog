<div align="center">

<img src="docs/assets/banner.png" alt="lablog" width="640" />

<br/>

<h1 style="margin-top: 0;">lablog</h1>

<p><em>A live LaTeX laboratory notebook for working scientists.</em></p>

<p>
  <a href="https://pypi.org/project/jose-labarca-lablog/"><img alt="version" src="https://img.shields.io/badge/version-v0.3.0-1C1C1E?style=flat-square&labelColor=1C1C1E&color=48484A" /></a>
  <a href="https://github.com/kegouro/lablog/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/kegouro/lablog/ci.yml?branch=main&style=flat-square&labelColor=1C1C1E&color=48484A&label=CI" /></a>
  <a href="https://github.com/kegouro/lablog/actions/workflows/pages.yml"><img alt="Pages" src="https://img.shields.io/github/actions/workflow/status/kegouro/lablog/pages.yml?branch=main&style=flat-square&labelColor=1C1C1E&color=48484A&label=Pages" /></a>
  <a href="#testing--quality"><img alt="tests" src="https://img.shields.io/github/actions/workflow/status/kegouro/lablog/ci.yml?branch=main&style=flat-square&labelColor=1C1C1E&color=48484A&label=tests" /></a>
  <a href="#testing--quality"><img alt="coverage" src="https://img.shields.io/badge/coverage-%E2%89%A580%25-1C1C1E?style=flat-square&labelColor=1C1C1E&color=48484A" /></a>
  <a href="#stack"><img alt="python" src="https://img.shields.io/badge/python-3.11+-1C1C1E?style=flat-square&labelColor=1C1C1E&color=A1A1A6" /></a>
  <a href="#stack"><img alt="react" src="https://img.shields.io/badge/react-19-1C1C1E?style=flat-square&labelColor=1C1C1E&color=A1A1A6" /></a>
  <a href="#license"><img alt="license" src="https://img.shields.io/badge/license-MIT-1C1C1E?style=flat-square&labelColor=1C1C1E&color=F2F2F7" /></a>
</p>

<p>
  <a href="https://kegouro.github.io/lablog/"><img alt="Live preview" src="https://img.shields.io/badge/live%20preview-kegouro.github.io%2Flablog-1C1C1E?style=for-the-badge&labelColor=1C1C1E&color=48484A" /></a>
</p>

<sub>Part of the <strong>Pharos Project</strong> &middot; José Labarca Baeza &middot; USM, Valparaíso</sub>

</div>

---

<table>
  <tr>
    <td><a href="#about"><strong>About</strong></a></td>
    <td><a href="#features"><strong>Features</strong></a></td>
    <td><a href="#architecture"><strong>Architecture</strong></a></td>
    <td><a href="#installation"><strong>Installation</strong></a></td>
    <td><a href="#quick-start"><strong>Quick start</strong></a></td>
    <td><a href="#configuration"><strong>Configuration</strong></a></td>
  </tr>
  <tr>
    <td><a href="#editor-experience"><strong>Editor</strong></a></td>
    <td><a href="#security-model"><strong>Security</strong></a></td>
    <td><a href="#testing--quality"><strong>Testing</strong></a></td>
    <td><a href="#publishing-to-github-pages"><strong>Publishing</strong></a></td>
    <td><a href="#roadmap"><strong>Roadmap</strong></a></td>
    <td><a href="#license"><strong>License</strong></a></td>
  </tr>
</table>

---

## About

> **lablog** is a research-grade notebook that lives where the experiment happens.
> It pairs a structural LaTeX editor with live preview, executable cells, voice dictation
> and an immutable, event-sourced history so that the record of an investigation can be
> reconstructed exactly as it unfolded.

Unlike a typesetting tool used after the experiment, `lablog` is meant to run **while the
work is in progress** &mdash; gloves on, instrument in front, hands occupied. It is built on
the premise that the act of writing the paper should not be separated from the act of
producing the data.

<table>
  <thead>
    <tr><th align="left">Tool</th><th align="left">When you use it</th></tr>
  </thead>
  <tbody>
    <tr><td>Overleaf</td><td>After the experiment, when the manuscript is being prepared.</td></tr>
    <tr><td>TeXstudio / TeXmacs</td><td>For traditional LaTeX editing on a desktop.</td></tr>
    <tr><td><strong>lablog</strong></td><td>During the experiment: to dictate, execute and preserve as it happens.</td></tr>
  </tbody>
</table>

---

## Features

<table>
  <thead>
    <tr>
      <th align="left">Module</th>
      <th align="left">Capability</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Structural LaTeX renderer</strong></td>
      <td>Sections, emphasis, lists, hyperlinks, and inline mathematics flow within paragraphs. KaTeX powers display environments (<code>align</code>, <code>equation</code>, <code>gather</code>, <code>cases</code>, <code>pmatrix</code>) with automatic equation numbering.</td>
    </tr>
    <tr>
      <td><strong>Editor</strong></td>
      <td>Line gutter, parameter overlay, auto-save, <kbd>Ctrl</kbd>+<kbd>F</kbd> find &amp; replace with hit counter, <kbd>Ctrl</kbd>+<kbd>Z</kbd> / <kbd>Ctrl</kbd>+<kbd>Y</kbd> undo / redo, <kbd>Ctrl</kbd>+<kbd>B</kbd>/<kbd>I</kbd>/<kbd>E</kbd> bold / italic / math, smart delimiter wrapping, snippet and symbol insertion at cursor.</td>
    </tr>
    <tr>
      <td><strong>Voice dictation</strong></td>
      <td>Browser <code>SpeechRecognition</code> with an intent detector and local Whisper pipeline. A session safety timeout prevents the recogniser from hanging if the API stalls.</td>
    </tr>
    <tr>
      <td><strong>Executable cells</strong></td>
      <td>Write <code>\begin{python}...\end{python}</code> and run real Jupyter kernels in place. Stdout, results and figures are captured back into the document; the kernel is interrupted on timeout to prevent runaway code.</td>
    </tr>
    <tr>
      <td><strong>Per-page vault</strong></td>
      <td>Attach images, CSV, PDF, DOCX, audio and scripts; preview them without leaving the notebook. Metadata is written atomically; uploads are sanitised against path traversal and bounded by an explicit size limit.</td>
    </tr>
    <tr>
      <td><strong>Event-sourced history</strong></td>
      <td>Every edit, execution and attachment is appended as an immutable JSONL event. The current state is a deterministic projection &mdash; reproducible, auditable, and the foundation for future time-travel UI.</td>
    </tr>
    <tr>
      <td><strong>Project grouping</strong></td>
      <td>Pages cluster into projects directly from the sidebar; renaming, deletion and reorganisation are first-class operations.</td>
    </tr>
    <tr>
      <td><strong>Export</strong></td>
      <td>LaTeX (<code>.tex</code>), plain text, HTML, PDF and DOCX via <em>pandoc</em>; <strong>Jupyter notebook (<code>.ipynb</code>)</strong>; static site for GitHub Pages; Canva-ready HTML. Titles are escaped to prevent LaTeX injection.</td>
    </tr>
    <tr>
      <td><strong>Diagram workbench</strong></td>
      <td>Twelve parameterized presets (circuits, control, mechanics, optics, Feynman). Dial values, re-apply TikZ, optional <strong>PySpice</strong> cells with numpy fallback, dual highlight (editor line + colored <code>circuitikz</code> nodes).</td>
    </tr>
    <tr>
      <td><strong>Personalization</strong></td>
      <td>Density, editor font, Nord palette, reduced motion, lab/paper/teaching profiles, exportable preferences JSON, configurable keyboard shortcuts.</td>
    </tr>
  </tbody>
</table>

---

## Architecture

```mermaid
%%{init: { 'theme': 'base', 'themeVariables': { 'primaryColor':'#1C1C1E', 'primaryTextColor':'#F2F2F7', 'primaryBorderColor':'#48484A', 'lineColor':'#A1A1A6', 'secondaryColor':'#48484A', 'tertiaryColor':'#1C1C1E' }}}%%
flowchart LR
    subgraph UI[lablog UI]
        direction TB
        React["React 19 + Vite"]
        Tailwind["Tailwind CSS v4"]
        Zustand["Zustand store"]
        KaTeX["KaTeX renderer"]
    end

    subgraph Engine[lablog Engine]
        direction TB
        FastAPI["FastAPI"]
        Events["Event Store (JSONL)"]
        Projector["Projector"]
        AST["LaTeX AST"]
        Jupyter["Jupyter / Python"]
        Vault["Vault"]
    end

    User((Researcher))
    User --> UI
    UI <-->|HTTP| Engine
    Engine -->|export| Site["Static site"]
    Site -->|GitHub Actions| Pages["GitHub Pages"]
```

The engine is decoupled from the interface: it can be driven from the CLI, embedded in
tests, or replaced by another front-end. The projector reconstructs the current
`DocumentNode` from the event log; the renderer reduces that tree to HTML.

<details>
<summary><strong>Module map</strong></summary>

<br/>

| Path | Responsibility |
| :--- | :--- |
| [`src/lablog/api.py`](src/lablog/api.py) | FastAPI routes; export pipeline; vault uploads. |
| [`src/lablog/event_store.py`](src/lablog/event_store.py) | Append-only JSONL log; path-validated page identifiers. |
| [`src/lablog/events.py`](src/lablog/events.py) | Event schema and constructors. |
| [`src/lablog/projector.py`](src/lablog/projector.py) | Pure folding of events into a `DocumentNode`. |
| [`src/lablog/latex_ast.py`](src/lablog/latex_ast.py) | Tokeniser; environment whitelist; round-trip serialiser. |
| [`src/lablog/code_engine.py`](src/lablog/code_engine.py) | Jupyter kernel manager with enforced timeout. |
| [`src/lablog/vault.py`](src/lablog/vault.py) | Attachment store with atomic metadata and time-locked deletion. |
| [`src/lablog/exporter.py`](src/lablog/exporter.py) | Static site exporter for GitHub Pages. |
| [`ui/src/lib/latex-render.ts`](ui/src/lib/latex-render.ts) | Structural renderer (prose &times; mathematics). |
| [`ui/src/components/editor/latex-editor.tsx`](ui/src/components/editor/latex-editor.tsx) | Editor, find &amp; replace, undo / redo, shortcuts. |
| [`ui/src/components/preview/latex-preview.tsx`](ui/src/components/preview/latex-preview.tsx) | Node coalescing &amp; live preview. |
| [`ui/src/stores/app-store.ts`](ui/src/stores/app-store.ts) | Single source of truth on the client; persistent state. |

</details>

---

## Stack

<table>
  <thead>
    <tr>
      <th align="left">Layer</th>
      <th align="left">Stack</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>Engine</td><td>Python 3.11+, FastAPI, Pydantic, Jupyter Client, faster-whisper.</td></tr>
    <tr><td>Persistence</td><td>JSONL event log; atomic metadata writes; deterministic projection.</td></tr>
    <tr><td>Interface</td><td>React 19, TypeScript, Vite 8, Tailwind CSS v4, Zustand, shadcn/ui, Radix.</td></tr>
    <tr><td>Mathematics</td><td>KaTeX with automatic numbering for display environments.</td></tr>
    <tr><td>Tooling</td><td>uv (Python), npm (Node), Ruff, Mypy (strict), oxlint, pytest, GitHub Actions.</td></tr>
  </tbody>
</table>

---

## Installation

### From PyPI (recommended)

```bash
pip install jose-labarca-lablog
lablog serve
```

The wheel bundles the compiled UI, so a simple `pip install` is enough to run the
application. The optional `desktop` extra adds the native window:

```bash
pip install jose-labarca-lablog[desktop]
lablog app
```

### From source

> **Prerequisites.** Python 3.11 or newer, Node 22, [`uv`](https://docs.astral.sh/uv/),
> and `npm`. Optional: `pandoc` and `xelatex` (or `pdflatex`) for PDF and DOCX export.

```bash
git clone https://github.com/kegouro/lablog.git
cd lablog
uv sync --extra dev
source .venv/bin/activate
cp .env.example .env

cd ui && npm install && cd ..
```

Optional extras (the core install stays lean):

| Extra | Command | Adds |
| :--- | :--- | :--- |
| Desktop app | `uv sync --extra desktop` | `pywebview` &mdash; native window via `lablog app`. |
| Offline voice | `uv sync --extra voice` | local Whisper model + audio capture (several hundred MB). |

---

## Quick start

### Run the engine

```bash
source .venv/bin/activate
uvicorn lablog.api:app --host 127.0.0.1 --port 8000 --reload
```

### Run the interface

```bash
cd ui
npm run dev
```

| Endpoint | URL |
| :--- | :--- |
| User interface | <http://127.0.0.1:5173> |
| API | <http://127.0.0.1:8000/api/v1> |
| Liveness probe | <http://127.0.0.1:8000/api/v1/health> |

For a production build served by the engine itself:

```bash
cd ui && npm run build && cd ..
uvicorn lablog.api:app --host 127.0.0.1 --port 8000
```

The interface is then served statically from `ui/dist` by FastAPI.

---

## Desktop application

`lablog` runs as a **native desktop window** &mdash; no browser, no internet. The engine
binds to `127.0.0.1` on an ephemeral port inside the process and the interface opens in
the operating system's own webview (WKWebView on macOS, WebView2 on Windows, WebKitGTK on
Linux). Every asset &mdash; JavaScript, CSS, fonts and the KaTeX renderer &mdash; is
bundled, so the application is **fully offline**.

```bash
uv sync --extra desktop      # installs pywebview
cd ui && npm run build && cd ..
lablog app                   # opens the native window
```

> **Offline note.** The core notebook (editor, live preview, executable cells, vault) is
> entirely offline. The in-browser dictation button relies on the platform speech API and
> degrades gracefully when offline; for offline dictation install the local Whisper model
> with `uv sync --extra voice`.

### Packaging a portable bundle

To ship a self-contained folder that runs without any Python install:

```bash
./scripts/package_desktop.sh      # builds the UI, then PyInstaller
# → dist/lablog/  (zip it and run dist/lablog/lablog)
```

The bundle is described by [`lablog.spec`](lablog.spec). It includes `ui/dist` and the
Jupyter kernel used for cell execution, and excludes the heavy voice model by default.
The kernel and `pyzmq` are discovered dynamically, so on a fresh platform the spec's
`collect_all` lists may need a small adjustment &mdash; treat it as a verified starting
point rather than a one-click cross-platform installer.

---

## Real PDF compilation

The live preview is fast but **approximate** &mdash; it renders the common subset of
LaTeX with KaTeX and a focused HTML renderer. For a faithful document, lablog compiles
the page to a **real PDF** with [Tectonic](https://tectonic-typesetting.github.io/)
(a self-contained XeTeX engine). The first compile downloads and caches the required
TeX packages once; **every subsequent compile is fully offline**.

- The **Compilar PDF** button lives in the preview header; the preview itself is
  labelled **"Aproximada"** so the distinction is explicit.
- Executable `\begin{python}` cells are rendered into the PDF as **code + output +
  figure** (code and output via `fancyvrb`, figures via `\includegraphics`).
- Compilation runs asynchronously with a hard timeout; runaway documents return `504`
  instead of hanging the engine. Output is cached by document hash, so recompiling an
  unchanged page is instant.
- When compilation fails, the error panel maps TeX errors back to the source via
  injected `% lablog-src` markers, showing **"Celda N · línea M: message"** rather than
  a meaningless line in the generated `.tex`.

> **Security.** Tectonic runs **without `--shell-escape`** &mdash; LaTeX cannot execute
> operating-system commands. lablog is local and single-user; the compile endpoint
> assumes you are compiling your own content and must not be exposed publicly without
> adding rate limiting and isolation.

> **Engine note.** If `tectonic` is already on your `PATH` it is used directly.
> Otherwise the preview shows an **install banner** that downloads the pinned,
> checksum-verified binary once to `LABLOG_DATA_DIR/bin/` and warms the common
> packages (offline afterwards). When a managed binary falls behind the version
> this app pins, the banner offers a verified re-install &mdash; it never fetches
> "latest" at runtime, preserving the checksum trust chain.

---

## Configuration

All configurable paths and addresses are surfaced through environment variables.
See [`.env.example`](.env.example) for the full list.

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `LABLOG_DATA_DIR` | `~/.lablog` | Root for events, vault, figures and exported site. |
| `LABLOG_HOST` | `127.0.0.1` | Bind address for the API. |
| `LABLOG_PORT` | `8000` | Port for the API. |
| `LABLOG_CORS_ORIGINS` | `http://localhost:5173, http://127.0.0.1:5173` | Comma-separated CORS origins. |
| `LABLOG_SITE_DIR` | `${data_dir}/site` | Destination of the static site exporter. |

> **Note.** `lablog` never reads secrets from the data directory and never embeds them
> in exports. Treat `LABLOG_DATA_DIR` as personal notes; commit only what you intend to
> publish.

---

## Editor experience

| Action | Shortcut |
| :--- | :---: |
| Find &amp; replace (in-editor) | <kbd>Ctrl</kbd>+<kbd>F</kbd> &middot; <kbd>Ctrl</kbd>+<kbd>H</kbd> |
| Next / previous match | <kbd>Enter</kbd> &middot; <kbd>Shift</kbd>+<kbd>Enter</kbd> |
| Undo / redo | <kbd>Ctrl</kbd>+<kbd>Z</kbd> &middot; <kbd>Ctrl</kbd>+<kbd>Y</kbd> |
| Bold &middot; Italic &middot; Inline math | <kbd>Ctrl</kbd>+<kbd>B</kbd> &middot; <kbd>Ctrl</kbd>+<kbd>I</kbd> &middot; <kbd>Ctrl</kbd>+<kbd>E</kbd> |
| Indent selection | <kbd>Tab</kbd> |
| Command palette | <kbd>Ctrl</kbd>+<kbd>K</kbd> |
| Wrap selection in delimiters | type <kbd>{</kbd> <kbd>(</kbd> <kbd>[</kbd> <kbd>$</kbd> on a selection |

The history stack survives programmatic insertions (symbols, snippets, voice dictation),
which is where browser-native `undo` typically breaks.

---

## Security model

Security is treated as a correctness property. The following invariants are enforced
in the engine and exercised by the test suite where applicable:

| Invariant | Mechanism |
| :--- | :--- |
| Page identifiers cannot escape the events directory. | Regex-validated identifiers (UUID-shaped) reject path traversal at the `EventStore` boundary. |
| Uploaded filenames cannot escape the vault. | The filename is reduced to its basename before reaching the filesystem. |
| Uploads are bounded. | Hard ceiling of 100&nbsp;MB; oversized requests return `413`. |
| User code cannot block the kernel indefinitely. | A monotonic deadline triggers `interrupt_kernel()`; the error is reported back to the cell. |
| The document title cannot inject LaTeX during export. | All ten LaTeX-meta characters are escaped before reaching `\title{...}`. |
| Cell figures cannot be served from outside the figure root. | Paths are resolved against `figures_dir` and rejected if they escape. |
| Vault metadata cannot be corrupted by concurrent writes. | `meta.json` is written via tempfile and atomic `rename`. |
| Corrupted events do not brick a page. | Invalid JSONL lines are skipped at read time and the rest of the log is recovered. |

---

## Testing &amp; quality

```bash
# Backend
pytest -q
ruff check .
mypy .
bandit -r src/lablog tests -ll -x .venv,prototypes,dist,ui

# Frontend
cd ui
npx tsc --noEmit
npm run build
npm run lint
npm test -- --run
```

The project ships with **130+ backend tests** covering the parser, projector, event store,
vault, code engine, snippets, symbols, and the public API, with a coverage threshold of
**80%**. The frontend is type-checked under strict TypeScript, linted with oxlint, tested
with Vitest and built with Vite.

---

## Publishing to GitHub Pages

`lablog` exports a static, KaTeX-rendered version of the notebook for public sharing.
The interactive surface (editor, executable cells, voice) remains local.

```bash
source .venv/bin/activate
uv run python - <<'PY'
from lablog.exporter import export_site
export_site()
PY
```

A workflow at [`.github/workflows/pages.yml`](.github/workflows/pages.yml) reproduces the
same export in CI and publishes it on every push to `main`. To enable it on a fork:

1. In **Settings &rarr; Pages**, set the source to **GitHub Actions**.
2. Push to `main`.
3. The deployment URL appears in the workflow summary.

---

## Roadmap

<table>
  <thead>
    <tr><th align="left">Milestone</th><th align="center">Status</th></tr>
  </thead>
  <tbody>
    <tr><td>Event-sourced engine with deterministic projection</td><td align="center">Done</td></tr>
    <tr><td>Voice &rarr; intent &rarr; LaTeX pipeline</td><td align="center">Done</td></tr>
    <tr><td>Structural LaTeX renderer (sections, lists, environments)</td><td align="center">Done</td></tr>
    <tr><td>Executable cells with kernel timeout</td><td align="center">Done</td></tr>
    <tr><td>Vault with previews and time-locked deletion</td><td align="center">Done</td></tr>
    <tr><td>Editor: find &amp; replace, undo / redo, cursor-aware insertion</td><td align="center">Done</td></tr>
    <tr><td>Static export &amp; GitHub Pages deployment</td><td align="center">Done</td></tr>
    <tr><td>Native desktop app (offline, pywebview)</td><td align="center">Done</td></tr>
    <tr><td>Time-travel: scrub and restore any point of a page's history</td><td align="center">Done</td></tr>
    <tr><td>Full LaTeX mode: raw compilation, templates menu, error-to-line jump</td><td align="center">Done</td></tr>
    <tr><td>Version diff inside the time-travel panel</td><td align="center">Done</td></tr>
    <tr><td>Portable PyInstaller bundle</td><td align="center">Beta</td></tr>
    <tr><td>In-app PDF compilation with line-aware error reporting</td><td align="center">Done</td></tr>
    <tr><td>LaTeX autocomplete + physics templates + <code>lablog new --template</code></td><td align="center">Done</td></tr>
    <tr><td>Multi-file includes (<code>\input{page:…}</code>) at compile time</td><td align="center">Done (minimal)</td></tr>
    <tr><td>Diagram presets + Jupyter / optional PySpice</td><td align="center">Done (0.3.0)</td></tr>
    <tr><td>Re-apply params, dual highlight, .ipynb export</td><td align="center">Done (0.3.0)</td></tr>
    <tr><td>UI profiles + configurable shortcuts</td><td align="center">Done (0.3.0)</td></tr>
    <tr><td>BibTeX / full citeproc</td><td align="center">Planned</td></tr>
    <tr><td>Section and equation cross-references</td><td align="center">Planned</td></tr>
    <tr><td>P2P collaboration and device sync</td><td align="center">Exploratory</td></tr>
  </tbody>
</table>

---

## Citing

If `lablog` supports work that leads to publication, the recommended citation is:

```bibtex
@software{labarca_lablog,
  author  = {Labarca Baeza, José},
  title   = {{lablog}: a live LaTeX laboratory notebook for working scientists},
  year    = {2026},
  version = {0.3.0},
  url     = {https://github.com/kegouro/lablog},
  note    = {Part of the Pharos Project}
}
```

Also see [`CITATION.cff`](CITATION.cff).

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Security reports: [SECURITY.md](SECURITY.md).
Community standards: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

---

## License

`lablog` is released under the [MIT License](LICENSE).

---

## Acknowledgements

`lablog` is part of the **Pharos Project** &mdash; an effort to lower the barrier of entry
to scientific and educational infrastructure. Identity, logo and banner by
José&nbsp;Labarca&nbsp;Baeza. Original idea conceived with Vicente Muñoz Tolosa.

<div align="center">

<sub>USM &middot; Valparaíso &middot; Chile &middot; built to let the science flow</sub>

</div>
