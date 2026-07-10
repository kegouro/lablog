"""Parser y serializador mínimo LaTeX ↔ AST."""

from __future__ import annotations

import re

from lablog.ast_nodes import CellNode, DocumentNode, MathNode, Node, TextNode

# Lenguajes que lablog ejecuta como celdas de código. Cualquier otro
# \begin{...} (align, equation, itemize, figure, table, …) es LaTeX normal
# y se preserva verbatim para que lo renderice el preview, no una celda.
# Incluye lenguajes de texto del lab (markdown/latex) para round-trip por
# document_replaced: sin esto se pierden como CellNode al re-parsear.
CODE_ENVIRONMENTS = frozenset(
    {
        "python",
        "py",
        "code",
        "sage",
        "julia",
        "r",
        "octave",
        "bash",
        "sh",
        "markdown",
        "latex",
    }
)


def parse_latex(source: str) -> DocumentNode:
    """Parsea un string LaTeX a un AST mínimo."""
    doc = DocumentNode()
    remaining = source
    cell_counter = 0

    # Patrón unificado para celdas ejecutables con o sin opciones.
    cell_pattern = re.compile(
        r"\\begin\{([a-zA-Z0-9_]+)\}(?:\s*\[(.*?)\])?(.*?)\\end\{\1\}",
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
            if lang not in CODE_ENVIRONMENTS:
                continue
            opts = m.group(2) or ""
            source_code = m.group(3).strip()
            cell_id = _extract_option(opts, "label") or _extract_option(opts, "id") or ""
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

        # Asigna un id único a celdas sin label (evita colisiones "cell_1").
        if isinstance(node, CellNode) and not node.cell_id:
            cell_counter += 1
            node.cell_id = f"cell_{cell_counter}"

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
