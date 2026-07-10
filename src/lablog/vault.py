"""Bóveda segura para archivos de investigación."""

from __future__ import annotations

import hashlib
import json
import secrets
import shutil
import threading
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from lablog.config import settings


@dataclass
class VaultFile:
    id: str
    name: str
    hash: str
    mime_type: str
    size: int
    stored_path: Path
    uploaded_at: datetime
    status: Literal["active", "pending_deletion"] = "active"
    scheduled_for_deletion_at: datetime | None = None
    deletion_phrase: str = ""


class VaultService:
    TIMELOCK_DAYS = 7

    def __init__(self, root_dir: Path | None = None) -> None:
        self.root = Path(root_dir or settings.vault_dir)
        self.files_dir = self.root / "files"
        self.previews_dir = self.root / "previews"
        self.meta_path = self.root / "meta.json"
        self.files_dir.mkdir(parents=True, exist_ok=True)
        self.previews_dir.mkdir(parents=True, exist_ok=True)
        self._meta: dict[str, VaultFile] = {}
        self._lock = threading.Lock()
        self._load_meta()

    def _load_meta(self) -> None:
        if not self.meta_path.exists():
            return
        data = json.loads(self.meta_path.read_text(encoding="utf-8"))
        for item in data.values():
            item["stored_path"] = Path(item["stored_path"])
            item["uploaded_at"] = datetime.fromisoformat(item["uploaded_at"])
            if item["scheduled_for_deletion_at"]:
                scheduled = datetime.fromisoformat(item["scheduled_for_deletion_at"])
                item["scheduled_for_deletion_at"] = scheduled
            self._meta[item["id"]] = VaultFile(**item)

    def _save_meta(self) -> None:
        data: dict[str, dict[str, Any]] = {}
        for vf in self._meta.values():
            data[vf.id] = {
                "id": vf.id,
                "name": vf.name,
                "hash": vf.hash,
                "mime_type": vf.mime_type,
                "size": vf.size,
                "stored_path": str(vf.stored_path),
                "uploaded_at": vf.uploaded_at.isoformat(),
                "status": vf.status,
                "scheduled_for_deletion_at": (
                    vf.scheduled_for_deletion_at.isoformat()
                    if vf.scheduled_for_deletion_at
                    else None
                ),
                "deletion_phrase": vf.deletion_phrase,
            }
        # Escritura atómica: evita meta.json corrupto si dos escrituras coinciden.
        tmp = self.meta_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp.replace(self.meta_path)

    def add_file(self, source: Path) -> VaultFile:
        content = source.read_bytes()
        file_hash = hashlib.sha256(content).hexdigest()[:16]
        file_id = str(uuid4())
        # Solo basename del origen (uploads usan uuid_name).
        display_name = Path(source.name).name
        # Quitar prefijo uuid_ del temp si existe.
        if "_" in display_name and len(display_name.split("_", 1)[0]) == 32:
            display_name = display_name.split("_", 1)[1] or display_name
        dest = self.files_dir / f"{file_id}_{display_name}"
        shutil.copy2(source, dest)

        mime = _guess_mime(display_name)
        # Token aleatorio: no derivable del nombre de archivo.
        phrase = secrets.token_urlsafe(16)
        vf = VaultFile(
            id=file_id,
            name=display_name,
            hash=file_hash,
            mime_type=mime,
            size=len(content),
            stored_path=dest,
            uploaded_at=datetime.now(UTC),
            deletion_phrase=phrase,
        )
        with self._lock:
            self._meta[file_id] = vf
            self._save_meta()
        return vf

    def list_files(self, include_pending: bool = True) -> list[VaultFile]:
        files = list(self._meta.values())
        if not include_pending:
            files = [f for f in files if f.status == "active"]
        return files

    def get_file(self, file_id: str) -> VaultFile | None:
        return self._meta.get(file_id)

    def request_deletion(self, file_id: str) -> tuple[datetime, str] | None:
        """Marca borrado diferido y rota el token de confirmación.

        Devuelve ``(scheduled_at, confirmation_phrase)`` — la frase solo se
        entrega en esta respuesta, no en GET list/detail.
        """
        with self._lock:
            vf = self._meta.get(file_id)
            if not vf:
                return None
            vf.status = "pending_deletion"
            vf.scheduled_for_deletion_at = datetime.now(UTC) + timedelta(
                days=self.TIMELOCK_DAYS
            )
            # Nueva frase al solicitar borrado (token de un solo uso en UX).
            vf.deletion_phrase = secrets.token_urlsafe(16)
            self._save_meta()
            return vf.scheduled_for_deletion_at, vf.deletion_phrase

    def cancel_deletion(self, file_id: str) -> bool:
        with self._lock:
            vf = self._meta.get(file_id)
            if not vf:
                return False
            vf.status = "active"
            vf.scheduled_for_deletion_at = None
            vf.deletion_phrase = secrets.token_urlsafe(16)
            self._save_meta()
            return True

    def force_delete(self, file_id: str, phrase: str) -> bool:
        """Borrado inmediato solo si ya está pending_deletion y la frase coincide."""
        with self._lock:
            vf = self._meta.get(file_id)
            if not vf:
                return False
            if vf.status != "pending_deletion":
                return False
            if not secrets.compare_digest(
                phrase.strip(),
                vf.deletion_phrase.strip(),
            ):
                return False
            self._remove(vf)
            return True

    def purge_expired(self) -> list[str]:
        now = datetime.now(UTC)
        with self._lock:
            expired = [
                vf.id
                for vf in self._meta.values()
                if vf.status == "pending_deletion"
                and vf.scheduled_for_deletion_at
                and vf.scheduled_for_deletion_at <= now
            ]
            for file_id in expired:
                vf = self._meta[file_id]
                self._remove(vf)
            return expired

    def _remove(self, vf: VaultFile) -> None:
        if vf.stored_path.exists():
            vf.stored_path.unlink()
        preview = self.previews_dir / f"{vf.id}.png"
        if preview.exists():
            preview.unlink()
        del self._meta[vf.id]
        self._save_meta()

    def generate_preview(self, file_id: str) -> dict[str, Any]:
        vf = self._meta.get(file_id)
        if not vf:
            raise FileNotFoundError(file_id)

        if vf.mime_type.startswith("image/"):
            return self._image_preview(vf)
        if vf.mime_type == "text/plain":
            text = vf.stored_path.read_text(encoding="utf-8", errors="ignore")
            return {"type": "text", "content": text[:2000]}
        if vf.mime_type == "text/markdown":
            text = vf.stored_path.read_text(encoding="utf-8", errors="ignore")
            return {"type": "markdown", "content": text[:2000]}
        if vf.mime_type == "text/csv":
            return self._csv_preview(vf)
        if vf.mime_type == "application/pdf":
            return {"type": "pdf", "mime_type": vf.mime_type}
        if vf.mime_type in (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        ):
            return self._word_preview(vf)
        # NID y otros formatos de texto desconocidos se intentan como texto
        if vf.mime_type.startswith("text/") or vf.name.lower().endswith(".nid"):
            text = vf.stored_path.read_text(encoding="utf-8", errors="ignore")
            return {"type": "text", "content": text[:2000]}
        return {"type": "unsupported", "mime_type": vf.mime_type}

    def _image_preview(self, vf: VaultFile) -> dict[str, Any]:
        try:
            from PIL import Image

            preview_path = self.previews_dir / f"{vf.id}.png"
            with Image.open(vf.stored_path) as img:
                img.thumbnail((800, 800))
                img.save(preview_path, "PNG")
            return {"type": "image", "path": f"/api/v1/vault/{vf.id}/download"}
        except Exception:
            return {"type": "unsupported", "mime_type": vf.mime_type}

    def _csv_preview(self, vf: VaultFile) -> dict[str, Any]:
        import csv

        try:
            with vf.stored_path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
                reader = csv.reader(f)
                rows = list(reader)[:50]
            return {"type": "csv", "rows": rows}
        except Exception:
            text = vf.stored_path.read_text(encoding="utf-8", errors="ignore")
            return {"type": "text", "content": text[:2000]}

    def _word_preview(self, vf: VaultFile) -> dict[str, Any]:
        try:
            text = _extract_docx_text(vf.stored_path)
            return {"type": "docx", "content": text[:3000]}
        except Exception:
            return {"type": "unsupported", "mime_type": vf.mime_type}


def _extract_docx_text(path: Path) -> str:
    import zipfile
    from xml.etree import ElementTree as ET

    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: list[str] = []
    with (
        zipfile.ZipFile(path, "r") as zf,
        zf.open("word/document.xml") as xml_file,
    ):
        tree = ET.parse(xml_file)  # nosec B314 (DOCX interno generado por la app)
    for elem in tree.iter():
        if elem.tag == f"{{{ns['w']}}}t":
            paragraphs.append(elem.text or "")
        elif elem.tag == f"{{{ns['w']}}}p":
            paragraphs.append("\n")
    return "".join(paragraphs).strip()


def _guess_mime(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    mapping = {
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".csv": "text/csv",
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc": "application/msword",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".nid": "text/plain",
    }
    return mapping.get(ext, "application/octet-stream")
