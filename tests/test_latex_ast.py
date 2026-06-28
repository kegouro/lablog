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
