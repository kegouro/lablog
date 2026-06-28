"""Definición de eventos del sistema lablog."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class Event(BaseModel):
    """Evento inmutable del sistema."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    actor: Literal["user", "plugin", "system"] = "user"
    page_id: str
    payload: dict[str, Any]

    def model_dump_json(self, **kwargs: Any) -> str:
        return super().model_dump_json(**kwargs)


class PageCreatedPayload(BaseModel):
    title: str
    project_id: str | None = None


class TextInsertedPayload(BaseModel):
    position: int
    text: str


class TextDeletedPayload(BaseModel):
    position: int
    length: int


class DocumentReplacedPayload(BaseModel):
    latex: str


class MathInsertedPayload(BaseModel):
    ast_path: str
    latex: str
    mode: Literal["inline", "display"] = "inline"


class CellInsertedPayload(BaseModel):
    cell_id: str
    language: str
    source: str


class CellUpdatedPayload(BaseModel):
    cell_id: str
    language: str | None = None
    source: str | None = None


class CellExecutedPayload(BaseModel):
    cell_id: str
    output: str | None = None
    figure_path: str | None = None


class CellDeletedPayload(BaseModel):
    cell_id: str


class CellMovedPayload(BaseModel):
    cell_id: str
    new_index: int


class PageMetadataUpdatedPayload(BaseModel):
    title: str | None = None
    project_id: str | None = None


class PageDeletedPayload(BaseModel):
    pass


class VaultFileAddedPayload(BaseModel):
    file_id: str
    name: str
    hash: str
    mime_type: str
    size: int


class VaultFileScheduledForDeletionPayload(BaseModel):
    file_id: str
    scheduled_at: datetime


class VaultFileDeletedPayload(BaseModel):
    file_id: str
    reason: Literal["expired", "forced"]


# Helpers para crear eventos comunes


def page_created(page_id: str, title: str, project_id: str | None = None) -> Event:
    return Event(
        type="page_created",
        page_id=page_id,
        payload=PageCreatedPayload(title=title, project_id=project_id).model_dump(),
    )


def text_inserted(page_id: str, position: int, text: str) -> Event:
    return Event(
        type="text_inserted",
        page_id=page_id,
        payload=TextInsertedPayload(position=position, text=text).model_dump(),
    )


def text_deleted(page_id: str, position: int, length: int) -> Event:
    return Event(
        type="text_deleted",
        page_id=page_id,
        payload=TextDeletedPayload(position=position, length=length).model_dump(),
    )


def document_replaced(page_id: str, latex: str) -> Event:
    return Event(
        type="document_replaced",
        page_id=page_id,
        payload=DocumentReplacedPayload(latex=latex).model_dump(),
    )


def math_inserted(
    page_id: str,
    ast_path: str,
    latex: str,
    mode: Literal["inline", "display"] = "inline",
) -> Event:
    return Event(
        type="math_inserted",
        page_id=page_id,
        payload=MathInsertedPayload(ast_path=ast_path, latex=latex, mode=mode).model_dump(),
    )


def cell_inserted(page_id: str, cell_id: str, language: str, source: str) -> Event:
    return Event(
        type="cell_inserted",
        page_id=page_id,
        payload=CellInsertedPayload(cell_id=cell_id, language=language, source=source).model_dump(),
    )


def cell_updated(
    page_id: str,
    cell_id: str,
    language: str | None = None,
    source: str | None = None,
) -> Event:
    return Event(
        type="cell_updated",
        page_id=page_id,
        payload=CellUpdatedPayload(cell_id=cell_id, language=language, source=source).model_dump(),
    )


def cell_executed(
    page_id: str, cell_id: str, output: str | None = None, figure_path: str | None = None
) -> Event:
    return Event(
        type="cell_executed",
        page_id=page_id,
        payload=CellExecutedPayload(
            cell_id=cell_id, output=output, figure_path=figure_path
        ).model_dump(),
    )


def cell_deleted(page_id: str, cell_id: str) -> Event:
    return Event(
        type="cell_deleted",
        page_id=page_id,
        payload=CellDeletedPayload(cell_id=cell_id).model_dump(),
    )


def cell_moved(page_id: str, cell_id: str, new_index: int) -> Event:
    return Event(
        type="cell_moved",
        page_id=page_id,
        payload=CellMovedPayload(cell_id=cell_id, new_index=new_index).model_dump(),
    )


def page_metadata_updated(
    page_id: str, title: str | None = None, project_id: str | None = None
) -> Event:
    return Event(
        type="page_metadata_updated",
        page_id=page_id,
        payload=PageMetadataUpdatedPayload(title=title, project_id=project_id).model_dump(
            exclude_none=True
        ),
    )


def page_deleted(page_id: str) -> Event:
    return Event(
        type="page_deleted",
        page_id=page_id,
        payload=PageDeletedPayload().model_dump(),
    )


def vault_file_added(file_id: str, name: str, file_hash: str, mime_type: str, size: int) -> Event:
    return Event(
        type="vault_file_added",
        page_id="vault",
        payload=VaultFileAddedPayload(
            file_id=file_id, name=name, hash=file_hash, mime_type=mime_type, size=size
        ).model_dump(),
    )


def vault_deletion_scheduled(file_id: str, scheduled_at: datetime) -> Event:
    return Event(
        type="vault_deletion_scheduled",
        page_id="vault",
        payload=VaultFileScheduledForDeletionPayload(
            file_id=file_id, scheduled_at=scheduled_at
        ).model_dump(),
    )


def vault_file_deleted(file_id: str, reason: Literal["expired", "forced"]) -> Event:
    return Event(
        type="vault_file_deleted",
        page_id="vault",
        payload=VaultFileDeletedPayload(file_id=file_id, reason=reason).model_dump(),
    )
