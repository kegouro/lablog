"""Exporta páginas lablog a un sitio estático listo para GitHub Pages."""

from __future__ import annotations

import html
import re
import shutil
from pathlib import Path
from typing import Any

from lablog.ast_nodes import CellNode, DocumentNode, MathNode, TextNode
from lablog.config import settings
from lablog.event_store import EventStore
from lablog.latex_ast import serialize_ast
from lablog.projector import project

_KATEX_CSS = "https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css"
_KATEX_JS = "https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"
_AUTO_RENDER_JS = "https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"


_INLINE_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\\(?:textbf|textmd)\{([^{}]*)\}"), r"<strong>\1</strong>"),
    (re.compile(r"\\(?:textit|emph|textsl)\{([^{}]*)\}"), r"<em>\1</em>"),
    (re.compile(r"\\underline\{([^{}]*)\}"), r"<u>\1</u>"),
    (re.compile(r"\\(?:texttt|verb)\{([^{}]*)\}"), r"<code>\1</code>"),
]

_HREF_RE = re.compile(r"\\href\{([^{}]*)\}\{([^{}]*)\}")
_URL_RE = re.compile(r"\\url\{([^{}]*)\}")
_SAFE_URL = re.compile(r"^(https?://|mailto:)", re.IGNORECASE)


def _safe_href(url: str, label: str) -> str:
    """Solo http(s)/mailto; escapa atributos para evitar XSS en export HTML."""
    cleaned = url.strip()
    if not _SAFE_URL.match(cleaned):
        return html.escape(label or cleaned)
    return (
        f'<a href="{html.escape(cleaned, quote=True)}">'
        f"{html.escape(label or cleaned)}</a>"
    )


def _items(body: str) -> str:
    pieces = body.split(r"\item")
    return "".join(f"<li>{_inline(chunk.strip())}</li>" for chunk in pieces[1:])


def _inline(text: str) -> str:
    for _ in range(6):
        before = text
        for pattern, repl in _INLINE_RULES:
            text = pattern.sub(repl, text)
        text = _HREF_RE.sub(lambda m: _safe_href(m.group(1), m.group(2)), text)
        text = _URL_RE.sub(lambda m: _safe_href(m.group(1), m.group(1)), text)
        if text == before:
            break
    return text.replace(r"\\", "<br/>")


def _render_prose(text: str) -> str:
    text = re.sub(
        r"\\begin\{itemize\}([\s\S]*?)\\end\{itemize\}",
        lambda m: f"<ul>{_items(m.group(1))}</ul>",
        text,
    )
    text = re.sub(
        r"\\begin\{enumerate\}([\s\S]*?)\\end\{enumerate\}",
        lambda m: f"<ol>{_items(m.group(1))}</ol>",
        text,
    )
    text = re.sub(r"\\section\*?\{([^{}]*)\}", r"<h2>\1</h2>", text)
    text = re.sub(r"\\subsection\*?\{([^{}]*)\}", r"<h3>\1</h3>", text)
    text = re.sub(r"\\subsubsection\*?\{([^{}]*)\}", r"<h4>\1</h4>", text)
    text = re.sub(
        r"\\(maketitle|tableofcontents|noindent|centering|clearpage|newpage|hline)\b\*?",
        "",
        text,
    )
    blocks = re.split(r"\n\s*\n", text)
    out: list[str] = []
    for raw in blocks:
        block = raw.strip()
        if not block:
            continue
        if re.match(r"^<(h[1-6]|ul|ol|div|table)", block):
            out.append(_inline(block))
        else:
            out.append(f"<p>{_inline(block.replace(chr(10), ' '))}</p>")
    return "\n".join(out)


def _ast_to_html(doc: DocumentNode, figure_base: str = "figures") -> str:
    """Render the document AST to HTML, coalescing prose for KaTeX auto-render.

    Sections, lists, emphasis and inline mathematics share the same paragraphs.
    Cells are split out so their code, output and figure are styled separately.
    """
    out: list[str] = []
    buffer: list[Any] = []

    def flush() -> None:
        if not buffer:
            return
        # Reconstruye el LaTeX original con las marcas de delimitadores que
        # KaTeX auto-render reconoce ($...$ y \[...\]).
        latex = serialize_ast(DocumentNode(children=list(buffer)))
        # KaTeX procesa la matemática en el navegador; aquí solo hacemos prosa.
        out.append(_render_prose(html.escape(latex, quote=False)))
        buffer.clear()

    for node in doc.children:
        if isinstance(node, CellNode):
            flush()
            code = (
                f'<pre class="code"><code class="language-{html.escape(node.language)}">'
                f"{html.escape(node.source)}</code></pre>"
            )
            parts = [code]
            if node.output:
                parts.append(f'<pre class="output">{html.escape(node.output)}</pre>')
            if node.figure_path:
                figure_name = Path(node.figure_path).name
                page_name = Path(node.figure_path).parent.name
                rel = f"{figure_base}/{page_name}/{figure_name}"
                parts.append(f'<img src="{rel}" alt="figura" loading="lazy">')
            out.append("\n".join(parts))
        elif isinstance(node, TextNode | MathNode):
            buffer.append(node)
    flush()
    return "\n".join(out)


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


_STYLE_CSS = """
:root {
  --bg: #1C1C1E;
  --surface: #242427;
  --divider: #48484A;
  --text: #F2F2F7;
  --muted: #A1A1A6;
  --accent: #F2F2F7;
}
* { box-sizing: border-box; }
body {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  max-width: 820px;
  margin: 0 auto;
  padding: 3rem 1.5rem;
  background: var(--bg);
  color: var(--text);
  line-height: 1.65;
}
header { border-bottom: 1px solid var(--divider); padding-bottom: 1.25rem; margin-bottom: 1.5rem; }
header h1 { font-size: 2rem; margin: 0; letter-spacing: -0.02em; }
header p { color: var(--muted); margin: 0.25rem 0 0; font-size: 0.95rem; }
nav {
  background: var(--surface);
  border: 1px solid var(--divider);
  border-radius: 12px;
  padding: 1rem 1.25rem;
  margin-bottom: 2rem;
}
nav h2 {
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--muted);
  margin: 0 0 0.5rem;
}
nav ul { margin: 0; padding-left: 1.1rem; }
nav a { color: var(--text); text-decoration: none; border-bottom: 1px dashed var(--divider); }
nav a:hover { border-bottom-color: var(--accent); }
section { border-top: 1px solid var(--divider); padding: 2rem 0; }
h2, h3, h4 { color: var(--text); letter-spacing: -0.01em; }
h2 { font-size: 1.45rem; margin: 0 0 1rem; }
h3 { font-size: 1.15rem; margin: 1.5rem 0 0.5rem; }
p { margin: 0.75rem 0; }
ul, ol { margin: 0.75rem 0 0.75rem 1.25rem; padding: 0; }
li { margin: 0.25rem 0; }
strong { color: var(--text); }
em { color: var(--text); }
a { color: var(--text); }
code {
  background: var(--surface);
  border: 1px solid var(--divider);
  border-radius: 4px;
  padding: 0.05rem 0.35rem;
  font-size: 0.9em;
}
pre {
  background: var(--surface);
  border: 1px solid var(--divider);
  padding: 1rem;
  border-radius: 8px;
  overflow-x: auto;
  font-size: 0.9rem;
}
pre.code code { background: transparent; border: 0; padding: 0; }
pre.output { background: #1f2a1f; border-color: #2d4a2d; color: #d3eed3; }
img { max-width: 100%; height: auto; border-radius: 8px; border: 1px solid var(--divider); }
.katex-display { overflow-x: auto; overflow-y: hidden; }
"""


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
<link rel="preconnect" href="https://rsms.me">
<link rel="stylesheet" href="https://rsms.me/inter/inter.css">
<style>
{_STYLE_CSS}
</style>
</head>
<body>
<header>
<h1>lablog</h1>
<p>A live LaTeX laboratory notebook for working scientists &mdash; static preview.</p>
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
      {{left: "$", right: "$", display: false}},
      {{left: "\\\\(", right: "\\\\)", display: false}}
    ],
    throwOnError: false
  }});
</script>
</body>
</html>
"""
    (out_dir / "index.html").write_text(html_doc, encoding="utf-8")
    return out_dir
