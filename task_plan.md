> **Plan maestro APROBADO.** Ver `docs/ARCHITECTURE_MASTER_PLAN.md`.

# Ejecución — Acto I: Amputación y Sutura

> Backend devuelve AST JSON. Frontend renderiza nativamente. Un solo endpoint `PUT /pages/{id}` con debounce.

## Acto I — Tareas

### Backend

- [ ] **B1.** Extender `PageDetail` con `raw` y `version` sin romper contratos existentes.
  - Verify: `GET /pages/{id}` sigue devolviendo 200; `pytest tests/test_api.py::test_create_and_get_page -q` pasa.
- [ ] **B2.** Crear `PUT /pages/{id}` (recibe `{ "raw": string }`, parsea con `parse_latex`, emite `document_replaced`, devuelve `PageDetail`).
  - Verify: Nuevo test `test_put_page_raw_returns_ast` pasa; status 200 con `ast`, `raw`, `version`.
- [ ] **B3.** Añadir tests de validación para `PUT /pages/{id}` (page_id inválido, página no encontrada, payload vacío).
  - Verify: `pytest tests/test_api.py -q` verde.

### Frontend

- [ ] **F1.** Crear `ui/src/lib/ast-render.tsx`: switch sobre tipos de nodo (`text`, `math`, `cell`) → JSX seguro, sin `dangerouslySetInnerHTML`.
  - Verify: Renderiza texto plano, math con KaTeX, y placeholder de celda sin advertencias de seguridad.
- [ ] **F2.** Crear hook `ui/src/hooks/use-page-update.ts`: `fetch` con debounce 300ms a `PUT /pages/{id}`; expone `updateRaw(raw)`.
  - Verify: Escribir en textarea no dispara request inmediatamente; tras 300ms de inactividad llega request.
- [ ] **F3.** Reemplazar `LatexPreview` para que consuma `page.ast` y use `ast-render.tsx`.
  - Verify: Preview muestra mismo contenido que antes pero con AST del backend.
- [ ] **F4.** Reemplazar `LatexEditor` para que mantenga `raw` local, use `use-page-update.ts`, y no pierda cursor/foco.
  - Verify: Editar texto no resetea selección; guardar actualiza preview.
- [ ] **F5.** Eliminar `ui/src/lib/latex-parser.ts` y `ui/src/lib/latex-parser.test.ts`.
  - Verify: `npm run build` no falla por imports rotos; no queda parser LaTeX en frontend.
- [ ] **F6.** Eliminar `ui/src/lib/latex-render.ts` como renderizador HTML.
  - Verify: No queda `dangerouslySetInnerHTML` en renderizado de contenido.
- [ ] **F7.** Fix dictado de voz: consumir y vaciar transcript atómicamente; evitar bucles.
  - Verify: Dictar una frase la inserta una sola vez; `isListening` no queda atrapado.

### Integración

- [ ] **I1.** Actualizar `ui/src/lib/api.ts` con `updatePage(pageId, raw)` y tipos `PageState`.
  - Verify: TypeScript compila; tipos coinciden con respuesta backend.
- [ ] **I2.** Actualizar `app-store.ts` para usar `PUT /pages/{id}` en lugar de `POST .../replace` y `POST .../text`.
  - Verify: Crear página, editar, guardar, recargar funciona end-to-end.
- [ ] **I3.** Validación completa: `pytest -q`, `ruff check src tests`, `cd ui && npm run build && npm run lint`.
  - Verify: Todos los comandos terminan exitosos.

## Hecho cuando (Acto I)

- [ ] No queda parser LaTeX en frontend.
- [ ] No queda `dangerouslySetInnerHTML` en renderizado de contenido.
- [ ] `PUT /pages/{id}` devuelve AST actualizado.
- [ ] Editor usa debounce y no pierde cursor.
- [ ] Dictado de voz no buclea.
- [ ] CI verde (backend + frontend).

## Errores Encontrados

| Error | Tarea | Resolución |
|-------|-------|------------|
