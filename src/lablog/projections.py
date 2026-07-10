"""Proyecciones de lectura del dominio lablog."""

from __future__ import annotations

from typing import Any

from lablog.ast_nodes import CellNode, node_to_json
from lablog.event_store import EventStore
from lablog.events import Event
from lablog.latex_ast import serialize_ast
from lablog.projector import PageProjection, project


class PageNotFoundError(ValueError):
    """La página solicitada no existe o fue eliminada."""


def _events(store: EventStore, page_id: str) -> list[Event]:
    events = store.get_events(page_id)
    if not events:
        raise PageNotFoundError(page_id)
    return events


def page_summary(store: EventStore, page_id: str) -> dict[str, Any]:
    events = _events(store, page_id)
    proj = project(page_id, events)
    if proj.deleted:
        raise PageNotFoundError(page_id)
    return {
        "page_id": page_id,
        "title": proj.title,
        "project_id": proj.project_id,
        "updated_at": events[-1].timestamp,
    }


def list_page_summaries(store: EventStore) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for pid in store.list_pages():
        try:
            summaries.append(page_summary(store, pid))
        except PageNotFoundError:
            continue
    return summaries


def page_detail(store: EventStore, page_id: str) -> dict[str, Any]:
    events = _events(store, page_id)
    proj = project(page_id, events)
    if proj.deleted:
        raise PageNotFoundError(page_id)
    latex = serialize_ast(proj.ast)
    return {
        "page_id": page_id,
        "title": proj.title,
        "latex": latex,
        "raw": latex,
        "ast": [node_to_json(child) for child in proj.ast.children],
        "version": len(events),
    }


def list_cells(store: EventStore, page_id: str) -> list[dict[str, Any]]:
    events = _events(store, page_id)
    proj = project(page_id, events)
    if proj.deleted:
        raise PageNotFoundError(page_id)
    return [
        node_to_json(child)
        for child in proj.ast.children
        if isinstance(child, CellNode)
    ]


def find_cell(store: EventStore, page_id: str, cell_id: str) -> CellNode | None:
    events = _events(store, page_id)
    proj = project(page_id, events)
    if proj.deleted:
        raise PageNotFoundError(page_id)
    for child in proj.ast.children:
        if isinstance(child, CellNode) and child.cell_id == cell_id:
            return child
    return None


def page_history(store: EventStore, page_id: str) -> list[dict[str, Any]]:
    events = _events(store, page_id)
    proj = project(page_id, events)
    if proj.deleted:
        raise PageNotFoundError(page_id)
    return [
        {
            "index": i,
            "type": e.type,
            "timestamp": e.timestamp,
            "summary": _event_summary(e),
        }
        for i, e in enumerate(events)
    ]


def assert_active(store: EventStore, page_id: str) -> None:
    """Falla si la página no existe o está soft-deleted."""
    events = _events(store, page_id)
    if project(page_id, events).deleted:
        raise PageNotFoundError(page_id)


def page_projection(store: EventStore, page_id: str) -> PageProjection:
    events = _events(store, page_id)
    return project(page_id, events)


def page_at(store: EventStore, page_id: str, event_index: int) -> dict[str, Any]:
    events = _events(store, page_id)
    idx = _clamp_index(event_index, len(events))
    proj = project(page_id, events[: idx + 1])
    latex = serialize_ast(proj.ast)
    return {
        "page_id": page_id,
        "title": proj.title,
        "latex": latex,
        "raw": latex,
        "ast": [node_to_json(child) for child in proj.ast.children],
        "version": idx + 1,
    }


_SUMMARY_LEN = 40


def _event_summary(event: Event) -> str:
    payload = event.payload
    if event.type.startswith("cell_"):
        text = str(payload.get("cell_id", ""))
    elif event.type == "document_replaced":
        text = f"{len(payload.get('latex', ''))} chars"
    elif event.type in ("page_created", "page_metadata_updated"):
        text = str(payload.get("title") or "")
    elif event.type == "text_inserted":
        text = str(payload.get("text", ""))
    elif event.type == "math_inserted":
        text = str(payload.get("latex", ""))
    else:
        text = ""
    return text[:_SUMMARY_LEN]


def _clamp_index(index: int, count: int) -> int:
    return max(0, min(index, count - 1))
