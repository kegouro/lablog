import 'katex/dist/katex.min.css'
import { useMemo } from 'react'

import { useDebouncedValue } from '@/hooks/use-debounced-value'
import { renderLatexToHtml } from '@/lib/latex-render'
import { useAppStore } from '@/stores/app-store'
import type { CellNode, Page } from '@/types'

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

function renderCell(cell: CellNode, pageId: string | null): string {
  const figureHtml =
    cell.figure_path && pageId
      ? `<img src="/api/v1/pages/${pageId}/cells/${cell.cell_id}/figure" alt="figura" class="mt-2 max-h-48 rounded border object-contain" />`
      : ''

  const outputHtml = cell.output
    ? `<div class="rounded border bg-card p-2 text-xs"><p class="font-semibold text-muted-foreground">Output</p><pre class="whitespace-pre-wrap font-mono">${escapeHtml(cell.output)}</pre></div>`
    : ''

  return `
    <div class="my-3 rounded-lg border bg-muted/30 p-3">
      <div class="mb-2 flex items-center justify-between text-[10px] uppercase tracking-wider text-muted-foreground">
        <span>Celda ${escapeHtml(cell.language)}</span>
      </div>
      <pre class="mb-2 max-h-24 overflow-auto rounded bg-muted p-2 text-xs font-mono">${escapeHtml(cell.source)}</pre>
      ${outputHtml}
      ${figureHtml}
    </div>
  `
}

function renderDocument(
  ast: Page['ast'],
  pageId: string | null,
  values: Record<string, string>,
): string {
  if (!ast || ast.length === 0) {
    return `
      <div class="flex h-full flex-col items-center justify-center gap-3 text-center">
        <div class="rounded-full bg-muted p-4 text-2xl">👀</div>
        <div class="max-w-xs space-y-1">
          <h3 class="font-semibold">Vista previa en vivo</h3>
          <p class="text-sm text-muted-foreground">
            Escribe LaTeX en el editor. Soporta <code class="rounded bg-muted px-1 text-xs">$...$</code>,
            <code class="rounded bg-muted px-1 text-xs">$$...$$</code> y
            <code class="rounded bg-muted px-1 text-xs">\\[...\\]</code>.
          </p>
        </div>
      </div>`
  }

  // Reconstruye el LaTeX de nodos texto+matemática contiguos y los renderiza
  // como un solo bloque, para que la matemática inline fluya dentro del párrafo
  // y los entornos (itemize, …) no lleguen fragmentados. Las celdas, que llevan
  // output/figura del AST, se renderizan aparte.
  let html = ''
  let buffer = ''
  const flush = () => {
    if (buffer.trim()) html += renderLatexToHtml(buffer, values)
    buffer = ''
  }
  for (const node of ast) {
    if (!node || typeof node !== 'object') continue
    if (node.type === 'cell') {
      flush()
      html += renderCell(node as CellNode, pageId)
    } else if (node.type === 'math') {
      const m = node as { latex?: string; mode?: string }
      const src = m.latex ?? ''
      buffer += m.mode === 'display' ? `\n\n\\[${src}\\]\n\n` : `$${src}$`
    } else if (node.type === 'text') {
      buffer += (node as { text?: string }).text ?? ''
    }
  }
  flush()
  return html
}

export function LatexPreview() {
  const { activeAst, activePageId, parameterValues } = useAppStore()
  const debouncedAst = useDebouncedValue(activeAst, 150)

  const html = useMemo(
    () => renderDocument(debouncedAst, activePageId, parameterValues),
    [debouncedAst, activePageId, parameterValues],
  )

  return (
    <div className="flex h-full flex-col gap-2">
      <div className="flex items-center justify-between px-1">
        <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
          Vista previa
        </span>
      </div>
      <div
        className="min-h-0 flex-1 overflow-auto rounded-lg border bg-card p-5 text-sm shadow-sm"
        dangerouslySetInnerHTML={{ __html: html }}
      />
    </div>
  )
}
