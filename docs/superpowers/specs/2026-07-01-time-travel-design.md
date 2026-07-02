# Diseño: Máquina del tiempo (time-travel sobre el event log)

- **Fecha:** 2026-07-01
- **Estado:** Borrador (pendiente panel adversarial + implementación)
- **Alcance:** Ver la página en cualquier punto de su historia y restaurar versiones,
  sin destruir nada.
- **Fuera de alcance (ciclos futuros):** diff visual entre versiones, branching de
  historias, time-travel de la bóveda.

## 1. Motivación

lablog ya guarda **cada evento** de cada página en un log append-only (JSONL) y
reconstruye el estado con `project(page_id, events)` — una función pura. Eso
significa que "ver la página como estaba en el evento N" es literalmente
`project(events[:N+1])`: la feature ya existe a nivel de datos y nadie la expone.

Para una bitácora científica esto es un diferenciador real: auditoría y
reproducibilidad ("cómo se veía el experimento antes de cambiar el parámetro"),
deshacer histórico más allá de la sesión, y confianza total (restaurar nunca
borra: se registra como un evento más).

## 2. Backend (`src/lablog/api.py` — sin módulos nuevos)

Tres rutas, todas reutilizando `EventStore.get_events` + `project` + `serialize_ast`:

### `GET /pages/{page_id}/history`
Lista resumida de eventos (payload chico, no el payload completo del evento):

```json
[
  {"index": 0, "type": "page_created", "timestamp": "...", "summary": "Experimento"},
  {"index": 5, "type": "document_replaced", "timestamp": "...", "summary": "1024 chars"}
]
```

`summary` por tipo (helper `_event_summary(e) -> str`):
- `page_created` / `page_metadata_updated` → título si viene en payload.
- `text_inserted` → primeros 40 chars del texto.
- `document_replaced` → `f"{len(latex)} chars"`.
- `math_inserted` → primeros 40 chars del latex.
- `cell_*` → cell_id.
- resto → `""`.

### `GET /pages/{page_id}/at/{event_index}`
Proyección parcial: `project(page_id, events[:event_index+1])` → mismo shape que
`PageDetail` (`title`, `latex`, `ast`). Clampa `event_index` a `[0, len-1]`.
Solo lectura; no muta nada.

### `POST /pages/{page_id}/restore/{event_index}`
Restauración **no destructiva**: serializa el AST en ese índice y lo agrega como
un `document_replaced` nuevo al final del log. Como `serialize_ast` no persiste
`output`/`figure_path` de las celdas (hallazgo del panel), tras el
`document_replaced` se appendea un **`cell_executed` por cada celda que tenía
output o figura en ese índice** — así los resultados de ejecución sobreviven el
round-trip usando solo eventos ya existentes. La historia completa se preserva;
restaurar son eventos más (auditable). Devuelve el `PageDetail` resultante.

Guard: si la proyección completa tiene `deleted=True`, `409 Conflict`
("página eliminada") — evita el estado inconsistente contenido-nuevo/página-oculta.

Notas:
- Índices: **clamp explícito** `max(0, min(idx, len(events)-1))` en `at` y
  `restore` (un `-1` sin clamp produciría documento vacío silencioso).
- Reutiliza `_events(page_id)` (404 si no existe) y validación de `page_id` ya
  existente en EventStore (anti-traversal).
- Proyectar cientos de eventos es barato (folding puro en memoria); no se agrega
  cache. // ponytail: si una página llega a >10k eventos, snapshot cada 1k.

## 3. Frontend

### Nuevo componente: `ui/src/components/history/time-travel.tsx`
Overlay sobre el preview (mismo patrón que el visor PDF):

- **Apertura:** botón "Historia" (icono Clock) en la cabecera del preview, junto a
  "Compilar PDF". Deshabilitado sin página activa.
- **Contenido:**
  - Slider (`@/components/ui/slider`, ya existe) de `0..N-1` eventos + contador
    "evento K de N" + timestamp del evento seleccionado.
  - Lista compacta de eventos (tipo + summary + hora), clicable para saltar.
  - Vista previa **read-only** del documento en ese punto: reutiliza
    `renderLatexToHtml`/`renderDocument` del preview (extraer `renderDocument` a
    export nombrado en `latex-preview.tsx` para reutilizarlo).
  - Botón **"Restaurar esta versión"** → `POST /restore/{k}` → recarga la página
    activa (getPage + setActiveLatex/setActiveAst) → cierra overlay → toast.
- **Scrub:** al mover el slider, `GET /at/{k}` con debounce 200 ms; render local.

### `ui/src/lib/api.ts`
- `getHistory(pageId): Promise<HistoryEvent[]>`
- `getPageAt(pageId, index): Promise<Page>` (mapea igual que `getPage`)
- `restoreVersion(pageId, index): Promise<Page>`

## 4. Casos borde

- Historia con 1 evento (recién creada): slider fijo en 0, restaurar = no-op válido.
- Índice fuera de rango: backend clampa (no 500).
- Página con celdas: la proyección parcial incluye celdas con su output de ese
  momento; el preview read-only las muestra sin botones de ejecución.
- Scrub rápido: debounce + descartar respuestas fuera de orden (guardar índice
  pedido y comparar al resolver).
- **Race autosave↔restore (hallazgo del panel):** el autosave debounced (600 ms)
  podría dispararse DESPUÉS del restore y pisarlo con texto viejo. Fix: el editor
  registra `flushSave` en el store (mismo patrón que `insertAtCursor`); el flujo
  de restore hace `await flushSave()` antes del POST. Nada se pierde: el texto
  pendiente queda como evento previo al restore.
- Tras restaurar, el editor NO se recarga vía `useEffect[activePageId]` (el id no
  cambia): el panel setea `setActiveLatex/setActiveAst` con la respuesta —
  `Textarea` es controlado y el baseline de undo ya se resincroniza.
- Overlays: historia usa `z-40` (PDF usa `z-30`) y al abrirse cierra el visor PDF.
- Parámetros `{{...}}`: el preview histórico usa los valores ACTUALES del panel de
  parámetros (los params son estado de UI, no eventos). Documentado, no bug.

## 5. Tests (`tests/test_api.py` — mismos patrones/fixtures)

- `history` devuelve N eventos con shape `{index,type,timestamp,summary}`.
- `at/{k}` reproduce el estado intermedio (texto A en k=1, texto A+B al final).
- `restore/{k}` appendea evento (len(events) crece) y el latex resultante coincide
  con el de `at/{k}`.
- Índice fuera de rango en `at` → 200 con clamp (documentado).

## 6. Seguridad / rendimiento

- Solo lectura salvo `restore`, que es append-only (nada se sobrescribe/borra).
- Sin dependencias nuevas. Sin cambios de esquema de eventos.
- Payload de `history` acotado por summaries (≤40 chars).
