"""Tests del Event Store."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from lablog.event_store import EventStore
from lablog.events import page_created, text_inserted


@pytest.fixture
def store(tmp_path: Path) -> EventStore:
    return EventStore(tmp_path)


def test_append_and_get_events(store: EventStore) -> None:
    page_id = str(uuid4())
    store.append(page_created(page_id=page_id, title="Test"))
    store.append(text_inserted(page_id=page_id, position=0, text="Hola"))

    events = store.get_events(page_id)
    assert len(events) == 2
    assert events[0].type == "page_created"
    assert events[1].type == "text_inserted"


def test_get_events_returns_empty_list(store: EventStore) -> None:
    events = store.get_events("non-existent")
    assert events == []


def test_events_are_immutable_on_disk(store: EventStore) -> None:
    page_id = str(uuid4())
    event = page_created(page_id=page_id, title="Test")
    store.append(event)

    file_path = store._page_file(page_id)
    assert file_path.exists()
    content = file_path.read_text(encoding="utf-8").strip()
    assert event.id in content


def test_get_events_skips_truncated_last_line(store: EventStore) -> None:
    page_id = str(uuid4())
    store.append(page_created(page_id=page_id, title="Ok"))
    store.append(text_inserted(page_id=page_id, position=0, text="alive"))

    path = store._page_file(page_id)
    # Simula crash a mitad del write: línea JSON incompleta sin newline final.
    with path.open("a", encoding="utf-8") as f:
        f.write('{"type":"document_replaced","page_id":"')

    events = store.get_events(page_id)
    assert len(events) == 2
    assert events[0].type == "page_created"
    assert events[1].type == "text_inserted"


def test_append_ends_with_newline(store: EventStore) -> None:
    page_id = str(uuid4())
    store.append(page_created(page_id=page_id, title="NL"))
    raw = store._page_file(page_id).read_bytes()
    assert raw.endswith(b"\n")


def test_list_pages_excludes_vault_stream(store: EventStore) -> None:
    """vault.jsonl no es una página de laboratorio."""
    from lablog.events import Event

    page_id = str(uuid4())
    store.append(page_created(page_id=page_id, title="Real"))
    store.append(
        Event(
            type="vault_file_added",
            page_id="vault",
            payload={"file_id": "f1", "name": "a.pdf"},
        )
    )
    pages = store.list_pages()
    assert page_id in pages
    assert "vault" not in pages
