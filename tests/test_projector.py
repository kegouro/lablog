"""Tests de proyección de páginas."""

from __future__ import annotations

from uuid import uuid4

from lablog.ast_nodes import MathNode, TextNode
from lablog.events import math_inserted, page_created, text_inserted
from lablog.projector import project


def test_project_page_created() -> None:
    page_id = str(uuid4())
    events = [page_created(page_id=page_id, title="Experimento")]
    projection = project(page_id, events)

    assert projection.title == "Experimento"
    assert projection.ast.title == "Experimento"


def test_project_text_inserted() -> None:
    page_id = str(uuid4())
    events = [
        page_created(page_id=page_id, title="Test"),
        text_inserted(page_id=page_id, position=0, text="Hola "),
        text_inserted(page_id=page_id, position=-1, text="mundo"),
    ]
    projection = project(page_id, events)

    assert len(projection.ast.children) == 1
    assert isinstance(projection.ast.children[0], TextNode)
    assert projection.ast.children[0].text == "Hola mundo"


def test_project_math_inserted() -> None:
    page_id = str(uuid4())
    events = [
        page_created(page_id=page_id, title="Test"),
        text_inserted(page_id=page_id, position=0, text="Resultado: "),
        math_inserted(page_id=page_id, ast_path="", latex="E=mc^2", mode="inline"),
    ]
    projection = project(page_id, events)

    assert len(projection.ast.children) == 2
    assert isinstance(projection.ast.children[0], TextNode)
    assert isinstance(projection.ast.children[1], MathNode)
    assert projection.ast.children[1].latex == "E=mc^2"
    assert projection.ast.children[1].mode == "inline"
