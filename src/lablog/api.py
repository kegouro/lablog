"""Servidor FastAPI del engine de lablog."""

from __future__ import annotations

import asyncio
import re
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from shutil import which
from subprocess import CalledProcessError, run
from tempfile import NamedTemporaryFile
from typing import Annotated, Any, Literal, NoReturn

from fastapi import APIRouter, FastAPI, File, HTTPException, Response, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from lablog import commands, completions, diagrams, pdf_engine, projections, templates
from lablog.ast_nodes import node_to_json
from lablog.code_engine import CodeEngine, EngineStartError
from lablog.commands import (
    CellNotFoundError,
    EngineExecutionError,
    PageDeletedError,
    UnsupportedLanguageError,
)
from lablog.config import settings, ui_dist_dir
from lablog.event_store import EventStore
from lablog.events import (
    Event,
    vault_deletion_scheduled,
    vault_file_added,
    vault_file_deleted,
)
from lablog.exporter import export_site
from lablog.latex_symbols import FavoritesStore, list_symbols
from lablog.projections import PageNotFoundError
from lablog.snippets import Snippet, find_snippet, render_snippet
from lablog.vault import VaultFile, VaultService

# Límite de cuerpo LaTeX por PUT/replace (evita reventar el event log).
_MAX_LATEX_CHARS = 5_000_000
_SAFE_CELL_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

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
    from lablog import __version__

    return {
        "status": "ok",
        "version": __version__,
        "engine_ready": _engine_ready(),
        "diagram_presets": len(diagrams.list_presets()),
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


@router.get("/templates")
def list_latex_templates() -> list[dict[str, str]]:
    return templates.templates_as_dicts()


@router.get("/templates/{template_id}")
def get_latex_template(template_id: str) -> dict[str, str]:
    tmpl = templates.get_template(template_id)
    if tmpl is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Plantilla no encontrada: {template_id}")
    return {
        "id": tmpl.id,
        "name": tmpl.name,
        "description": tmpl.description,
        "content": tmpl.content,
    }


@router.get("/suggest")
def suggest_latex(q: str = "", limit: int = 40) -> list[dict[str, str]]:
    return completions.suggest_as_dicts(q, limit=min(max(limit, 1), 100))


class DiagramExpandRequest(BaseModel):
    params: dict[str, float] | None = None


@router.get("/diagrams/presets")
def list_diagram_presets() -> list[dict[str, Any]]:
    return [p.summary_dict() for p in diagrams.list_presets()]


@router.get("/diagrams/presets/{preset_id}")
def get_diagram_preset(preset_id: str) -> dict[str, Any]:
    preset = diagrams.get_preset(preset_id)
    if preset is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Preset no encontrado: {preset_id}")
    return preset.model_dump()


@router.post("/diagrams/presets/{preset_id}/expand")
def expand_diagram_preset(preset_id: str, body: DiagramExpandRequest) -> dict[str, Any]:
    preset = diagrams.get_preset(preset_id)
    if preset is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Preset no encontrado: {preset_id}")
    return diagrams.expand_preset(preset, body.params)


@router.post("/diagrams/presets/{preset_id}/simulate-source")
def diagram_simulate_source(preset_id: str, body: DiagramExpandRequest) -> dict[str, Any]:
    preset = diagrams.get_preset(preset_id)
    if preset is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Preset no encontrado: {preset_id}")
    try:
        return diagrams.expand_simulation(preset, body.params)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


class DiagramApplyRequest(BaseModel):
    """Reaplica un preset sobre el LaTeX de la página (params opcionales)."""

    latex: str = Field(max_length=_MAX_LATEX_CHARS)
    params: dict[str, float] | None = None
    preset_id: str | None = None


@router.post("/diagrams/apply")
def apply_diagram_params(body: DiagramApplyRequest) -> dict[str, Any]:
    """Detecta preset en el doc o usa preset_id; reexpande y sustituye el bloque."""
    preset_id = body.preset_id or diagrams.parse_lablog_preset_id(body.latex)
    if not preset_id:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "No hay lablog-diagram en el documento ni preset_id",
        )
    preset = diagrams.get_preset(preset_id)
    if preset is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Preset no encontrado: {preset_id}")
    # Params del body > comentarios del doc > defaults
    from_doc = diagrams.parse_lablog_params(body.latex)
    merged = {**from_doc, **(body.params or {})}
    expanded = diagrams.expand_preset(preset, merged)
    new_latex = diagrams.replace_or_append_diagram(body.latex, expanded["latex"])
    return {
        **expanded,
        "document_latex": new_latex,
    }


store = EventStore(settings.event_dir)
favorites = FavoritesStore()
vault = VaultService()
_code_engine: CodeEngine | None = None
_engine_lock = threading.Lock()
_pdf_locks: dict[str, asyncio.Lock] = {}
# Un solo worker: serializa Jupyter fuera del event loop sin saturar el pool default.
_compute_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="lablog-compute")


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
    latex: str = Field(max_length=_MAX_LATEX_CHARS)
    version: int | None = None


class UpdatePageRawRequest(BaseModel):
    raw: str = Field(max_length=_MAX_LATEX_CHARS)
    """Versión esperada (len(events)). Si no coincide → 409."""
    version: int | None = None


class MathPayload(BaseModel):
    latex: str = Field(max_length=_MAX_LATEX_CHARS)
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
    cell_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    language: str = "python"
    source: str = Field(max_length=_MAX_LATEX_CHARS)


class UpdateCellPayload(BaseModel):
    language: str = "python"
    source: str = Field(max_length=_MAX_LATEX_CHARS)


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
    # Solo se rellena en la respuesta de request-deletion (token de un solo uso).
    deletion_phrase: str | None = None


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


def _require_active_page(page_id: str) -> list[Event]:
    """Exige página existente y no soft-deleted antes de escribir."""
    events = _events(page_id)
    try:
        projections.assert_active(store, page_id)
    except PageNotFoundError:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Página eliminada o no disponible",
        ) from None
    return events


def _check_version(page_id: str, expected: int | None) -> None:
    if expected is None:
        return
    current = len(store.get_events(page_id))
    if expected != current:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail={
                "error_code": "VERSION_CONFLICT",
                "message": "La página cambió en otro cliente; recarga e inténtalo de nuevo",
                "expected": expected,
                "current": current,
            },
        )


def _safe_download_filename(title: str, ext: str) -> str:
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", (title or "lablog").strip())[:80]
    base = base.strip("._") or "lablog"
    return f"{base}.{ext.lstrip('.')}"


def _handle_projection_not_found(page_id: str) -> NoReturn:
    """Convierte errores de proyección en respuestas HTTP 404."""
    raise HTTPException(status.HTTP_404_NOT_FOUND, f"Página no encontrada: {page_id}")


@router.post("/pages", status_code=status.HTTP_201_CREATED, response_model=PageSummary)
def create_page(req: CreatePageRequest) -> PageSummary:
    page_id = commands.create_page(store, title=req.title, project_id=req.project_id)
    try:
        return PageSummary(**projections.page_summary(store, page_id))
    except PageNotFoundError:
        _handle_projection_not_found(page_id)


@router.get("/pages", response_model=list[PageSummary])
def list_pages() -> list[PageSummary]:
    return [PageSummary(**s) for s in projections.list_page_summaries(store)]


@router.patch("/pages/{page_id}", response_model=PageSummary)
def update_page(page_id: str, req: UpdatePageRequest) -> PageSummary:
    if not _is_valid_page_id(page_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"page_id inválido: {page_id}")
    _require_active_page(page_id)
    commands.update_page_metadata(
        store,
        page_id=page_id,
        title=req.title,
        project_id=req.project_id,
    )
    try:
        return PageSummary(**projections.page_summary(store, page_id))
    except PageNotFoundError:
        _handle_projection_not_found(page_id)


@router.put("/pages/{page_id}", response_model=PageDetail)
def update_page_raw(page_id: str, req: UpdatePageRawRequest) -> PageDetail:
    if not _is_valid_page_id(page_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"page_id inválido: {page_id}")
    _require_active_page(page_id)
    _check_version(page_id, req.version)
    commands.replace_document(store, page_id=page_id, latex=req.raw)
    try:
        return PageDetail(**projections.page_detail(store, page_id))
    except PageNotFoundError:
        _handle_projection_not_found(page_id)


@router.delete("/pages/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_page(page_id: str) -> None:
    if not _is_valid_page_id(page_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"page_id inválido: {page_id}")
    _require_active_page(page_id)
    commands.delete_page(store, page_id=page_id)


@router.get("/pages/{page_id}", response_model=PageDetail)
def get_page(page_id: str) -> PageDetail:
    try:
        return PageDetail(**projections.page_detail(store, page_id))
    except PageNotFoundError:
        _handle_projection_not_found(page_id)


@router.get("/pages/{page_id}/latex")
def get_latex(page_id: str) -> dict[str, str]:
    try:
        detail = projections.page_detail(store, page_id)
    except PageNotFoundError:
        _handle_projection_not_found(page_id)
    return {"latex": detail["latex"]}


@router.post("/pages/{page_id}/text", status_code=status.HTTP_201_CREATED)
def append_text(page_id: str, payload: TextPayload) -> dict[str, str]:
    if not _is_valid_page_id(page_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"page_id inválido: {page_id}")
    _require_active_page(page_id)
    commands.insert_text(store, page_id=page_id, position=payload.position, text=payload.text)
    return {"status": "ok"}


@router.post("/pages/{page_id}/replace", status_code=status.HTTP_201_CREATED)
def replace_page(page_id: str, payload: ReplacePayload) -> dict[str, Any]:
    if not _is_valid_page_id(page_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"page_id inválido: {page_id}")
    _require_active_page(page_id)
    _check_version(page_id, payload.version)
    commands.replace_document(store, page_id=page_id, latex=payload.latex)
    try:
        detail = projections.page_detail(store, page_id)
    except PageNotFoundError:
        _handle_projection_not_found(page_id)
    return {
        "status": "ok",
        "latex": detail["latex"],
        "ast": detail["ast"],
        "version": detail["version"],
    }


@router.post("/pages/{page_id}/math", status_code=status.HTTP_201_CREATED)
def insert_math(page_id: str, payload: MathPayload) -> dict[str, str]:
    if not _is_valid_page_id(page_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"page_id inválido: {page_id}")
    _require_active_page(page_id)
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
    _require_active_page(page_id)
    intent = commands.voice_insert(store, page_id=page_id, text=payload.text)
    return {"status": "ok", "intent": intent}


@router.get("/pages/{page_id}/events", response_model=list[Event])
def get_events(page_id: str) -> list[Event]:
    return store.get_events(page_id)


@router.get("/pages/{page_id}/history", response_model=list[HistoryEntry])
def page_history(page_id: str) -> list[HistoryEntry]:
    try:
        entries = projections.page_history(store, page_id)
    except PageNotFoundError:
        _handle_projection_not_found(page_id)
    return [HistoryEntry(**entry) for entry in entries]


@router.get("/pages/{page_id}/at/{event_index}", response_model=PageDetail)
def page_at(page_id: str, event_index: int) -> PageDetail:
    try:
        return PageDetail(**projections.page_at(store, page_id, event_index))
    except PageNotFoundError:
        _handle_projection_not_found(page_id)


@router.post("/pages/{page_id}/restore/{event_index}", response_model=PageDetail)
def restore_version(page_id: str, event_index: int) -> PageDetail:
    if not _is_valid_page_id(page_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"page_id inválido: {page_id}")
    _require_active_page(page_id)
    try:
        commands.restore_version(store, page_id=page_id, event_index=event_index)
    except PageDeletedError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Página eliminada") from None
    try:
        return PageDetail(**projections.page_detail(store, page_id))
    except PageNotFoundError:
        _handle_projection_not_found(page_id)


@router.post("/pages/{page_id}/cells", status_code=status.HTTP_201_CREATED)
def insert_cell(page_id: str, payload: CellPayload) -> dict[str, str]:
    if not _is_valid_page_id(page_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"page_id inválido: {page_id}")
    _require_active_page(page_id)
    commands.insert_cell(
        store,
        page_id=page_id,
        cell_id=payload.cell_id,
        language=payload.language,
        source=payload.source,
    )
    return {"status": "ok"}


@router.post("/pages/{page_id}/cells/{cell_id}/update", status_code=status.HTTP_200_OK)
def update_cell(page_id: str, cell_id: str, payload: UpdateCellPayload) -> dict[str, str]:
    if not _is_valid_page_id(page_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"page_id inválido: {page_id}")
    _require_active_page(page_id)
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
    _require_active_page(page_id)
    figure_dir = settings.figures_dir / page_id
    try:
        engine = get_engine()
    except EngineStartError as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error_code": "KERNEL_DEAD", "message": str(exc), "cell_id": cell_id},
        ) from exc

    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(
            _compute_pool,
            lambda: commands.execute_cell(
                store,
                page_id=page_id,
                cell_id=cell_id,
                engine=engine,
                figure_dir=figure_dir,
            ),
        )
    except CellNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except UnsupportedLanguageError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except EngineExecutionError as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error_code": "KERNEL_DEAD", "message": str(exc), "cell_id": cell_id},
        ) from exc

    cell = projections.find_cell(store, page_id, cell_id)
    if cell is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Celda no encontrada: {cell_id}")
    return node_to_json(cell)


@router.delete("/pages/{page_id}/cells/{cell_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cell(page_id: str, cell_id: str) -> None:
    if not _is_valid_page_id(page_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"page_id inválido: {page_id}")
    _require_active_page(page_id)
    commands.delete_cell(store, page_id=page_id, cell_id=cell_id)


@router.post("/pages/{page_id}/cells/{cell_id}/move", status_code=status.HTTP_200_OK)
def move_cell(page_id: str, cell_id: str, payload: MoveCellPayload) -> dict[str, str]:
    if not _is_valid_page_id(page_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"page_id inválido: {page_id}")
    _require_active_page(page_id)
    commands.move_cell(store, page_id=page_id, cell_id=cell_id, new_index=payload.new_index)
    return {"status": "ok"}


@router.get("/pages/{page_id}/cells")
def list_cells(page_id: str) -> list[dict[str, Any]]:
    try:
        return projections.list_cells(store, page_id)
    except PageNotFoundError:
        _handle_projection_not_found(page_id)


@router.get("/pages/{page_id}/cells/{cell_id}/figure")
def get_cell_figure(page_id: str, cell_id: str) -> Response:
    try:
        cell = projections.find_cell(store, page_id, cell_id)
    except PageNotFoundError:
        _handle_projection_not_found(page_id)
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
    # Nombre único: evita colisión entre uploads concurrentes del mismo filename.
    dest = temp_path / f"{uuid.uuid4().hex}_{safe_name}"
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
    # Nunca devolver la frase de borrado en GET (no es secreto si se lista).
    return VaultDetail(
        id=vf.id,
        name=vf.name,
        mime_type=vf.mime_type,
        size=vf.size,
        uploaded_at=vf.uploaded_at,
        status=vf.status,
        scheduled_for_deletion_at=vf.scheduled_for_deletion_at,
        deletion_phrase=None,
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
    result = vault.request_deletion(file_id)
    if result is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Archivo no encontrado")
    scheduled, phrase = result
    store.append(vault_deletion_scheduled(file_id=file_id, scheduled_at=scheduled))
    # La frase solo se devuelve aquí (confirmación de un solo uso en la UI).
    return {
        "status": "pending_deletion",
        "scheduled_for_deletion_at": scheduled,
        "deletion_phrase": phrase,
    }


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
    filename = _safe_download_filename(title, suffix)
    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
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
    import html as html_mod

    safe_title = html_mod.escape(title, quote=True)
    escaped = html_mod.escape(latex, quote=False)
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
<title>{safe_title}</title>
<style>
body {{ {style} }}
section {{ {section_style} }}
h1 {{ font-size: 2.5rem; margin-bottom: 0.5em; }}
p {{ font-size: 1.1rem; line-height: 1.7; margin: 0.6em 0; }}
code {{ background: #e9ecef; padding: 2px 6px; border-radius: 4px; font-family: monospace; }}
</style>
</head>
<body>
<section><h1>{safe_title}</h1></section>
<section>{"".join(paragraphs)}</section>
</body>
</html>"""


def _page_includes() -> dict[str, str]:
    """Mapa page_id / page:<id> → raw para resolver \\input en compile."""
    out: dict[str, str] = {}
    for summary in projections.list_page_summaries(store):
        pid = str(summary["page_id"])
        try:
            detail = projections.page_detail(store, pid)
        except PageNotFoundError:
            continue
        raw = str(detail["raw"])
        out[pid] = raw
        out[f"page:{pid}"] = raw
    return out


@router.get("/pages/{page_id}/export/pdf")
async def export_page_pdf(page_id: str) -> Response:
    try:
        proj = projections.page_projection(store, page_id)
    except PageNotFoundError:
        _handle_projection_not_found(page_id)
    title = proj.title or "lablog_export"
    # figure_path se guarda relativo a figures_dir (p.ej. "{page_id}/fig_0.png").
    # No pasar figures_dir/page_id o se duplica el segmento.
    figures_dir = settings.figures_dir
    includes = _page_includes()
    async with _pdf_lock(page_id):
        result = await pdf_engine.compile_page(
            page_id,
            proj.ast,
            title,
            figures_dir=figures_dir,
            includes=includes,
        )
    if result.status == "ok" and result.pdf is not None:
        filename = _safe_download_filename(title, "pdf")
        return Response(
            content=result.pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{filename}"'},
        )
    if result.status == "no_engine":
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error_code": "PUBLISH_ENGINE_CRASH", "message": "Tectonic no disponible"},
        )
    if result.status == "timeout":
        raise HTTPException(status.HTTP_504_GATEWAY_TIMEOUT, "Compilación excedió el tiempo límite")
    raise HTTPException(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={"errors": [asdict(e) for e in result.errors], "log": result.log[-4000:]},
    )


@router.get("/pages/{page_id}/export/{format}")
def export_page(page_id: str, format: str) -> Response:
    try:
        detail = projections.page_detail(store, page_id)
    except PageNotFoundError:
        _handle_projection_not_found(page_id)
    latex = detail["latex"]
    title = str(detail["title"] or "lablog_export")

    if format == "tex":
        content = _latex_document(latex, title)
        filename = _safe_download_filename(title, "tex")
        return Response(
            content=content.encode("utf-8"),
            media_type="application/x-tex",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    if format == "txt":
        content = _latex_to_plain(latex, title)
        filename = _safe_download_filename(title, "txt")
        return Response(
            content=content.encode("utf-8"),
            media_type="text/plain",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
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
        filename = _safe_download_filename(f"{title}_canva", "html")
        return Response(
            content=content.encode("utf-8"),
            media_type="text/html",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Formato no soportado: {format}")


app.include_router(router)

_dist_dir = ui_dist_dir()
if _dist_dir.exists():
    app.mount("/", StaticFiles(directory=_dist_dir, html=True), name="static")
