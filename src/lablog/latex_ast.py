"""Parser y serializador mínimo LaTeX ↔ AST."""

from __future__ import annotations

import re

from lablog.ast_nodes import CellNode, DocumentNode, MathNode, Node, TextNode


def parse_latex(source: str) -> DocumentNode:
    """Parsea un string LaTeX a un AST mínimo."""
    doc = DocumentNode()
    remaining = source

    # Patrón para celdas ejecutables
    cell_pattern = re.compile(
        r"\\begin\{([a-zA-Z0-9_]+)\}\s*\[(.*?)\](.*?)\\end\{\1\}",
        re.DOTALL,
    )
    # Patrón simple para celdas sin opciones
    cell_pattern_no_opts = re.compile(
        r"\\begin\{([a-zA-Z0-9_]+)\}(.*?)\\end\{\1\}",
        re.DOTALL,
    )

    # Matemática display $$ ... $$
    display_block_pattern = re.compile(r"\$\$(.*?)\$\$", re.DOTALL)
    # Matemática display \[ ... \]
    display_math_pattern = re.compile(r"\\\[(.*?)\\\]", re.DOTALL)
    # Matemática inline $ ... $
    inline_math_pattern = re.compile(r"\$(.*?)\$", re.DOTALL)

    while remaining:
        # Buscar el siguiente token especial
        matches: list[tuple[int, int, str, Node]] = []

        for m in cell_pattern.finditer(remaining):
            lang = m.group(1)
            opts = m.group(2)
            source_code = m.group(3).strip()
            cell_id = _extract_option(opts, "label") or _extract_option(opts, "id") or "cell_1"
            matches.append(
                (
                    m.start(),
                    m.end(),
                    "cell",
                    CellNode(
                        cell_id=cell_id,
                        language=lang,
                        source=source_code,
                    ),
                )
            )

        if not matches:
            for m in cell_pattern_no_opts.finditer(remaining):
                lang = m.group(1)
                source_code = m.group(2).strip()
                matches.append(
                    (
                        m.start(),
                        m.end(),
                        "cell",
                        CellNode(
                            cell_id="cell_1",
                            language=lang,
                            source=source_code,
                        ),
                    )
                )

        for m in display_block_pattern.finditer(remaining):
            matches.append(
                (
                    m.start(),
                    m.end(),
                    "math",
                    MathNode(
                        latex=m.group(1).strip(),
                        mode="display",
                    ),
                )
            )

        for m in display_math_pattern.finditer(remaining):
            matches.append(
                (
                    m.start(),
                    m.end(),
                    "math",
                    MathNode(
                        latex=m.group(1).strip(),
                        mode="display",
                    ),
                )
            )

        for m in inline_math_pattern.finditer(remaining):
            matches.append(
                (
                    m.start(),
                    m.end(),
                    "math",
                    MathNode(
                        latex=m.group(1).strip(),
                        mode="inline",
                    ),
                )
            )

        if not matches:
            doc.children.append(TextNode(text=remaining))
            break

        # Tomar el match más cercano al inicio
        matches.sort(key=lambda x: x[0])
        start, end, _kind, node = matches[0]

        if start > 0:
            doc.children.append(TextNode(text=remaining[:start]))

        doc.children.append(node)
        remaining = remaining[end:]

    return doc


def serialize_ast(doc: DocumentNode) -> str:
    """Serializa un AST a string LaTeX."""
    parts: list[str] = []
    for child in doc.children:
        parts.append(_serialize_node(child))
    return "".join(parts)


def _serialize_node(node: Node) -> str:
    match node:
        case TextNode(text=text):
            return text
        case MathNode(latex=latex, mode="display"):
            latex = latex.strip()
            if latex.startswith("\\[") and latex.endswith("\\]"):
                return latex
            if latex.startswith("$$") and latex.endswith("$$"):
                return latex
            return f"\\[{latex}\\]"
        case MathNode(latex=latex, mode="inline"):
            latex = latex.strip()
            if latex.startswith("$") and latex.endswith("$"):
                return latex
            return f"${latex}$"
        case CellNode(cell_id=cell_id, language=language, source=source):
            return f"\\begin{{{language}}}[label={cell_id}]\n{source}\n\\end{{{language}}}"
        case _:
            return ""


def _extract_option(options: str, key: str) -> str | None:
    """Extrae una opción tipo key=value de un string."""
    pattern = re.compile(rf"\b{re.escape(key)}\s*=\s*([^,\]]+)")
    m = pattern.search(options)
    return m.group(1).strip() if m else None
