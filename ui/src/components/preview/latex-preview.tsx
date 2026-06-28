import katex from 'katex'
import 'katex/dist/katex.min.css'
import { useMemo } from 'react'

import { useDebouncedValue } from '@/hooks/use-debounced-value'
import { useAppStore } from '@/stores/app-store'
import type { CellNode, Page } from '@/types'

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

function applyParameterValues(text: string, values: Record<string, string>): string {
  return text.replace(/\{\{(\w+)\}\}/g, (_, name) => values[name] ?? `{{${name}}}`)
}

function renderKatex(latex: string, displayMode: boolean): string {
  try {
    return katex.renderToString(latex, { throwOnError: false, displayMode })
  } catch {
    return escapeHtml(latex)
  }
}

function renderTextNode(text: string, values: Record<string, string>): string {
  text = applyParameterValues(text, values)
  if (!text.trim()) return ''

  const parts = text.split(/(\$\$[\s\S]*?\$\$|\\\[[\s\S]*?\\\]|\$[\s\S]*?\$)/g)
  let html = ''

  for (const part of parts) {
    if (!part) continue
    const trimmed = part.trim()

    if (part.startsWith('$$') && part.endsWith('$$')) {
      html += `<div class="my-2 block">${renderKatex(trimmed.slice(2, -2).trim(), true)}</div>`
    } else if (part.startsWith('\\[') && part.endsWith('\\]')) {
      html += `<div class="my-2 block">${renderKatex(trimmed.slice(2, -2).trim(), true)}</div>`
    } else if (part.startsWith('$') && part.endsWith('$')) {
      html += `<span>${renderKatex(trimmed.slice(1, -1).trim(), false)}</span>`
    } else {
      html += `<p class="whitespace-pre-wrap break-words">${escapeHtml(part)}</p>`
    }
  }

  return html
}

function renderMathNode(node: { latex?: string; mode?: string }, values: Record<string, string>): string {
  const source = applyParameterValues(node.latex ?? '', values)
  const displayMode = node.mode === 'display'
  return `<div class="my-2 block">${renderKatex(source, displayMode)}</div>`
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

  let html = ''
  for (const node of ast) {
    if (!node || typeof node !== 'object') continue
    switch (node.type) {
      case 'cell':
        html += renderCell(node as CellNode, pageId)
        break
      case 'math':
        html += renderMathNode(node as { latex?: string; mode?: string }, values)
        break
      case 'text':
        html += renderTextNode((node as { text?: string }).text ?? '', values)
        break
      default:
        html += `<p class="whitespace-pre-wrap break-words">${escapeHtml(JSON.stringify(node))}</p>`
    }
  }
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
