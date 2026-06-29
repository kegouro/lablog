"""Construye y compila documentos LaTeX reales con Tectonic (XeTeX)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from lablog.ast_nodes import CellNode, DocumentNode, MathNode, Node, TextNode
from lablog.latex_ast import serialize_ast

_PREAMBLE = (
    "\\documentclass{article}\n"
    "\\usepackage{geometry}\n"
    "\\usepackage{fontspec}\n"
    "\\usepackage{amsmath,amssymb}\n"
    "\\usepackage{graphicx}\n"
    "\\usepackage{fancyvrb}\n"
    "\\usepackage{hyperref}\n"  # debe ir último
    "\\begin{document}\n"
)

_LATEX_ESCAPES = {
    "\\": "\\textbackslash{}", "&": "\\&", "%": "\\%", "$": "\\$",
    "#": "\\#", "_": "\\_", "{": "\\{", "}": "\\}",
    "~": "\\textasciitilde{}", "^": "\\textasciicircum{}",
}


def _escape_latex(text: str) -> str:
    return "".join(_LATEX_ESCAPES.get(ch, ch) for ch in text)


def figure_basename(figure_path: str) -> str:
    return Path(figure_path).name


@dataclass
class SourceMarker:
    tex_line: int
    kind: str
    ref: str


@dataclass
class CompileError:
    message: str
    source_line: int | None = None
    ref: str | None = None
    kind: str | None = None


def _verbatim(body: str) -> str:
    return (
        "\\begin{Verbatim}[breaklines=true,breakanywhere=true]\n"
        f"{body}\n"
        "\\end{Verbatim}\n"
    )


def build_document(doc: DocumentNode, title: str) -> tuple[str, list[SourceMarker], list[str]]:
    parts: list[str] = []
    markers: list[SourceMarker] = []
    figures: list[str] = []

    def cur_line() -> int:
        return sum(p.count("\n") for p in parts) + 1

    parts.append(_PREAMBLE)
    if title:
        parts.append(f"\\title{{{_escape_latex(title)}}}\n\\maketitle\n")

    buffer: list[Node] = []

    def flush() -> None:
        if not buffer:
            return
        markers.append(SourceMarker(cur_line(), "text", "prose"))
        parts.append("% lablog-src: kind=text ref=prose\n")
        parts.append(serialize_ast(DocumentNode(children=list(buffer))) + "\n")
        buffer.clear()

    for node in doc.children:
        if isinstance(node, CellNode):
            flush()
            markers.append(SourceMarker(cur_line(), "cell", node.cell_id))
            parts.append(f"% lablog-src: kind=cell ref={node.cell_id}\n")
            parts.append(_verbatim(node.source))
            if node.output:
                parts.append(_verbatim(node.output))
            if node.figure_path:
                figures.append(node.figure_path)
                parts.append(
                    f"\\includegraphics[width=\\linewidth]{{{figure_basename(node.figure_path)}}}\n"
                )
        elif isinstance(node, (TextNode, MathNode)):
            buffer.append(node)

    flush()
    parts.append("\\end{document}\n")
    return "".join(parts), markers, figures


def parse_errors(log: str, markers: list[SourceMarker]) -> list[CompileError]:
    ordered = sorted(markers, key=lambda m: m.tex_line)
    errors: list[CompileError] = []
    for m in re.finditer(r"(?:main\.tex|\.tex)?:(\d+):\s*(.+)", log):
        line = int(m.group(1))
        message = m.group(2).strip()
        marker = None
        for mk in ordered:
            if mk.tex_line <= line:
                marker = mk
            else:
                break
        errors.append(
            CompileError(
                message=message,
                source_line=line,
                ref=marker.ref if marker else None,
                kind=marker.kind if marker else None,
            )
        )
    return errors
