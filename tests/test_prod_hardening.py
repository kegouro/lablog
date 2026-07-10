"""Regresión de bugs de producción (soft-delete, parse, version, restore)."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from lablog import commands
from lablog.api import app
from lablog.ast_nodes import CellNode
from lablog.event_store import EventStore
from lablog.events import (
    cell_executed,
    cell_inserted,
    execution_failed,
    page_created,
)
from lablog.latex_ast import parse_latex, serialize_ast
from lablog.projector import project

client = TestClient(app)


def test_soft_deleted_rejects_writes() -> None:
    pid = client.post("/api/v1/pages", json={"title": "Del"}).json()["page_id"]
    assert client.delete(f"/api/v1/pages/{pid}").status_code == 204
    r = client.put(f"/api/v1/pages/{pid}", json={"raw": "nope"})
    assert r.status_code == 409
    r = client.post(
        f"/api/v1/pages/{pid}/cells",
        json={"cell_id": "c1", "language": "python", "source": "1"},
    )
    assert r.status_code == 409


def test_list_cells_deleted_is_404() -> None:
    pid = client.post("/api/v1/pages", json={"title": "C"}).json()["page_id"]
    client.delete(f"/api/v1/pages/{pid}")
    assert client.get(f"/api/v1/pages/{pid}/cells").status_code == 404


def test_version_conflict_on_put() -> None:
    pid = client.post("/api/v1/pages", json={"title": "V"}).json()["page_id"]
    detail = client.get(f"/api/v1/pages/{pid}").json()
    ver = detail["version"]
    assert client.put(f"/api/v1/pages/{pid}", json={"raw": "a", "version": ver}).status_code == 200
    # Versión vieja
    r = client.put(f"/api/v1/pages/{pid}", json={"raw": "b", "version": ver})
    assert r.status_code == 409
    assert r.json()["detail"]["error_code"] == "VERSION_CONFLICT"


def test_create_page_rejects_huge_title_and_project_id() -> None:
    huge = "x" * 10_000
    r = client.post("/api/v1/pages", json={"title": huge})
    assert r.status_code == 422
    r = client.post("/api/v1/pages", json={"title": "ok", "project_id": "p" * 500})
    assert r.status_code == 422


def test_page_detail_preserves_project_id_and_updated_at() -> None:
    """getPage no debe borrar project_id: el detail incluye metadatos de list."""
    res = client.post(
        "/api/v1/pages",
        json={"title": "Proyecto", "project_id": "lab-optics"},
    )
    assert res.status_code == 201
    pid = res.json()["page_id"]
    assert res.json()["project_id"] == "lab-optics"

    detail = client.get(f"/api/v1/pages/{pid}").json()
    assert detail["project_id"] == "lab-optics"
    assert detail["title"] == "Proyecto"
    assert detail.get("updated_at") is not None

    # Tras PUT raw se conserva el project_id
    ver = detail["version"]
    put = client.put(f"/api/v1/pages/{pid}", json={"raw": "x=1", "version": ver})
    assert put.status_code == 200
    assert put.json()["project_id"] == "lab-optics"


def test_document_env_does_not_swallow_python_cells() -> None:
    src = r"""\documentclass{article}
\begin{document}
\begin{python}[label=c1]
print(1)
\end{python}
\end{document}"""
    doc = parse_latex(src)
    cells = [c for c in doc.children if isinstance(c, CellNode)]
    assert len(cells) == 1
    assert cells[0].cell_id == "c1"
    assert "print(1)" in cells[0].source


def test_end_tag_in_source_roundtrips() -> None:
    doc = parse_latex("")  # empty
    from lablog.ast_nodes import DocumentNode

    doc = DocumentNode(
        children=[
            CellNode(
                cell_id="c1",
                language="python",
                source='print(r"\\end{python}")',
            )
        ]
    )
    again = parse_latex(serialize_ast(doc))
    cells = [c for c in again.children if isinstance(c, CellNode)]
    assert len(cells) == 1
    assert cells[0].source == 'print(r"\\end{python}")'


def test_restore_preserves_error_status(tmp_path: Path) -> None:
    store = EventStore(tmp_path)
    pid = str(uuid4())
    store.append(page_created(page_id=pid, title="R"))
    store.append(cell_inserted(page_id=pid, cell_id="c1", language="python", source="1/0"))
    store.append(
        execution_failed(
            page_id=pid,
            cell_id="c1",
            ename="ZeroDivisionError",
            evalue="div0",
            traceback=["ZeroDivisionError: div0"],
        )
    )
    # Un evento extra para poder restaurar al índice del fallo
    store.append(cell_executed(page_id=pid, cell_id="c1", output="ok", figure_path=None))
    commands.restore_version(store, pid, event_index=2)
    proj = project(pid, store.get_events(pid))
    cell = next(c for c in proj.ast.children if isinstance(c, CellNode))
    assert cell.status == "error"


def test_invalid_cell_id_rejected() -> None:
    pid = client.post("/api/v1/pages", json={"title": "I"}).json()["page_id"]
    r = client.post(
        f"/api/v1/pages/{pid}/cells",
        json={"cell_id": "bad]id", "language": "python", "source": "1"},
    )
    assert r.status_code == 422
