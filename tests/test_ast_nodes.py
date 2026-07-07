from lablog.ast_nodes import CellNode


def test_cell_node_defaults_to_idle_status():
    cell = CellNode(cell_id="c1", language="python", source="1+1")
    assert cell.status == "idle"
