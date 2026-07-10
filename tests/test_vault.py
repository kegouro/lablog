"""Tests del servicio de bóveda."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from lablog.vault import VaultService


def test_add_and_list(tmp_path: Path) -> None:
    vault = VaultService(tmp_path)
    src = tmp_path / "src.txt"
    src.write_text("hola", encoding="utf-8")
    vf = vault.add_file(src)
    assert vf.name == "src.txt"
    assert vault.get_file(vf.id) is not None
    assert any(f.id == vf.id for f in vault.list_files())


def test_request_deletion_creates_timelock(tmp_path: Path) -> None:
    vault = VaultService(tmp_path)
    src = tmp_path / "a.txt"
    src.write_text("x", encoding="utf-8")
    vf = vault.add_file(src)
    result = vault.request_deletion(vf.id)
    assert result is not None
    scheduled, phrase = result
    assert scheduled > datetime.now(UTC)
    assert phrase
    loaded = vault.get_file(vf.id)
    assert loaded is not None
    assert loaded.status == "pending_deletion"
    assert loaded.deletion_phrase == phrase


def test_cancel_deletion(tmp_path: Path) -> None:
    vault = VaultService(tmp_path)
    src = tmp_path / "b.txt"
    src.write_text("x", encoding="utf-8")
    vf = vault.add_file(src)
    vault.request_deletion(vf.id)
    assert vault.cancel_deletion(vf.id) is True
    loaded = vault.get_file(vf.id)
    assert loaded is not None
    assert loaded.status == "active"


def test_force_delete_with_phrase(tmp_path: Path) -> None:
    vault = VaultService(tmp_path)
    src = tmp_path / "c.txt"
    src.write_text("x", encoding="utf-8")
    vf = vault.add_file(src)
    # Force sin pending → rechazado
    assert vault.force_delete(vf.id, vf.deletion_phrase) is False
    _, phrase = vault.request_deletion(vf.id)  # type: ignore[misc]
    assert vault.force_delete(vf.id, "frase incorrecta") is False
    assert vault.force_delete(vf.id, phrase) is True
    assert vault.get_file(vf.id) is None


def test_purge_expired(tmp_path: Path) -> None:
    vault = VaultService(tmp_path)
    src = tmp_path / "d.txt"
    src.write_text("x", encoding="utf-8")
    vf = vault.add_file(src)
    vault.request_deletion(vf.id)
    loaded = vault.get_file(vf.id)
    assert loaded is not None and loaded.scheduled_for_deletion_at is not None
    loaded.scheduled_for_deletion_at = loaded.scheduled_for_deletion_at.replace(year=2000)
    vault._save_meta()
    purged = vault.purge_expired()
    assert vf.id in purged
    assert vault.get_file(vf.id) is None
