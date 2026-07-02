# Diseño: Modo LaTeX completo + Plantillas + Diff de versiones

- **Fecha:** 2026-07-02
- **Alcance:** (1) escribir documentos LaTeX completos (con preámbulo propio) y
  compilarlos tal cual; (2) menú de plantillas con preámbulos clave; (3) salto
  editor↔error; (4) diff de versiones en la máquina del tiempo.
- **Fuera de alcance:** editor CodeMirror, multi-archivo, BibTeX (ciclos futuros).

## 1. Modo LaTeX completo (sin estado nuevo)

**Principio:** no hay flag de modo. Si el documento contiene `\documentclass`
en sus nodos de TEXTO (no dentro de celdas de código), es un documento LaTeX
completo:

- **Compilación (backend `pdf_engine.build_document`):** modo raw — el `.tex`
  es exactamente `serialize_ast(doc)`, sin preámbulo nuestro ni `\title` inyectado.
  Devuelve `markers=[]`. Como el `.tex` raw es idéntico al contenido del editor,
  **línea de error = línea del editor** (mapeo 1:1, mejor que en modo bitácora).
  `parse_errors` sin marcadores → `CompileError(kind="raw", source_line=M, ref=None)`.
- **Preview (frontend `latex-render.ts`):** si el texto contiene
  `\begin{document}`, renderizar solo el cuerpo (entre `\begin{document}` y
  `\end{document}`). Extraer `\title{...}` → `<h1>`, `\author{...}`/`\date{...}`
  → línea secundaria, en el punto donde aparezca `\maketitle`. El preámbulo no
  se muestra. Badge "LaTeX completo" en la cabecera del preview cuando
  `activeLatex` contiene `\documentclass`.
- **Limitación documentada:** celdas ejecutables (`\begin{python}`) dentro de un
  documento completo no se transforman en modo raw; el compilador reportará la
  línea. Modo completo = LaTeX puro.
- Detección con falso positivo (`\documentclass` citado en prosa) es aceptable y
  documentado; escribirlo escapado (`\\documentclass`) o en celda no dispara.

## 2. Menú "Plantillas" (UX sin sobrepoblar)

Un único botón **"Plantillas"** (icono `LayoutTemplate`) en el grupo central de
la toolbar, junto a Exportar — mismo patrón `DropdownMenu` que ExportMenu.
Cada item: nombre + descripción de una línea. Al elegir: si el editor tiene
contenido, `window.confirm("¿Reemplazar el contenido actual?")` (patrón ya usado
en sidebar); inserta la plantilla completa vía `insertAtCursor`-equivalente
(replace total + guardar). Nuevo `ui/src/components/shell/templates-menu.tsx`.

Plantillas (todas XeTeX/Tectonic-safe: `fontspec`, sin `inputenc`; paquetes del
bundle estándar):

1. **Artículo científico** — article + geometry, fontspec, amsmath/amssymb,
   graphicx, hyperref; title/author/date, abstract, secciones.
2. **Informe de laboratorio** — article + siunitx, booktabs; secciones objetivo/
   método/resultados/conclusión, tabla ejemplo con `\SI`.
3. **Tarea de problemas** — article + amsthm, enumitem; entornos problema/solución.
4. **Presentación (Beamer)** — beamer + tema metropolis-fallback (default),
   3 frames de ejemplo.
5. **Carta formal** — letter, remitente/destinatario/firma.

Nota: paquetes fuera de la caché warm (siunitx, beamer) se descargan una vez en
el primer compile; offline después. Documentado en el menú no — en README sí.

## 3. Click en error → línea del editor

- Store: `goToLine: ((line: number) => void) | null` + setter (patrón
  `insertAtCursor`/`flushSave`). El editor lo registra: calcula offset del inicio
  de la línea, `focus + setSelectionRange(inicio, fin_de_línea)` y ajusta
  `scrollTop ≈ (line-1) * 24` (leading-6).
- Panel de errores del preview: cuando `kind === "raw"` y hay `source_line`, el
  item es clicable → `goToLine(source_line)`. En modo bitácora queda como está
  (mapea a celdas; las líneas del tex no corresponden al editor).

## 4. Diff de versiones (máquina del tiempo)

- Botón "Diff" (toggle, icono `GitCompare`) en el footer del overlay Historia.
- Activo: en lugar del preview renderizado, muestra **diff por líneas** entre el
  `latex` del snapshot seleccionado y el `latex` actual (store.activeLatex):
  líneas eliminadas en rojo (`-`), añadidas en verde (`+`), contexto normal.
- Implementación: util puro `diffLines(a, b)` en `ui/src/lib/diff.ts` — LCS
  clásico O(n·m) sobre líneas. // ponytail: cap 3000 líneas por lado; si excede,
  mensaje "documento muy grande para diff".
- Sin backend nuevo (el snapshot ya trae `latex`).

## 5. Tests

- Backend: raw passthrough exacto (tex == serialize del doc, sin doble preámbulo);
  `\documentclass` dentro de celda NO dispara raw; parse_errors sin markers →
  kind raw + línea; modo bitácora intacto (tests existentes).
- Frontend: `diffLines` — casos igual/inserción/borrado/reemplazo (archivo de
  test no hay runner JS: validar con asserts en un `demo()` invocable por node?
  No — sin runner: tsc + revisión; diff util pequeño y determinista con casos
  cubiertos por el panel adversarial).
- E2E visual: plantilla → compilar PDF real raw; error inducido → click → salto
  de línea; diff entre versiones.

## 6. Riesgos

| Riesgo | Mitigación |
|---|---|
| Falso positivo `\documentclass` en prosa | Documentado; escapado no dispara |
| Plantilla pisa trabajo | confirm antes de reemplazar; y time-travel lo recupera |
| Paquetes de plantillas fuera del warm | descarga única on-demand; README |
| Diff O(n·m) en docs enormes | cap 3000 líneas + mensaje |
| beamer no compile en Tectonic | verificación E2E antes de merge |
