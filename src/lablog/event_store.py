"""Persistencia de eventos en formato JSONL."""

from __future__ import annotations

import os
import re
import threading
from collections.abc import Iterator
from pathlib import Path

from lablog.events import Event

# page_id solo puede ser un identificador seguro (uuid4 u similar). Bloquea
# path traversal: un page_id como "../../etc/passwd" no debe escapar root_dir.
_SAFE_PAGE_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


class EventStore:
    """Almacén inmutable de eventos por página."""

    def __init__(self, root_dir: Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self._locks: dict[str, threading.Lock] = {}
        self._locks_guard = threading.Lock()

    def _page_file(self, page_id: str) -> Path:
        if not _SAFE_PAGE_ID.match(page_id):
            raise ValueError(f"page_id inválido: {page_id!r}")
        return self.root_dir / f"{page_id}.jsonl"

    def _lock_for(self, page_id: str) -> threading.Lock:
        with self._locks_guard:
            lock = self._locks.get(page_id)
            if lock is None:
                lock = threading.Lock()
                self._locks[page_id] = lock
            return lock

    def append(self, event: Event) -> None:
        """Añade un evento al final del log de la página.

        Escribe la línea completa y hace fsync para reducir el riesgo de
        eventos truncados si el proceso muere a mitad del write.
        Lock por página: serializa appends concurrentes (autosave + execute).
        """
        page_file = self._page_file(event.page_id)
        line = event.model_dump_json() + "\n"
        with self._lock_for(event.page_id), page_file.open("a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())

    def get_events(self, page_id: str) -> list[Event]:
        """Devuelve todos los eventos de una página en orden.

        Líneas vacías o JSON truncado/corrupto se omiten: un corte a mitad
        de la última línea no tumba la proyección de la página.
        """
        return list(self.iter_events(page_id))

    def iter_events(self, page_id: str) -> Iterator[Event]:
        """Itera eventos de una página omitiendo líneas corruptas."""
        page_file = self._page_file(page_id)
        if not page_file.exists():
            return

        # Lectura bajo el mismo lock que append: evita ver línea a medias.
        with self._lock_for(page_id), page_file.open("r", encoding="utf-8") as f:
            lines = f.readlines()

        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                yield Event.model_validate_json(line)
            except ValueError:
                continue

    def snapshot_at(self, page_id: str, timestamp: str) -> list[Event]:
        """Devuelve eventos hasta un timestamp dado (ISO 8601)."""
        events = self.get_events(page_id)
        return [e for e in events if e.timestamp.isoformat() <= timestamp]

    def list_pages(self) -> list[str]:
        """Lista page_id de documentos (excluye streams auxiliares como vault)."""
        return [
            f.stem
            for f in self.root_dir.glob("*.jsonl")
            if f.stem != "vault"
        ]
