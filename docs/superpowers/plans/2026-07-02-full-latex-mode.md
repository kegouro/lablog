# Full LaTeX Mode + Templates + Version Diff — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development. Steps use checkbox syntax.

**Goal:** Documentos LaTeX completos compilados tal cual (raw), menú de plantillas con preámbulos listos, click-error→línea del editor, y diff de versiones en la máquina del tiempo.

**Architecture:** Detección `\documentclass` en nodos texto (sin flags ni migración). Raw → `.tex` == contenido del editor (errores 1:1). Preview extrae el cuerpo. Plantillas = dropdown en toolbar (patrón ExportMenu). Diff = util LCS puro + toggle en el overlay Historia.

## Global Constraints

- Ruff `E,F,I,N,W,UP,B,C4,SIM` línea 100; mypy strict; tsc estricto.
- Plantillas XeTeX-safe: `fontspec`, NUNCA `inputenc`. Beamer verificado compilando en Tectonic.
- Commits conventional + trailer `Co-Authored-By: Kimi Code <noreply@example.com>` (hook; `git commit -F`).
- Gate backend: `ruff check src tests && mypy -p lablog && pytest -q`. Gate frontend: `cd ui && npx tsc --noEmit && npm run build`.

---

### Task 1: Backend — modo raw (TDD)

**Files:** Modify `src/lablog/pdf_engine.py`; test `tests/test_pdf_engine.py` (append).

**Interfaces (Produces):** `_is_full_document(doc) -> bool`; `build_document` devuelve passthrough en raw; `parse_errors(log, [])` → `CompileError.kind == "raw"`.

- [ ] **Step 1: tests que fallan** (append):

```python
def test_full_document_compiles_raw() -> None:
    src = (
        "\\documentclass{article}\n\\begin{document}\nHola $x$\n\\end{document}"
    )
    doc = parse_latex(src)
    tex, markers, figs = pdf_engine.build_document(doc, "T")
    assert tex == serialize_ast(doc)  # passthrough exacto
    assert "fvextra" not in tex  # sin doble preámbulo
    assert markers == [] and figs == []


def test_documentclass_inside_cell_not_raw() -> None:
    src = "\\begin{python}\nprint('documentclass test \\\\documentclass')\n\\end{python}"
    doc = parse_latex(src)
    tex, _markers, _figs = pdf_engine.build_document(doc, "T")
    assert "fvextra" in tex  # sigue en modo bitácora con nuestro preámbulo


def test_parse_errors_without_markers_is_raw() -> None:
    errors = pdf_engine.parse_errors("main.tex:7: Undefined control sequence", [])
    assert errors[0].source_line == 7
    assert errors[0].ref is None and errors[0].kind == "raw"
```

Imports ya presentes en el archivo de tests (`parse_latex` desde `lablog.latex_ast`
— agregar `serialize_ast` al import existente si falta).

- [ ] **Step 2: correr → FAIL.** `pytest tests/test_pdf_engine.py -q`
- [ ] **Step 3: implementar.** En `pdf_engine.py`:

Añadir antes de `build_document`:

```python
def _is_full_document(doc: DocumentNode) -> bool:
    """Documento LaTeX completo: el usuario trae su propio preámbulo."""
    return any(
        isinstance(node, TextNode) and "\\documentclass" in node.text
        for node in doc.children
    )
```

Al inicio de `build_document` (tras la firma):

```python
    if _is_full_document(doc):
        # Modo raw: compilar exactamente lo escrito. Sin marcadores: la línea
        # del .tex ES la línea del editor (mapeo 1:1). Celdas no soportadas aquí.
        return serialize_ast(doc), [], []
```

En `parse_errors`, al construir cada `CompileError`, cuando `markers` está
vacío usar `kind="raw"` (y `ref=None`):

```python
        errors.append(
            CompileError(
                message=message,
                source_line=line,
                ref=marker.ref if marker else None,
                kind=marker.kind if marker else ("raw" if not markers else None),
            )
        )
```

- [ ] **Step 4: correr → PASS.** Suite completa también (los tests de modo bitácora no cambian).
- [ ] **Step 5: gate + commit** `feat(latex): raw compilation for full documents`.

---

### Task 2: Frontend — preview de doc completo, badge, error→línea

**Files:** Modify `ui/src/lib/latex-render.ts`, `ui/src/stores/app-store.ts`, `ui/src/components/editor/latex-editor.tsx`, `ui/src/components/preview/latex-preview.tsx`.

**Interfaces:** store gana `goToLine: ((line: number) => void) | null` + `setGoToLine`.

- [ ] **Step 1: latex-render.ts — extraer cuerpo y bloque de título.** En
`renderLatexToHtml`, después de `const input = applyParameterValues(...)` y del
early-return, y ANTES de la extracción de matemática, insertar (convertir
`input` a `let source = input` y usar `source` de ahí en adelante):

```ts
  let source = input
  // Documento LaTeX completo: renderizar solo el cuerpo. \maketitle se vuelve
  // un bloque de título con \title/\author/\date del preámbulo.
  const bodyMatch = source.match(/\\begin\{document\}([\s\S]*?)(?:\\end\{document\}|$)/)
  if (bodyMatch && bodyMatch.index != null) {
    const preamble = source.slice(0, bodyMatch.index)
    const title = preamble.match(/\\title\{([^{}]*)\}/)?.[1]
    const author = preamble.match(/\\author\{([^{}]*)\}/)?.[1]
    const date = preamble.match(/\\date\{([^{}]*)\}/)?.[1]
    const meta = [author, date].filter(Boolean).join(' · ')
    const titleBlock =
      (title ? `<h1 class="mb-1 text-2xl font-bold tracking-tight">${escapeHtml(title)}</h1>` : '') +
      (meta ? `<p class="mb-4 text-sm text-muted-foreground">${escapeHtml(meta)}</p>` : '')
    source = bodyMatch[1].replace(/\\maketitle/g, () => stash(titleBlock))
  }
```

Nota de orden: `tokens`/`stash` deben declararse ANTES de este bloque (mover su
declaración arriba). El pipeline posterior usa `source` en lugar de `input`.

- [ ] **Step 2: store — `goToLine`** (mismo patrón que `flushSave`): interfaz,
estado inicial `null`, `setGoToLine`.

- [ ] **Step 3: editor — registrar goToLine:**

```ts
  const goToLine = useCallback((line: number) => {
    const ta = textareaRef.current
    if (!ta) return
    const lines = ta.value.split('\n')
    const clamped = Math.max(1, Math.min(line, lines.length))
    const start = lines.slice(0, clamped - 1).reduce((n, l) => n + l.length + 1, 0)
    ta.focus()
    ta.setSelectionRange(start, start + (lines[clamped - 1]?.length ?? 0))
    ta.scrollTop = Math.max(0, (clamped - 3) * 24) // leading-6 = 24px por línea
  }, [])

  useEffect(() => {
    setGoToLine(goToLine)
    return () => setGoToLine(null)
  }, [goToLine, setGoToLine])
```

`setGoToLine` sale del mismo destructure del store.

- [ ] **Step 4: preview — badge + errores clicables.** En `LatexPreview`:
  - `const isFullDoc = activeLatex.includes('\\documentclass')` (traer
    `activeLatex` y `goToLine` del store).
  - Junto al chip "Aproximada", cuando `isFullDoc`:
    `<span class=…mismo estilo…>LaTeX completo</span>`.
  - En el panel de errores, item clicable cuando `e.kind === 'raw' && e.source_line != null`:

```tsx
              <li key={i} className="font-mono">
                {e.kind === 'raw' && e.source_line != null ? (
                  <button
                    type="button"
                    className="underline decoration-dotted hover:text-destructive"
                    onClick={() => goToLine?.(e.source_line as number)}
                  >
                    línea {e.source_line}
                  </button>
                ) : (
                  <span>
                    {e.kind === 'cell' ? `Celda ${e.ref}` : 'Documento'}
                    {e.source_line != null ? ` · línea ${e.source_line}` : ''}
                  </span>
                )}
                : {e.message}
              </li>
```

- [ ] **Step 5: gate + commit** `feat(latex): full-document preview, badge and error-to-line jump`.

---

### Task 3: Frontend — menú Plantillas + diff de versiones

**Files:** Create `ui/src/components/shell/templates-menu.tsx`, `ui/src/lib/latex-templates.ts`, `ui/src/lib/diff.ts`; modify `ui/src/components/shell/toolbar.tsx`, `ui/src/components/history/time-travel.tsx`.

- [ ] **Step 1: `ui/src/lib/latex-templates.ts`** — data pura:

```ts
export interface LatexTemplate {
  id: string
  name: string
  description: string
  content: string
}

export const LATEX_TEMPLATES: LatexTemplate[] = [
  {
    id: 'articulo',
    name: 'Artículo científico',
    description: 'article · abstract, secciones, matemática y figuras',
    content: `\\documentclass[11pt]{article}
\\usepackage[margin=2.5cm]{geometry}
\\usepackage{fontspec}
\\usepackage{amsmath,amssymb}
\\usepackage{graphicx}
\\usepackage{hyperref}

\\title{Título del trabajo}
\\author{Nombre Apellido}
\\date{\\today}

\\begin{document}
\\maketitle

\\begin{abstract}
Resumen del trabajo en un párrafo.
\\end{abstract}

\\section{Introducción}
El contexto y la motivación. Una ecuación inline: $E = mc^2$.

\\section{Método}
\\begin{equation}
  F = ma
\\end{equation}

\\section{Resultados}

\\section{Conclusiones}

\\end{document}
`,
  },
  {
    id: 'informe',
    name: 'Informe de laboratorio',
    description: 'article · siunitx y booktabs para datos y unidades',
    content: `\\documentclass[11pt]{article}
\\usepackage[margin=2.5cm]{geometry}
\\usepackage{fontspec}
\\usepackage{amsmath,amssymb}
\\usepackage{graphicx}
\\usepackage{siunitx}
\\usepackage{booktabs}
\\usepackage{hyperref}

\\title{Informe de laboratorio}
\\author{Nombre Apellido}
\\date{\\today}

\\begin{document}
\\maketitle

\\section{Objetivo}

\\section{Montaje y método}

\\section{Resultados}
\\begin{table}[h]
  \\centering
  \\begin{tabular}{S[table-format=1.2] S[table-format=2.1]}
    \\toprule
    {$t$ (\\si{\\second})} & {$v$ (\\si{\\metre\\per\\second})} \\\\
    \\midrule
    0.10 & 1.0 \\\\
    0.20 & 2.1 \\\\
    \\bottomrule
  \\end{tabular}
  \\caption{Mediciones.}
\\end{table}

La aceleración medida fue \\SI{9.81}{\\metre\\per\\second\\squared}.

\\section{Conclusión}

\\end{document}
`,
  },
  {
    id: 'tarea',
    name: 'Tarea de problemas',
    description: 'article · entornos problema/solución con amsthm',
    content: `\\documentclass[11pt]{article}
\\usepackage[margin=2.5cm]{geometry}
\\usepackage{fontspec}
\\usepackage{amsmath,amssymb,amsthm}
\\usepackage{enumitem}

\\newtheorem{problema}{Problema}
\\theoremstyle{remark}
\\newtheorem*{solucion}{Solución}

\\title{Tarea N}
\\author{Nombre Apellido}
\\date{\\today}

\\begin{document}
\\maketitle

\\begin{problema}
Enunciado del primer problema.
\\end{problema}

\\begin{solucion}
Desarrollo: $\\int_0^1 x\\,dx = \\tfrac{1}{2}$.
\\end{solucion}

\\end{document}
`,
  },
  {
    id: 'beamer',
    name: 'Presentación (Beamer)',
    description: 'beamer · portada y diapositivas de ejemplo',
    content: `\\documentclass{beamer}
\\usepackage{fontspec}
\\usepackage{amsmath}

\\title{Título de la presentación}
\\author{Nombre Apellido}
\\date{\\today}

\\begin{document}

\\frame{\\titlepage}

\\begin{frame}{Motivación}
  \\begin{itemize}
    \\item Primer punto.
    \\item Segundo punto.
  \\end{itemize}
\\end{frame}

\\begin{frame}{Resultado central}
  \\begin{equation}
    E = mc^2
  \\end{equation}
\\end{frame}

\\end{document}
`,
  },
  {
    id: 'carta',
    name: 'Carta formal',
    description: 'letter · remitente, destinatario y firma',
    content: `\\documentclass[11pt]{letter}
\\usepackage[margin=2.5cm]{geometry}
\\usepackage{fontspec}

\\signature{Nombre Apellido}
\\address{Tu dirección \\\\ Ciudad}

\\begin{document}
\\begin{letter}{Destinatario \\\\ Institución \\\\ Ciudad}

\\opening{Estimado/a:}

Cuerpo de la carta.

\\closing{Atentamente,}

\\end{letter}
\\end{document}
`,
  },
]
```

- [ ] **Step 2: `templates-menu.tsx`** (patrón ExportMenu — leerlo primero):

```tsx
import { LayoutTemplate } from 'lucide-react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { replacePageLatex } from '@/lib/api'
import { LATEX_TEMPLATES } from '@/lib/latex-templates'
import { useAppStore } from '@/stores/app-store'

export function TemplatesMenu() {
  const { activePageId, activeLatex, setActiveLatex, setActiveAst, flushSave } = useAppStore()

  const applyTemplate = async (content: string) => {
    if (!activePageId) {
      toast.info('Selecciona una página primero')
      return
    }
    if (activeLatex.trim() && !window.confirm('¿Reemplazar el contenido actual con la plantilla?')) {
      return
    }
    try {
      if (flushSave) await flushSave()
      const result = await replacePageLatex(activePageId, content)
      setActiveLatex(result.latex)
      setActiveAst(result.ast)
      toast.success('Plantilla aplicada')
    } catch {
      toast.error('No se pudo aplicar la plantilla')
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm" className="gap-2 rounded-lg" disabled={!activePageId}>
          <LayoutTemplate className="size-4" />
          <span className="hidden sm:inline">Plantillas</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="center" className="w-72">
        {LATEX_TEMPLATES.map((t) => (
          <DropdownMenuItem key={t.id} onClick={() => applyTemplate(t.content)} className="flex flex-col items-start gap-0.5">
            <span className="font-medium">{t.name}</span>
            <span className="text-xs text-muted-foreground">{t.description}</span>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
```

- [ ] **Step 3: toolbar** — `<TemplatesMenu />` entre el botón Dictar y `<ExportMenu />` (grupo central).

- [ ] **Step 4: `ui/src/lib/diff.ts`:**

```ts
export interface DiffLine {
  kind: 'same' | 'add' | 'del'
  text: string
}

// ponytail: LCS por líneas con recorte de prefijo/sufijo común. Cubre documentos
// de bitácora; si el núcleo editado excede 1500×1500 líneas devuelve null y la
// UI muestra un aviso (upgrade path: diff de Myers).
export function diffLines(a: string, b: string): DiffLine[] | null {
  const A = a.split('\n')
  const B = b.split('\n')
  let pre = 0
  while (pre < A.length && pre < B.length && A[pre] === B[pre]) pre++
  let endA = A.length
  let endB = B.length
  while (endA > pre && endB > pre && A[endA - 1] === B[endB - 1]) {
    endA--
    endB--
  }
  const midA = A.slice(pre, endA)
  const midB = B.slice(pre, endB)
  if (midA.length * midB.length > 1500 * 1500) return null

  const n = midA.length
  const m = midB.length
  const dp: Uint16Array[] = Array.from({ length: n + 1 }, () => new Uint16Array(m + 1))
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      dp[i][j] = midA[i] === midB[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1])
    }
  }

  const out: DiffLine[] = A.slice(0, pre).map((text) => ({ kind: 'same' as const, text }))
  let i = 0
  let j = 0
  while (i < n && j < m) {
    if (midA[i] === midB[j]) {
      out.push({ kind: 'same', text: midA[i] })
      i++
      j++
    } else if (dp[i + 1][j] >= dp[i][j + 1]) {
      out.push({ kind: 'del', text: midA[i] })
      i++
    } else {
      out.push({ kind: 'add', text: midB[j] })
      j++
    }
  }
  while (i < n) out.push({ kind: 'del', text: midA[i++] })
  while (j < m) out.push({ kind: 'add', text: midB[j++] })
  out.push(...A.slice(endA).map((text) => ({ kind: 'same' as const, text })))
  return out
}
```

- [ ] **Step 5: diff en Historia.** En `time-travel.tsx`: traer `activeLatex`
del store; estado `const [showDiff, setShowDiff] = useState(false)`; import
`GitCompare` de lucide + `diffLines` de `@/lib/diff`. En el footer, antes de
Restaurar:

```tsx
        <Button
          variant={showDiff ? 'secondary' : 'outline'}
          size="sm"
          className="h-7 gap-1.5 text-xs"
          onClick={() => setShowDiff((v) => !v)}
        >
          <GitCompare className="size-3.5" />
          Diff
        </Button>
```

En el cuerpo, cuando `showDiff && snapshot`, reemplazar el div del preview por:

```tsx
          <div className="min-w-0 flex-1 overflow-auto p-3 font-mono text-xs leading-5">
            {(() => {
              const diff = diffLines(snapshot.latex, useAppStore.getState().activeLatex)
              if (!diff) return <p className="text-muted-foreground">Documento muy grande para diff.</p>
              return diff.map((l, i) => (
                <div
                  key={i}
                  className={
                    l.kind === 'add'
                      ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
                      : l.kind === 'del'
                        ? 'bg-rose-500/15 text-rose-700 dark:text-rose-300 line-through decoration-1'
                        : 'text-muted-foreground'
                  }
                >
                  <span className="select-none pr-2">{l.kind === 'add' ? '+' : l.kind === 'del' ? '−' : ' '}</span>
                  {l.text || ' '}
                </div>
              ))
            })()}
          </div>
```

(usar `activeLatex` del destructure, NO `useAppStore.getState()` — el snippet
anterior es orientativo; con el destructure el componente re-renderiza al
cambiar). Encabezado del panel cuando showDiff: texto pequeño
"Cambios desde esta versión hasta el estado actual".

- [ ] **Step 6: gate + commits** — `feat(latex): templates menu with XeTeX-ready preambles` y `feat(history): line diff between any version and the present`.

## Self-review

Spec§1→T1+T2; §2→T3 S1-3; §3→T2 S2-4; §4→T3 S4-5. Firmas consistentes: `goToLine(line:number)`, `diffLines(a,b)`, `LATEX_TEMPLATES`. Sin placeholders.
