"""Tests del parser/serializador LaTeX ↔ AST."""

from __future__ import annotations

from lablog.ast_nodes import CellNode, MathNode, TextNode
from lablog.latex_ast import parse_latex, serialize_ast


def test_parse_text_only() -> None:
    doc = parse_latex("Hola mundo")
    assert len(doc.children) == 1
    assert isinstance(doc.children[0], TextNode)
    assert doc.children[0].text == "Hola mundo"


def test_parse_inline_math() -> None:
    doc = parse_latex("La energía es $E=mc^2$")
    assert len(doc.children) == 2
    assert isinstance(doc.children[0], TextNode)
    assert isinstance(doc.children[1], MathNode)
    assert doc.children[1].latex == "E=mc^2"
    assert doc.children[1].mode == "inline"


def test_parse_display_math() -> None:
    doc = parse_latex("\\[ \\int_0^1 x dx \\]")
    assert len(doc.children) == 1
    assert isinstance(doc.children[0], MathNode)
    assert doc.children[0].latex == "\\int_0^1 x dx"
    assert doc.children[0].mode == "display"


def test_parse_cell() -> None:
    source = "\\begin{python}[label=fig1]\nprint(1)\n\\end{python}"
    doc = parse_latex(source)
    assert len(doc.children) == 1
    assert isinstance(doc.children[0], CellNode)
    assert doc.children[0].cell_id == "fig1"
    assert doc.children[0].language == "python"
    assert "print(1)" in doc.children[0].source


def test_roundtrip() -> None:
    original = "Texto $x^2$ más \\[ \\int_a^b f(x) dx \\]"
    doc = parse_latex(original)
    restored = serialize_ast(doc)
    # El parser normaliza espacios alrededor de math, pero preserva el contenido
    assert "Texto" in restored
    assert "$x^2$" in restored
    assert "\\[\\int_a^b f(x) dx\\]" in restored


def test_roundtrip_cell() -> None:
    original = "\\begin{python}[label=fig1]\nprint(1)\n\\end{python}"
    doc = parse_latex(original)
    restored = serialize_ast(doc)
    assert restored == original


def test_math_environment_is_not_a_cell() -> None:
    # Regresión: \begin{align} se trataba como celda ejecutable.
    for env in ("align", "equation", "gather", "itemize", "figure", "table"):
        src = f"\\begin{{{env}}}\nE = mc^2\n\\end{{{env}}}"
        doc = parse_latex(src)
        assert all(not isinstance(c, CellNode) for c in doc.children), env
        # Se preserva verbatim para el round-trip y el preview.
        assert serialize_ast(doc) == src, env


def test_code_environment_is_a_cell() -> None:
    for lang in ("python", "bash", "julia", "r"):
        src = f"\\begin{{{lang}}}\nx = 1\n\\end{{{lang}}}"
        doc = parse_latex(src)
        assert any(isinstance(c, CellNode) for c in doc.children), lang


def test_markdown_and_latex_lab_cells_roundtrip() -> None:
    """Celdas de texto del lab sobreviven serialize → parse (document_replaced)."""
    for lang in ("markdown", "latex"):
        src = f"\\begin{{{lang}}}[label=lab1]\nhola $x$\n\\end{{{lang}}}"
        doc = parse_latex(src)
        cells = [c for c in doc.children if isinstance(c, CellNode)]
        assert len(cells) == 1, lang
        assert cells[0].cell_id == "lab1"
        assert cells[0].language == lang
        again = parse_latex(serialize_ast(doc))
        cells2 = [c for c in again.children if isinstance(c, CellNode)]
        assert len(cells2) == 1 and cells2[0].cell_id == "lab1"


def test_parse_mixed_cells_with_and_without_options() -> None:
    """Regresión: celdas sin [options] deben parsearse junto a celdas con options."""
    source = (
        "\\begin{python}\nprint(1)\n\\end{python}\n"
        "\\begin{python}[label=second]\nprint(2)\n\\end{python}\n"
        "\\begin{python}\nprint(3)\n\\end{python}"
    )
    doc = parse_latex(source)
    cells = [c for c in doc.children if isinstance(c, CellNode)]
    assert len(cells) == 3
    assert cells[0].cell_id == "cell_1"
    assert cells[0].source == "print(1)"
    assert cells[1].cell_id == "second"
    assert cells[1].source == "print(2)"
    assert cells[2].cell_id == "cell_2"
    assert cells[2].source == "print(3)"
