# Findings — lablog Producción Estable

## Descubrimientos del Estado Actual

### Agent Instructions
- `AGENTS.md` presente en raíz.
- `CLAUDE.md` es symlink a `AGENTS.md`.
- No existe `/init` ni scripts adicionales de inicialización de agentes.

### Estructura Actual (resumen)
- Backend: 17 módulos Python en `src/lablog/` (~3.700 LOC sin contar UI).
- Frontend: 60+ componentes/hooks en `ui/src/`.
- `api.py`: 984 líneas — indica acoplamiento API + lógica de negocio.
- `app-store.ts`: 147 líneas — god store con UI state + datos de negocio.

### Plan Preexistente
- `lablog-production-plan.md` documenta 10 tareas y 6 bugs raíz (voz, parser, Zustand, CodeEngine, preview, XSS).
- `docs/IMPLEMENTATION_PLAN.md` es un roadmap histórico/futuro de features.

## Problemas Arquitectónicos Confirmados

### Backend
1. **`api.py` es un "god router"** (984 líneas): mezcla rutas HTTP, schemas Pydantic, lógica de exportación, serialización AST y validaciones.
2. **Sin capa de aplicación ni dominio separado**: `EventStore`, `VaultService`, `CodeEngine` son globales en `api.py`.
3. **Acoplamiento core/UI**: `config.py:ui_dist_dir()` y `api.py` sirven la UI compilada desde el backend.
4. **Duplicación LaTeX**: `latex_ast.py` y `ui/src/lib/latex-parser.ts` implementan el mismo algoritmo.
5. **`projector.py` expone mutabilidad interna**: `PageProjection.ast` es mutable.
6. **Extensibilidad limitada**: exportadores, lenguajes de celda y snippets son cadenas de `if`/frozentset hardcodeados.

### Frontend
1. **`app-store.ts` es un "god store"**: UI state + datos de negocio + callbacks del editor mezclados.
2. **Lógica de negocio en componentes**: `toolbar.tsx`, `app-shell.tsx`, `latex-preview.tsx` acoplan UI con reglas.
3. **Dos interfaces de celdas**: `cells-panel.tsx` y `lab-canvas.tsx` duplican estado/tipos.
4. **Sin Error Boundaries**: un error en KaTeX o celdas tumba la app.
5. **Tipado frágil**: `Page['ast']` usa unions poco específicas.

### Bugs Críticos
| Bug | Archivo/línea | Raíz | Severidad |
|---|---|---|---|
| Dictado de voz: bucle/double append | `toolbar.tsx:32-46` | `useEffect` depende de `listening`/`transcript`/`activeLatex`; no se resetea transcript tras insertar | Alto |
| Recargas infinitas al iniciar | `app-shell.tsx:54-73` | Efecto sin dependencias estables ni protección contra re-ejecución | Medio |
| Celdas Python: errores opacos / lenguajes no soportados | `cells-panel.tsx:58-71` / `lab-canvas.tsx:107-135` | `LANGUAGE_OPTIONS` incluye markdown/latex; lógica invertida | Alto |
| Preview aproximado reconstruye LaTeX | `latex-render.ts:222-269` | `renderDocument` junta nodos de texto y pasa por regex | Medio |

## Arquitectura Objetivo (resumen)
- Backend: Clean Architecture / DDD ligero con capas `domain/`, `application/`, `infrastructure/`, `interfaces/`, `plugins/`.
- Frontend: feature-based con stores atómicos, `shared/api-client.ts` y `features/*/store.ts`.
- Entry points: registries de plugins para exportadores, executors de celdas, voice providers, themes UI y snippet sources.

## Próximo Paso
- Redactar plan maestro en `docs/ARCHITECTURE_MASTER_PLAN.md`.
