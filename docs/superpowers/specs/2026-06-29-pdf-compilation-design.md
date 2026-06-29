# Diseño: Compilación PDF real con Tectonic

- **Fecha:** 2026-06-29
- **Estado:** Aprobado (pendiente review del spec escrito)
- **Alcance:** Compilación de la página actual a PDF real con Tectonic, más el
  *affordance* de "vista aproximada → compilar PDF real".
- **Fuera de alcance (ciclo aparte):** Time-travel UI, multi-archivo, BibTeX,
  numeración/refs cruzadas.

## 1. Motivación

El preview de lablog es una aproximación (KaTeX + renderer de regex para el
subconjunto común de LaTeX). No es LaTeX real: paquetes custom, TikZ,
bibliografías y tipografía precisa divergen. La exportación PDF actual usa
pandoc y serializa las celdas como entornos `python` que **no existen en
LaTeX**, por lo que el PDF de celdas no compila. Esta feature cierra la brecha
de credibilidad: un PDF compilado de verdad, idéntico a lo que produciría una
toolchain LaTeX, manteniendo el preview rápido como vista previa aproximada.

Decisiones del usuario:
- **Motor:** Tectonic, offline tras la primera vez (descarga y cachea paquetes
  la 1ª compilación; luego 100% offline).
- **Celdas en el PDF:** código + output + figura.

## 2. Decisiones de arquitectura (resumen)

| Tema | Decisión |
|---|---|
| Motor | Tectonic (XeTeX + TeXLive), binario único. |
| Ejecución | `async` con `asyncio.create_subprocess_exec` + `asyncio.wait_for`. |
| Timeout | 120 s primer run (descarga paquetes), 60 s después → `504`, proceso terminado. |
| Aislamiento | `tempfile.TemporaryDirectory` por compilación; figuras copiadas dentro; cleanup en `finally`. |
| Errores | `422 {errors:[{cell|node, line, message}], log}`, mapeando línea `.tex` → marcador de origen. |
| Concurrencia | `asyncio.Lock` por `page_id`; botón deshabilitado en el frontend mientras compila. |
| Cache | `LABLOG_DATA_DIR/pdf_cache/{page_id}/{hash}.pdf` (hash del documento serializado). |
| Trust chain | Versión de Tectonic pineada + **SHA256 hardcoded en el código** + TLS de GitHub. |
| Sandboxing | **Sin `--shell-escape`** (no ejecución de comandos desde LaTeX). |
| Visualización | Bytes → blob URL en `<iframe>` (panel/modal) + botón descargar. |

## 3. Backend

### 3.1 `src/lablog/pdf_engine.py` (módulo nuevo)

Separa **construcción del documento** (puro, testeable) de **ejecución**
(I/O, async).

#### Adquisición del binario — `tectonic_path() -> Path`
Orden de búsqueda:
1. `tectonic` en `PATH` (`shutil.which`).
2. Cache local: `LABLOG_DATA_DIR/bin/tectonic[.exe]`.
3. Descarga única desde una **release pineada** de GitHub para
   `(sistema, arquitectura)`, verificando el **SHA256 hardcoded** en una tabla
   del módulo (no leído del release). Se desempaqueta a `LABLOG_DATA_DIR/bin/`
   y se marca ejecutable.

Constantes en el módulo:
```python
TECTONIC_VERSION = "0.15.0"   # pineado
TECTONIC_SHA256 = {
    ("Darwin", "arm64"): "<sha256>",
    ("Darwin", "x86_64"): "<sha256>",
    ("Linux", "x86_64"): "<sha256>",
    ("Windows", "AMD64"): "<sha256>",
}
```
Si la plataforma no está en la tabla o falla el checksum → error claro
("instala tectonic manualmente"). Los SHA256 reales se completan al
implementar, leyéndolos de los assets de la release pineada (tarea explícita
del plan; el spec no deja el valor a medias en el código final).

#### Construcción del documento — `build_document(page) -> tuple[str, list[SourceMarker]]`
Recibe la proyección (`PageProjection`/`DocumentNode`). Devuelve el `.tex`
completo y la lista de marcadores de origen.

Preámbulo (orden estricto; `hyperref` último):
```latex
\documentclass{article}
\usepackage{geometry}
\usepackage{fontspec}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{fancyvrb}
\usepackage{hyperref}
```
- **Prosa + matemática:** se emiten verbatim vía `serialize_ast` (ya
  preservan el LaTeX original; `tabular`, `tikz`, etc. compilan nativo). No se
  usa `inputenc` (XeTeX es Unicode-nativo).
- **Celdas:** código y output en
  `\begin{Verbatim}[breaklines=true,breakanywhere=true] ... \end{Verbatim}`
  (`fancyvrb`, Unicode-safe y con wrap de líneas largas). Figura con
  `\includegraphics[width=\linewidth]{<archivo copiado al tempdir>}`.
- **Título:** escapado con el `_escape_latex` ya existente.
- **Marcadores:** antes de cada bloque se inserta un comentario
  `% lablog-src: kind=<text|math|cell> ref=<cell_id|node_index> line=1`.
  `SourceMarker` registra `(tex_line, kind, ref)`.

Nota de glifos: emojis u otros símbolos sin glifo en la fuente XeTeX por
defecto (Latin Modern) saldrán como caja vacía, no como fallo de compilación.
Aceptable y documentado.

#### Ejecución — `async def compile_pdf(page, *, tempdir) -> CompileResult`
1. `build_document` → escribe `main.tex` en `tempdir`.
2. Copia las figuras referenciadas a `tempdir`.
3. `asyncio.create_subprocess_exec(tectonic, "main.tex", "--outdir", tempdir, ...)`
   sin `--shell-escape`. (Usar la invocación clásica de Tectonic.)
4. `asyncio.wait_for(proc.communicate(), timeout)`. En `TimeoutError`: matar el
   proceso y devolver estado `timeout`.
5. Lee `main.pdf` si existe → bytes. Persiste el log a
   `LABLOG_DATA_DIR/logs/last_compile.log`.
6. `CompileResult(status="ok"|"error"|"timeout", pdf=bytes|None, errors=[...], log=str)`.

#### Parseo de errores — `parse_errors(log, markers) -> list[CompileError]`
Extrae líneas con patrón `:(\d+):` (y `! ...` de TeX). Para cada una resuelve
el `SourceMarker` con `tex_line` máximo `<=` la línea reportada →
`CompileError(cell|node, source_line, message)`. Si no hay marcador previo,
`ref=None`.

### 3.2 Cache — `pdf_cache.py` helpers o dentro de `pdf_engine`
Hash = `sha256(serialize_ast(projection) + version_preámbulo)`. Ruta
`LABLOG_DATA_DIR/pdf_cache/{page_id}/{hash}.pdf`. Si existe, se sirve sin
recompilar. Escritura atómica (tempfile + rename), como en vault.

### 3.3 Endpoints (`api.py`)

Para no mezclar I/O async (Tectonic) con el handler sync de pandoc, se usa una
**ruta dedicada** declarada **antes** de la genérica (FastAPI resuelve por orden
de registro, así la específica gana sobre `{format}`):

- `GET /pages/{page_id}/export/pdf` → **`async def`** nuevo, usa `pdf_engine`.
  Adquiere `asyncio.Lock` por página. Respuestas:
  - `200` `application/pdf` (bytes) en éxito (o cache hit).
  - `422` `{errors, log}` si la compilación falla.
  - `504` si excede el timeout.
  - `503` si no hay binario y no se pudo obtener.
- `GET /api/v1/pdf/engine-status` → `{binary_ready: bool, bundle_warmed: bool}`
  (`bundle_warmed` = existe la caché de paquetes de Tectonic). Para el UX del
  primer compile.
- El `export_page` genérico **sigue sync** y se queda con `tex` / `txt` /
  `docx` / `canva` (pandoc). Se elimina su branch `pdf` (lo sirve la ruta
  dedicada). No se mezcla subprocess bloqueante de pandoc dentro de un handler
  async.

### 3.4 Threat model (documentado)
Tectonic ejecuta XeTeX sobre contenido del usuario. LaTeX es Turing-completo,
pero se corre **sin `--shell-escape`** (sin ejecución de comandos del SO) y con
timeout duro. lablog es local, mono-usuario; **no** es un servicio
multi-tenant. El endpoint asume contenido propio del usuario; no debe exponerse
públicamente sin añadir rate limiting y aislamiento.

## 4. Frontend

### 4.1 `lib/api.ts`
- `compilePdf(pageId)`: `GET .../export/pdf`; si `200` → `Blob`; si `422` →
  parsea JSON y lanza un error tipado con `errors`; si `504`/`503` → error con
  mensaje.
- `pdfEngineStatus()`: `GET /pdf/engine-status`.

### 4.2 Preview (`latex-preview.tsx`) — affordance
En la cabecera del preview: badge **"Vista aproximada"** + botón
**"Compilar PDF"**. El botón:
- Se deshabilita mientras compila (anti doble-click).
- Si `engine-status` indica binario no listo → toast/inline "Primera vez:
  preparando el motor (~1 min)" antes de compilar.
- Éxito → muestra el PDF en un `<iframe>` (blob URL) en un panel/modal con
  botón **Descargar**.
- `422` → panel de errores: lista `Celda N, línea M: mensaje` (o
  `Documento, línea M` si `ref` es nodo de prosa).
- `504` → toast "La compilación superó el tiempo límite".

### 4.3 ExportMenu
El item "PDF" usa la misma ruta de compilación (con manejo de errores), en
lugar del pandoc actual.

## 5. Tests

- `test_pdf_engine.py`:
  - `build_document`: celdas → `Verbatim` (code + output) e `includegraphics`;
    marcadores `% lablog-src` presentes y alineados; título escapado; orden de
    paquetes con `hyperref` al final; sin `inputenc`.
  - `parse_errors`: mapea una línea `.tex` al marcador de celda correcto;
    maneja "sin marcador previo".
  - Cache: mismo documento → mismo hash/ruta; documento distinto → ruta
    distinta.
- Path real de Tectonic: `@pytest.mark.tectonic`, ejecutado solo con
  `LABLOG_RUN_TECTONIC_TESTS=1` (skip en CI normal; sin descargas en CI).

## 6. Plan de implementación (orden)

1. `pdf_engine.build_document` + `parse_errors` + tests puros (TDD).
2. Adquisición del binario (`tectonic_path`) + tabla de versión/SHA256.
3. `compile_pdf` async + tempdir + timeout + log.
4. Cache de PDF.
5. Endpoints (`export/pdf` async + `engine-status`) + `asyncio.Lock`.
6. Frontend: `api.ts`, affordance en el preview, panel de errores, ExportMenu.
7. Threat model en docs; README sección "PDF real".
8. Validación: `pytest`, `ruff`, `mypy`, `tsc`, `npm build`.

## 7. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Primer compile lento (descarga paquetes) | `engine-status` + mensaje de UX; timeout 120 s. |
| Runaway LaTeX | Timeout duro + kill → `504`. |
| Líneas de error inútiles | Marcadores `% lablog-src` + resolución al más cercano. |
| Binario comprometido | Versión pineada + SHA256 hardcoded + TLS. |
| Unicode en code/output | `fancyvrb` `Verbatim` (no `listings`). |
| Glifos faltantes (emoji) | Caja vacía, no fallo; documentado. |
| Contaminación del workspace | `TemporaryDirectory` + cleanup. |
| Doble compilación | Lock por página + botón deshabilitado. |
