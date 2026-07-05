"""Tests de integración del router de vault."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient

from lablog.api import app, vault

client = TestClient(app)


def _upload(filename: str, content: bytes) -> str:
    response = client.post(
        "/api/v1/vault",
        files={"file": (filename, BytesIO(content), "text/plain")},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_upload_and_list() -> None:
    file_id = _upload("nota.txt", b"contenido importante")

    response = client.get("/api/v1/vault")
    assert response.status_code == 200
    items = response.json()
    assert any(item["id"] == file_id for item in items)


def test_get_file_detail() -> None:
    file_id = _upload("detalle.txt", b"detalle")

    response = client.get(f"/api/v1/vault/{file_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "detalle.txt"
    assert data["status"] == "active"
    assert "deletion_phrase" in data


def test_preview_text() -> None:
    file_id = _upload("preview.txt", b"primera linea\nsegunda linea")

    response = client.get(f"/api/v1/vault/{file_id}/preview")
    assert response.status_code == 200
    assert response.json()["type"] == "text"
    assert "primera linea" in response.json()["content"]


def test_deletion_request_and_cancel() -> None:
    file_id = _upload("temp.txt", b"temporal")

    response = client.post(f"/api/v1/vault/{file_id}/delete-request")
    assert response.status_code == 200
    assert response.json()["status"] == "pending_deletion"
    assert response.json()["scheduled_for_deletion_at"] is not None

    response = client.get(f"/api/v1/vault/{file_id}")
    assert response.json()["status"] == "pending_deletion"

    response = client.post(f"/api/v1/vault/{file_id}/cancel-delete")
    assert response.status_code == 200
    assert response.json()["status"] == "active"


def test_force_delete_wrong_phrase() -> None:
    file_id = _upload("seguro.txt", b"confidencial")

    response = client.post(
        f"/api/v1/vault/{file_id}/force-delete",
        json={"phrase": "frase incorrecta"},
    )
    assert response.status_code == 403

    response = client.get(f"/api/v1/vault/{file_id}")
    assert response.status_code == 200


def test_force_delete_correct_phrase() -> None:
    file_id = _upload("borrar.txt", b"para borrar")

    detail = client.get(f"/api/v1/vault/{file_id}").json()
    phrase = detail["deletion_phrase"]

    response = client.post(
        f"/api/v1/vault/{file_id}/force-delete",
        json={"phrase": phrase},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"

    response = client.get(f"/api/v1/vault/{file_id}")
    assert response.status_code == 404


def test_purge_endpoint(tmp_path: Path) -> None:
    file_id = _upload("expira.txt", b"expirara")
    client.post(f"/api/v1/vault/{file_id}/delete-request")

    vf = vault.get_file(file_id)
    assert vf is not None
    vf.scheduled_for_deletion_at = vf.scheduled_for_deletion_at.replace(year=2000)
    vault._save_meta()

    response = client.post("/api/v1/vault/purge")
    assert response.status_code == 200
    assert response.json()["purged"] >= 1

    response = client.get(f"/api/v1/vault/{file_id}")
    assert response.status_code == 404


def test_preview_not_found() -> None:
    response = client.get("/api/v1/vault/no-existe/preview")
    assert response.status_code == 404


def test_download_not_found() -> None:
    response = client.get("/api/v1/vault/no-existe/download")
    assert response.status_code == 404


def test_cancel_and_force_delete_not_found() -> None:
    response = client.post("/api/v1/vault/no-existe/cancel-delete")
    assert response.status_code == 404

    response = client.post(
        "/api/v1/vault/no-existe/force-delete", json={"phrase": "x"}
    )
    assert response.status_code == 403


def test_download_success() -> None:
    file_id = _upload("download.txt", b"descargar esto")
    response = client.get(f"/api/v1/vault/{file_id}/download")
    assert response.status_code == 200
    assert response.content == b"descargar esto"
    assert 'inline; filename="download.txt"' in response.headers["content-disposition"]


def test_get_file_not_found() -> None:
    response = client.get("/api/v1/vault/no-existe")
    assert response.status_code == 404
