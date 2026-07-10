"""Persistencia de eventos en formato JSONL."""

from __future__ import annotations

import os
import re
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

    def _page_file(self, page_id: str) -> Path:
        if not _SAFE_PAGE_ID.match(page_id):
            raise ValueError(f"page_id inválido: {page_id!r}")
        return self.root_dir / f"{page_id}.jsonl"

    def append(self, event: Event) -> None:
        """Añade un evento al final del log de la página.

        Escribe la línea completa y hace fsync para reducir el riesgo de
        eventos truncados si el proceso muere a mitad del write.
        """
        page_file = self._page_file(event.page_id)
        line = event.model_dump_json() + "\n"
        with page_file.open("a", encoding="utf-8") as f:
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

        with page_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield Event.model_validate_json(line)
                except ValueError:
                    # Salta un evento corrupto en vez de tumbar toda la página.
                    continue

    def snapshot_at(self, page_id: str, timestamp: str) -> list[Event]:
        """Devuelve eventos hasta un timestamp dado (ISO 8601)."""
        events = self.get_events(page_id)
        return [e for e in events if e.timestamp.isoformat() <= timestamp]

    def list_pages(self) -> list[str]:
        """Lista page_id de documentos (excluye streams auxiliares como vault)."""
        # vault.jsonl reutiliza el EventStore para auditoría de archivos; no es
        # una página del laboratorio y no debe aparecer en listados/export.
        return [
            f.stem
            for f in self.root_dir.glob("*.jsonl")
            if f.stem != "vault"
        ]
