"""Comandos de escritura del dominio lablog (lado write del CQRS).

Solo emiten eventos. No devuelven proyecciones de lectura: el adaptador HTTP
relee el estado con ``projections`` después del comando.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal
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
from lablog.latex_ast import serialize_ast
from lablog.projector import project
from lablog.voice.parser import IntentType, parse_intent, translate


class CellNotFoundError(ValueError):
    """La celda solicitada no existe en la página."""


class UnsupportedLanguageError(ValueError):
    """El lenguaje de la celda no está soportado por el motor."""


class EngineExecutionError(RuntimeError):
    """El motor de ejecución no pudo ejecutar la celda."""


class PageDeletedError(ValueError):
    """La página está marcada como eliminada."""


def create_page(store: EventStore, title: str, project_id: str | None = None) -> str:
    """Crea una página. Devuelve el ``page_id`` (no la proyección)."""
    page_id = str(uuid4())
    store.append(page_created(page_id=page_id, title=title, project_id=project_id))
    return page_id


def update_page_metadata(
    store: EventStore,
    page_id: str,
    title: str | None,
    project_id: str | None,
) -> None:
    store.append(page_metadata_updated(page_id=page_id, title=title, project_id=project_id))


def delete_page(store: EventStore, page_id: str) -> None:
    store.append(page_deleted(page_id=page_id))


def replace_document(
    store: EventStore,
    page_id: str,
    latex: str,
    *,
    expected_version: int | None = None,
) -> None:
    store.append(
        document_replaced(page_id=page_id, latex=latex),
        expected_version=expected_version,
    )


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
) -> None:
    """Ejecuta una celda y persiste el resultado como evento de dominio.

    Emite ``execution_failed`` si el motor o el código fallan.
    Emite ``cell_executed`` solo cuando ``result.status == "ok"``.

    No devuelve la proyección: el caller relee con ``projections.find_cell``.
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
        return

    figure_path = _relative_figure_path(result.figure_paths)
    store.append(
        cell_executed(
            page_id=page_id,
            cell_id=cell_id,
            output=result.text,
            figure_path=figure_path,
        )
    )


def restore_version(store: EventStore, page_id: str, event_index: int) -> None:
    """Restaura el documento al estado proyectado hasta ``event_index`` (inclusive)."""
    events = store.get_events(page_id)
    if not events:
        raise ValueError(f"Página sin eventos: {page_id}")
    proj = project(page_id, events)
    if proj.deleted:
        raise PageDeletedError(page_id)

    idx = max(0, min(event_index, len(events) - 1))
    past = project(page_id, events[: idx + 1])
    store.append(document_replaced(page_id=page_id, latex=serialize_ast(past.ast)))
    # serialize_ast no persiste output/figura/status: re-emitir por celda.
    for child in past.ast.children:
        if not isinstance(child, CellNode):
            continue
        if not (child.output or child.figure_path or child.status == "error"):
            continue
        if child.status == "error":
            store.append(
                execution_failed(
                    page_id=page_id,
                    cell_id=child.cell_id,
                    ename="RestoredError",
                    evalue=child.output or "error",
                    traceback=(child.output or "").splitlines(),
                )
            )
        else:
            store.append(
                cell_executed(
                    page_id=page_id,
                    cell_id=child.cell_id,
                    output=child.output or "",
                    figure_path=child.figure_path,
                )
            )


def voice_insert(store: EventStore, page_id: str, text: str) -> str:
    """Inserta texto o math según el intent de voz. Devuelve el intent como string.

    Descarta dictados vacíos/ruido tras limpieza. El texto narrativo se inserta
    limpio (sin reemplazos matemáticos agresivos); la math sí se traduce.
    """
    from lablog.voice.parser import clean_dictation_text

    cleaned = clean_dictation_text(text)
    if not cleaned:
        return IntentType.TEXT.value

    intent = parse_intent(cleaned)
    result = translate(cleaned, intent.type)
    math_intents = (IntentType.MATH, IntentType.INTEGRAL, IntentType.EQUATION, IntentType.MATRIX)
    if intent.type in math_intents and result.latex:
        body, mode = _extract_math_body(result.latex)
        if body:
            store.append(
                math_inserted(page_id=page_id, ast_path="/document", latex=body, mode=mode)
            )
    else:
        # Preferir el texto limpio de translate (TEXT) o el cleaned original.
        payload = result.latex if result.latex else cleaned
        store.append(text_inserted(page_id=page_id, position=-1, text=payload))
    return intent.type.value


def _extract_math_body(latex: str) -> tuple[str, Literal["inline", "display"]]:
    latex = latex.strip()
    if latex.startswith("\\[") and latex.endswith("\\]"):
        return latex[2:-2].strip(), "display"
    if latex.startswith("$") and latex.endswith("$"):
        return latex[1:-1].strip(), "inline"
    return latex, "inline"


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
