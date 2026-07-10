from lablog.ast_nodes import CellNode, MathNode, TextNode, node_to_json


def test_cell_node_defaults_to_idle_status():
    cell = CellNode(cell_id="c1", language="python", source="1+1")
    assert cell.status == "idle"


def test_node_to_json_serializes_all_fields():
    cell = CellNode(cell_id="c1", language="python", source="1+1", status="ok")
    assert node_to_json(cell) == {
        "type": "cell",
        "cell_id": "c1",
        "language": "python",
        "source": "1+1",
        "output": None,
        "figure_path": None,
        "status": "ok",
    }


def test_node_to_json_serializes_text_and_math():
    assert node_to_json(TextNode(text="hello")) == {"type": "text", "text": "hello"}
    assert node_to_json(MathNode(latex="x^2", mode="inline")) == {
        "type": "math",
        "latex": "x^2",
        "mode": "inline",
    }
