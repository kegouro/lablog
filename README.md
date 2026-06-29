<div align="center">

<img src="docs/assets/banner.png" alt="lablog" width="640" />

<br/>

<h1 style="margin-top: 0;">lablog</h1>

<p><em>A live LaTeX laboratory notebook for working scientists.</em></p>

<p>
  <a href="#about"><img alt="status" src="https://img.shields.io/badge/status-beta-1C1C1E?style=flat-square&labelColor=1C1C1E" /></a>
  <a href="https://github.com/kegouro/lablog/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/kegouro/lablog/ci.yml?branch=main&style=flat-square&labelColor=1C1C1E&color=48484A&label=CI" /></a>
  <a href="https://github.com/kegouro/lablog/actions/workflows/pages.yml"><img alt="Pages" src="https://img.shields.io/github/actions/workflow/status/kegouro/lablog/pages.yml?branch=main&style=flat-square&labelColor=1C1C1E&color=48484A&label=Pages" /></a>
  <a href="#testing--quality"><img alt="tests" src="https://img.shields.io/badge/tests-50%20passing-1C1C1E?style=flat-square&labelColor=1C1C1E&color=48484A" /></a>
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
      <td>LaTeX (<code>.tex</code>), plain text, HTML, PDF and DOCX via <em>pandoc</em>; static site for GitHub Pages; Canva-ready HTML. The export pipeline escapes the document title to prevent LaTeX injection.</td>
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
    UI <-->|HTTP / WebSocket| Engine
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
ruff check src tests
mypy -p lablog

# Frontend
cd ui
npx tsc --noEmit
npm run build
npm run lint
```

The project ships with **50 backend tests** covering the parser, projector, event store,
vault, code engine, snippets, symbols, and the public API. The frontend is type-checked
under strict TypeScript and built with Vite.

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
    <tr><td>In-app PDF compilation with line-aware error reporting</td><td align="center">Planned</td></tr>
    <tr><td>Multi-file documents and BibTeX</td><td align="center">Planned</td></tr>
    <tr><td>Section and equation cross-references</td><td align="center">Planned</td></tr>
    <tr><td>Tauri desktop bundle</td><td align="center">Planned</td></tr>
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
  url     = {https://github.com/kegouro/lablog},
  note    = {Part of the Pharos Project}
}
```

---

## License

`lablog` is released under the [MIT License](LICENSE).

---

## Acknowledgements

`lablog` is part of the **Pharos Project** &mdash; an effort to lower the barrier of entry
to scientific and educational infrastructure. Identity, logo and banner by
José&nbsp;Labarca&nbsp;Baeza. Original idea conceived with Vicente.

<div align="center">

<sub>USM &middot; Valparaíso &middot; Chile &middot; built to let the science flow</sub>

</div>
