<div align="center">

<img src="docs/assets/banner.png" alt="lablog identity" width="280" />

# lablog

**Bitácora de laboratorio LaTeX en vivo para científicos en activo**

*Proyecto Pharos · José Labarca Baeza · Universidad Técnica Federico Santa María · Valparaíso*

<br/>

<img src="docs/assets/hero-academic.jpg" alt="lablog academic hero" width="920" />

<br/>

<p>
  <a href="https://pypi.org/project/jose-labarca-lablog/"><img alt="PyPI version" src="https://img.shields.io/pypi/v/jose-labarca-lablog?style=flat-square&label=PyPI&labelColor=1C1C1E&color=48484A" /></a>
  <a href="https://pypi.org/project/jose-labarca-lablog/"><img alt="Python versions" src="https://img.shields.io/pypi/pyversions/jose-labarca-lablog?style=flat-square&labelColor=1C1C1E&color=A1A1A6" /></a>
  <a href="https://pypi.org/project/jose-labarca-lablog/"><img alt="PyPI downloads" src="https://img.shields.io/pypi/dm/jose-labarca-lablog?style=flat-square&labelColor=1C1C1E&color=48484A" /></a>
  <a href="https://github.com/kegouro/lablog/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/kegouro/lablog/ci.yml?branch=main&style=flat-square&label=CI&labelColor=1C1C1E&color=48484A" /></a>
  <a href="https://github.com/kegouro/lablog/actions/workflows/pages.yml"><img alt="Pages" src="https://img.shields.io/github/actions/workflow/status/kegouro/lablog/pages.yml?branch=main&style=flat-square&label=Pages&labelColor=1C1C1E&color=48484A" /></a>
  <a href="https://github.com/kegouro/lablog/actions/workflows/release.yml"><img alt="Release" src="https://img.shields.io/github/actions/workflow/status/kegouro/lablog/release.yml?style=flat-square&label=release&labelColor=1C1C1E&color=48484A" /></a>
  <a href="https://github.com/kegouro/lablog/commits/main"><img alt="last commit" src="https://img.shields.io/github/last-commit/kegouro/lablog?style=flat-square&labelColor=1C1C1E&color=48484A" /></a>
  <a href="https://github.com/kegouro/lablog/issues"><img alt="issues" src="https://img.shields.io/github/issues/kegouro/lablog?style=flat-square&labelColor=1C1C1E&color=48484A" /></a>
  <a href="https://github.com/kegouro/lablog/pulls"><img alt="PRs" src="https://img.shields.io/github/issues-pr/kegouro/lablog?style=flat-square&labelColor=1C1C1E&color=48484A" /></a>
  <a href="https://github.com/kegouro/lablog/stargazers"><img alt="stars" src="https://img.shields.io/github/stars/kegouro/lablog?style=flat-square&labelColor=1C1C1E&color=A1A1A6" /></a>
  <a href="https://github.com/kegouro/lablog/network/members"><img alt="forks" src="https://img.shields.io/github/forks/kegouro/lablog?style=flat-square&labelColor=1C1C1E&color=A1A1A6" /></a>
  <a href="https://github.com/kegouro/lablog"><img alt="languages" src="https://img.shields.io/github/languages/top/kegouro/lablog?style=flat-square&labelColor=1C1C1E" /></a>
  <a href="https://github.com/kegouro/lablog"><img alt="code size" src="https://img.shields.io/github/languages/code-size/kegouro/lablog?style=flat-square&labelColor=1C1C1E&color=48484A" /></a>
  <a href="#pruebas-y-calidad"><img alt="coverage" src="https://img.shields.io/badge/coverage-%E2%89%A580%25-48484A?style=flat-square&labelColor=1C1C1E" /></a>
  <a href="LICENSE"><img alt="license" src="https://img.shields.io/github/license/kegouro/lablog?style=flat-square&labelColor=1C1C1E&color=F2F2F7" /></a>
  <a href="https://www.repostatus.org/#active"><img alt="Project status" src="https://www.repostatus.org/badges/latest/active.svg" /></a>
</p>

<p>
  <a href="README.md"><img alt="English" src="https://img.shields.io/badge/lang-English-A1A1A6?style=for-the-badge&labelColor=1C1C1E" /></a>
  <a href="README.es.md"><img alt="Español" src="https://img.shields.io/badge/lang-Espa%C3%B1ol-48484A?style=for-the-badge&labelColor=1C1C1E" /></a>
  <a href="https://kegouro.github.io/lablog/"><img alt="Live preview" src="https://img.shields.io/badge/docs%20site-kegouro.github.io%2Flablog-1C1C1E?style=for-the-badge&labelColor=1C1C1E&color=48484A" /></a>
  <a href="https://pypi.org/project/jose-labarca-lablog/"><img alt="Install from PyPI" src="https://img.shields.io/badge/install-pip%20install%20jose--labarca--lablog-1C1C1E?style=for-the-badge&labelColor=1C1C1E&color=A1A1A6" /></a>
  <a href="https://github.com/kegouro/lablog/releases/tag/v0.3.0"><img alt="v0.3.0" src="https://img.shields.io/badge/release-v0.3.0-1C1C1E?style=for-the-badge&labelColor=1C1C1E&color=48484A" /></a>
</p>

<sub>
  <a href="#acerca-de">Acerca de</a>
  · <a href="#galería">Galería</a>
  · <a href="#funcionalidades">Funcionalidades</a>
  · <a href="#arquitectura">Arquitectura</a>
  · <a href="#atajos-de-teclado">Atajos</a>
  · <a href="#instalación">Instalación</a>
  · <a href="#tutoriales">Tutoriales</a>
  · <a href="#referencia-cli">CLI</a>
  · <a href="#modelo-de-seguridad">Seguridad</a>
  · <a href="#cómo-citar">Citar</a>
  · <a href="README.es.md">Español</a>
</sub>

</div>

---

## Tabla de contenidos

<table>
  <tr>
    <td><a href="#acerca-de"><strong>1. Acerca de</strong></a></td>
    <td><a href="#galería"><strong>2. Galería</strong></a></td>
    <td><a href="#funcionalidades"><strong>3. Funcionalidades</strong></a></td>
    <td><a href="#arquitectura"><strong>4. Arquitectura</strong></a></td>
  </tr>
  <tr>
    <td><a href="#stack"><strong>5. Stack</strong></a></td>
    <td><a href="#instalación"><strong>6. Instalación</strong></a></td>
    <td><a href="#inicio-rápido"><strong>7. Inicio rápido</strong></a></td>
    <td><a href="#tutoriales"><strong>8. Tutoriales</strong></a></td>
  </tr>
  <tr>
    <td><a href="#referencia-cli"><strong>9. CLI</strong></a></td>
    <td><a href="#http-api-surface"><strong>10. HTTP API</strong></a></td>
    <td><a href="#diagram-workbench"><strong>11. Diagrams</strong></a></td>
    <td><a href="#atajos-de-teclado"><strong>12. Atajos</strong></a></td>
  </tr>
  <tr>
    <td><a href="#laboratory-mode"><strong>13. Lab mode</strong></a></td>
    <td><a href="#real-pdf-compilation"><strong>14. PDF</strong></a></td>
    <td><a href="#vault--attachments"><strong>15. Vault</strong></a></td>
    <td><a href="#export-formats"><strong>16. Export</strong></a></td>
  </tr>
  <tr>
    <td><a href="#configuration"><strong>17. Config</strong></a></td>
    <td><a href="#on-disk-layout"><strong>18. Data layout</strong></a></td>
    <td><a href="#modelo-de-seguridad"><strong>19. Security</strong></a></td>
    <td><a href="#pruebas-y-calidad"><strong>20. Testing</strong></a></td>
  </tr>
  <tr>
    <td><a href="#publishing-to-github-pages"><strong>21. Pages</strong></a></td>
    <td><a href="#roadmap"><strong>22. Roadmap</strong></a></td>
    <td><a href="#cómo-citar"><strong>23. Citing</strong></a></td>
    <td><a href="#license"><strong>24. License</strong></a></td>
  </tr>
</table>

---

## Acerca de

> **lablog** es una bitácora de laboratorio de grado de investigación que vive donde ocurre
> el experimento. Combina un editor LaTeX estructural con vista previa en vivo, celdas
> ejecutables, diagramas parametrizados, dictado por voz e historial inmutable por event
> sourcing, de modo que el registro de una investigación pueda reconstruirse tal como se produjo.

A diferencia de un procesador usado *después* del experimento, lablog is designed to run **while
the work is in progress** — instrument open, notes incomplete, values still moving. The
guiding premise is simple: the act of writing the paper should not be separated from the
act of producing the data.

| Tool | Cuándo se usa habitualmente |
| :--- | :--- |
| Overleaf | Tras el experimento, al preparar el manuscrito. |
| TeXstudio / TeXmacs | Autoría LaTeX clásica en escritorio. |
| Jupyter / JupyterLab | Notebooks computacionales; la prosa es secundaria. |
| **lablog** | **Durante** el experimento: dictar, ejecutar, parametrizar diagramas y preservar. |

### Principios de diseño

1. **Local-first.** Default bind address is loopback. Your notes stay under `LABLOG_DATA_DIR`.
2. **Event sourcing, no mutación silenciosa.** Writes append immutable events; state is a pure projection.
3. **Preview aproximada + PDF fiel.** KaTeX is for speed; Tectonic is for truth.
4. **Peso opcional.** Core install is lean; voice, desktop, and PySpice are extras.
5. **Seguridad como corrección.** Path traversal, shell-escape, size limits, and OCC are invariants, not afterthoughts.

### Estado

| Item | Value |
| :--- | :--- |
| Distribución | [`jose-labarca-lablog`](https://pypi.org/project/jose-labarca-lablog/) on PyPI |
| Versión actual | **v0.3.0** ([notes](docs/release-notes-v0.3.0.md)) |
| Licencia | MIT |
| Lenguaje principal (motor) | Python 3.11+ |
| Lenguaje principal (UI) | TypeScript / React 19 |
| Mantenedor | José Labarca Baeza |

---

## Galería

Capturas reales de una instancia en ejecución (Vite + FastAPI, dark theme, v0.3.x). Script de regeneración: [`scripts/capture_ui_screenshots.mjs`](scripts/capture_ui_screenshots.mjs).

<div align="center">

### Mesa de trabajo

<img src="docs/assets/screenshots/01-workbench.png" alt="Main workbench with editor and preview" width="920" />

<sub>Figure 1. Shell principal: grupos de proyecto, editor LaTeX estructural, vista previa (<code>\section</code>, equation, <code>% lablog-param</code>).</sub>

<br/><br/>

### Presets de diagramas

<img src="docs/assets/screenshots/02-diagrams-panel.png" alt="Diagrams panel with circuit presets" width="920" />

<sub>Figure 2. Banco de diagramas: presets de circuitos / control / óptica con Insertar, +Sim y SPICE.</sub>

<br/><br/>

### Parámetros

<img src="docs/assets/screenshots/03-parameters-panel.png" alt="Parameters panel with sliders" width="920" />

<sub>Figure 3. Panel de parámetros: valores, resaltado dual, reaplicar diagrama / reaplicar + sim.</sub>

<br/><br/>

### Modo laboratorio

<img src="docs/assets/screenshots/07-lab-mode.png" alt="Laboratory mode with Python cell" width="920" />

<sub>Figure 4. Modo laboratorio: layout denso de celdas, fuente Python, controles de ejecución.</sub>

<br/><br/>

### Preferencias y atajos de teclado

<img src="docs/assets/screenshots/05-shortcuts.png" alt="Settings dialog showing keyboard shortcuts" width="920" />

<sub>Figure 5. Preferencias: fuente del editor, paletas, color de acento y chords globales editables (<code>mod+…</code>).</sub>

<br/><br/>

### Vista de ajustes

<img src="docs/assets/screenshots/04-settings.png" alt="Settings dialog overview" width="920" />

<sub>Figure 6. Superficie completa de preferencias (densidad, movimiento, layout laboratorio, import/export JSON).</sub>

<br/><br/>

### Panel de celdas

<img src="docs/assets/screenshots/08-cells-panel.png" alt="Cells and document with python environment" width="920" />

<sub>Figure 7. Documento con <code>\begin{python}</code> y parámetros abiertos para reaplicar.</sub>

<br/><br/>

### Identidad y arquitectura

<img src="docs/assets/graphic_kit.png" alt="lablog graphic kit" width="400" />
&nbsp;
<img src="docs/assets/architecture-layers.jpg" alt="Architecture illustration" width="480" />

<sub>Figure 8. Kit de identidad e ilustración de arquitectura por capas.</sub>

</div>

---

## Funcionalidades

<table>
  <thead>
    <tr>
      <th align="left">Módulo</th>
      <th align="left">Capacidad</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Structural LaTeX renderer</strong></td>
      <td>Sections, emphasis, lists, hyperlinks, and inline mathematics within prose. KaTeX for display environments (<code>align</code>, <code>equation</code>, <code>gather</code>, <code>cases</code>, <code>pmatrix</code>) with automatic equation numbering.</td>
    </tr>
    <tr>
      <td><strong>Editor</strong></td>
      <td>Line gutter, parameter overlay, debounced auto-save with optimistic concurrency (OCC), find &amp; replace, undo / redo that survives programmatic inserts, smart delimiter wrapping, snippets and symbols at the cursor.</td>
    </tr>
    <tr>
      <td><strong>Voice dictation</strong></td>
      <td>Browser <code>SpeechRecognition</code> with intent parsing, plus optional local Whisper (<code>[voice]</code> extra). Session timeout prevents hung recognisers.</td>
    </tr>
    <tr>
      <td><strong>Executable cells</strong></td>
      <td><code>\begin{python}...\end{python}</code> (and lab-mode cells) run on a real Jupyter kernel. Stdout, results, and figures return into the document; kernels are interrupted on timeout.</td>
    </tr>
    <tr>
      <td><strong>Vault</strong></td>
      <td>Attach images, CSV, PDF, DOCX, audio, scripts; preview in place. Atomic metadata; basename-only filenames; 100&nbsp;MB ceiling; time-locked deletion.</td>
    </tr>
    <tr>
      <td><strong>Event-sourced history</strong></td>
      <td>Every edit, execution, and attachment is append-only JSONL. Time-travel UI scrubs and restores any event index with version-aware OCC on the client.</td>
    </tr>
    <tr>
      <td><strong>Diagram workbench</strong></td>
      <td>Twelve parameterised presets (circuits, control, mechanics, optics, Feynman). Re-apply without <code>{{placeholders}}</code> via <code>% lablog-param</code>. Dual highlight (editor line + Circuitikz colour). Optional PySpice cells with numpy fallback.</td>
    </tr>
    <tr>
      <td><strong>Personalisation</strong></td>
      <td>Density, editor font, Nord palette, reduced motion, profiles (Laboratory / Paper / Teaching), exportable preferences JSON, configurable keyboard shortcuts.</td>
    </tr>
    <tr>
      <td><strong>Export</strong></td>
      <td><code>.tex</code>, plain text, HTML, PDF, DOCX (pandoc), <strong>Jupyter <code>.ipynb</code></strong>, static site for GitHub Pages, Canva-ready HTML. Titles LaTeX-escaped.</td>
    </tr>
    <tr>
      <td><strong>Desktop</strong></td>
      <td>Native window via <code>pywebview</code> (<code>[desktop]</code>); portable PyInstaller bundle for offline distribution.</td>
    </tr>
  </tbody>
</table>

---

## Arquitectura

<div align="center">
<img src="docs/assets/architecture-layers.jpg" alt="Architecture layers" width="860" />
</div>

```mermaid
%%{init: { 'theme': 'base', 'themeVariables': { 'primaryColor':'#1C1C1E', 'primaryTextColor':'#F2F2F7', 'primaryBorderColor':'#48484A', 'lineColor':'#A1A1A6', 'secondaryColor':'#48484A', 'tertiaryColor':'#1C1C1E' }}}%%
flowchart TB
    subgraph Client["Client (browser or pywebview)"]
      UI["React 19 · Vite 8 · Zustand"]
      ED["LaTeX editor · OCC autosave"]
      PV["KaTeX preview · PDF panel"]
      LB["Lab canvas · cells"]
      DG["Diagrams · parameters"]
    end

    subgraph Motor["Motor (FastAPI · localhost)"]
      API["REST /api/v1"]
      CMD["commands.py"]
      PRJ["projector · projections"]
      AST["latex_ast · serialize"]
      KER["code_engine · Jupyter"]
      PDF["pdf_engine · Tectonic"]
      VLT["vault"]
      DIA["diagrams · expand · pyspice"]
    end

    subgraph Disk["LABLOG_DATA_DIR"]
      EV["events/*.jsonl"]
      FIG["figures/"]
      VAULT["vault/"]
      BIN["bin/tectonic"]
      SITE["site/ export"]
    end

    UI --> API
    ED --> API
    LB --> API
    DG --> API
    API --> CMD
    CMD --> EV
    PRJ --> EV
    KER --> FIG
    VLT --> VAULT
    PDF --> BIN
    API --> SITE
```

### Event sourcing

```mermaid
%%{init: { 'theme': 'base', 'themeVariables': { 'primaryColor':'#1C1C1E', 'primaryTextColor':'#F2F2F7', 'primaryBorderColor':'#48484A', 'lineColor':'#A1A1A6' }}}%%
sequenceDiagram
    participant UI as UI / CLI
    participant API as FastAPI
    participant ES as EventStore
    participant P as Projector

    UI->>API: PUT /pages/{id} raw + version
    API->>ES: append(document_replaced, expected_version)
    alt version mismatch
        ES-->>API: VersionConflictError
        API-->>UI: 409 VERSION_CONFLICT + current
    else ok
        ES-->>API: fsync JSONL line
        API->>P: project(events)
        P-->>API: PageDetail
        API-->>UI: latex, ast, version, project_id
    end
```

**Rules enforced in code and CONTRIBUTING:**

1. Never mutate the projected AST from the API; append an event and re-project.
2. Paths only through `src/lablog/config.py`.
3. Wire shapes mirrored in `ui/src/lib/api.ts`.
4. Network I/O kept out of leaf components when possible (Zustand + hooks).
5. Diagrams: presets in `catalog.py`, clamp/expand in `expand.py`, SPICE optional in `pyspice_sim.py`.

<details>
<summary><strong>Módulo map (source tree)</strong></summary>

<br/>

| Path | Responsibility |
| :--- | :--- |
| [`src/lablog/api.py`](src/lablog/api.py) | HTTP surface, OCC on replace, vault, diagrams, export. |
| [`src/lablog/event_store.py`](src/lablog/event_store.py) | Append-only JSONL; per-page lock; conditional append (`expected_version`). |
| [`src/lablog/events.py`](src/lablog/events.py) | Event types and constructors. |
| [`src/lablog/projector.py`](src/lablog/projector.py) | Pure fold of events into page state. |
| [`src/lablog/projections.py`](src/lablog/projections.py) | Read models: detail, summary, history, cells. |
| [`src/lablog/commands.py`](src/lablog/commands.py) | Domain commands (create, replace, cells, restore). |
| [`src/lablog/latex_ast.py`](src/lablog/latex_ast.py) | Parse / serialise document tree. |
| [`src/lablog/code_engine.py`](src/lablog/code_engine.py) | Jupyter kernel with timeout interrupt. |
| [`src/lablog/vault.py`](src/lablog/vault.py) | Attachments, atomic meta, deletion schedule. |
| [`src/lablog/exporter.py`](src/lablog/exporter.py) | Static site and notebook export. |
| [`src/lablog/pdf_engine.py`](src/lablog/pdf_engine.py) | Tectonic install, warm, compile, error mapping. |
| [`src/lablog/diagrams/`](src/lablog/diagrams/) | Presets, expand, highlight, PySpice / numpy. |
| [`src/lablog/cli.py`](src/lablog/cli.py) | `lablog` entry point. |
| [`ui/src/stores/app-store.ts`](ui/src/stores/app-store.ts) | Client state, preferences, flush hooks. |
| [`ui/src/hooks/use-page-update.ts`](ui/src/hooks/use-page-update.ts) | Debounced autosave, serialised PUT, 409 retry. |
| [`ui/src/components/editor/latex-editor.tsx`](ui/src/components/editor/latex-editor.tsx) | Editor surface. |
| [`ui/src/components/lab/lab-canvas.tsx`](ui/src/components/lab/lab-canvas.tsx) | Lab mode; dirty-cell flush on exit. |

</details>

---

## Stack

| Capa | Tecnologías |
| :--- | :--- |
| Motor | Python 3.11+, FastAPI, Pydantic v2, Jupyter Client, optional faster-whisper / PySpice |
| Persistencia | JSONL event log, atomic renames for vault meta, deterministic projection |
| Interfaz | React 19, TypeScript, Vite 8, Tailwind CSS v4, Zustand, shadcn/ui, Radix |
| Matemática | KaTeX (preview); Tectonic / XeTeX (PDF) |
| Herramientas | uv, npm, Ruff, Mypy (strict), oxlint, pytest (≥80% cov), Vitest, Playwright (smoke), pre-commit, GitHub Accións |

---

## Instalación

### Desde PyPI (recomendado)

```bash
pip install -U jose-labarca-lablog
lablog serve
```

Open the UI served by the engine (bundled wheel includes compiled `ui/dist`), or point a
dev front-end at the API.

| Extra | Install | Purpose |
| :--- | :--- | :--- |
| Desktop | `pip install "jose-labarca-lablog[desktop]"` | Native window (`lablog app`) |
| Offline voice | `pip install "jose-labarca-lablog[voice]"` | Local Whisper (large download) |
| SPICE | `pip install "jose-labarca-lablog[pyspice]"` | PySpice cells (needs `ngspice` on PATH) |
| Dev | `pip install "jose-labarca-lablog[dev]"` | pytest, ruff, mypy, bandit, pre-commit |

### Desde el código fuente

> **Prerequisites.** Python ≥ 3.11, Node 22, [uv](https://docs.astral.sh/uv/), `npm`.
> Optional: `pandoc` (+ TeX) for DOCX/PDF via pandoc; Tectonic is managed by lablog for in-app PDF.

```bash
git clone https://github.com/kegouro/lablog.git
cd lablog
uv sync --extra dev
source .venv/bin/activate
cp .env.example .env

cd ui && npm install && cd ..
```

```bash
# Optional extras
uv sync --extra desktop
uv sync --extra voice
uv sync --extra pyspice
```

---

## Inicio rápido

### Desarrollo (dos procesos)

```bash
# Terminal A — API
source .venv/bin/activate
uvicorn lablog.api:app --host 127.0.0.1 --port 8000 --reload

# Terminal B — UI
cd ui && npm run dev
```

| Surface | URL |
| :--- | :--- |
| UI (Vite) | http://127.0.0.1:5173 |
| API | http://127.0.0.1:8000/api/v1 |
| Health | http://127.0.0.1:8000/api/v1/health |
| OpenAPI | http://127.0.0.1:8000/docs |

### Un proceso (tipo producción)

```bash
cd ui && npm run build && cd ..
uvicorn lablog.api:app --host 127.0.0.1 --port 8000
# or
lablog serve --host 127.0.0.1 --port 8000
```

### Escritorio

```bash
uv sync --extra desktop
cd ui && npm run build && cd ..
lablog app
```

### One-liner smoke (API only)

```bash
curl -s http://127.0.0.1:8000/api/v1/health | python -m json.tool
```

---

## Tutoriales

### Tutorial 1 — First page from the CLI

```bash
source .venv/bin/activate

# Create an empty page
lablog create-page --title "RC lab session"

# Or seed from a physics template
lablog new --title "Optics notes" --template article_physics

lablog list-pages
lablog render <page_id>          # print projected LaTeX
lablog events <page_id>          # inspect JSONL history
```

### Tutorial 2 — Parameterised RC circuit in the UI

1. Start API + UI (Quick start).
2. Create a page from the sidebar.
3. Open **Diagrams** → **RC serie — carga**.
4. Insert diagram (or insert + simulation cell).
5. Open **Parameters**: adjust `R`, `C`, `V0`.
6. Re-apply; confirm `% lablog-param` comments and TikZ update.
7. Focus a parameter: dual highlight (gutter line + Circuitikz `color=`).
8. Export **Notebook Jupyter (.ipynb)** or **Compilar PDF**.

```bash
# Equivalent expand from CLI
lablog diagrams list
lablog diagrams expand rc_series_charge --json
```

### Tutorial 3 — Executable cell and figure

In the editor (or Lab mode):

```latex
\begin{python}[label=demo]
import numpy as np
import matplotlib.pyplot as plt
t = np.linspace(0, 5, 200)
plt.plot(t, np.exp(-t))
plt.xlabel("t")
plt.ylabel("e^{-t}")
\end{python}
```

Run the cell from the **Cells** panel or Lab canvas. Output and figures are stored under
`LABLOG_DATA_DIR/figures/<page_id>/` and projected into the AST.

### Tutorial 4 — Time travel and OCC

1. Edit the page several times (autosave every ~300&nbsp;ms of idle).
2. Open history / time-travel; scrub the event index; restore a past version.
3. Concurrent edits: client sends `version`; on conflict the API returns `409` with
   `error_code: VERSION_CONFLICT` and `current`. The UI retries once or requeues the draft.

### Tutorial 5 — Static site for GitHub Pages

```bash
source .venv/bin/activate
# Prefer versioning data inside the repo for public notes:
# LABLOG_DATA_DIR=./data

python - <<'PY'
from lablog.exporter import export_site
print(export_site())
PY
```

Enable **Settings → Pages → GitHub Accións** on a fork; [`.github/workflows/pages.yml`](.github/workflows/pages.yml)
publishes on push to `main`.

---

## Referencia CLI

```text
lablog {create-page,new,list-pages,append-text,render,events,serve,app,diagrams}
```

| Command | Purpose |
| :--- | :--- |
| `create-page` | Create a page (title / project). |
| `new` | Create page; optional `--template`. |
| `list-pages` | List page summaries. |
| `append-text` | Append text event. |
| `render` | Project and print LaTeX. |
| `events` | Dump event log for a page. |
| `serve` | Run uvicorn-backed API (serves UI if built). |
| `app` | Desktop shell (`[desktop]`). |
| `diagrams list` | Catalogue presets. |
| `diagrams expand <id>` | Expand TikZ (+ params) to stdout / JSON. |

Examples:

```bash
lablog serve --host 127.0.0.1 --port 8000
lablog diagrams list
lablog diagrams expand thin_lens --set f=0.1 --set do=0.3
```

---

## Superficie HTTP

Base path: **`/api/v1`**. Interactive schema: `/docs` (Swagger) when the server is running.

<details>
<summary><strong>Core resources (summary)</strong></summary>

<br/>

| Method | Path | Notas |
| :--- | :--- | :--- |
| GET | `/health` | Liveness / engine flags. |
| GET/POST | `/pages` | List / create (`title`, `project_id` bounded). |
| GET/PUT/PATCH/DELETE | `/pages/{id}` | Detail (incl. `project_id`, `updated_at`, `version`); raw replace with OCC; metadata; soft-delete. |
| POST | `/pages/{id}/text`, `/math`, `/voice`, `/replace` | Domain inserts / replace. |
| GET | `/pages/{id}/history`, `/at/{i}`, POST `/restore/{i}` | Time travel. |
| POST/GET | `/pages/{id}/cells...` | Insert, update (**returns `version`**), execute, move (**returns `version`**), figure. |
| GET/POST | `/diagrams/presets...` | List, expand, simulate-source, apply. |
| GET/POST | `/snippets...`, `/latex-symbols...` | Catalogues and favourites. |
| GET/POST | `/vault...` | Upload, preview, download, delayed delete, purge. |
| GET/POST | `/pdf/*`, `/pages/{id}/export/*` | Motor status, install, compile, multi-format export. |
| POST | `/export` | Static site export. |

</details>

**OCC contract (PUT raw / replace):**

```json
{
  "detail": {
    "error_code": "VERSION_CONFLICT",
    "message": "La página cambió en otro cliente; recarga e inténtalo de nuevo",
    "expected": 5,
    "current": 6
  }
}
```

Conditional append is atomic under the per-page file lock (`EventStore.append(..., expected_version=)`).

---

## Banco de diagramas

| `preset_id` | Title | Category |
| :--- | :--- | :--- |
| `voltage_divider` | Divisor de tensión | circuitos |
| `noninverting_opamp` | Op-amp no inversor | circuitos |
| `wheatstone` | Puente de Wheatstone (DC) | circuitos |
| `rc_lowpass` | RC pasa-bajos | circuitos |
| `rc_series_charge` | RC serie — carga | circuitos |
| `half_wave_rectifier` | Rectificador media onda + C | circuitos |
| `rlc_series_step` | RLC serie — escalón | circuitos |
| `second_order_step` | 2º orden — respuesta al escalón | control |
| `pi_controller` | PI + planta 1er orden | control |
| `mass_spring_damper` | Masa-resorte-amortiguador | mecanica |
| `thin_lens` | Lente delgada | optica |
| `qed_moller` | QED e⁻e⁻ (árbol) | particulas |

Presets with PySpice support degrade to pedagogical numpy code when PySpice / ngspice
are absent. Headers in generated LaTeX:

```latex
% lablog-diagram: preset=rc_series_charge version=1
% lablog-param: C=1e-06
% lablog-param: R=1000
% lablog-highlight: R
```

---

## Atajos de teclado

`mod` is **⌘** on macOS and **Ctrl** on Windows / Linux. Chords are editable under
**Preferencias → Atajos** and exported with preferences JSON.

### Globales (configurables)

| Acción | Chord por defecto | Visualización macOS | Notas |
| :--- | :--- | :--- | :--- |
| Paleta de comandos | `mod+k` | ⌘K | Pages, panels, profiles |
| Guardar (flush del autosave) | `mod+s` | ⌘S | Forces pending PUT |
| Alternar panel de diagramas | `mod+shift+d` | ⌘⇧D | Sidebar tool |
| Alternar panel de parámetros | `mod+shift+p` | ⌘⇧P | Sliders / re-apply |
| Alternar panel de celdas | `mod+shift+c` | ⌘⇧C | Executable cells |
| Alternar modo laboratorio | `mod+shift+l` | ⌘⇧L | Flushes dirty cells on exit |
| Nueva página | `mod+n` | ⌘N | Creates via API |

Fuente de verdad: [`ui/src/lib/shortcuts.ts`](ui/src/lib/shortcuts.ts) (`DEFAULT_SHORTCUTS`).

### Editor (integrados)

| Acción | Shortcut |
| :--- | :---: |
| Buscar / reemplazar | <kbd>Ctrl</kbd>+<kbd>F</kbd> / <kbd>Ctrl</kbd>+<kbd>H</kbd> |
| Siguiente / anterior coincidencia | <kbd>Enter</kbd> / <kbd>Shift</kbd>+<kbd>Enter</kbd> |
| Deshacer / rehacer | <kbd>Ctrl</kbd>+<kbd>Z</kbd> / <kbd>Ctrl</kbd>+<kbd>Y</kbd> |
| Negrita · Cursiva · Math inline | <kbd>Ctrl</kbd>+<kbd>B</kbd> · <kbd>I</kbd> · <kbd>E</kbd> |
| Indentar selección | <kbd>Tab</kbd> |
| Envolver selección en delimitadores | type <kbd>{</kbd> <kbd>(</kbd> <kbd>[</kbd> <kbd>$</kbd> on a selection |

El historial del editor sobrevive a inserciones programáticas (symbols, snippets, voice), donde el undo nativo del navegador suele fallar.

<div align="center">
<img src="docs/assets/screenshots/05-shortcuts.png" alt="Keyboard shortcuts in preferences" width="720" />
</div>

---

## Experiencia de editor


Las preferencias (densidad, fuente, paleta, atajos, perfiles) viven en `localStorage` y se
exportan / importan como JSON desde Preferencias.

---

## Modo laboratorio

El modo laboratorio es un layout denso orientado a celdas (Python / markdown / LaTeX cells).

- Source is local until blur or explicit save; **al salir del lab se hace flush de celdas dirty**
  (toolbar, shortcuts, command palette, settings, and unmount) and resynchronises
  `activeVersion` via `GET /pages/{id}`.
- Keyboard profiles include a **Laboratory** preset (compact density, mono font, lab flag).

---

## Compilación PDF real

La vista previa es **aproximada** (KaTeX + HTML). La salida fiel usa
[Tectonic](https://tectonic-typesetting.github.io/) (self-contained XeTeX).

- **Compilar PDF** in the preview header; preview labelled **Aproximada**.
- Python cells render as code + output + figures (`fancyvrb`, `\includegraphics`).
- Async compile, hard timeout (`504` on runaway); cache by document hash.
- Errors map to source via `% lablog-src` markers (**Celda N · línea M**).
- **No `--shell-escape`.** LaTeX cannot run OS commands.
- Managed binary: checksum-pinned under `LABLOG_DATA_DIR/bin/`; never “latest” at runtime.

> lablog is local and single-user. Do not expose the compile endpoint publicly without
> rate limiting and isolation.

---

## Bóveda y adjuntos

| Property | Behaviour |
| :--- | :--- |
| Storage | `LABLOG_DATA_DIR/vault/` + atomic `meta.json` |
| Filenames | Basename only (blocks `../`) |
| Size | Max 100&nbsp;MB → HTTP 413 |
| Lifecycle | Soft delete schedule; force delete with confirmation phrase; purge expired |

---

## Formatos de exportación

| Format | How | Notas |
| :--- | :--- | :--- |
| `.tex` | Export menu | Full document serialisation |
| `.txt` | Export menu | Plain reduction |
| `.pdf` | In-app Tectonic or pandoc path | Prefer in-app for cells/figures |
| `.docx` | pandoc | Requires pandoc + TeX for math-heavy docs |
| `.ipynb` | Export menu | Jupyter notebook for cells + markdown |
| Static site | Export / CI | GitHub Pages |
| Canva HTML | Export menu | Presentation-oriented HTML |

---

## Configuración

See [`.env.example`](.env.example).

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `LABLOG_DATA_DIR` | `~/.lablog` | Events, vault, figures, managed binaries |
| `LABLOG_HOST` | `127.0.0.1` | API bind host (invalid port → 8000) |
| `LABLOG_PORT` | `8000` | API bind port (1–65535) |
| `LABLOG_CORS_ORIGINS` | Vite dev origins | Comma-separated |
| `LABLOG_CORS_CREDENTIALS` | `true` | CORS credentials |
| `LABLOG_SITE_DIR` | `${data_dir}/site` | Static export root |

Nunca commitees secretos. Trata `LABLOG_DATA_DIR` como datos personales de investigación.

---

## Diseño en disco

```text
$LABLOG_DATA_DIR/
├── events/                 # one JSONL stream per page_id
│   └── <uuid>.jsonl
├── vault/                  # attachments + meta.json
├── figures/                # per-page cell figures
│   └── <page_id>/
├── bin/                    # managed tectonic (optional)
└── site/                   # last static export (if configured)
```

Page identifiers are constrained to a safe alphabet (`[A-Za-z0-9_-]{1,128}`) so
filesystem paths cannot escape the events root.

---

## Modelo de seguridad

| Invariant | Mechanism |
| :--- | :--- |
| Page IDs cannot traverse directories | Regex validation at `EventStore` |
| Upload names cannot escape vault | Basename only |
| Upload size bounded | 100&nbsp;MB → 413 |
| User code cannot hang the kernel | Deadline + `interrupt_kernel()` |
| Titles cannot inject LaTeX | Meta-character escape on export |
| Figures cannot leave figure root | Resolve + containment check |
| Vault meta concurrent-safe | Tempfile + atomic rename |
| Corrupt events do not brick a page | Skip bad JSONL lines |
| Soft-deleted pages reject writes | 409 on mutate |
| OCC on document replace | Atomic `expected_version` under lock |
| Title / project_id length bounded | Pydantic max_length (500 / 128) |
| Tectonic isolation | No shell-escape |

Report vulnerabilities privately via GitHub Security Advisories or the maintainer
profile; see [SECURITY.md](SECURITY.md).

---

## Pruebas y calidad

```bash
# Motor
source .venv/bin/activate
pytest -q
ruff check src tests
mypy -p lablog
bandit -r src/lablog -ll

# UI
cd ui
npx tsc --noEmit
npm run lint
npm test -- --run
npm run build

# Optional e2e
npm run test:e2e:install && npm run test:e2e
```

| Gate | Threshold / tool |
| :--- | :--- |
| Backend coverage | **≥ 80%** (`pytest-cov`) |
| Typecheck | Mypy strict (package), `tsc --noEmit` |
| Lint | Ruff, oxlint / ESLint pipeline |
| Pre-commit | whitespace, ruff, mypy, tsc, oxlint |
| CI | [`.github/workflows/ci.yml`](.github/workflows/ci.yml) — backend + frontend |

---

## Publicar en GitHub Pages

Interactive features (editor, cells, voice) remain local. The static exporter produces a
KaTeX-rendered site for sharing.

```bash
source .venv/bin/activate
uv run python - <<'PY'
from lablog.exporter import export_site
print(export_site())
PY
```

1. Repository **Settings → Pages → Source: GitHub Accións**
2. Push to `main`
3. Workflow [`.github/workflows/pages.yml`](.github/workflows/pages.yml) deploys

Live instance: [kegouro.github.io/lablog](https://kegouro.github.io/lablog/)

---

## Empaquetado de escritorio

```bash
./scripts/package_desktop.sh
# → dist/lablog/  (zip and distribute)
```

Spec: [`lablog.spec`](lablog.spec). Voice model excluded by default. Treat the bundle as
a verified starting point for portable builds, not a universal one-click installer.

---

## Hoja de ruta

| Milestone | Estado |
| :--- | :---: |
| Event-sourced engine + projection | Done |
| Voice → intent → LaTeX | Done |
| Structural renderer | Done |
| Executable cells + timeout | Done |
| Vault + delayed delete | Done |
| Editor F&R, undo/redo, cursor insert | Done |
| Static export + Pages | Done |
| Desktop (pywebview) | Done |
| Time-travel restore | Done |
| In-app PDF + error mapping | Done |
| Autocomplete + templates CLI | Done |
| Diagram presets + re-apply + dual highlight | Done (0.3.0) |
| Jupyter export + optional PySpice | Done (0.3.0) |
| UI profiles + shortcuts | Done (0.3.0) |
| OCC harden + lab dirty flush | Done (post-0.3.0) |
| BibTeX / citeproc | Planned |
| Section / equation cross-refs | Planned |
| P2P collab / multi-device sync | Exploratory |

---

## Cómo citar

Si lablog apoya trabajo que derive en publicación, cita:

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

Metadatos legibles por máquina: [`CITATION.cff`](CITATION.cff).

---

## Contribuir

See [CONTRIBUTING.md](CONTRIBUTING.md). Security: [SECURITY.md](SECURITY.md).
Conduct: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Changelog: [CHANGELOG.md](CHANGELOG.md).

Preferred contribution shape: small PR, tests for the behaviour you change, no drive-by
refactors. Architecture rules in CONTRIBUTING are binding.

---

## Licencia

Publicado bajo la [MIT License](LICENSE).

---

## Agradecimientos

lablog forma parte del **Proyecto Pharos** — infrastructure for scientific and educational
work that should feel local, honest, and reconstructible. Identidad y gráficos por
José Labarca Baeza. Idea original concebida con Vicente Muñoz Tolosa.

<div align="center">

<img src="docs/assets/logo.png" alt="lablog logo" width="120" />

<br/>

<sub>USM · Valparaíso · Chile · para escribir la ciencia mientras se hace</sub>

<br/><br/>

[![GitHub](https://img.shields.io/badge/github-kegouro%2Flablog-1C1C1E?style=for-the-badge&labelColor=1C1C1E&color=48484A)](https://github.com/kegouro/lablog)
[![PyPI](https://img.shields.io/badge/pypi-jose--labarca--lablog-1C1C1E?style=for-the-badge&labelColor=1C1C1E&color=A1A1A6)](https://pypi.org/project/jose-labarca-lablog/)
[![Docs](https://img.shields.io/badge/docs-site-1C1C1E?style=for-the-badge&labelColor=1C1C1E&color=48484A)](https://kegouro.github.io/lablog/)

</div>
