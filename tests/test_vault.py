"""Tests de la bóveda segura."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from lablog.vault import VaultService


def test_add_and_list_file(tmp_path: Path) -> None:
    vault = VaultService(tmp_path)
    file_path = tmp_path / "doc.txt"
    file_path.write_text("hello vault")

    vf = vault.add_file(file_path)
    assert vf.name == "doc.txt"
    assert vf.status == "active"

    files = vault.list_files()
    assert len(files) == 1
    assert files[0].id == vf.id


def test_request_deletion_creates_timelock(tmp_path: Path) -> None:
    vault = VaultService(tmp_path)
    file_path = tmp_path / "doc.txt"
    file_path.write_text("hello")
    vf = vault.add_file(file_path)

    scheduled = vault.request_deletion(vf.id)
    assert scheduled is not None
    assert scheduled > datetime.now(UTC)
    assert scheduled < datetime.now(UTC) + timedelta(days=8)

    files = vault.list_files()
    assert files[0].status == "pending_deletion"


def test_cancel_deletion(tmp_path: Path) -> None:
    vault = VaultService(tmp_path)
    file_path = tmp_path / "doc.txt"
    file_path.write_text("hello")
    vf = vault.add_file(file_path)

    vault.request_deletion(vf.id)
    vault.cancel_deletion(vf.id)

    files = vault.list_files()
    assert files[0].status == "active"
    assert files[0].scheduled_for_deletion_at is None


def test_force_delete_with_phrase(tmp_path: Path) -> None:
    vault = VaultService(tmp_path)
    file_path = tmp_path / "doc.txt"
    file_path.write_text("hello")
    vf = vault.add_file(file_path)

    assert vault.force_delete(vf.id, "frase incorrecta") is False
    assert vault.force_delete(vf.id, vf.deletion_phrase) is True
    assert vault.get_file(vf.id) is None


def test_preview_text(tmp_path: Path) -> None:
    vault = VaultService(tmp_path)
    file_path = tmp_path / "doc.txt"
    file_path.write_text("línea 1\nlínea 2\nlínea 3")
    vf = vault.add_file(file_path)

    preview = vault.generate_preview(vf.id)
    assert preview["type"] == "text"
    assert "línea 1" in preview["content"]


def test_purge_expired(tmp_path: Path) -> None:
    vault = VaultService(tmp_path)
    file_path = tmp_path / "doc.txt"
    file_path.write_text("hello")
    vf = vault.add_file(file_path)

    vault.request_deletion(vf.id)
    vault._meta[vf.id].scheduled_for_deletion_at = datetime.now(UTC) - timedelta(seconds=1)
    vault._save_meta()

    purged = vault.purge_expired()
    assert purged == [vf.id]
    assert vault.get_file(vf.id) is None
