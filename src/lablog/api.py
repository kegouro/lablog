"""Servidor FastAPI del engine de lablog."""

from __future__ import annotations

import asyncio
import threading
import uuid
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from shutil import which
from subprocess import CalledProcessError, run
from tempfile import NamedTemporaryFile
from typing import Annotated, Any, Literal

from fastapi import APIRouter, FastAPI, File, HTTPException, Response, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from lablog import commands, pdf_engine
from lablog.ast_nodes import CellNode, DocumentNode, node_to_json
from lablog.code_engine import CodeEngine, EngineStartError
from lablog.commands import CellNotFoundError, EngineExecutionError, UnsupportedLanguageError
from lablog.config import settings, ui_dist_dir
from lablog.event_store import EventStore
from lablog.events import (
    Event,
    cell_executed,
    document_replaced,
    math_inserted,
    text_inserted,
    vault_deletion_scheduled,
    vault_file_added,
    vault_file_deleted,
)
from lablog.exporter import export_site
from lablog.latex_ast import serialize_ast
from lablog.latex_symbols import FavoritesStore, list_symbols
from lablog.projector import project
from lablog.snippets import Snippet, find_snippet, render_snippet
from lablog.vault import VaultFile, VaultService
from lablog.voice.parser import IntentType, parse_intent, translate

app = FastAPI(title="lablog engine")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)
router = APIRouter(prefix="/api/v1")


def _engine_ready() -> bool:
    return _code_engine is not None and _code_engine.is_ready()


@router.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "engine_ready": _engine_ready(),
        "tools": {
            "pandoc": which("pandoc") is not None,
            "xelatex": which("xelatex") is not None,
            "pdflatex": which("pdflatex") is not None,
        },
    }


@router.get("/pdf/engine-status")
def pdf_engine_status() -> dict[str, object]:
    return pdf_engine.engine_status()


@router.post("/pdf/install")
async def pdf_install(force: bool = False) -> dict[str, object]:
    return await pdf_engine.install_engine(force=force)


@router.post("/export")
def export_pages() -> dict[str, str]:
    out_dir = export_site()
    return {"status": "ok", "path": str(out_dir)}


store = EventStore(settings.event_dir)
favorites = FavoritesStore()
vault = VaultService()
_code_engine: CodeEngine | None = None
_engine_lock = threading.Lock()
_pdf_locks: dict[str, asyncio.Lock] = {}


def _pdf_lock(page_id: str) -> asyncio.Lock:
    lock = _pdf_locks.get(page_id)
    if lock is None:
        lock = asyncio.Lock()
        _pdf_locks[page_id] = lock
    return lock


def get_engine() -> CodeEngine:
    global _code_engine
    if _code_engine is None:
        with _engine_lock:
            if _code_engine is None:
                _code_engine = CodeEngine()
                _code_engine.start()
    return _code_engine


class CreatePageRequest(BaseModel):
    title: str = "Sin título"
    project_id: str | None = None


class UpdatePageRequest(BaseModel):
    title: str | None = None
    project_id: str | None = None


class MoveCellPayload(BaseModel):
    new_index: int


class TextPayload(BaseModel):
    text: str
    position: int = -1


class ReplacePayload(BaseModel):
    latex: str


class UpdatePageRawRequest(BaseModel):
    raw: str


class MathPayload(BaseModel):
    latex: str
    mode: Literal["inline", "display"] = "inline"


class VoicePayload(BaseModel):
    text: str


class PageSummary(BaseModel):
    page_id: str
    title: str
    project_id: str | None
    updated_at: datetime | None


class PageDetail(BaseModel):
    page_id: str
    title: str
    latex: str
    raw: str
    ast: list[dict[str, Any]]
    version: int


class HistoryEntry(BaseModel):
    index: int
    type: str
    timestamp: datetime
    summary: str


class CellPayload(BaseModel):
    cell_id: str
    language: str = "python"
    source: str


class ExecutePayload(BaseModel):
    cell_id: str


class RenderPayload(BaseModel):
    values: dict[str, Any]


class VaultSummary(BaseModel):
    id: str
    name: str
    mime_type: str
    size: int
    uploaded_at: datetime
    status: Literal["active", "pending_deletion"]
    scheduled_for_deletion_at: datetime | None


class VaultDetail(BaseModel):
    id: str
    name: str
    mime_type: str
    size: int
    uploaded_at: datetime
    status: Literal["active", "pending_deletion"]
    scheduled_for_deletion_at: datetime | None
    deletion_phrase: str


class ForceDeletePayload(BaseModel):
    phrase: str


def _is_valid_page_id(page_id: str) -> bool:
    try:
        uuid.UUID(page_id)
    except ValueError:
        return False
    return True


def _events(page_id: str) -> list[Event]:
    events = store.get_events(page_id)
    if not events:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Página no encontrada")
    return events


def _summary(page_id: str) -> PageSummary:
    events = _events(page_id)
    proj = project(page_id, events)
    return PageSummary(
        page_id=page_id,
        title=proj.title,
        project_id=proj.project_id,
        updated_at=events[-1].timestamp,
    )


def _ast_to_json(doc: DocumentNode) -> list[dict[str, Any]]:
    return [asdict(child) for child in doc.children]


@router.post("/pages", status_code=status.HTTP_201_CREATED, response_model=PageSummary)
def create_page(req: CreatePageRequest) -> PageSummary:
    return PageSummary(**commands.create_page(store, title=req.title, project_id=req.project_id))


@router.get("/pages", response_model=list[PageSummary])
def list_pages() -> list[PageSummary]:
    summaries: list[PageSummary] = []
    for pid in store.list_pages():
        events = store.get_events(pid)
        proj = project(pid, events)
        if proj.deleted:
            continue
        summaries.append(
            PageSummary(
                page_id=pid,
                title=proj.title,
                project_id=proj.project_id,
                updated_at=events[-1].timestamp if events else None,
            )
        )
    return summaries


@router.patch("/pages/{page_id}", response_model=PageSummary)
def update_page(page_id: str, req: UpdatePageRequest) -> PageSummary:
    if not _is_valid_page_id(page_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"page_id inválido: {page_id}")
    _events(page_id)
    return PageSummary(
        **commands.update_page_metadata(
            store,
            page_id=page_id,
            title=req.title,
            project_id=req.project_id,
        )
    )


@router.put("/pages/{page_id}", response_model=PageDetail)
def update_page_raw(page_id: str, req: UpdatePageRawRequest) -> PageDetail:
    if not _is_valid_page_id(page_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"page_id inválido: {page_id}")
    _events(page_id)
    commands.replace_document(store, page_id=page_id, latex=req.raw)
    return _detail_from(page_id, _events(page_id))


@router.delete("/pages/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_page(page_id: str) -> None:
    if not _is_valid_page_id(page_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"page_id inválido: {page_id}")
    _events(page_id)
    commands.delete_page(store, page_id=page_id)


@router.get("/pages/{page_id}", response_model=PageDetail)
def get_page(page_id: str) -> PageDetail:
    events = _events(page_id)
    return _detail_from(page_id, events)


@router.get("/pages/{page_id}/latex")
def get_latex(page_id: str) -> dict[str, str]:
    events = _events(page_id)
    return {"latex": serialize_ast(project(page_id, events).ast)}


@router.post("/pages/{page_id}/text", status_code=status.HTTP_201_CREATED)
def append_text(page_id: str, payload: TextPayload) -> dict[str, str]:
    if not _is_valid_page_id(page_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"page_id inválido: {page_id}")
    _events(page_id)
    commands.insert_text(store, page_id=page_id, position=payload.position, text=payload.text)
    return {"status": "ok"}


@router.post("/pages/{page_id}/replace", status_code=status.HTTP_201_CREATED)
def replace_page(page_id: str, payload: ReplacePayload) -> dict[str, Any]:
    if not _is_valid_page_id(page_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"page_id inválido: {page_id}")
    _events(page_id)
    store.append(document_replaced(page_id=page_id, latex=payload.latex))
    proj = project(page_id, _events(page_id))
    return {"status": "ok", "latex": serialize_ast(proj.ast), "ast": _ast_to_json(proj.ast)}


@router.post("/pages/{page_id}/math", status_code=status.HTTP_201_CREATED)
def insert_math(page_id: str, payload: MathPayload) -> dict[str, str]:
    if not _is_valid_page_id(page_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"page_id inválido: {page_id}")
    _events(page_id)
    commands.insert_math(
        store,
        page_id=page_id,
        latex=payload.latex,
        mode=payload.mode,
    )
    return {"status": "ok"}


@router.post("/pages/{page_id}/voice", status_code=status.HTTP_201_CREATED)
def voice_text(page_id: str, payload: VoicePayload) -> dict[str, str]:
    if not _is_valid_page_id(page_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"page_id inválido: {page_id}")
    _events(page_id)
    intent = parse_intent(payload.text)
    result = translate(payload.text, intent.type)
    math_intents = (IntentType.MATH, IntentType.INTEGRAL, IntentType.EQUATION, IntentType.MATRIX)
    if intent.type in math_intents:
        body, mode = _extract_body(result.latex)
        store.append(math_inserted(page_id=page_id, ast_path="/document", latex=body, mode=mode))
    else:
        store.append(text_inserted(page_id=page_id, position=-1, text=payload.text))
    return {"status": "ok", "intent": intent.type.value}


@router.get("/pages/{page_id}/events", response_model=list[Event])
def get_events(page_id: str) -> list[Event]:
    return store.get_events(page_id)


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


def _detail_from(page_id: str, events: list[Event]) -> PageDetail:
    proj = project(page_id, events)
    return PageDetail(
        page_id=page_id,
        title=proj.title,
        latex=serialize_ast(proj.ast),
        raw=serialize_ast(proj.ast),
        ast=_ast_to_json(proj.ast),
        version=len(events),
    )


@router.get("/pages/{page_id}/history", response_model=list[HistoryEntry])
def page_history(page_id: str) -> list[HistoryEntry]:
    events = _events(page_id)
    return [
        HistoryEntry(
            index=i, type=e.type, timestamp=e.timestamp, summary=_event_summary(e)
        )
        for i, e in enumerate(events)
    ]


@router.get("/pages/{page_id}/at/{event_index}", response_model=PageDetail)
def page_at(page_id: str, event_index: int) -> PageDetail:
    events = _events(page_id)
    idx = _clamp_index(event_index, len(events))
    return _detail_from(page_id, events[: idx + 1])


@router.post("/pages/{page_id}/restore/{event_index}", response_model=PageDetail)
def restore_version(page_id: str, event_index: int) -> PageDetail:
    if not _is_valid_page_id(page_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"page_id inválido: {page_id}")
    events = _events(page_id)
    if project(page_id, events).deleted:
        raise HTTPException(status.HTTP_409_CONFLICT, "Página eliminada")
    idx = _clamp_index(event_index, len(events))
    past = project(page_id, events[: idx + 1])
    store.append(document_replaced(page_id=page_id, latex=serialize_ast(past.ast)))
    # serialize_ast no persiste output/figura: re-emitir ejecución de cada celda
    # para que los resultados sobrevivan el round-trip (append-only).
    for child in past.ast.children:
        if isinstance(child, CellNode) and (child.output or child.figure_path):
            store.append(
                cell_executed(
                    page_id=page_id,
                    cell_id=child.cell_id,
                    output=child.output or "",
                    figure_path=child.figure_path,
                )
            )
    return _detail_from(page_id, store.get_events(page_id))


@router.post("/pages/{page_id}/cells", status_code=status.HTTP_201_CREATED)
def insert_cell(page_id: str, payload: CellPayload) -> dict[str, str]:
    if not _is_valid_page_id(page_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"page_id inválido: {page_id}")
    _events(page_id)
    commands.insert_cell(
        store,
        page_id=page_id,
        cell_id=payload.cell_id,
        language=payload.language,
        source=payload.source,
    )
    return {"status": "ok"}


@router.post("/pages/{page_id}/cells/{cell_id}/update", status_code=status.HTTP_200_OK)
def update_cell(page_id: str, cell_id: str, payload: CellPayload) -> dict[str, str]:
    if not _is_valid_page_id(page_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"page_id inválido: {page_id}")
    _events(page_id)
    commands.update_cell(
        store,
        page_id=page_id,
        cell_id=cell_id,
        language=payload.language,
        source=payload.source,
    )
    return {"status": "ok"}


@router.post("/pages/{page_id}/cells/{cell_id}/execute", status_code=status.HTTP_200_OK)
async def execute_cell(page_id: str, cell_id: str) -> dict[str, Any]:
    if not _is_valid_page_id(page_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"page_id inválido: {page_id}")
    _events(page_id)
    figure_dir = settings.figures_dir / page_id
    try:
        engine = get_engine()
    except EngineStartError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc

    try:
        updated_cell = await asyncio.to_thread(
            commands.execute_cell,
            store,
            page_id=page_id,
            cell_id=cell_id,
            engine=engine,
            figure_dir=figure_dir,
        )
    except CellNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except UnsupportedLanguageError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except EngineExecutionError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc

    return node_to_json(updated_cell)


@router.delete("/pages/{page_id}/cells/{cell_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cell(page_id: str, cell_id: str) -> None:
    if not _is_valid_page_id(page_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"page_id inválido: {page_id}")
    _events(page_id)
    commands.delete_cell(store, page_id=page_id, cell_id=cell_id)


@router.post("/pages/{page_id}/cells/{cell_id}/move", status_code=status.HTTP_200_OK)
def move_cell(page_id: str, cell_id: str, payload: MoveCellPayload) -> dict[str, str]:
    if not _is_valid_page_id(page_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"page_id inválido: {page_id}")
    _events(page_id)
    commands.move_cell(store, page_id=page_id, cell_id=cell_id, new_index=payload.new_index)
    return {"status": "ok"}


@router.get("/pages/{page_id}/cells")
def list_cells(page_id: str) -> list[dict[str, Any]]:
    events = _events(page_id)
    proj = project(page_id, events)
    cells: list[dict[str, Any]] = []
    for child in proj.ast.children:
        if isinstance(child, CellNode):
            cells.append(
                {
                    "cell_id": child.cell_id,
                    "language": child.language,
                    "source": child.source,
                    "output": child.output,
                    "figure_path": child.figure_path,
                }
            )
    return cells


@router.get("/pages/{page_id}/cells/{cell_id}/figure")
def get_cell_figure(page_id: str, cell_id: str) -> Response:
    events = _events(page_id)
    cell = _find_cell(page_id, events, cell_id)
    if cell is None or not cell.figure_path:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Figura no encontrada")

    # Rutas relativas se resuelven contra figures_dir; las absolutas (legado) se
    # usan tal cual. En ambos casos se exige que queden dentro de figures_dir.
    raw = Path(cell.figure_path)
    figures_root = settings.figures_dir.resolve()
    path = (raw if raw.is_absolute() else figures_root / raw).resolve()
    if figures_root not in path.parents:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Figura no encontrada")
    if not path.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Archivo de figura no existe")

    suffix = path.suffix.lower()
    media_type = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".svg": "image/svg+xml",
        ".gif": "image/gif",
    }.get(suffix, "application/octet-stream")

    return Response(content=path.read_bytes(), media_type=media_type)


@router.get("/snippets", response_model=list[Snippet])
def list_snippets() -> list[Snippet]:
    return Snippet.catalog()


@router.get("/snippets/{snippet_id}", response_model=Snippet)
def get_snippet(snippet_id: str) -> Snippet:
    snippet = find_snippet(snippet_id)
    if snippet is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Snippet no encontrado")
    return snippet


@router.post("/snippets/{snippet_id}/render")
def render_snippet_endpoint(snippet_id: str, payload: RenderPayload) -> dict[str, str]:
    snippet = find_snippet(snippet_id)
    if snippet is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Snippet no encontrado")
    return {"code": render_snippet(snippet, payload.values)}


@router.get("/latex-symbols")
def get_symbols(category: str | None = None) -> list[dict[str, str]]:
    return [
        {
            "id": s.id,
            "char": s.char,
            "latex": s.latex,
            "category": s.category,
            "description": s.description,
        }
        for s in list_symbols(category)
    ]


@router.get("/latex-symbols/favorites")
def get_favorites() -> list[str]:
    return favorites.list_favorites()


@router.post("/latex-symbols/favorites/{symbol_id}", status_code=status.HTTP_201_CREATED)
def add_favorite(symbol_id: str) -> dict[str, str]:
    favorites.add(symbol_id)
    return {"status": "ok"}


@router.delete("/latex-symbols/favorites/{symbol_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite(symbol_id: str) -> None:
    favorites.remove(symbol_id)


def _find_cell(page_id: str, events: list[Event], cell_id: str) -> CellNode | None:
    proj = project(page_id, events)
    for child in proj.ast.children:
        if getattr(child, "type", None) == "cell" and getattr(child, "cell_id", None) == cell_id:
            return child  # type: ignore[return-value]
    return None


def _extract_body(latex: str) -> tuple[str, Literal["inline", "display"]]:
    latex = latex.strip()
    if latex.startswith("\\[") and latex.endswith("\\]"):
        return latex[2:-2].strip(), "display"
    if latex.startswith("$") and latex.endswith("$"):
        return latex[1:-1].strip(), "inline"
    return latex, "inline"


def _vault_summary(vf: VaultFile) -> VaultSummary:
    return VaultSummary(
        id=vf.id,
        name=vf.name,
        mime_type=vf.mime_type,
        size=vf.size,
        uploaded_at=vf.uploaded_at,
        status=vf.status,
        scheduled_for_deletion_at=vf.scheduled_for_deletion_at,
    )


MAX_UPLOAD_BYTES = 100 * 1024 * 1024  # 100 MB


@router.post("/vault", status_code=status.HTTP_201_CREATED, response_model=VaultSummary)
async def upload_vault_file(file: Annotated[UploadFile, File(...)]) -> VaultSummary:
    # Solo el nombre base: bloquea path traversal vía filename ("../../x").
    safe_name = Path(file.filename or "").name
    if not safe_name:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nombre de archivo requerido")
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Archivo demasiado grande")
    temp_path = settings.vault_dir / "tmp_upload"
    temp_path.mkdir(parents=True, exist_ok=True)
    dest = temp_path / safe_name
    dest.write_bytes(content)
    try:
        vf = vault.add_file(dest)
    finally:
        if dest.exists():
            dest.unlink()
    store.append(
        vault_file_added(
            file_id=vf.id,
            name=vf.name,
            file_hash=vf.hash,
            mime_type=vf.mime_type,
            size=vf.size,
        )
    )
    return _vault_summary(vf)


@router.get("/vault", response_model=list[VaultSummary])
def list_vault_files(include_pending: bool = True) -> list[VaultSummary]:
    return [_vault_summary(f) for f in vault.list_files(include_pending)]


@router.get("/vault/{file_id}", response_model=VaultDetail)
def get_vault_file(file_id: str) -> VaultDetail:
    vf = vault.get_file(file_id)
    if vf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Archivo no encontrado")
    return VaultDetail(
        id=vf.id,
        name=vf.name,
        mime_type=vf.mime_type,
        size=vf.size,
        uploaded_at=vf.uploaded_at,
        status=vf.status,
        scheduled_for_deletion_at=vf.scheduled_for_deletion_at,
        deletion_phrase=vf.deletion_phrase,
    )


@router.get("/vault/{file_id}/preview")
def preview_vault_file(file_id: str) -> dict[str, Any]:
    try:
        return vault.generate_preview(file_id)
    except FileNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Archivo no encontrado") from None


@router.get("/vault/{file_id}/download")
def download_vault_file(file_id: str) -> Response:
    vf = vault.get_file(file_id)
    if vf is None or not vf.stored_path.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Archivo no encontrado")
    content = vf.stored_path.read_bytes()
    media_type = vf.mime_type or "application/octet-stream"
    safe_name = vf.name.replace('"', "'")
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="{safe_name}"'},
    )


@router.post("/vault/{file_id}/delete-request", response_model=dict[str, Any])
def request_vault_deletion(file_id: str) -> dict[str, Any]:
    scheduled = vault.request_deletion(file_id)
    if scheduled is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Archivo no encontrado")
    store.append(vault_deletion_scheduled(file_id=file_id, scheduled_at=scheduled))
    return {"status": "pending_deletion", "scheduled_for_deletion_at": scheduled}


@router.post("/vault/{file_id}/cancel-delete")
def cancel_vault_deletion(file_id: str) -> dict[str, str]:
    if not vault.cancel_deletion(file_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Archivo no encontrado")
    return {"status": "active"}


@router.post("/vault/{file_id}/force-delete")
def force_delete_vault_file(file_id: str, payload: ForceDeletePayload) -> dict[str, str]:
    if not vault.force_delete(file_id, payload.phrase):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Frase incorrecta o archivo no encontrado")
    store.append(vault_file_deleted(file_id=file_id, reason="forced"))
    return {"status": "deleted"}


@router.post("/vault/purge")
def purge_vault() -> dict[str, int]:
    expired = vault.purge_expired()
    for file_id in expired:
        store.append(vault_file_deleted(file_id=file_id, reason="expired"))
    return {"purged": len(expired)}


_LATEX_ESCAPES = {
    "\\": "\\textbackslash{}",
    "&": "\\&",
    "%": "\\%",
    "$": "\\$",
    "#": "\\#",
    "_": "\\_",
    "{": "\\{",
    "}": "\\}",
    "~": "\\textasciitilde{}",
    "^": "\\textasciicircum{}",
}


def _escape_latex(text: str) -> str:
    """Escapa caracteres especiales de LaTeX (evita inyección desde el título)."""
    return "".join(_LATEX_ESCAPES.get(ch, ch) for ch in text)


def _latex_document(latex: str, title: str) -> str:
    return (
        "\\documentclass{article}\n"
        "\\usepackage[utf8]{inputenc}\n"
        "\\usepackage{amsmath,amssymb}\n"
        "\\usepackage{graphicx}\n"
        "\\begin{document}\n"
        f"\\title{{{_escape_latex(title)}}}\\maketitle\n"
        f"{latex}\n"
        "\\end{document}\n"
    )


def _pandoc_export(latex: str, title: str, suffix: str, media_type: str) -> Response:
    if which("pandoc") is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "pandoc no está instalado")

    doc = _latex_document(latex, title)
    with NamedTemporaryFile(mode="w", suffix=".tex", delete=False, encoding="utf-8") as src:
        src.write(doc)
        src_path = Path(src.name)

    out_path = src_path.with_suffix(f".{suffix}")
    cmd = ["pandoc", str(src_path), "-o", str(out_path)]
    if suffix == "pdf":
        engine = "xelatex" if which("xelatex") else "pdflatex"
        cmd.extend(["--pdf-engine", engine])

    try:
        run(cmd, check=True, capture_output=True, text=True)
    except CalledProcessError as exc:
        msg = f"Error de exportación: {exc.stderr}"
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, msg) from exc
    finally:
        src_path.unlink(missing_ok=True)

    if not out_path.exists():
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "No se generó el archivo")

    data = out_path.read_bytes()
    out_path.unlink(missing_ok=True)
    filename = f"{title.replace(' ', '_')}.{suffix}"
    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _latex_to_plain(latex: str, title: str) -> str:
    if which("pandoc") is None:
        # fallback simple
        return latex.replace("\\", "").replace("{", "").replace("}", "")
    doc = _latex_document(latex, title)
    with NamedTemporaryFile(mode="w", suffix=".tex", delete=False, encoding="utf-8") as src:
        src.write(doc)
        src_path = Path(src.name)
    out_path = src_path.with_suffix(".txt")
    try:
        run(
            ["pandoc", str(src_path), "-t", "plain", "-o", str(out_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        text = out_path.read_text(encoding="utf-8")
    except CalledProcessError:
        text = latex
    finally:
        src_path.unlink(missing_ok=True)
        out_path.unlink(missing_ok=True)
    return text


def _canva_html(latex: str, title: str) -> str:
    # Canva-friendly HTML: large sections, clean typography, copy-paste ready
    escaped = latex.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    paragraphs = [f"<p>{line}</p>" for line in escaped.split("\n") if line.strip()]
    style = "; ".join(
        [
            "font-family: system-ui, -apple-system, sans-serif",
            "margin: 0",
            "padding: 40px",
            "background: #fff",
            "color: #111",
        ]
    )
    section_style = "; ".join(
        [
            "max-width: 720px",
            "margin: 0 auto 48px",
            "padding: 32px",
            "border-radius: 16px",
            "background: #f8f9fa",
        ]
    )
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
body {{ {style} }}
section {{ {section_style} }}
h1 {{ font-size: 2.5rem; margin-bottom: 0.5em; }}
p {{ font-size: 1.1rem; line-height: 1.7; margin: 0.6em 0; }}
code {{ background: #e9ecef; padding: 2px 6px; border-radius: 4px; font-family: monospace; }}
</style>
</head>
<body>
<section><h1>{title}</h1></section>
<section>{"".join(paragraphs)}</section>
</body>
</html>"""


@router.get("/pages/{page_id}/export/pdf")
async def export_page_pdf(page_id: str) -> Response:
    events = _events(page_id)
    proj = project(page_id, events)
    title = proj.title or "lablog_export"
    figures_dir = settings.figures_dir / page_id
    async with _pdf_lock(page_id):
        result = await pdf_engine.compile_page(page_id, proj.ast, title, figures_dir=figures_dir)
    if result.status == "ok" and result.pdf is not None:
        filename = f"{title.replace(' ', '_')}.pdf"
        return Response(
            content=result.pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename={filename}"},
        )
    if result.status == "no_engine":
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Tectonic no disponible")
    if result.status == "timeout":
        raise HTTPException(status.HTTP_504_GATEWAY_TIMEOUT, "Compilación excedió el tiempo límite")
    raise HTTPException(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={"errors": [asdict(e) for e in result.errors], "log": result.log[-4000:]},
    )


@router.get("/pages/{page_id}/export/{format}")
def export_page(page_id: str, format: str) -> Response:
    events = _events(page_id)
    proj = project(page_id, events)
    latex = serialize_ast(proj.ast)
    title = proj.title or "lablog_export"

    if format == "tex":
        content = _latex_document(latex, title)
        return Response(
            content=content.encode("utf-8"),
            media_type="application/x-tex",
            headers={"Content-Disposition": f"attachment; filename={title.replace(' ', '_')}.tex"},
        )
    if format == "txt":
        content = _latex_to_plain(latex, title)
        return Response(
            content=content.encode("utf-8"),
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={title.replace(' ', '_')}.txt"},
        )
    if format == "docx":
        return _pandoc_export(
            latex,
            title,
            "docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    if format == "canva":
        content = _canva_html(latex, title)
        filename = f"{title.replace(' ', '_')}_canva.html"
        return Response(
            content=content.encode("utf-8"),
            media_type="text/html",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Formato no soportado: {format}")


app.include_router(router)

_dist_dir = ui_dist_dir()
if _dist_dir.exists():
    app.mount("/", StaticFiles(directory=_dist_dir, html=True), name="static")
