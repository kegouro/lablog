# lablog · Plan de Implementación

> De cero a segundo cerebro científico, por fases.  
> **Versión actual:** `v0.1.0` (release pública inicial).

---

## Fase 0 — Fundamentos del Engine

**Objetivo**: tener un motor Python funcional con Event Store, proyección de páginas y AST LaTeX mínimo.

| # | Tarea | Estado |
|---|-------|--------|
| 0.1 | Crear estructura de proyecto Python (`pyproject.toml`, `src/lablog/...`) | ✅ |
| 0.2 | Implementar `EventStore` con persistencia JSONL | ✅ |
| 0.3 | Definir esquema de eventos base (`page_created`, `text_inserted`, etc.) | ✅ |
| 0.4 | Implementar `PageProjector` para reconstruir estado desde eventos | ✅ |
| 0.5 | Crear parser LaTeX → AST mínimo (secciones, párrafos, math, celdas) | ✅ |
| 0.6 | Serializar AST a LaTeX plano | ✅ |
| 0.7 | Tests unitarios del Event Store y proyección | ✅ |
| 0.8 | CLI básica: `lablog create-page`, `lablog append-text`, `lablog render` | ✅ |

**Entregable**: un paquete Python instalable que puede crear páginas, guardar eventos y renderizar LaTeX por consola.

---

## Fase 1 — Prototipo Voz → LaTeX

**Objetivo**: validar la killer feature con un script independiente.

| # | Tarea | Estado |
|---|-------|--------|
| 1.1 | Crear entorno virtual e instalar `faster-whisper`, `sounddevice`, `numpy` | ✅ |
| 1.2 | Script `prototypes/voice_to_latex/record.py` para grabar audio del micrófono | ✅ |
| 1.3 | Script `transcribe.py` usando `faster-whisper` (local) | ✅ |
| 1.4 | Implementar `IntentParser` que detecte jerga matemática | ✅ |
| 1.5 | Integrar Ollama (Llama 3.2) con prompt estricto para convertir a LaTeX | ✅ |
| 1.6 | Pipeline `voice_to_latex.py`: grabar → transcribir → intent → LaTeX | ✅ |
| 1.7 | Validar con frases de prueba (integral, Schrödinger, matriz, subíndices) | ✅ |
| 1.8 | Fallback a API remota (Claude/GPT) si Ollama no está disponible | ✅ |

**Entregable**: ejecutar `python voice_to_latex.py`, hablar, y ver LaTeX en consola.

---

## Fase 2 — Editor LaTeX en vivo

**Objetivo**: una UI funcional con editor y preview.

| # | Tarea | Estado |
|---|-------|--------|
| 2.1 | Elegir y configurar React + Vite + TypeScript + Tailwind v4 + shadcn/ui | ✅ |
| 2.2 | Crear layout split-pane: editor / preview | ✅ |
| 2.3 | Editor LaTeX con textarea sincronizada y guardado automático | ✅ |
| 2.4 | Renderizado con KaTeX (inline/display) | ✅ |
| 2.5 | Conectar UI con engine Python vía HTTP API | ✅ |
| 2.6 | Sincronizar AST ↔ texto del editor mediante `replace` | ✅ |
| 2.7 | Autocompletado de comandos LaTeX | 🔄 |
| 2.8 | Exportar a PDF y `.tex` | ✅ |
| 2.9 | Shell, navegación, command palette, tema y personalización | ✅ |
| 2.10 | Paneles: bóveda, snippets, símbolos favoritos | ✅ |

**Entregable**: aplicación web (y futura Tauri) donde escribes LaTeX y ves el renderizado en tiempo real.

> **Nota v0.1.0.** El autocompletado de comandos LaTeX sigue como mejora pendiente; el resto de la fase está operativo.

---

## Fase 3 — Code Engine (Jupyter)

**Objetivo**: ejecutar celdas Python dentro del documento.

| # | Tarea | Estado |
|---|-------|--------|
| 3.1 | Instalar `jupyter-client` y levantar kernel de Python | ✅ |
| 3.2 | Detectar bloques `\begin{python}...\end{python}` en el AST | ✅ |
| 3.3 | Implementar `vault://` → path absoluto | ✅ |
| 3.4 | Enviar código a Jupyter y capturar output | ✅ |
| 3.5 | Insertar output (texto/imagen) en el renderizado | ✅ |
| 3.6 | Cachear outputs y emitir evento `cell_executed` | ✅ |
| 3.7 | Manejo de errores de ejecución en la UI | ✅ |
| 3.8 | Hilo-seguridad del motor y mensajes de error legibles | ✅ |

**Entregable**: usuario escribe una celda Python, la ejecuta y ve la figura/tablas en el documento.

> **Nota v0.1.0.** El motor ahora es thread-safe, reinicia el kernel si muere y reporta errores accionables. La ejecución concurrente se serializa a una celda a la vez por seguridad del kernel de Jupyter.

---

## Fase 4 — Vault e Ingesta Mágica

**Objetivo**: bóveda de archivos con previsualización e ingesta inteligente.

| # | Tarea | Estado |
|---|-------|--------|
| 4.1 | Modelo de datos de Vault en Event Store | ✅ |
| 4.2 | Drag & drop de archivos a la bóveda | ✅ |
| 4.3 | Almacenamiento en disco con hash | ✅ |
| 4.4 | Previsualización de imágenes, PDFs, CSVs, audio, texto | ✅ |
| 4.5 | Detección de schema para CSVs | 🔄 |
| 4.6 | Sugerencias de ingesta: graficar, tabla LaTeX, estadísticas | 🔄 |
| 4.7 | Insertar código generado automáticamente en el documento | 🔄 |
| 4.8 | Slider de destrucción + time-lock de 7 días | ✅ |
| 4.9 | Log de auditoría de eliminaciones | ✅ |

**Entregable**: arrastrar un CSV genera una gráfica en el documento; eliminar un archivo requiere confirmación y time-lock.

> **Nota v0.1.0.** Vault funcional con almacenamiento, previews y time-lock. La ingesta mágica (schema + sugerencias) está parcialmente implementada y se completará en `v0.2.0`.

---

## Fase 5 — Time-Travel

**Objetivo**: historial inmutable y navegable.

| # | Tarea | Estado |
|---|-------|--------|
| 5.1 | Snapshots automáticos ante cada evento relevante | ✅ |
| 5.2 | Vista Timeline en la UI | ✅ |
| 5.3 | Diff entre dos snapshots | ✅ |
| 5.4 | Blame: ver origen de cada parte del documento | 🔄 |
| 5.5 | Restaurar página a un snapshot anterior | ✅ |

**Entregable**: usuario puede ver qué cambió y cuándo, y restaurar versiones anteriores.

> **Nota v0.1.0.** La vista timeline y el diff están disponibles; blame granular queda para una versión posterior.

---

## Fase 6 — Plugins y Colaboración

**Objetivo**: sistema extensible y sincronización.

| # | Tarea | Estado |
|---|-------|--------|
| 6.1 | Definir API de plugins | 🔄 |
| 6.2 | Cargar plugins dinámicamente | 🔄 |
| 6.3 | Plugin de física: snippets y comandos de voz comunes | 🔄 |
| 6.4 | Plugin de unidades y dimensiones | 🔄 |
| 6.5 | Sincronización encriptada opcional | 🔄 |
| 6.6 | Colaboración P2P por intercambio de eventos | 🔄 |

**Entregable**: ecosistema de plugins funcional y sincronización entre dispositivos.

> **Nota v0.1.0.** Esta fase se mantiene en roadmap a largo plazo; no bloquea la release inicial.

---

## Checklist global

- [x] Engine Python funcional con Event Sourcing.
- [x] Prototipo Voz → LaTeX validado.
- [x] UI de editor LaTeX en vivo.
- [x] Celdas Python ejecutables vía Jupyter.
- [x] Vault con ingesta y eliminación segura.
- [x] Time-Travel con Timeline y diff.
- [x] Exportación a PDF / `.tex` / HTML.
- [x] Documentación para desarrolladores.
- [x] CI verde, cobertura ≥80% y release automatizado a PyPI.
- [ ] Sistema de plugins (post-v0.1.0).
- [ ] Colaboración P2P (post-v0.1.0).

---

## Próximo paso inmediato

**v0.1.0**: publicar en PyPI, validar instalación limpia y continuar con ingesta mágica de Vault y autocompletado LaTeX en `v0.2.0`.
