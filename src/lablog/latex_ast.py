"""Parser y serializador mínimo LaTeX ↔ AST."""

from __future__ import annotations

import re

from lablog.ast_nodes import CellNode, DocumentNode, MathNode, Node, TextNode

# Lenguajes de celda lablog. Cualquier otro \begin{...} se preserva como texto.
# Incluye markdown/latex para round-trip de celdas de texto del lab.
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

# Solo estos nombres entran en el patrón: evita que \begin{document} consuma
# el span y se trague celdas anidadas (finditer no solapa matches).
_CODE_LANG_ALT = "|".join(
    sorted((re.escape(lang) for lang in CODE_ENVIRONMENTS), key=len, reverse=True)
)
# Marca en source al serializar \end{...} literal para no cortar el parse.
_END_ESCAPE = "\\end\u200b{"


def parse_latex(source: str) -> DocumentNode:
    """Parsea un string LaTeX a un AST mínimo."""
    doc = DocumentNode()
    remaining = source
    cell_counter = 0

    display_block_pattern = re.compile(r"\$\$(.*?)\$\$", re.DOTALL)
    display_math_pattern = re.compile(r"\\\[(.*?)\\\]", re.DOTALL)
    inline_math_pattern = re.compile(r"\$(.*?)\$", re.DOTALL)

    while remaining:
        matches: list[tuple[int, int, str, Node]] = []

        cell_hit = _find_next_cell(remaining)
        if cell_hit is not None:
            start, end, lang, opts, body = cell_hit
            cell_id = _extract_option(opts, "label") or _extract_option(opts, "id") or ""
            matches.append(
                (
                    start,
                    end,
                    "cell",
                    CellNode(
                        cell_id=cell_id,
                        language=lang,
                        source=_unescape_cell_source(body.strip()),
                    ),
                )
            )

        for m in display_block_pattern.finditer(remaining):
            matches.append(
                (
                    m.start(),
                    m.end(),
                    "math",
                    MathNode(latex=m.group(1).strip(), mode="display"),
                )
            )

        for m in display_math_pattern.finditer(remaining):
            matches.append(
                (
                    m.start(),
                    m.end(),
                    "math",
                    MathNode(latex=m.group(1).strip(), mode="display"),
                )
            )

        for m in inline_math_pattern.finditer(remaining):
            matches.append(
                (
                    m.start(),
                    m.end(),
                    "math",
                    MathNode(latex=m.group(1).strip(), mode="inline"),
                )
            )

        if not matches:
            doc.children.append(TextNode(text=remaining))
            break

        matches.sort(key=lambda x: x[0])
        start, end, _kind, node = matches[0]

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
    return "".join(_serialize_node(child) for child in doc.children)


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
            safe_id = _safe_cell_id_for_label(cell_id)
            safe_src = _escape_cell_source(source)
            return f"\\begin{{{language}}}[label={safe_id}]\n{safe_src}\n\\end{{{language}}}"
        case _:
            return ""


def _find_next_cell(text: str) -> tuple[int, int, str, str, str] | None:
    """Localiza la primera celda de código con matching balanceado begin/end."""
    begin_re = re.compile(
        rf"\\begin\{{({_CODE_LANG_ALT})\}}(?:\s*\[(.*?)\])?",
        re.DOTALL,
    )
    m = begin_re.search(text)
    if m is None:
        return None
    lang = m.group(1)
    opts = m.group(2) or ""
    body_start = m.end()
    begin_lang = re.compile(rf"\\begin\{{{re.escape(lang)}\}}")
    end_lang = re.compile(rf"\\end\{{{re.escape(lang)}\}}")
    depth = 1
    pos = body_start
    while depth > 0:
        b = begin_lang.search(text, pos)
        e = end_lang.search(text, pos)
        if e is None:
            return None
        if b is not None and b.start() < e.start():
            depth += 1
            pos = b.end()
            continue
        depth -= 1
        if depth == 0:
            body = text[body_start : e.start()]
            return m.start(), e.end(), lang, opts, body
        pos = e.end()
    return None


def _escape_cell_source(source: str) -> str:
    """Evita que un \\end{...} literal en el código cierre el entorno al re-parsear."""
    return source.replace("\\end{", _END_ESCAPE)


def _unescape_cell_source(source: str) -> str:
    return source.replace(_END_ESCAPE, "\\end{")


def _safe_cell_id_for_label(cell_id: str) -> str:
    """Labels sin comas ni ] para no romper el option parser."""
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "_", cell_id or "")
    return cleaned[:64] or "cell"


def _extract_option(options: str, key: str) -> str | None:
    """Extrae una opción tipo key=value de un string."""
    pattern = re.compile(rf"\b{re.escape(key)}\s*=\s*([^,\]]+)")
    m = pattern.search(options)
    return m.group(1).strip() if m else None
