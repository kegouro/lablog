"""Tests del servidor API."""

from __future__ import annotations

from fastapi.testclient import TestClient

from lablog.api import app

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
    assert set(r.json()) == {"binary_ready", "bundle_warmed"}


def test_pdf_export_503_without_engine(monkeypatch) -> None:
    from lablog import pdf_engine
    monkeypatch.setattr(pdf_engine, "tectonic_path", lambda **_: None)
    pid = client.post("/api/v1/pages", json={"title": "X"}).json()["page_id"]
    r = client.get(f"/api/v1/pages/{pid}/export/pdf")
    assert r.status_code == 503
