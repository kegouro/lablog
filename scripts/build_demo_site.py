"""Build a demo lablog static site for the GitHub Pages workflow.

Seeds an ephemeral data directory with a representative page so the published
site has real content (the repository never carries personal notebooks), then
delegates to :func:`lablog.exporter.export_site`. Designed to be a single
``uv run python scripts/build_demo_site.py`` invocation in CI.

After export, copies real UI screenshots and rewrites ``index.html`` as a
marketing landing (gallery + install) that links to the static notebook demo.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from uuid import uuid4

from lablog import __version__
from lablog.config import settings
from lablog.event_store import EventStore
from lablog.events import document_replaced, page_created
from lablog.exporter import export_site

DEMO_LATEX = r"""La energía total se conserva en un sistema \textbf{aislado}. Para un cuerpo
en caída libre con \textit{velocidad} $v$ y altura $h$:
$$E = \frac{1}{2} m v^{2} + m g h$$

\subsection{Sistema de ecuaciones}
\begin{align}
F &= m a \\
p &= m v \\
E_k &= \frac{p^{2}}{2 m}
\end{align}

\subsection{Pasos del experimento}
\begin{itemize}
\item Medir la masa $m$ del objeto.
\item Soltar desde una altura $h_{0} = 2.5$ m.
\item Registrar el tiempo $t$ de caída.
\end{itemize}

Matriz de rotación:
\[ R = \begin{pmatrix} \cos\theta & -\sin\theta \\ \sin\theta & \cos\theta \end{pmatrix} \]

\begin{python}[label=calc]
import numpy as np
print(np.sqrt(2 * 9.8 * 2.5))
\end{python}
"""

INTRO_LATEX = r"""Esta es una vista estática de lablog publicada con GitHub Pages. Muestra cómo
se renderiza un documento real con secciones, énfasis, listas, matemática
inline ($\nabla \cdot \mathbf{E} = \rho / \varepsilon_{0}$), entornos
matemáticos numerados y celdas de código.

La aplicación interactiva (editor, dictado por voz, ejecución de celdas)
corre localmente. Para probarla:

\begin{itemize}
\item Clona el repositorio.
\item Sigue las instrucciones del \textit{README}.
\item Abre la UI en tu navegador.
\end{itemize}
"""

# Captures shipped under docs/assets/screenshots/ (Playwright script).
SCREENSHOTS = (
    ("01-workbench.png", "Workbench — editor LaTeX + preview en vivo"),
    ("02-diagrams-panel.png", "Panel de diagramas (circuitos / presets)"),
    ("03-parameters-panel.png", "Parámetros con sliders"),
    ("07-lab-mode.png", "Modo laboratorio (celdas Python)"),
    ("05-shortcuts.png", "Atajos de teclado"),
    ("04-settings.png", "Preferencias"),
    ("08-cells-panel.png", "Celdas y entorno Python"),
)


def seed(store: EventStore, title: str, latex: str) -> str:
    page_id = str(uuid4())
    store.append(page_created(page_id=page_id, title=title))
    store.append(document_replaced(page_id=page_id, latex=latex))
    return page_id


def _copy_screenshots(site_dir: Path) -> list[tuple[str, str]]:
    src_dir = Path("docs/assets/screenshots").resolve()
    dst_dir = site_dir / "assets" / "screenshots"
    dst_dir.mkdir(parents=True, exist_ok=True)
    present: list[tuple[str, str]] = []
    for name, caption in SCREENSHOTS:
        src = src_dir / name
        if not src.is_file():
            continue
        shutil.copy2(src, dst_dir / name)
        present.append((name, caption))
    # Also copy brand bits if available
    for brand in ("banner.png", "logo.png", "hero-academic.jpg"):
        brand_src = Path("docs/assets") / brand
        if brand_src.is_file():
            brand_dst = site_dir / "assets" / brand
            brand_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(brand_src, brand_dst)
    return present


def _write_landing(site_dir: Path, shots: list[tuple[str, str]]) -> None:
    """Replace index.html with a marketing landing; keep notebook as notes.html."""
    notes = site_dir / "index.html"
    if notes.is_file():
        notes.replace(site_dir / "notes.html")

    gallery_items = "\n".join(
        f"""      <figure class="shot">
        <img src="assets/screenshots/{name}" alt="{caption}" loading="lazy" />
        <figcaption>{caption}</figcaption>
      </figure>"""
        for name, caption in shots
    )
    if not gallery_items:
        gallery_items = "      <p class=\"muted\">Screenshots unavailable in this build.</p>"

    html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="lablog v{__version__} — bitácora de laboratorio LaTeX-nativa, local-first. Parte del Pharos Project.">
<title>lablog · v{__version__} · Pharos Project</title>
<link rel="preconnect" href="https://rsms.me">
<link rel="stylesheet" href="https://rsms.me/inter/inter.css">
<style>
:root {{
  --bg: #1C1C1E;
  --surface: #242427;
  --divider: #48484A;
  --text: #F2F2F7;
  --muted: #A1A1A6;
  --accent: #F2F2F7;
}}
* {{ box-sizing: border-box; }}
body {{
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  margin: 0;
  background: var(--bg);
  color: var(--text);
  line-height: 1.65;
}}
.wrap {{ max-width: 980px; margin: 0 auto; padding: 2.5rem 1.25rem 4rem; }}
header {{
  border-bottom: 1px solid var(--divider);
  padding-bottom: 1.5rem;
  margin-bottom: 2rem;
}}
.brand {{ display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; }}
.brand img {{ height: 48px; width: auto; }}
h1 {{ font-size: 2.1rem; margin: 0; letter-spacing: -0.03em; }}
.tag {{
  display: inline-block;
  font-size: 0.75rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
  border: 1px solid var(--divider);
  border-radius: 999px;
  padding: 0.2rem 0.65rem;
}}
.lead {{ color: var(--muted); margin: 0.75rem 0 0; max-width: 42rem; }}
.actions {{ display: flex; flex-wrap: wrap; gap: 0.6rem; margin: 1.25rem 0 0; }}
.btn {{
  display: inline-block;
  text-decoration: none;
  color: var(--bg);
  background: var(--text);
  border-radius: 8px;
  padding: 0.55rem 0.95rem;
  font-size: 0.92rem;
  font-weight: 600;
}}
.btn.ghost {{
  background: transparent;
  color: var(--text);
  border: 1px solid var(--divider);
}}
.btn:hover {{ opacity: 0.92; }}
h2 {{ font-size: 1.25rem; letter-spacing: -0.02em; margin: 2rem 0 0.85rem; }}
.muted {{ color: var(--muted); }}
.gallery {{
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.25rem;
}}
@media (min-width: 720px) {{
  .gallery {{ grid-template-columns: 1fr 1fr; }}
  .gallery .shot:first-child {{ grid-column: 1 / -1; }}
}}
.shot {{
  margin: 0;
  background: var(--surface);
  border: 1px solid var(--divider);
  border-radius: 12px;
  overflow: hidden;
}}
.shot img {{ display: block; width: 100%; height: auto; }}
.shot figcaption {{
  padding: 0.55rem 0.85rem 0.75rem;
  font-size: 0.85rem;
  color: var(--muted);
}}
pre {{
  background: var(--surface);
  border: 1px solid var(--divider);
  border-radius: 10px;
  padding: 1rem 1.1rem;
  overflow-x: auto;
  font-size: 0.9rem;
}}
code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
footer {{
  margin-top: 3rem;
  padding-top: 1.25rem;
  border-top: 1px solid var(--divider);
  color: var(--muted);
  font-size: 0.88rem;
}}
footer a {{ color: var(--text); }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="brand">
      <img src="assets/banner.png" alt="lablog" onerror="this.style.display='none'" />
      <div>
        <h1>lablog</h1>
        <span class="tag">v{__version__} · Pharos Project</span>
      </div>
    </div>
    <p class="lead">
      Bitácora de laboratorio LaTeX-nativa, local-first: preview en vivo, celdas
      ejecutables, voz, bóveda, PDF con Tectonic y export Jupyter.
      Parte del <strong>Pharos Project</strong> · José Labarca Baeza · UTFSM.
    </p>
    <div class="actions">
      <a class="btn" href="https://pypi.org/project/jose-labarca-lablog/">pip install jose-labarca-lablog</a>
      <a class="btn ghost" href="https://github.com/kegouro/lablog">GitHub</a>
      <a class="btn ghost" href="notes.html">Demo de notas (estático)</a>
      <a class="btn ghost" href="https://github.com/kegouro/lablog/releases/tag/v{__version__}">Release notes</a>
      <a class="btn ghost" href="https://kegouro.github.io/">Pharos landing</a>
    </div>
  </header>

  <h2>Galería de la UI real</h2>
  <p class="muted">Capturas de una instancia en ejecución (Vite + FastAPI, tema oscuro).</p>
  <div class="gallery">
{gallery_items}
  </div>

  <h2>Instalación rápida</h2>
  <pre><code>pip install -U jose-labarca-lablog
lablog serve
# UI: http://127.0.0.1:5173 (dev) o embebida según README</code></pre>

  <h2>Documentación</h2>
  <p class="muted">
    README académico bilingüe en el repositorio:
    <a href="https://github.com/kegouro/lablog/blob/main/README.md">English</a> ·
    <a href="https://github.com/kegouro/lablog/blob/main/README.es.md">Español</a>.
    Incluye arquitectura, atajos, API HTTP y tutoriales.
  </p>

  <footer>
    lablog v{__version__} · MIT ·
    <a href="https://orcid.org/0009-0006-8890-4048">ORCID</a> ·
    <a href="https://github.com/kegouro/lablog">código fuente</a>
  </footer>
</div>
</body>
</html>
"""
    (site_dir / "index.html").write_text(html, encoding="utf-8")


def _patch_notes_header(site_dir: Path) -> None:
    notes = site_dir / "notes.html"
    if not notes.is_file():
        return
    text = notes.read_text(encoding="utf-8")
    text = text.replace(
        "<title>lablog notes</title>",
        f"<title>lablog notes · v{__version__}</title>",
    )
    text = re.sub(
        r"<header>\s*<h1>lablog</h1>\s*<p>.*?</p>\s*</header>",
        f"""<header>
<h1>lablog <span style="font-size:0.55em;color:#A1A1A6;font-weight:500">v{__version__}</span></h1>
<p>Vista estática exportada · <a href="index.html" style="color:#F2F2F7">← volver a la galería</a> · <a href="https://github.com/kegouro/lablog" style="color:#F2F2F7">GitHub</a></p>
</header>""",
        text,
        count=1,
        flags=re.S,
    )
    notes.write_text(text, encoding="utf-8")


def main() -> None:
    data_dir = Path("data").resolve()
    site_dir = Path("site").resolve()
    settings.data_dir = data_dir
    settings.site_dir = site_dir
    data_dir.mkdir(parents=True, exist_ok=True)

    store = EventStore(settings.event_dir)
    seed(store, "Bienvenido a lablog", INTRO_LATEX)
    seed(store, "Conservación de la energía", DEMO_LATEX)

    out = export_site(site_dir)
    shots = _copy_screenshots(out)
    _write_landing(out, shots)
    _patch_notes_header(out)
    print(f"Static site exported to {out} ({len(shots)} screenshots)")


if __name__ == "__main__":
    main()
