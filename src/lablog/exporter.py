"""Exporta páginas lablog a un sitio estático listo para GitHub Pages."""

from __future__ import annotations

import html
import shutil
from pathlib import Path
from typing import Any

from lablog.ast_nodes import CellNode, DocumentNode, MathNode, TextNode
from lablog.config import settings
from lablog.event_store import EventStore
from lablog.projector import project

_KATEX_CSS = "https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css"
_KATEX_JS = "https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"
_AUTO_RENDER_JS = "https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"


def _node_to_html(node: Any, figure_base: str = "figures") -> str:
    if isinstance(node, TextNode):
        return f"<p>{html.escape(node.text).replace(chr(10), '<br>')}</p>"
    if isinstance(node, MathNode):
        if node.mode == "display":
            return f"<p>\\[{html.escape(node.latex)}\\]</p>"
        return f"\\({html.escape(node.latex)}\\)"
    if isinstance(node, CellNode):
        code = f'<pre class="code"><code class="language-{node.language}">'
        code += f"{html.escape(node.source)}</code></pre>"
        parts = [code]
        if node.output:
            parts.append(f'<pre class="output">{html.escape(node.output)}</pre>')
        if node.figure_path:
            figure_name = Path(node.figure_path).name
            page_name = Path(node.figure_path).parent.name
            rel = f"{figure_base}/{page_name}/{figure_name}"
            parts.append(f'<img src="{rel}" alt="figura" loading="lazy">')
        return "\n".join(parts)
    return ""


def _ast_to_html(doc: DocumentNode, figure_base: str = "figures") -> str:
    return "\n".join(_node_to_html(child, figure_base) for child in doc.children)


def _copy_figures(page_ids: set[str], out_dir: Path) -> None:
    figures_dir = settings.figures_dir
    if not figures_dir.exists():
        return
    for page_id in page_ids:
        src = figures_dir / page_id
        if not src.exists():
            continue
        dst = out_dir / "figures" / page_id
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst, dirs_exist_ok=True)


_STYLE_CSS = (
    "body { font-family: system-ui, -apple-system, sans-serif; "
    "max-width: 800px; margin: 0 auto; padding: 2rem; line-height: 1.6; }\n"
    "h1, h2 { color: #111; }\n"
    "section { border-bottom: 1px solid #ddd; padding: 2rem 0; }\n"
    "pre { background: #f4f4f4; padding: 1rem; border-radius: 6px; "
    "overflow-x: auto; }\n"
    "pre.output { background: #e8f5e9; }\n"
    "img { max-width: 100%; height: auto; }\n"
    "a { color: #0366d6; }"
)


def export_site(out_dir: Path | None = None) -> Path:
    """Genera un sitio estático con todas las páginas agrupadas por proyecto."""
    out_dir = Path(out_dir or settings.site_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    store = EventStore(settings.event_dir)
    pages: list[tuple[str, Any]] = []
    page_ids: set[str] = set()

    for page_id in store.list_pages():
        events = store.get_events(page_id)
        proj = project(page_id, events)
        if proj.deleted or not events:
            continue
        pages.append((page_id, proj))
        page_ids.add(page_id)

    _copy_figures(page_ids, out_dir)

    by_project: dict[str, list[tuple[str, Any]]] = {}
    for page_id, proj in pages:
        project_key = proj.project_id or "Sin proyecto"
        by_project.setdefault(project_key, []).append((page_id, proj))

    sections: list[str] = []
    toc: list[str] = ["<h2>Índice</h2>", "<ul>"]
    for project_name in sorted(by_project):
        toc.append(f"<li><strong>{html.escape(project_name)}</strong><ul>")
        for page_id, proj in sorted(by_project[project_name], key=lambda x: x[1].title):
            anchor = f"page-{page_id}"
            toc.append(f'<li><a href="#{anchor}">{html.escape(proj.title)}</a></li>')
            body = _ast_to_html(proj.ast)
            sections.append(
                f'<section id="{anchor}">\n'
                f"<h2>{html.escape(proj.title)}</h2>\n"
                f"{body}\n"
                "</section>\n"
            )
        toc.append("</ul></li>")
    toc.append("</ul>")

    html_doc = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>lablog notes</title>
<link rel="stylesheet" href="{_KATEX_CSS}">
<style>
{_STYLE_CSS}
</style>
</head>
<body>
<header>
<h1>lablog notes</h1>
<p>Exportado automáticamente desde <a href="https://github.com">lablog</a>.</p>
</header>
<nav>
{chr(10).join(toc)}
</nav>
<main>
{chr(10).join(sections)}
</main>
<script src="{_KATEX_JS}"></script>
<script src="{_AUTO_RENDER_JS}"></script>
<script>
  renderMathInElement(document.body, {{
    delimiters: [
      {{left: "$$", right: "$$", display: true}},
      {{left: "\\\\[", right: "\\\\]", display: true}},
      {{left: "\\\\(", right: "\\\\)", display: false}}
    ]
  }});
</script>
</body>
</html>
"""
    (out_dir / "index.html").write_text(html_doc, encoding="utf-8")
    return out_dir
