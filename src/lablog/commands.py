"""Comandos puros de escritura del dominio lablog."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from lablog.ast_nodes import CellNode, DocumentNode
from lablog.code_engine import CodeEngine, EngineStartError
from lablog.event_store import EventStore
from lablog.events import (
    cell_deleted,
    cell_executed,
    cell_inserted,
    cell_moved,
    cell_updated,
    document_replaced,
    execution_failed,
    math_inserted,
    page_created,
    page_deleted,
    page_metadata_updated,
    text_inserted,
)
from lablog.projector import project


class CellNotFoundError(ValueError):
    """La celda solicitada no existe en la página."""


class UnsupportedLanguageError(ValueError):
    """El lenguaje de la celda no está soportado por el motor."""


class EngineExecutionError(RuntimeError):
    """El motor de ejecución no pudo ejecutar la celda."""


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


def insert_cell(store: EventStore, page_id: str, cell_id: str, language: str, source: str) -> None:
    store.append(
        cell_inserted(
            page_id=page_id,
            cell_id=cell_id,
            language=language,
            source=source,
        )
    )


def update_cell(
    store: EventStore,
    page_id: str,
    cell_id: str,
    language: str | None = None,
    source: str | None = None,
) -> None:
    store.append(
        cell_updated(
            page_id=page_id,
            cell_id=cell_id,
            language=language,
            source=source,
        )
    )


def delete_cell(store: EventStore, page_id: str, cell_id: str) -> None:
    store.append(cell_deleted(page_id=page_id, cell_id=cell_id))


def move_cell(store: EventStore, page_id: str, cell_id: str, new_index: int) -> None:
    store.append(cell_moved(page_id=page_id, cell_id=cell_id, new_index=new_index))


def execute_cell(
    store: EventStore,
    page_id: str,
    cell_id: str,
    engine: CodeEngine,
    figure_dir: Path,
) -> CellNode:
    """Ejecuta una celda y persiste el resultado como evento de dominio.

    Emite `execution_failed` tanto si el motor falla como si el código del
    usuario arroja un error. Solo emite `cell_executed` cuando la ejecución
    termina con `result.status == "ok"`.

    Devuelve la celda actualizada proyectada desde el AST para evitar un
    segundo viaje del frontend.
    """
    events = store.get_events(page_id)
    proj = project(page_id, events)
    cell = _find_cell(proj.ast, cell_id)
    if cell is None:
        raise CellNotFoundError(f"Celda no encontrada: {cell_id}")

    if cell.language not in CodeEngine.SUPPORTED_LANGUAGES:
        raise UnsupportedLanguageError(f"Lenguaje no soportado: {cell.language}")

    try:
        result = engine.execute(cell.source, figure_dir=figure_dir)
    except EngineStartError as exc:
        store.append(
            execution_failed(
                page_id=page_id,
                cell_id=cell_id,
                ename="EngineStartError",
                evalue=str(exc),
                traceback=[],
            )
        )
        raise EngineExecutionError(str(exc)) from exc
    except Exception as exc:
        store.append(
            execution_failed(
                page_id=page_id,
                cell_id=cell_id,
                ename="EngineError",
                evalue=str(exc),
                traceback=[],
            )
        )
        raise EngineExecutionError(str(exc)) from exc

    if result.status == "error":
        store.append(
            execution_failed(
                page_id=page_id,
                cell_id=cell_id,
                ename="UserCodeError",
                evalue="Execution failed",
                traceback=result.text.splitlines(),
            )
        )
    else:
        figure_path = _relative_figure_path(result.figure_paths)
        store.append(
            cell_executed(
                page_id=page_id,
                cell_id=cell_id,
                output=result.text,
                figure_path=figure_path,
            )
        )

    updated = project(page_id, store.get_events(page_id))
    updated_cell = _find_cell(updated.ast, cell_id)
    if updated_cell is None:
        # Defensa: la celda nunca debería desaparecer tras ejecutarla.
        raise CellNotFoundError(f"Celda no encontrada tras ejecutar: {cell_id}")
    return updated_cell


def _find_cell(ast: DocumentNode, cell_id: str) -> CellNode | None:
    for child in ast.children:
        if isinstance(child, CellNode) and child.cell_id == cell_id:
            return child
    return None


def _relative_figure_path(figure_paths: list[str]) -> str | None:
    if not figure_paths:
        return None
    abs_path = Path(figure_paths[0])
    try:
        return str(abs_path.relative_to(_figures_root()))
    except ValueError:
        return str(abs_path)


def _figures_root() -> Path:
    from lablog.config import settings

    return settings.figures_dir
