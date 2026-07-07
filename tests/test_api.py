"""Tests del servidor API."""

from __future__ import annotations

from datetime import UTC
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from lablog.api import app
from lablog.ast_nodes import CellNode
from lablog.code_engine import CodeEngine, EngineStartError

client = TestClient(app)


def test_create_and_get_page() -> None:
    res = client.post("/api/v1/pages", json={"title": "Test"})
    assert res.status_code == 201
    page_id = res.json()["page_id"]

    res = client.get(f"/api/v1/pages/{page_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Test"
    assert data["latex"] == ""


def test_append_text() -> None:
    res = client.post("/api/v1/pages", json={"title": "T"})
    page_id = res.json()["page_id"]

    res = client.post(f"/api/v1/pages/{page_id}/text", json={"text": "hola "})
    assert res.status_code == 201

    res = client.get(f"/api/v1/pages/{page_id}/latex")
    assert res.json()["latex"] == "hola "


def test_replace_page() -> None:
    res = client.post("/api/v1/pages", json={"title": "R"})
    page_id = res.json()["page_id"]

    client.post(f"/api/v1/pages/{page_id}/text", json={"text": "old text"})
    res = client.post(f"/api/v1/pages/{page_id}/replace", json={"latex": "new latex"})
    assert res.status_code == 201

    res = client.get(f"/api/v1/pages/{page_id}/latex")
    assert res.json()["latex"] == "new latex"


def test_put_page_raw_returns_ast_and_version() -> None:
    res = client.post("/api/v1/pages", json={"title": "Put"})
    page_id = res.json()["page_id"]

    res = client.put(f"/api/v1/pages/{page_id}", json={"raw": "Hola $x^2$"})
    assert res.status_code == 200
    data = res.json()
    assert data["page_id"] == page_id
    assert data["title"] == "Put"
    assert data["raw"] == "Hola $x^2$"
    assert data["latex"] == data["raw"]
    assert isinstance(data["ast"], list)
    assert data["version"] == 2  # page_created + document_replaced

    # El AST refleja el texto y la matemática inline.
    node_types = {n["type"] for n in data["ast"]}
    assert "text" in node_types
    assert "math" in node_types


def test_put_page_raw_overwrites_previous_content() -> None:
    res = client.post("/api/v1/pages", json={"title": "Overwrite"})
    page_id = res.json()["page_id"]

    client.put(f"/api/v1/pages/{page_id}", json={"raw": "first"})
    res = client.put(f"/api/v1/pages/{page_id}", json={"raw": "second"})
    assert res.status_code == 200
    assert res.json()["raw"] == "second"
    assert res.json()["version"] == 3

    res = client.get(f"/api/v1/pages/{page_id}")
    assert res.json()["raw"] == "second"


def test_put_page_raw_missing_payload_returns_422() -> None:
    res = client.post("/api/v1/pages", json={"title": "Payload"})
    page_id = res.json()["page_id"]

    res = client.put(f"/api/v1/pages/{page_id}", json={})
    assert res.status_code == 422


def test_put_page_raw_not_found_returns_404() -> None:
    res = client.put("/api/v1/pages/00000000-0000-0000-0000-000000000000", json={"raw": "x"})
    assert res.status_code == 404


def test_insert_math() -> None:
    res = client.post("/api/v1/pages", json={"title": "M"})
    page_id = res.json()["page_id"]

    client.post(f"/api/v1/pages/{page_id}/text", json={"text": "La integral es "})

    url = f"/api/v1/pages/{page_id}/math"
    res = client.post(url, json={"latex": "\\int_0^1 x dx", "mode": "display"})
    assert res.status_code == 201

    res = client.get(f"/api/v1/pages/{page_id}/latex")
    assert "\\[\\int_0^1 x dx\\]" in res.json()["latex"]


def test_voice_endpoint() -> None:
    res = client.post("/api/v1/pages", json={"title": "V"})
    page_id = res.json()["page_id"]

    url = f"/api/v1/pages/{page_id}/voice"
    res = client.post(url, json={"text": "integral de cero a infinito"})
    assert res.status_code == 201
    assert res.json()["intent"] == "integral"

    res = client.get(f"/api/v1/pages/{page_id}/latex")
    assert "\\int" in res.json()["latex"]


def test_list_pages() -> None:
    res = client.get("/api/v1/pages")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_404() -> None:
    res = client.get("/api/v1/pages/no-existe")
    assert res.status_code == 404


def test_insert_and_execute_cell() -> None:
    res = client.post("/api/v1/pages", json={"title": "Cell"})
    page_id = res.json()["page_id"]

    res = client.post(
        f"/api/v1/pages/{page_id}/cells",
        json={"cell_id": "c1", "language": "python", "source": "2 + 2"},
    )
    assert res.status_code == 201

    res = client.post(f"/api/v1/pages/{page_id}/cells/c1/execute")
    assert res.status_code == 201
    assert res.json()["status"] == "ok"
    assert "4" in res.json()["output"]


def test_list_snippets() -> None:
    res = client.get("/api/v1/snippets")
    assert res.status_code == 200
    data = res.json()
    assert len(data) > 0
    assert "line_plot" in [s["id"] for s in data]


def test_render_snippet() -> None:
    res = client.post(
        "/api/v1/snippets/line_plot/render",
        json={"values": {"x0": 0, "x1": 5, "y0": 0, "y1": 5}},
    )
    assert res.status_code == 200
    assert "plt.plot([0, 5], [0, 5], marker='o')" in res.json()["code"]


def test_latex_symbols_and_favorites() -> None:
    res = client.get("/api/v1/latex-symbols")
    assert res.status_code == 200
    assert any(s["id"] == "alpha" for s in res.json())

    res = client.post("/api/v1/latex-symbols/favorites/alpha")
    assert res.status_code == 201

    res = client.get("/api/v1/latex-symbols/favorites")
    assert res.status_code == 200
    assert "alpha" in res.json()

    res = client.delete("/api/v1/latex-symbols/favorites/alpha")
    assert res.status_code == 204

    res = client.get("/api/v1/latex-symbols/favorites")
    assert "alpha" not in res.json()


def test_engine_status_shape() -> None:
    r = client.get("/api/v1/pdf/engine-status")
    assert r.status_code == 200
    assert {"binary_ready", "bundle_warmed", "update_available"} <= set(r.json())


def test_pdf_export_503_without_engine(monkeypatch) -> None:
    from lablog import pdf_engine
    monkeypatch.setattr(pdf_engine, "tectonic_path", lambda **_: None)
    pid = client.post("/api/v1/pages", json={"title": "X"}).json()["page_id"]
    r = client.get(f"/api/v1/pages/{pid}/export/pdf")
    assert r.status_code == 503


def test_history_shape_and_time_travel() -> None:
    pid = client.post("/api/v1/pages", json={"title": "TT"}).json()["page_id"]
    client.post(f"/api/v1/pages/{pid}/replace", json={"latex": "A"})
    client.post(f"/api/v1/pages/{pid}/replace", json={"latex": "A B"})

    history = client.get(f"/api/v1/pages/{pid}/history").json()
    assert len(history) == 3
    assert {"index", "type", "timestamp", "summary"} <= set(history[0])
    assert history[0]["type"] == "page_created"

    assert client.get(f"/api/v1/pages/{pid}/at/1").json()["latex"] == "A"
    # clamp documentado: índice alto → estado final; negativo → primer evento
    assert client.get(f"/api/v1/pages/{pid}/at/999").json()["latex"] == "A B"
    assert client.get(f"/api/v1/pages/{pid}/at/-5").status_code == 200


def test_restore_appends_and_matches_past_state() -> None:
    pid = client.post("/api/v1/pages", json={"title": "TT2"}).json()["page_id"]
    client.post(f"/api/v1/pages/{pid}/replace", json={"latex": "v1"})
    client.post(f"/api/v1/pages/{pid}/replace", json={"latex": "v2"})
    before = len(client.get(f"/api/v1/pages/{pid}/events").json())

    restored = client.post(f"/api/v1/pages/{pid}/restore/1")
    assert restored.status_code == 200
    assert restored.json()["latex"] == "v1"
    assert len(client.get(f"/api/v1/pages/{pid}/events").json()) == before + 1
    # la historia previa sigue intacta (append-only)
    assert client.get(f"/api/v1/pages/{pid}/at/2").json()["latex"] == "v2"


def test_restore_deleted_page_is_conflict() -> None:
    pid = client.post("/api/v1/pages", json={"title": "TT3"}).json()["page_id"]
    client.delete(f"/api/v1/pages/{pid}")
    assert client.post(f"/api/v1/pages/{pid}/restore/0").status_code == 409


def test_health_includes_engine_readiness() -> None:
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "engine_ready" in data
    assert isinstance(data["engine_ready"], bool)
    assert {"pandoc", "xelatex", "pdflatex"} <= set(data["tools"])


def test_invalid_page_id_returns_400_for_command() -> None:
    res = client.post("/api/v1/pages/not-a-uuid/text", json={"text": "hola"})
    assert res.status_code == 400
    assert "page_id inválido" in res.json()["detail"]


_CELL_PAYLOAD = {"cell_id": "c", "language": "python", "source": ""}


@pytest.mark.parametrize(
    "method, url, payload",
    [
        ("patch", "/api/v1/pages/{pid}", {"title": "x"}),
        ("put", "/api/v1/pages/{pid}", {"raw": "x"}),
        ("delete", "/api/v1/pages/{pid}", None),
        ("post", "/api/v1/pages/{pid}/replace", {"latex": "x"}),
        ("post", "/api/v1/pages/{pid}/math", {"latex": "x"}),
        ("post", "/api/v1/pages/{pid}/voice", {"text": "x"}),
        ("post", "/api/v1/pages/{pid}/restore/0", None),
        ("post", "/api/v1/pages/{pid}/cells", _CELL_PAYLOAD),
        ("post", "/api/v1/pages/{pid}/cells/c/update", _CELL_PAYLOAD),
        ("post", "/api/v1/pages/{pid}/cells/c/execute", None),
        ("delete", "/api/v1/pages/{pid}/cells/c", None),
        ("post", "/api/v1/pages/{pid}/cells/c/move", {"new_index": 0}),
    ],
)
def test_invalid_page_id_returns_400_for_various_commands(
    method: str,
    url: str,
    payload: dict | None,
) -> None:
    url = url.format(pid="not-a-uuid")
    caller = getattr(client, method)
    kwargs = {"json": payload} if payload is not None else {}
    res = caller(url, **kwargs)
    assert res.status_code == 400
    assert "page_id inválido" in res.json()["detail"]


def test_execute_cell_unsupported_language_returns_422() -> None:
    pid = client.post("/api/v1/pages", json={"title": "Lang"}).json()["page_id"]
    client.post(
        f"/api/v1/pages/{pid}/cells",
        json={"cell_id": "md1", "language": "markdown", "source": "# hi"},
    )
    res = client.post(f"/api/v1/pages/{pid}/cells/md1/execute")
    assert res.status_code == 422
    assert "Lenguaje no soportado" in res.json()["detail"]


def test_execute_cell_engine_unavailable_returns_503(monkeypatch) -> None:
    pid = client.post("/api/v1/pages", json={"title": "EngineDown"}).json()["page_id"]
    client.post(
        f"/api/v1/pages/{pid}/cells",
        json={"cell_id": "c1", "language": "python", "source": "1 + 1"},
    )

    def _broken_engine() -> CodeEngine:
        raise EngineStartError("kernel caído")

    monkeypatch.setattr("lablog.api.get_engine", _broken_engine)
    res = client.post(f"/api/v1/pages/{pid}/cells/c1/execute")
    assert res.status_code == 503
    assert "kernel caído" in res.json()["detail"]


def test_update_cell_and_list_cells() -> None:
    pid = client.post("/api/v1/pages", json={"title": "Cells"}).json()["page_id"]
    client.post(
        f"/api/v1/pages/{pid}/cells",
        json={"cell_id": "c1", "language": "python", "source": "1"},
    )
    res = client.post(
        f"/api/v1/pages/{pid}/cells/c1/update",
        json={"cell_id": "c1", "language": "python", "source": "2"},
    )
    assert res.status_code == 200

    res = client.get(f"/api/v1/pages/{pid}/cells")
    assert res.status_code == 200
    cells = res.json()
    assert len(cells) == 1
    assert cells[0]["source"] == "2"


def test_move_and_delete_cell() -> None:
    pid = client.post("/api/v1/pages", json={"title": "Move"}).json()["page_id"]
    for i in range(3):
        client.post(
            f"/api/v1/pages/{pid}/cells",
            json={"cell_id": f"c{i}", "language": "python", "source": str(i)},
        )
    res = client.post(f"/api/v1/pages/{pid}/cells/c0/move", json={"new_index": 2})
    assert res.status_code == 200

    res = client.delete(f"/api/v1/pages/{pid}/cells/c1")
    assert res.status_code == 204

    res = client.get(f"/api/v1/pages/{pid}/cells")
    ids = [c["cell_id"] for c in res.json()]
    assert "c1" not in ids
    assert ids == ["c2", "c0"]


def test_get_cell_figure() -> None:
    pid = client.post("/api/v1/pages", json={"title": "Fig"}).json()["page_id"]
    client.post(
        f"/api/v1/pages/{pid}/cells",
        json={
            "cell_id": "plot",
            "language": "python",
            "source": "import matplotlib.pyplot as plt\nplt.plot([1,2],[3,4])",
        },
    )
    res = client.post(f"/api/v1/pages/{pid}/cells/plot/execute")
    assert res.status_code == 201
    assert res.json()["figure_paths"]

    res = client.get(f"/api/v1/pages/{pid}/cells/plot/figure")
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/png"


def test_execute_cell_not_found() -> None:
    pid = client.post("/api/v1/pages", json={"title": "NoCell"}).json()["page_id"]
    res = client.post(f"/api/v1/pages/{pid}/cells/missing/execute")
    assert res.status_code == 404


def test_get_cell_figure_not_found() -> None:
    pid = client.post("/api/v1/pages", json={"title": "NoFig"}).json()["page_id"]
    client.post(
        f"/api/v1/pages/{pid}/cells",
        json={"cell_id": "c1", "language": "python", "source": "1"},
    )
    res = client.get(f"/api/v1/pages/{pid}/cells/c1/figure")
    assert res.status_code == 404


def test_update_page_title() -> None:
    pid = client.post("/api/v1/pages", json={"title": "Old"}).json()["page_id"]
    res = client.patch(f"/api/v1/pages/{pid}", json={"title": "New"})
    assert res.status_code == 200
    assert res.json()["title"] == "New"


def test_export_tex_txt_canva() -> None:
    pid = client.post("/api/v1/pages", json={"title": "Export Me"}).json()["page_id"]
    client.post(f"/api/v1/pages/{pid}/text", json={"text": "Hola $x^2$"})

    cases = (
        ("tex", "application/x-tex", "Export Me"),
        ("txt", "text/plain", "Hola"),
        ("canva", "text/html", "Export Me"),
    )
    for fmt, mime, expected in cases:
        res = client.get(f"/api/v1/pages/{pid}/export/{fmt}")
        assert res.status_code == 200, fmt
        assert res.headers["content-type"].startswith(mime), fmt
        assert expected in res.text, fmt


def test_snippet_not_found() -> None:
    res = client.get("/api/v1/snippets/no_existe")
    assert res.status_code == 404


def test_render_snippet_not_found() -> None:
    res = client.post("/api/v1/snippets/no_existe/render", json={"values": {}})
    assert res.status_code == 404


def test_delete_page() -> None:
    pid = client.post("/api/v1/pages", json={"title": "ToDelete"}).json()["page_id"]
    res = client.delete(f"/api/v1/pages/{pid}")
    assert res.status_code == 204
    assert pid not in {p["page_id"] for p in client.get("/api/v1/pages").json()}


def test_get_events() -> None:
    pid = client.post("/api/v1/pages", json={"title": "Events"}).json()["page_id"]
    res = client.get(f"/api/v1/pages/{pid}/events")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    assert res.json()[0]["type"] == "page_created"


def test_voice_text_non_math() -> None:
    pid = client.post("/api/v1/pages", json={"title": "VoiceText"}).json()["page_id"]
    res = client.post(f"/api/v1/pages/{pid}/voice", json={"text": "hola mundo"})
    assert res.status_code == 201
    assert res.json()["intent"] == "text"
    assert "hola mundo" in client.get(f"/api/v1/pages/{pid}/latex").json()["latex"]


def test_restore_preserves_cell_outputs() -> None:
    pid = client.post("/api/v1/pages", json={"title": "RestoreOut"}).json()["page_id"]
    client.post(
        f"/api/v1/pages/{pid}/cells",
        json={"cell_id": "c1", "language": "python", "source": "42"},
    )
    client.post(f"/api/v1/pages/{pid}/cells/c1/execute")
    client.post(f"/api/v1/pages/{pid}/replace", json={"latex": "v2"})

    # Restaurar al índice del evento cell_executed para que el output se re-emita.
    res = client.post(f"/api/v1/pages/{pid}/restore/2")
    assert res.status_code == 200
    cell = [c for c in res.json()["ast"] if c.get("type") == "cell"][0]
    assert cell["output"] is not None and "42" in cell["output"]


def test_export_unsupported_format_returns_400() -> None:
    pid = client.post("/api/v1/pages", json={"title": "BadFmt"}).json()["page_id"]
    res = client.get(f"/api/v1/pages/{pid}/export/unknown")
    assert res.status_code == 400
    assert "Formato no soportado" in res.json()["detail"]




def test_get_cell_figure_path_outside_root(monkeypatch) -> None:
    pid = client.post("/api/v1/pages", json={"title": "Outside"}).json()["page_id"]
    fake_cell = CellNode(
        cell_id="c1",
        language="python",
        source="",
        figure_path="/tmp/outside.png",  # nosec B108 (path de prueba intencional)
    )
    monkeypatch.setattr("lablog.api._find_cell", lambda _p, _e, _c: fake_cell)
    res = client.get(f"/api/v1/pages/{pid}/cells/c1/figure")
    assert res.status_code == 404


def test_get_cell_figure_file_missing(monkeypatch) -> None:
    from lablog.config import settings

    pid = client.post("/api/v1/pages", json={"title": "MissingFig"}).json()["page_id"]
    missing_path = str(settings.figures_dir / "missing.png")
    fake_cell = CellNode(
        cell_id="c1",
        language="python",
        source="",
        figure_path=missing_path,
    )
    monkeypatch.setattr("lablog.api._find_cell", lambda _p, _e, _c: fake_cell)
    res = client.get(f"/api/v1/pages/{pid}/cells/c1/figure")
    assert res.status_code == 404


def test_pdf_install(monkeypatch) -> None:
    async def fake_install(force: bool = False) -> dict[str, bool]:
        return {"installed": True}

    monkeypatch.setattr("lablog.api.pdf_engine.install_engine", fake_install)
    res = client.post("/api/v1/pdf/install")
    assert res.status_code == 200
    assert res.json()["installed"] is True


def test_export_pages() -> None:
    res = client.post("/api/v1/export")
    assert res.status_code == 200
    assert Path(res.json()["path"]).exists()


def test_export_docx_503_without_pandoc(monkeypatch) -> None:
    monkeypatch.setattr("lablog.api.which", lambda _cmd: None)
    pid = client.post("/api/v1/pages", json={"title": "Docx"}).json()["page_id"]
    res = client.get(f"/api/v1/pages/{pid}/export/docx")
    assert res.status_code == 503
    assert "pandoc" in res.json()["detail"]


def test_export_txt_fallback_without_pandoc(monkeypatch) -> None:
    monkeypatch.setattr("lablog.api.which", lambda _cmd: None)
    pid = client.post("/api/v1/pages", json={"title": "Plain"}).json()["page_id"]
    client.post(f"/api/v1/pages/{pid}/text", json={"text": "Hola $x^2$"})
    res = client.get(f"/api/v1/pages/{pid}/export/txt")
    assert res.status_code == 200
    assert "Hola" in res.text
    assert "\\" not in res.text


def test_execute_cell_generic_engine_error_returns_503(monkeypatch) -> None:
    pid = client.post("/api/v1/pages", json={"title": "EngineGeneric"}).json()["page_id"]
    client.post(
        f"/api/v1/pages/{pid}/cells",
        json={"cell_id": "c1", "language": "python", "source": "1"},
    )

    class BrokenEngine:
        def execute(self, *_args, **_kwargs):
            raise RuntimeError("boom")

    monkeypatch.setattr("lablog.api.get_engine", lambda: BrokenEngine())
    res = client.post(f"/api/v1/pages/{pid}/cells/c1/execute")
    assert res.status_code == 503
    assert "boom" in res.json()["detail"]


def test_execute_cell_figure_path_outside_root_is_stored(
    monkeypatch, tmp_path: Path
) -> None:
    pid = client.post("/api/v1/pages", json={"title": "OutsideFig"}).json()["page_id"]
    client.post(
        f"/api/v1/pages/{pid}/cells",
        json={"cell_id": "c1", "language": "python", "source": "1"},
    )
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"png")

    class EngineWithOutsideFigure:
        def execute(self, *_args, **_kwargs):
            from lablog.code_engine import ExecutionResult

            return ExecutionResult(
                status="ok", text="ok", figure_paths=[str(outside)]
            )

    monkeypatch.setattr("lablog.api.get_engine", lambda: EngineWithOutsideFigure())
    res = client.post(f"/api/v1/pages/{pid}/cells/c1/execute")
    assert res.status_code == 201
    events = client.get(f"/api/v1/pages/{pid}/events").json()
    executed = [e for e in events if e["type"] == "cell_executed"]
    assert executed
    # Se almacena la ruta absoluta cuando no es posible calcular la relativa.
    assert executed[0]["payload"]["figure_path"] == str(outside)


def test_event_summary_for_unknown_event_type() -> None:
    from datetime import datetime

    from lablog.api import _event_summary
    from lablog.events import Event

    event = Event(
        type="vault_file_added",
        page_id="page-x",
        payload={"file_id": "x", "name": "y"},
        timestamp=datetime.now(UTC),
    )
    assert _event_summary(event) == ""


def test_extract_body_formats() -> None:
    from lablog.api import _extract_body

    assert _extract_body("$x^2$") == ("x^2", "inline")
    assert _extract_body("\\[x^2\\]") == ("x^2", "display")
    assert _extract_body("plain") == ("plain", "inline")


def test_request_vault_deletion_not_found() -> None:
    res = client.post("/api/v1/vault/no-existe/delete-request")
    assert res.status_code == 404


def test_upload_vault_too_large() -> None:
    from io import BytesIO

    big = b"x" * (100 * 1024 * 1024 + 1)
    res = client.post(
        "/api/v1/vault",
        files={"file": ("big.txt", BytesIO(big), "text/plain")},
    )
    assert res.status_code == 413
