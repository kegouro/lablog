# Acto II: Backend Headless — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Convertir `api.py` en un adapter HTTP delgado: toda la lógica de escritura vive en `commands.py`, toda la lógica de lectura en `projections.py`, y `CodeEngine` ejecuta sin bloquear emitiendo eventos de dominio (`cell_executed` para éxitos, `execution_failed` para cualquier fallo).

**Architecture:** CQRS ligero. Los endpoints HTTP solo validan, deserializan y delegan. El dominio (`commands`) decide qué eventos escribir. Las proyecciones reconstruyen el estado de lectura desde el event store. El motor de celdas corre fuera del hilo de FastAPI y sus fallos se modelan como eventos de dominio, nunca como errores HTTP opacos.

**Tech Stack:** Python 3.13, FastAPI, Pydantic, Event Sourcing (JSONL), Jupyter Client (`jupyter_client`), pytest.

---

## Contexto necesario

- `src/lablog/api.py` tiene ~1000 líneas con lógica de negocio mezclada con HTTP.
- `src/lablog/projector.py` ya existe y proyecta eventos a `PageProjection`.
- `src/lablog/code_engine.py` bloquea el hilo de FastAPI porque `execute_cell` lo llama directamente.
- El evento `cell_executed` solo guarda `output` y `figure_path`; si el kernel falla, el frontend recibe un 503 genérico.
- Los nodos AST son `dataclasses`. La serialización actual mezcla `vars()` con `asdict()`; este plan estandariza una función `node_to_json` en `ast_nodes.py`.
- El frontend tiene dos vistas de celdas (`cells-panel.tsx`, `lab-canvas.tsx`) que mantienen estado local duplicado. En este Acto solo se tocan para leer `status`/`output` directamente del AST y actualizar un solo nodo tras la ejecución.

---

## Task 1: Añadir evento de dominio `execution_failed`

**Files:**
- Modify: `src/lablog/events.py`
- Test: `tests/test_events.py` (crear si no existe)

**Step 1: Write the failing test**

```python
from lablog.events import execution_failed


def test_execution_failed_event_has_traceback():
    event = execution_failed(
        page_id="p1",
        cell_id="c1",
        ename="ZeroDivisionError",
        evalue="division by zero",
        traceback=["Traceback (most recent call last):", "ZeroDivisionError: division by zero"],
    )
    assert event.type == "execution_failed"
    assert event.payload["cell_id"] == "c1"
    assert "traceback" in event.payload
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_events.py::test_execution_failed_event_has_traceback -v`
Expected: FAIL with `name 'execution_failed' is not defined`

**Step 3: Write minimal implementation**

Añadir en `src/lablog/events.py`:

```python
class ExecutionFailedPayload(BaseModel):
    cell_id: str
    ename: str
    evalue: str
    traceback: list[str]


def execution_failed(
    page_id: str,
    cell_id: str,
    ename: str,
    evalue: str,
    traceback: list[str],
) -> Event:
    return Event(
        type="execution_failed",
        page_id=page_id,
        payload=ExecutionFailedPayload(
            cell_id=cell_id,
            ename=ename,
            evalue=evalue,
            traceback=traceback,
        ).model_dump(),
    )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_events.py::test_execution_failed_event_has_traceback -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/lablog/events.py tests/test_events.py
git commit -m "feat(domain): add execution_failed event"
```

---

## Task 2: Extender `CellNode` con campo `status`

**Files:**
- Modify: `src/lablog/ast_nodes.py`
- Modify: `ui/src/types/index.ts`
- Test: `tests/test_ast_nodes.py` (crear si no existe)

**Step 1: Write the failing test**

```python
from lablog.ast_nodes import CellNode


def test_cell_node_defaults_to_idle_status():
    cell = CellNode(cell_id="c1", language="python", source="1+1")
    assert cell.status == "idle"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_ast_nodes.py::test_cell_node_defaults_to_idle_status -v`
Expected: FAIL (`CellNode` no tiene `status`)

**Step 3: Write minimal implementation**

En `src/lablog/ast_nodes.py`:

```python
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class CellNode:
    type: str = "cell"
    cell_id: str = ""
    language: str = ""
    source: str = ""
    output: str | None = None
    figure_path: str | None = None
    status: Literal["idle", "running", "ok", "error"] = "idle"
```

En `ui/src/types/index.ts`:

```typescript
export interface CellNode {
  type: 'cell'
  cell_id: string
  language: string
  source: string
  output: string
  figure_path: string | null
  status?: 'idle' | 'running' | 'ok' | 'error'
}
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_ast_nodes.py::test_cell_node_defaults_to_idle_status -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/lablog/ast_nodes.py ui/src/types/index.ts tests/test_ast_nodes.py
git commit -m "feat(ast): add status field to CellNode"
```

---

## Task 3: Estandarizar serialización del AST con `node_to_json`

**Files:**
- Modify: `src/lablog/ast_nodes.py`
- Test: `tests/test_ast_nodes.py`

**Step 1: Write the failing test**

```python
from lablog.ast_nodes import CellNode, MathNode, TextNode, node_to_json


def test_node_to_json_serializes_all_fields():
    cell = CellNode(cell_id="c1", language="python", source="1+1", status="ok")
    assert node_to_json(cell) == {
        "type": "cell",
        "cell_id": "c1",
        "language": "python",
        "source": "1+1",
        "output": None,
        "figure_path": None,
        "status": "ok",
    }
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_ast_nodes.py::test_node_to_json_serializes_all_fields -v`
Expected: FAIL (`node_to_json` no existe)

**Step 3: Write minimal implementation**

Añadir en `src/lablog/ast_nodes.py`:

```python
from dataclasses import asdict


def node_to_json(node: Node) -> dict[str, Any]:
    """Serializa un nodo AST a dict JSON-safe de forma determinista."""
    return asdict(node)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_ast_nodes.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/lablog/ast_nodes.py tests/test_ast_nodes.py
git commit -m "feat(ast): add deterministic node_to_json serializer"
```

---

## Task 4: Actualizar `PageProjection` para aplicar `execution_failed` y estados de ejecución

**Files:**
- Modify: `src/lablog/projector.py`
- Test: `tests/test_projector.py`

**Step 1: Write the failing test**

```python
from lablog.events import cell_executed, cell_inserted, execution_failed
from lablog.projector import project


def test_execution_failed_sets_cell_error_status():
    events = [
        cell_inserted(page_id="p1", cell_id="c1", language="python", source="1/0"),
        execution_failed(
            page_id="p1",
            cell_id="c1",
            ename="ZeroDivisionError",
            evalue="division by zero",
            traceback=["ZeroDivisionError: division by zero"],
        ),
    ]
    proj = project("p1", events)
    cell = proj.ast.children[0]
    assert cell.status == "error"
    assert "ZeroDivisionError" in cell.output


def test_cell_executed_sets_cell_ok_status():
    events = [
        cell_inserted(page_id="p1", cell_id="c1", language="python", source="1+1"),
        cell_executed(page_id="p1", cell_id="c1", output="2"),
    ]
    proj = project("p1", events)
    assert proj.ast.children[0].status == "ok"
    assert proj.ast.children[0].output == "2"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_projector.py::test_execution_failed_sets_cell_error_status -v`
Expected: FAIL (`cell.status` no se actualiza)

**Step 3: Write minimal implementation**

En `src/lablog/projector.py`, actualizar `_update_cell_output` y añadir manejador de `execution_failed`:

```python
case "cell_executed":
    self._update_cell_output(event.payload, status="ok")

case "execution_failed":
    self._update_cell_output(
        {
            "cell_id": event.payload["cell_id"],
            "output": "\n".join(event.payload["traceback"]),
            "figure_path": None,
        },
        status="error",
    )
```

Y cambiar `_update_cell_output` para aceptar `status`:

```python
def _update_cell_output(self, payload: dict[str, Any], status: str = "ok") -> None:
    cell_id = payload.get("cell_id")
    for child in self.ast.children:
        if isinstance(child, CellNode) and child.cell_id == cell_id:
            child.output = payload.get("output")
            child.figure_path = payload.get("figure_path")
            child.status = status
            break
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_projector.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/lablog/projector.py tests/test_projector.py
git commit -m "feat(projector): apply execution_failed and cell status"
```

---

## Task 5: Extraer `commands.py` — comandos de página y texto

**Files:**
- Create: `src/lablog/commands.py`
- Modify: `src/lablog/api.py`
- Test: `tests/test_commands.py` (crear)

**Step 1: Write the failing test**

```python
from lablog.commands import create_page, replace_document
from lablog.event_store import EventStore


def test_create_page_returns_summary(tmp_path):
    store = EventStore(tmp_path)
    summary = create_page(store, title="Test")
    assert summary.title == "Test"
    assert summary.page_id


def test_replace_document_returns_projection(tmp_path):
    store = EventStore(tmp_path)
    summary = create_page(store, title="Test")
    detail = replace_document(store, summary.page_id, "hello world")
    assert detail.raw == "hello world"
    assert len(detail.ast) == 1
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_commands.py -v`
Expected: FAIL (`commands` no existe)

**Step 3: Write minimal implementation**

Crear `src/lablog/commands.py` con los comandos de página:

```python
from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

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
from lablog.projector import PageProjection, project


def create_page(store: EventStore, title: str, project_id: str | None = None) -> Any:
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


def update_page_metadata(store: EventStore, page_id: str, title: str | None, project_id: str | None) -> Any:
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


def replace_document(store: EventStore, page_id: str, latex: str) -> Any:
    store.append(document_replaced(page_id=page_id, latex=latex))


def insert_text(store: EventStore, page_id: str, position: int, text: str) -> None:
    store.append(text_inserted(page_id=page_id, position=position, text=text))


def insert_math(store: EventStore, page_id: str, latex: str, mode: str) -> None:
    store.append(math_inserted(page_id=page_id, ast_path="/document", latex=latex, mode=mode))
```

Nota: `replace_document` no devuelve el detalle; eso lo hace `projections.page_detail` tras guardar.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_commands.py::test_create_page_returns_summary tests/test_commands.py::test_replace_document_returns_projection -v`
Expected: PASS

**Step 5: Refactorizar `api.py` para usar `commands`**

Reemplazar `create_page`, `update_page`, `update_page_raw`, `delete_page`, `append_text`, `insert_math` para que llamen a `commands`.

**Step 6: Run backend tests**

Run: `pytest -q`
Expected: PASS (o fallos esperados por funciones aún no migradas)

**Step 7: Commit**

```bash
git add src/lablog/commands.py tests/test_commands.py src/lablog/api.py
git commit -m "refactor(backend): extract page commands"
```

---

## Task 6: Extraer `commands.py` — comandos de celdas y ejecución robusta

**Files:**
- Modify: `src/lablog/commands.py`
- Modify: `src/lablog/api.py`
- Test: `tests/test_commands.py`

**Step 1: Añadir funciones de comando de celda**

En `src/lablog/commands.py`:

```python
def _find_cell(projection: PageProjection, cell_id: str):
    for child in projection.ast.children:
        if getattr(child, "cell_id", None) == cell_id:
            return child
    return None


def insert_cell(store: EventStore, page_id: str, cell_id: str, language: str, source: str) -> None:
    store.append(cell_inserted(page_id=page_id, cell_id=cell_id, language=language, source=source))


def update_cell(store: EventStore, page_id: str, cell_id: str, language: str | None, source: str | None) -> None:
    store.append(cell_updated(page_id=page_id, cell_id=cell_id, language=language, source=source))


def delete_cell(store: EventStore, page_id: str, cell_id: str) -> None:
    store.append(cell_deleted(page_id=page_id, cell_id=cell_id))


def move_cell(store: EventStore, page_id: str, cell_id: str, new_index: int) -> None:
    store.append(cell_moved(page_id=page_id, cell_id=cell_id, new_index=new_index))


def execute_cell(store: EventStore, engine: CodeEngine, page_id: str, cell_id: str, figure_dir: Path) -> dict[str, Any]:
    events = store.get_events(page_id)
    proj = project(page_id, events)
    cell = _find_cell(proj, cell_id)
    if cell is None:
        raise ValueError("Celda no encontrada")
    if cell.language not in CodeEngine.SUPPORTED_LANGUAGES:
        raise ValueError(f"Lenguaje no soportado: {cell.language}")

    try:
        result = engine.execute(cell.source, figure_dir=figure_dir)
    except EngineStartError as exc:
        store.append(
            execution_failed(
                page_id=page_id,
                cell_id=cell_id,
                ename="EngineStartError",
                evalue=str(exc),
                traceback=[str(exc)],
            )
        )
        return {"status": "error", "output": str(exc), "figure_paths": []}
    except Exception as exc:
        store.append(
            execution_failed(
                page_id=page_id,
                cell_id=cell_id,
                ename=type(exc).__name__,
                evalue=str(exc),
                traceback=[str(exc)],
            )
        )
        return {"status": "error", "output": str(exc), "figure_paths": []}

    # Código del usuario falló (p. ej. 1/0): modelo como execution_failed.
    if result.status == "error":
        store.append(
            execution_failed(
                page_id=page_id,
                cell_id=cell_id,
                ename="UserCodeError",
                evalue="Execution failed",
                traceback=result.text.splitlines() or ["Execution failed"],
            )
        )
        return {"status": "error", "output": result.text, "figure_paths": []}

    figure_path: str | None = None
    if result.figure_paths:
        abs_path = Path(result.figure_paths[0])
        try:
            figure_path = str(abs_path.relative_to(figure_dir.parent))
        except ValueError:
            figure_path = str(abs_path)

    store.append(
        cell_executed(
            page_id=page_id,
            cell_id=cell_id,
            output=result.text,
            figure_path=figure_path,
        )
    )
    return {"status": "ok", "output": result.text, "figure_paths": result.figure_paths}
```

**Step 2: Añadir tests de ejecución fallida (kernel y código de usuario)**

```python
from unittest.mock import MagicMock
from lablog.code_engine import EngineStartError
from lablog.commands import create_page, execute_cell, insert_cell
from lablog.event_store import EventStore


def test_execute_cell_engine_failure_becomes_event(tmp_path):
    store = EventStore(tmp_path)
    summary = create_page(store, "Test")
    insert_cell(store, summary["page_id"], "c1", "python", "1/0")
    engine = MagicMock()
    engine.execute.side_effect = EngineStartError("kernel down")
    result = execute_cell(store, engine, summary["page_id"], "c1", tmp_path / "figures")
    assert result["status"] == "error"
    events = store.get_events(summary["page_id"])
    assert events[-1].type == "execution_failed"


def test_execute_cell_user_code_error_becomes_event(tmp_path):
    store = EventStore(tmp_path)
    summary = create_page(store, "Test")
    insert_cell(store, summary["page_id"], "c1", "python", "1/0")
    engine = MagicMock()
    engine.execute.return_value = MagicMock(status="error", text="ZeroDivisionError", figure_paths=[])
    result = execute_cell(store, engine, summary["page_id"], "c1", tmp_path / "figures")
    assert result["status"] == "error"
    events = store.get_events(summary["page_id"])
    assert events[-1].type == "execution_failed"
```

**Step 3: Run test to verify it passes**

Run: `pytest tests/test_commands.py::test_execute_cell_engine_failure_becomes_event tests/test_commands.py::test_execute_cell_user_code_error_becomes_event -v`
Expected: PASS

**Step 4: Refactorizar endpoints de celdas en `api.py`**

Reemplazar `insert_cell`, `update_cell`, `delete_cell`, `move_cell`, `execute_cell` para que llamen a `commands`.

Para `execute_cell`, usar `asyncio.to_thread` y devolver la celda actualizada:

```python
import asyncio

@router.post("/pages/{page_id}/cells/{cell_id}/execute", status_code=status.HTTP_200_OK)
async def execute_cell_endpoint(page_id: str, cell_id: str) -> dict[str, Any]:
    if not _is_valid_page_id(page_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"page_id inválido: {page_id}")
    _events(page_id)
    figure_dir = settings.figures_dir / page_id
    await asyncio.to_thread(
        commands.execute_cell,
        store,
        get_engine(),
        page_id,
        cell_id,
        figure_dir,
    )
    cells = projections.list_cells(store, page_id)
    updated = next((c for c in cells if c["cell_id"] == cell_id), None)
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Celda no encontrada tras ejecutar")
    return updated
```

**Step 5: Run backend tests**

Run: `pytest -q`
Expected: PASS

**Step 6: Commit**

```bash
git add src/lablog/commands.py src/lablog/api.py tests/test_commands.py
git commit -m "refactor(backend): extract cell commands and async execution"
```

---

## Task 7: Extraer `projections.py` y eliminar duplicación de serialización

**Files:**
- Create: `src/lablog/projections.py`
- Modify: `src/lablog/commands.py`
- Modify: `src/lablog/api.py`
- Test: `tests/test_projections.py` (crear)

**Step 1: Mover queries de lectura**

Crear `src/lablog/projections.py`:

```python
from __future__ import annotations

from typing import Any

from lablog.ast_nodes import CellNode, node_to_json
from lablog.event_store import EventStore
from lablog.events import Event
from lablog.latex_ast import serialize_ast
from lablog.projector import project


def page_detail(store: EventStore, page_id: str) -> dict[str, Any]:
    events = store.get_events(page_id)
    if not events:
        raise ValueError("Página no encontrada")
    proj = project(page_id, events)
    return {
        "page_id": page_id,
        "title": proj.title,
        "latex": serialize_ast(proj.ast),
        "raw": serialize_ast(proj.ast),
        "ast": [node_to_json(c) for c in proj.ast.children],
        "version": len(events),
    }


def page_summary(store: EventStore, page_id: str) -> dict[str, Any]:
    events = store.get_events(page_id)
    proj = project(page_id, events)
    return {
        "page_id": page_id,
        "title": proj.title,
        "project_id": proj.project_id,
        "updated_at": events[-1].timestamp if events else None,
    }


def list_page_summaries(store: EventStore) -> list[dict[str, Any]]:
    summaries = []
    for pid in store.list_pages():
        events = store.get_events(pid)
        proj = project(pid, events)
        if proj.deleted:
            continue
        summaries.append({
            "page_id": pid,
            "title": proj.title,
            "project_id": proj.project_id,
            "updated_at": events[-1].timestamp if events else None,
        })
    return summaries


def list_cells(store: EventStore, page_id: str) -> list[dict[str, Any]]:
    events = store.get_events(page_id)
    proj = project(page_id, events)
    cells = []
    for child in proj.ast.children:
        if isinstance(child, CellNode):
            cells.append(node_to_json(child))
    return cells


def page_history(store: EventStore, page_id: str) -> list[dict[str, Any]]:
    events = store.get_events(page_id)
    return [
        {
            "index": i,
            "type": e.type,
            "timestamp": e.timestamp,
            "summary": _event_summary(e),
        }
        for i, e in enumerate(events)
    ]


def page_at(store: EventStore, page_id: str, event_index: int) -> dict[str, Any]:
    events = store.get_events(page_id)
    idx = max(0, min(event_index, len(events) - 1))
    proj = project(page_id, events[: idx + 1])
    return {
        "page_id": page_id,
        "title": proj.title,
        "latex": serialize_ast(proj.ast),
        "raw": serialize_ast(proj.ast),
        "ast": [node_to_json(c) for c in proj.ast.children],
        "version": idx + 1,
    }


def _event_summary(event: Event) -> str:
    payload = event.payload
    summary_len = 40
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
    return text[:summary_len]
```

**Step 2: Eliminar helpers locales de `commands.py` y `api.py`**

En `commands.py` ya no hace falta `_detail_from`. En `api.py` eliminar `_summary`, `_detail_from`, `_ast_to_json`, `_event_summary`, `_clamp_index`.

**Step 3: Añadir test de proyección**

```python
from lablog.commands import create_page, insert_cell
from lablog.event_store import EventStore
from lablog.projections import list_cells, page_detail


def test_list_cells_includes_status(tmp_path):
    store = EventStore(tmp_path)
    summary = create_page(store, "Test")
    insert_cell(store, summary["page_id"], "c1", "python", "1+1")
    cells = list_cells(store, summary["page_id"])
    assert len(cells) == 1
    assert cells[0]["status"] == "idle"


def test_page_detail_serializes_ast(tmp_path):
    store = EventStore(tmp_path)
    summary = create_page(store, "Test")
    detail = page_detail(store, summary["page_id"])
    assert detail["page_id"] == summary["page_id"]
    assert "ast" in detail
```

**Step 4: Run backend tests**

Run: `pytest -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/lablog/projections.py src/lablog/commands.py src/lablog/api.py tests/test_projections.py
git commit -m "refactor(backend): extract projections module"
```

---

## Task 8: Frontend — reflejar `status` y `output` desde el AST sin doble GET

**Files:**
- Modify: `ui/src/lib/api.ts`
- Modify: `ui/src/components/panels/cells-panel.tsx`
- Modify: `ui/src/components/lab/lab-canvas.tsx`
- Modify: `ui/src/components/panels/cells-panel.test.tsx`
- Modify: `ui/src/components/lab/lab-canvas.test.tsx`

**Step 1: Actualizar contrato de `executeCell` en `api.ts`**

```typescript
export async function executeCell(pageId: string, cellId: string): Promise<CellNode> {
  return fetchJson(`/pages/${pageId}/cells/${cellId}/execute`, { method: 'POST' })
}
```

**Step 2: Actualizar `cells-panel.tsx` para leer del AST y actualizar un nodo**

```typescript
import { useMemo } from 'react'
import type { CellNode } from '@/types'

const activeAst = useAppStore((s) => s.activeAst)
const cells = useMemo(
  () => (activeAst || []).filter((n): n is CellNode => n.type === 'cell'),
  [activeAst]
)

const runCell = async (cellId: string) => {
  if (!activePageId) return
  const updated = await executeCell(activePageId, cellId)
  setActiveAst((prev) => {
    if (!prev) return prev
    return prev.map((n) => (n.type === 'cell' && n.cell_id === cellId ? updated : n))
  })
}
```

Eliminar `refreshCells`, `useEffect` de carga y estado local `cells`.

**Step 3: Actualizar `lab-canvas.tsx` de forma similar**

Leer celdas de `activeAst`. Mantener `collapsed` como estado UI local.

**Step 4: Run frontend tests**

Run: `cd ui && npm test -- --run`
Expected: PASS (ajustar mocks según sea necesario)

**Step 5: Commit**

```bash
git add ui/src/lib/api.ts ui/src/components/panels/cells-panel.tsx ui/src/components/lab/lab-canvas.tsx ui/src/components/panels/cells-panel.test.tsx ui/src/components/lab/lab-canvas.test.tsx
git commit -m "refactor(ui): derive cell state from AST; single-trip execution"
```

---

## Task 9: Validación final

**Step 1: Run backend tests**

Run: `.venv/bin/pytest -q`
Expected: 140+ passed, coverage >= 80%

**Step 2: Run backend linter**

Run: `.venv/bin/ruff check src tests`
Expected: All checks passed

**Step 3: Run frontend build**

Run: `cd ui && npm run build`
Expected: exit 0

**Step 4: Run frontend linter**

Run: `cd ui && npm run lint`
Expected: 0 errors

**Step 5: Commit si hay cambios de lint**

```bash
git add -A
git commit -m "chore: lint and validation"
```

---

## Decisiones de arquitectura incluidas en este plan

1. **CQRS ligero**: `commands.py` escribe eventos; `projections.py` lee estado. `api.py` solo hace HTTP.
2. **Eventos de dominio para fallos**: `execution_failed` cubre fallos del kernel Y errores del código del usuario. `cell_executed` siempre significa `"ok"`.
3. **Async execution**: `execute_cell` corre en thread pool; FastAPI no se bloquea.
4. **AST como fuente de verdad de celdas**: el frontend no necesita `listCells` ni un GET extra tras ejecutar; recibe la celda actualizada en el POST.
5. **Serialización determinista**: `node_to_json` en `ast_nodes.py` es el único punto de serialización de nodos a JSON.
6. **No se añaden features**: no hay SSE, React Query ni plugin system en este Acto. Solo se sanea la arquitectura existente.

## No incluido en este Acto (reservado para Acto III)

- Server-Sent Events / WebSockets para notificaciones push.
- React Query / SWR para server state.
- Plugin system abstracto.
- Migración de todos los endpoints REST a un solo `PUT /pages/{id}` (las operaciones de celda siguen siendo endpoints específicos por ahora).
