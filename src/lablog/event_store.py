"""Persistencia de eventos en formato JSONL."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from lablog.events import Event


class EventStore:
    """Almacén inmutable de eventos por página."""

    def __init__(self, root_dir: Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def _page_file(self, page_id: str) -> Path:
        return self.root_dir / f"{page_id}.jsonl"

    def append(self, event: Event) -> None:
        """Añade un evento al final del log de la página."""
        page_file = self._page_file(event.page_id)
        with page_file.open("a", encoding="utf-8") as f:
            f.write(event.model_dump_json() + "\n")

    def get_events(self, page_id: str) -> list[Event]:
        """Devuelve todos los eventos de una página en orden."""
        page_file = self._page_file(page_id)
        if not page_file.exists():
            return []

        events: list[Event] = []
        with page_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                events.append(Event.model_validate_json(line))
        return events

    def iter_events(self, page_id: str) -> Iterator[Event]:
        """Itera eventos de una página sin cargarlos todos en memoria."""
        page_file = self._page_file(page_id)
        if not page_file.exists():
            return

        with page_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                yield Event.model_validate_json(line)

    def snapshot_at(self, page_id: str, timestamp: str) -> list[Event]:
        """Devuelve eventos hasta un timestamp dado (ISO 8601)."""
        events = self.get_events(page_id)
        return [e for e in events if e.timestamp.isoformat() <= timestamp]

    def list_pages(self) -> list[str]:
        """Lista todos los page_id almacenados."""
        return [f.stem for f in self.root_dir.glob("*.jsonl")]
