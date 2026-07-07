"""Comandos puros de escritura del dominio lablog."""

from __future__ import annotations

from typing import Any, Literal
from uuid import uuid4

from lablog.event_store import EventStore
from lablog.events import (
    document_replaced,
    math_inserted,
    page_created,
    page_deleted,
    page_metadata_updated,
    text_inserted,
)
from lablog.projector import project


def create_page(store: EventStore, title: str, project_id: str | None = None) -> dict[str, Any]:
    page_id = str(uuid4())
    store.append(page_created(page_id=page_id, title=title, project_id=project_id))
    events = store.get_events(page_id)
    proj = project(page_id, events)
    return {
        "page_id": page_id,
        "title": proj.title,
        "project_id": proj.project_id,
        "updated_at": events[-1].timestamp,
    }


def update_page_metadata(
    store: EventStore,
    page_id: str,
    title: str | None,
    project_id: str | None,
) -> dict[str, Any]:
    store.append(page_metadata_updated(page_id=page_id, title=title, project_id=project_id))
    events = store.get_events(page_id)
    proj = project(page_id, events)
    return {
        "page_id": page_id,
        "title": proj.title,
        "project_id": proj.project_id,
        "updated_at": events[-1].timestamp,
    }


def delete_page(store: EventStore, page_id: str) -> None:
    store.append(page_deleted(page_id=page_id))


def replace_document(store: EventStore, page_id: str, latex: str) -> None:
    store.append(document_replaced(page_id=page_id, latex=latex))


def insert_text(store: EventStore, page_id: str, position: int, text: str) -> None:
    store.append(text_inserted(page_id=page_id, position=position, text=text))


def insert_math(
    store: EventStore, page_id: str, latex: str, mode: Literal["inline", "display"]
) -> None:
    store.append(math_inserted(page_id=page_id, ast_path="/document", latex=latex, mode=mode))
