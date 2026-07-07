"""Tests de proyección de páginas."""

from __future__ import annotations

from uuid import uuid4

from lablog.ast_nodes import CellNode, MathNode, TextNode
from lablog.events import (
    cell_executed,
    cell_inserted,
    cell_moved,
    execution_failed,
    math_inserted,
    page_created,
    text_inserted,
)
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


def test_move_cell_preserves_document_order() -> None:
    # Regresión: _move_cell movía todo el texto antes de las celdas.
    page_id = str(uuid4())
    events = [
        page_created(page_id=page_id, title="Test"),
        cell_inserted(page_id=page_id, cell_id="a", language="python", source="1"),
        text_inserted(page_id=page_id, position=-1, text="entre celdas"),
        cell_inserted(page_id=page_id, cell_id="b", language="python", source="2"),
        cell_moved(page_id=page_id, cell_id="a", new_index=1),
    ]
    children = project(page_id, events).ast.children
    kinds = [type(c).__name__ for c in children]
    # El TextNode sigue en su slot; solo se reordenan las celdas.
    assert kinds == ["CellNode", "TextNode", "CellNode"]
    cell_ids = [c.cell_id for c in children if isinstance(c, CellNode)]
    assert cell_ids == ["b", "a"]


def test_execution_failed_sets_cell_error_status():
    page_id = str(uuid4())
    events = [
        page_created(page_id=page_id, title="Test"),
        cell_inserted(page_id=page_id, cell_id="c1", language="python", source="1/0"),
        execution_failed(
            page_id=page_id,
            cell_id="c1",
            ename="ZeroDivisionError",
            evalue="division by zero",
            traceback=["ZeroDivisionError: division by zero"],
        ),
    ]
    proj = project(page_id, events)
    cell = proj.ast.children[0]
    assert cell.status == "error"
    assert "ZeroDivisionError" in cell.output


def test_cell_executed_sets_cell_ok_status():
    page_id = str(uuid4())
    events = [
        page_created(page_id=page_id, title="Test"),
        cell_inserted(page_id=page_id, cell_id="c1", language="python", source="1+1"),
        cell_executed(page_id=page_id, cell_id="c1", output="2"),
    ]
    proj = project(page_id, events)
    assert proj.ast.children[0].status == "ok"
    assert proj.ast.children[0].output == "2"
