# Time-Travel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Ver la página en cualquier punto de su historia (slider sobre el event log) y restaurar versiones de forma append-only.

**Architecture:** Backend expone 3 rutas que reutilizan `project()` sobre prefijos del log. Frontend agrega un overlay de historia sobre el preview con slider + lista + preview read-only + restaurar. El renderer `renderDocument` se mueve a `lib/latex-render.ts` para reutilizarlo sin ciclos de import.

**Tech stack:** FastAPI (sync, mismo patrón), React 19 + slider shadcn existente.

## Global Constraints

- Ruff `E,F,I,N,W,UP,B,C4,SIM`, línea 100; mypy strict.
- Restore es append-only: JAMÁS reescribir/borrar eventos.
- Clamp de índices `max(0, min(idx, len-1))` en `at` y `restore`.
- Restore sobre página `deleted` → `409`.
- Commits conventional + trailer `Co-Authored-By: Kimi Code <noreply@example.com>` (hook; usar `git commit -F`).
- Gate backend: `ruff check src tests && mypy -p lablog && pytest -q`.
- Gate frontend: `cd ui && npx tsc --noEmit && npm run build`.

---

### Task 1: Backend — history / at / restore (TDD)

**Files:**
- Modify: `src/lablog/api.py`
- Test: `tests/test_api.py` (append; usar el `client` module-level existente)

**Interfaces (Produces):**
- `GET /api/v1/pages/{page_id}/history` → `list[HistoryEntry]` con `{index:int, type:str, timestamp:datetime, summary:str}`
- `GET /api/v1/pages/{page_id}/at/{event_index}` → `PageDetail`
- `POST /api/v1/pages/{page_id}/restore/{event_index}` → `PageDetail` (409 si deleted)

- [ ] **Step 1: tests que fallan** (append a `tests/test_api.py`):

```python
def test_history_shape_and_time_travel() -> None:
    pid = client.post("/api/v1/pages", json={"title": "TT"}).json()["page_id"]
    client.post(f"/api/v1/pages/{pid}/replace", json={"latex": "A"})
    client.post(f"/api/v1/pages/{pid}/replace", json={"latex": "A B"})

    history = client.get(f"/api/v1/pages/{pid}/history").json()
    assert len(history) == 3
    assert {"index", "type", "timestamp", "summary"} <= set(history[0])
    assert history[0]["type"] == "page_created"

    assert client.get(f"/api/v1/pages/{pid}/at/1").json()["latex"] == "A"
    # clamp documentado: índice alto → estado final; negativo → primer evento
    assert client.get(f"/api/v1/pages/{pid}/at/999").json()["latex"] == "A B"
    assert client.get(f"/api/v1/pages/{pid}/at/-5").status_code == 200


def test_restore_appends_and_matches_past_state() -> None:
    pid = client.post("/api/v1/pages", json={"title": "TT2"}).json()["page_id"]
    client.post(f"/api/v1/pages/{pid}/replace", json={"latex": "v1"})
    client.post(f"/api/v1/pages/{pid}/replace", json={"latex": "v2"})
    before = len(client.get(f"/api/v1/pages/{pid}/events").json())

    restored = client.post(f"/api/v1/pages/{pid}/restore/1")
    assert restored.status_code == 200
    assert restored.json()["latex"] == "v1"
    assert len(client.get(f"/api/v1/pages/{pid}/events").json()) == before + 1
    # la historia previa sigue intacta (append-only)
    assert client.get(f"/api/v1/pages/{pid}/at/2").json()["latex"] == "v2"


def test_restore_deleted_page_is_conflict() -> None:
    pid = client.post("/api/v1/pages", json={"title": "TT3"}).json()["page_id"]
    client.delete(f"/api/v1/pages/{pid}")
    assert client.post(f"/api/v1/pages/{pid}/restore/0").status_code == 409
```

- [ ] **Step 2: correr → FAIL.** `pytest tests/test_api.py -q`

- [ ] **Step 3: implementar en `api.py`.** Colocar junto a `get_events` (después de la ruta `/pages/{page_id}/events`). `CellNode`, `document_replaced`, `cell_executed`, `project`, `serialize_ast` ya están importados. Añadir modelo cerca de `PageDetail`:

```python
class HistoryEntry(BaseModel):
    index: int
    type: str
    timestamp: datetime
    summary: str
```

```python
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
        ast=_ast_to_json(proj.ast),
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
```

Nota: el test de "before + 1" usa páginas sin celdas con output, así que el conteo
es exacto con un solo `document_replaced`.

- [ ] **Step 4: correr → PASS.** `pytest tests/test_api.py -q`
- [ ] **Step 5: gate + commit.**

```bash
ruff check src tests && mypy -p lablog && pytest -q
git add src/lablog/api.py tests/test_api.py
git commit -m "feat(history): time-travel endpoints (history, at, restore)"
```

---

### Task 2: Frontend — api, flushSave, overlay de historia

**Files:**
- Modify: `ui/src/lib/api.ts`, `ui/src/lib/latex-render.ts`, `ui/src/stores/app-store.ts`, `ui/src/components/editor/latex-editor.tsx`, `ui/src/components/preview/latex-preview.tsx`
- Create: `ui/src/components/history/time-travel.tsx`

**Interfaces:**
- Consumes: rutas de Task 1.
- Produces: `getHistory/getPageAt/restoreVersion` en api.ts; `renderDocument` exportado desde `lib/latex-render.ts`; `flushSave` en el store; `<TimeTravelOverlay pageId onClose />`.

- [ ] **Step 1: api.ts** (append; mapear igual que `getPage`):

```ts
export interface HistoryEvent {
  index: number
  type: string
  timestamp: string
  summary: string
}

interface PageDetailWire {
  page_id: string
  title: string
  latex: string
  ast: Page['ast']
}

function detailToPage(d: PageDetailWire): Page {
  return {
    id: d.page_id,
    title: d.title,
    project_id: null,
    latex: d.latex,
    ast: d.ast,
    updated_at: new Date().toISOString(),
  }
}

export async function getHistory(pageId: string): Promise<HistoryEvent[]> {
  return fetchJson(`/pages/${pageId}/history`)
}

export async function getPageAt(pageId: string, index: number): Promise<Page> {
  return detailToPage(await fetchJson<PageDetailWire>(`/pages/${pageId}/at/${index}`))
}

export async function restoreVersion(pageId: string, index: number): Promise<Page> {
  return detailToPage(
    await fetchJson<PageDetailWire>(`/pages/${pageId}/restore/${index}`, { method: 'POST' }),
  )
}
```

- [ ] **Step 2: mover `renderDocument` a `lib/latex-render.ts`.** Cortar de
`latex-preview.tsx` las funciones `escapeHtml` (la local), `renderCell` y
`renderDocument` y pegarlas EXPORTADAS en `latex-render.ts` (que ya tiene su
propio `escapeHtml` — fusionar: conservar uno). `renderDocument(ast, pageId, values)`
mantiene firma. `latex-preview.tsx` la importa desde `@/lib/latex-render`.
Importar `type { CellNode, Page }` en latex-render.ts (`import type`).

- [ ] **Step 3: store `flushSave`** (mismo patrón que `insertAtCursor`):
agregar a la interfaz `flushSave: (() => Promise<void>) | null`, al estado
inicial `flushSave: null`, y setter `setFlushSave: (fn) => set({ flushSave: fn })`
(+ firma en la interfaz de acciones).

- [ ] **Step 4: editor — save cancelable + registro de flush.** En
`latex-editor.tsx`, reemplazar `debouncedSave` (y borrar el helper `debounce`
local si queda sin uso) por refs:

```ts
const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

const scheduleSave = useCallback(
  (latex: string) => {
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current)
    saveTimerRef.current = setTimeout(() => {
      saveTimerRef.current = null
      void save(latex)
    }, 600)
  },
  [save],
)

const flushSave = useCallback(async () => {
  if (saveTimerRef.current) {
    clearTimeout(saveTimerRef.current)
    saveTimerRef.current = null
    await save(valueRef.current)
  }
}, [save])

useEffect(() => {
  setFlushSave(flushSave)
  return () => setFlushSave(null)
}, [flushSave, setFlushSave])
```

`applyValue` llama `scheduleSave(value)` donde llamaba `debouncedSave(value)`.
Traer `setFlushSave` del store junto a `setInsertAtCursor`.

- [ ] **Step 5: componente `time-travel.tsx`:**

```tsx
import { Clock, RotateCcw, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Slider } from '@/components/ui/slider'
import { getHistory, getPageAt, restoreVersion, type HistoryEvent } from '@/lib/api'
import { renderDocument } from '@/lib/latex-render'
import { useAppStore } from '@/stores/app-store'
import type { Page } from '@/types'

interface TimeTravelOverlayProps {
  pageId: string
  onClose: () => void
}

export function TimeTravelOverlay({ pageId, onClose }: TimeTravelOverlayProps) {
  const { parameterValues, setActiveLatex, setActiveAst, flushSave } = useAppStore()
  const [history, setHistory] = useState<HistoryEvent[]>([])
  const [index, setIndex] = useState(0)
  const [snapshot, setSnapshot] = useState<Page | null>(null)
  const [restoring, setRestoring] = useState(false)
  const pendingIndexRef = useRef(0)
  const scrubTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    getHistory(pageId)
      .then((h) => {
        setHistory(h)
        const last = Math.max(0, h.length - 1)
        setIndex(last)
        pendingIndexRef.current = last
        return getPageAt(pageId, last)
      })
      .then(setSnapshot)
      .catch(() => toast.error('No se pudo cargar la historia'))
  }, [pageId])

  const scrub = (k: number) => {
    setIndex(k)
    if (scrubTimerRef.current) clearTimeout(scrubTimerRef.current)
    scrubTimerRef.current = setTimeout(async () => {
      pendingIndexRef.current = k
      try {
        const page = await getPageAt(pageId, k)
        if (pendingIndexRef.current === k) setSnapshot(page)
      } catch {
        toast.error('No se pudo cargar esa versión')
      }
    }, 200)
  }

  const handleRestore = async () => {
    setRestoring(true)
    try {
      if (flushSave) await flushSave()
      const page = await restoreVersion(pageId, index)
      setActiveLatex(page.latex)
      setActiveAst(page.ast)
      toast.success(`Versión del evento ${index} restaurada`)
      onClose()
    } catch {
      toast.error('No se pudo restaurar')
    } finally {
      setRestoring(false)
    }
  }

  const selected = history[index]
  const html = snapshot ? renderDocument(snapshot.ast, pageId, parameterValues) : ''

  return (
    <div className="absolute inset-0 z-40 flex flex-col rounded-lg border bg-card shadow-lg">
      <div className="flex items-center justify-between border-b px-3 py-1.5">
        <span className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
          <Clock className="size-3.5" /> Historia
        </span>
        <Button variant="ghost" size="icon" className="size-6" onClick={onClose} title="Cerrar">
          <X className="size-3.5" />
        </Button>
      </div>

      <div className="flex min-h-0 flex-1">
        <ScrollArea className="w-56 shrink-0 border-r">
          <ul className="p-1.5 text-xs">
            {history.map((e) => (
              <li key={e.index}>
                <button
                  type="button"
                  onClick={() => scrub(e.index)}
                  className={`w-full rounded px-2 py-1 text-left transition-colors ${
                    e.index === index ? 'bg-primary/15 text-primary' : 'hover:bg-muted'
                  }`}
                >
                  <span className="font-mono">{e.index}</span> · {e.type.replace(/_/g, ' ')}
                  {e.summary && (
                    <span className="block truncate text-muted-foreground">{e.summary}</span>
                  )}
                </button>
              </li>
            ))}
          </ul>
        </ScrollArea>
        <div
          className="min-w-0 flex-1 overflow-auto p-4 text-sm"
          dangerouslySetInnerHTML={{ __html: html }}
        />
      </div>

      <div className="flex items-center gap-3 border-t px-3 py-2">
        <Slider
          value={[index]}
          min={0}
          max={Math.max(0, history.length - 1)}
          step={1}
          onValueChange={([v]) => scrub(v)}
          className="flex-1"
        />
        <span className="w-40 shrink-0 text-right text-[10px] tabular-nums text-muted-foreground">
          {history.length > 0 ? `evento ${index + 1}/${history.length}` : '—'}
          {selected && ` · ${new Date(selected.timestamp).toLocaleString()}`}
        </span>
        <Button size="sm" className="h-7 gap-1.5 text-xs" disabled={restoring} onClick={handleRestore}>
          <RotateCcw className="size-3.5" />
          Restaurar
        </Button>
      </div>
    </div>
  )
}
```

- [ ] **Step 6: botón en el preview.** En `latex-preview.tsx`: estado
`historyOpen`; botón junto a "Compilar PDF" (variant ghost, icono `Clock`,
texto "Historia", disabled sin `activePageId`); al abrir: `setPdfUrl(null)`
(cerrar visor PDF) y `setHistoryOpen(true)`. Dentro del contenedor `relative`,
render `{historyOpen && activePageId && (<TimeTravelOverlay pageId={activePageId} onClose={() => setHistoryOpen(false)} />)}`.

- [ ] **Step 7: gate + commit.**

```bash
cd ui && npx tsc --noEmit && npm run build
git add ui/src && git commit -m "feat(history): time-travel overlay with scrub and append-only restore"
```

---

### Task 3: Validación final + docs (controller)

- [ ] Suite completa backend+frontend; verificación visual (scrub + restore reales); CHANGELOG + README roadmap; merge a main + push.

## Self-review

- Spec cubierto: 3 rutas+clamp+409 (T1), cell_executed en restore (T1), flushSave (T2 S3-4), out-of-order pendingIndexRef (T2 S5), z-40 + cierre de PDF (T2 S6), params actuales documentado (spec). Tipos consistentes entre tasks (`HistoryEvent`, `PageDetailWire`, firma `renderDocument(ast, pageId, values)`).
