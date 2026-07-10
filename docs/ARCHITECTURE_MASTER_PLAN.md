> **Plan aprobado.** Ajustes finales aplicados: backend devuelve AST JSON, frontend renderiza nativamente, un solo endpoint con debounce.

# Plan Maestro — lablog v0.1.0: Producción Estable

> **Objetivo:** convertir `lablog` en un producto estable, sin añadir features, con una sola fuente de verdad: **el backend posee el AST y la historia; el frontend es un espejo seguro y eficiente.**
>
> **Backend devuelve AST JSON. Frontend renderiza el AST nativamente con React. Cero HTML crudo.**

---

## 1. Diagnóstico honesto

`lablog` tiene un núcleo de event sourcing sólido, pero la app cojea porque **el frontend y el backend creen ambos que son dueños del documento**. Eso genera duplicidad, estados contradictorios y bugs que no se matan con parches.

### Bugs raíz (no síntomas)

| # | Bug | Raíz real |
|---|---|---|
| B1 | Dictado de voz buclea | El frontend manipula `activeLatex` directamente y el efecto no consume/vacía el transcript en el mismo ciclo. |
| B2 | Recargas infinitas | El frontend no confía en el backend; hace fetching manual con un god store inestable. |
| B3 | Parser de celdas divergente | **Hay dos parsers del mismo lenguaje.** El frontend no debería parsear LaTeX. |
| B4 | Celdas Python opacas/inseguras | `CodeEngine` es un singleton sin ciclo de vida claro; la UI no recibe eventos de ejecución, inventa su propio estado. |
| B5 | Preview pierde formato | El frontend reconstruye LaTeX desde el AST porque no recibe un AST renderizable directamente. |
| B6 | XSS en MarkdownPreview | El frontend inyecta HTML crudo en lugar de renderizar una estructura tipada con React. |

### Problemas arquitectónicos graves

1. **Dualidad del parser**: `latex_ast.py` y `ui/src/lib/latex-parser.ts` modelan el mismo dato. Eso es inestable por definición.
2. **God store + lógica de negocio en UI**: `app-store.ts` guarda páginas, celdas, vault, snippets, UI shell y callbacks del editor. El frontend cree que es un backend.
3. **`api.py` monolítico**: 984 líneas mezclando HTTP, Pydantic, exportación, serialización AST y voz.
4. **CodeEngine sin contrato**: no emite eventos de dominio; la UI hace polling/refresh manual.
5. **Sobre-ingeniería en el plan anterior**: se proponían capas de aplicación, registries de plugins y división del store en 7 tiendas sin necesidad real.

---

## 2. Tesis central (la identidad de lablog)

> **El AST es el Rey y vive en el Backend. El frontend es una terminal tonta, segura y reactiva.**

- El usuario escribe texto crudo en el editor.
- Tras un debounce, el frontend envía el texto crudo al backend.
- El backend parsea, guarda el evento y **devuelve el AST JSON**.
- El frontend renderiza el AST nativamente con componentes React (`<ASTRenderer node={astNode} />`).
- Cuando una celda se ejecuta, el backend emite un evento; el frontend lo recibe y actualiza esa celda.

Si aplicamos esto, **B3, B5 y B6 desaparecen por diseño**, no por tests de regresión.

---

## 3. Arquitectura objetivo

### 3.1 Backend — headless, con eventos

```
src/lablog/
├── domain/               # Sin dependencias externas
│   ├── events.py         # Eventos de dominio inmutables
│   ├── ast_nodes.py      # Nodos del AST
│   ├── page.py           # Agregado Page
│   └── errors.py         # Excepciones de dominio
├── commands/             # Escrituras (CQRS ligero)
│   ├── create_page.py
│   ├── update_page.py    # texto crudo -> AST + evento
│   ├── execute_cell.py
│   └── attach_file.py
├── queries/              # Lecturas/proyecciones
│   ├── get_page.py
│   ├── list_pages.py
│   └── list_cells.py
├── interfaces/
│   ├── api/
│   │   ├── routes/       # Un archivo por recurso
│   │   ├── schemas.py    # Pydantic request/response
│   │   └── dependencies.py
│   ├── cli.py
│   └── sse.py            # Server-Sent Events: /events
├── infrastructure/
│   ├── persistence/
│   │   └── event_store.py
│   ├── engines/
│   │   ├── code_engine.py
│   │   └── pdf_engine.py
│   ├── files/
│   │   └── vault_storage.py
│   └── web/
│       └── static.py     # Sirve ui/dist; routes no lo conocen
└── config.py
```

**Reglas duras:**
- `domain/` no importa FastAPI, Jupyter, filesystem ni HTTP.
- `commands/` y `queries/` son funciones puras o orquestan infraestructura. **No son servicios vacíos.** Si un comando solo reenvía a `event_store`, no existe; se usa `event_store` directamente desde la ruta.
- `interfaces/api/routes/` solo hace validación HTTP y llama commands/queries.
- `interfaces/sse.py` empuja eventos de dominio al frontend.
- **El backend nunca devuelve HTML para renderizado de UI.** Solo AST JSON.

### 3.2 Frontend — espejo del backend

```
ui/src/
├── server-state/         # Todo lo que viene del backend
│   ├── api-client.ts     # fetch + tipos + errores
│   ├── queries.ts        # React Query / SWR hooks
│   ├── mutations.ts      # write hooks
│   └── sse.ts            # escucha de eventos del backend
├── ui-state/             # Solo estado local de la interfaz
│   └── shell-store.ts    # paneles, tema, modo escucha
├── components/
│   ├── shell/            # toolbar, sidebar, app-shell
│   ├── editor/
│   ├── preview/
│   ├── lab/
│   └── panels/
├── lib/
│   ├── ast-render.tsx    # AST JSON -> JSX seguro
│   └── utils.ts
└── types/
    └── domain.ts         # Tipos espejo de los schemas Pydantic
```

**Reglas duras:**
- **No hay parser LaTeX en el frontend.** Se borra `ui/src/lib/latex-parser.ts`.
- **No hay `dangerouslySetInnerHTML`** en renderizado de contenido.
- **No hay estado de páginas/celdas/vault en Zustand.** Van a React Query / SWR.
- Zustand solo guarda UI shell.
- `lib/ast-render.tsx` hace `switch` sobre `node.type` y devuelve componentes React (`<h1>`, `<KaTeX>`, `<PythonCell>`).

---

## 4. Contratos clave

### 4.1 Actualizar página (único viaje)

```
PUT /pages/{id}
Body: { "raw": "\\begin{python}...\\end{python}" }
Response: { "page": { "id": "...", "ast": [...], "version": 1 } }
```

El frontend:
1. Mantiene `raw` localmente en el `textarea`.
2. Envía al backend con **debounce de 300ms** (o en blur/ctrl+s).
3. Recibe `ast` y actualiza el Server State.
4. `<ASTRenderer />` renderiza el AST nativamente.

### 4.2 Obtener página

```
GET /pages/{id}
Response: { "page": { "id": "...", "raw": "...", "ast": [...], "version": 1 } }
```

### 4.3 Eventos SSE

```
GET /events?stream=page:{id}
Event: cell_execution_completed
Data: { "cell_id": "...", "outputs": [...] }
```

### 4.4 AST Renderer

```typescript
function ASTRenderer({ node }: { node: AstNode }) {
  switch (node.type) {
    case 'heading': return <h1>{node.children.map(ASTRenderer)}</h1>;
    case 'math': return <KaTeX math={node.value} />;
    case 'python_cell': return <PythonCell node={node} />;
    case 'paragraph': return <p>{node.children.map(ASTRenderer)}</p>;
    // ...
  }
}
```

---

## 5. Hoja de ruta: 4 actos

### Acto I — Amputación y Sutura (días 1-3)

Objetivo: matar la duplicidad y los bugs que nacieron de ella.

| # | Tarea | Resultado |
|---|---|---|
| I.1 | **Eliminar `ui/src/lib/latex-parser.ts` y su test** | El frontend no parsea LaTeX. |
| I.2 | **Backend: `PUT /pages/{id}`** | Recibe `raw`, parsea, guarda evento, devuelve `page` con `ast`. |
| I.3 | **Frontend: `lib/ast-render.tsx`** | Renderiza AST JSON a JSX seguro. Cero HTML crudo. |
| I.4 | **Editor con debounce** | Textarea mantiene `raw` local; envío con 300ms de debounce. |
| I.5 | **Fix dictado de voz** | `useSpeech` consume y vacía `transcript` en el mismo ciclo; selector atómico. |

### Acto II — Backend Headless (días 4-7)

Objetivo: el backend se convierte en una máquina de eventos limpia.

| # | Tarea | Resultado |
|---|---|---|
| II.1 | **Dividir `api.py` en routes + commands + queries** | Rutas finas; comandos y consultas explícitos. |
| II.2 | **`CodeEngine` con ciclo de vida propio** | Lock de ejecución, health check, reinicio automático. |
| II.3 | **Eventos de dominio para celdas** | `CellExecutionStarted`, `CellExecutionCompleted`, `CellExecutionFailed`. |
| II.4 | **Endpoint SSE `/events`** | Frontend recibe eventos sin polling. |
| II.5 | **Manejo de errores accionable** | `ExecutionFailed` incluye traceback legible; UI lo muestra tal cual. |

### Acto III — UI Refrescante (días 8-12)

Objetivo: el frontend deja de fingir que es un backend.

| # | Tarea | Resultado |
|---|---|---|
| III.1 | **Añadir React Query (o SWR)** | Preguntar/confirmar dependencia. |
| III.2 | **Migrar páginas/celdas/vault a server-state** | Desaparecen del Zustand global. |
| III.3 | **Crear `ui-state/shell-store.ts`** | Solo paneles, tema, modo escucha. |
| III.4 | **Unificar celdas con un solo hook** | `cells-panel` y `lab-canvas` consumen la misma query + SSE. |
| III.5 | **Error Boundaries** | Aíslan KaTeX, celdas y preview. |

### Acto IV — Release Estable (días 13-15)

Objetivo: producto publicable sin fantasías de extensibilidad.

| # | Tarea | Resultado |
|---|---|---|
| IV.1 | **Tests de regresión** | Voz, parser único, render AST, ejecución de celdas, XSS. |
| IV.2 | **CI verde** | Backend + frontend; pre-commit saneado. |
| IV.3 | **PyPI release** | Wheel/sdist, workflow de release, smoke test. |
| IV.4 | **README actualizado** | Refleja arquitectura y dependencias. |

**No hay Fase de Plugins.** Cuando existan 3 exporters o 2 lenguajes de celda, se diseña el plugin system. Hasta entonces, un `if format == 'pdf'` es perfectamente correcto.

---

## 6. Decisiones duras (anti-over-engineering)

| No hacer | Hacer en su lugar |
|---|---|
| Crear `application/page_service.py`, `cell_service.py`, etc. | Commands/queries directos; solo extraer si transforman datos o aplican reglas reales. |
| Registries de plugins abstractos | `if` simple hasta que haya 3 implementaciones. |
| Dividir Zustand en 7 stores | Un solo `shell-store.ts` para UI state; todo lo demás en React Query/SWR. |
| Backend devuelva HTML para la UI | Backend devuelve AST JSON; frontend renderiza nativamente. |
| Migrar componente por componente | Construir la nueva arquitectura en paralelo y cortar de una vez. |

---

## 7. Criterios de done

- [ ] No queda `ui/src/lib/latex-parser.ts`.
- [ ] No queda `dangerouslySetInnerHTML` en renderizado de contenido.
- [ ] `app-store.ts` ya no contiene páginas, celdas, vault ni snippets.
- [ ] `api.py` tiene <200 líneas.
- [ ] Existe endpoint SSE `/events` y el frontend lo consume.
- [ ] CodeEngine emite eventos de dominio y maneja su propio ciclo de vida.
- [ ] CI verde, cobertura backend ≥80%, tests frontend de voz/render/celdas pasan.
- [ ] Release `v0.1.0` publicable en PyPI.

---

## 8. Riesgos

| Riesgo | Mitigación |
|---|---|
| Reescribir el renderizado del frontend rompe la UI | Mantener el editor como textarea; solo cambia cómo se obtiene/renderiza el AST. |
| SSE añade complejidad | Es local/single-user; fallback a polling simple si SSE falla. |
| React Query es una dependencia nueva | Se propone; se confirma antes de instalar. |
| Cambiar CodeEngine afecta todos los tests de celdas | Refactorizar primero con tests de dominio, luego conectar HTTP. |
| Debounce de 300ms en editor puede sentirse lento | Ajustar a 150-300ms; renderizar preview inmediatamente con estado optimista del texto local. |

---

## 9. Próximo paso inmediato

**Ejecutar Acto I:**
1. Eliminar `ui/src/lib/latex-parser.ts`.
2. Crear `PUT /pages/{id}` en backend.
3. Crear `lib/ast-render.tsx` en frontend.
4. Implementar editor con debounce.
5. Fix dictado de voz.

**No se toca Acto II, III ni IV hasta que Acto I esté completo y verificado.**
