import katex from 'katex'
import 'katex/dist/katex.min.css'
import { useEffect, useRef } from 'react'

import { useAppStore } from '@/stores/app-store'
import type { CellNode, Page } from '@/types'

function renderKatex(latex: string, displayMode: boolean): string {
  try {
    return katex.renderToString(latex, { throwOnError: false, displayMode })
  } catch {
    return latex
  }
}

function applyParameterValues(text: string, values: Record<string, string>) {
  return text.replace(/\{\{(\w+)\}\}/g, (_, name) => values[name] ?? `{{${name}}}`)
}

function renderMixedLatex(container: HTMLDivElement, latex: string, values: Record<string, string>) {
  container.innerHTML = ''
  latex = applyParameterValues(latex, values)
  if (!latex.trim()) {
    container.innerHTML = `
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
    return
  }

  const parts = latex.split(/(\$\$[\s\S]*?\$\$|\\\[[\s\S]*?\\\]|\$[\s\S]*?\$)/g)

  for (const part of parts) {
    if (!part) continue
    const trimmed = part.trim()

    if (part.startsWith('$$') && part.endsWith('$$')) {
      const el = document.createElement('div')
      el.className = 'my-2 block'
      el.innerHTML = renderKatex(trimmed.slice(2, -2).trim(), true)
      container.appendChild(el)
    } else if (part.startsWith('\\[') && part.endsWith('\\]')) {
      const el = document.createElement('div')
      el.className = 'my-2 block'
      el.innerHTML = renderKatex(trimmed.slice(2, -2).trim(), true)
      container.appendChild(el)
    } else if (part.startsWith('$') && part.endsWith('$')) {
      const el = document.createElement('span')
      el.innerHTML = renderKatex(trimmed.slice(1, -1).trim(), false)
      container.appendChild(el)
    } else {
      const p = document.createElement('p')
      p.className = 'whitespace-pre-wrap break-words'
      p.textContent = part
      container.appendChild(p)
    }
  }
}

function renderCell(container: HTMLDivElement, cell: CellNode, pageId: string | null) {
  const wrapper = document.createElement('div')
  wrapper.className = 'my-3 rounded-lg border bg-muted/30 p-3'

  const header = document.createElement('div')
  header.className = 'mb-2 flex items-center justify-between text-[10px] uppercase tracking-wider text-muted-foreground'
  header.innerHTML = `<span>Celda ${cell.language}</span>`
  wrapper.appendChild(header)

  const source = document.createElement('pre')
  source.className = 'mb-2 max-h-24 overflow-auto rounded bg-muted p-2 text-xs font-mono'
  source.textContent = cell.source
  wrapper.appendChild(source)

  if (cell.output) {
    const out = document.createElement('div')
    out.className = 'rounded border bg-card p-2 text-xs'
    out.innerHTML = `<p class="font-semibold text-muted-foreground">Output</p><pre class="whitespace-pre-wrap font-mono">${cell.output}</pre>`
    wrapper.appendChild(out)
  }

  if (cell.figure_path && pageId) {
    const img = document.createElement('img')
    img.src = `/api/v1/pages/${pageId}/cells/${cell.cell_id}/figure`
    img.alt = 'figura'
    img.className = 'mt-2 max-h-48 rounded border object-contain'
    wrapper.appendChild(img)
  }

  container.appendChild(wrapper)
}

function renderDocument(
  container: HTMLDivElement,
  latex: string,
  ast: Page['ast'],
  pageId: string | null,
  values: Record<string, string>,
) {
  container.innerHTML = ''

  if (!ast || ast.length === 0) {
    renderMixedLatex(container, latex, values)
    return
  }

  for (const node of ast) {
    if (!node || typeof node !== 'object') continue
    if (node.type === 'cell') {
      renderCell(container, node as CellNode, pageId)
    } else if (node.type === 'math') {
      const el = document.createElement('div')
      el.className = 'my-2 block'
      const mode = (node as { mode?: string; latex?: string }).mode ?? 'inline'
      const latexSource = applyParameterValues((node as { latex?: string }).latex ?? '', values)
      el.innerHTML = renderKatex(latexSource, mode === 'display')
      container.appendChild(el)
    } else if (node.type === 'text') {
      const text = applyParameterValues((node as { text?: string }).text ?? '', values)
      const p = document.createElement('p')
      p.className = 'whitespace-pre-wrap break-words'
      p.textContent = text
      container.appendChild(p)
    } else {
      const p = document.createElement('p')
      p.className = 'whitespace-pre-wrap break-words'
      p.textContent = JSON.stringify(node)
      container.appendChild(p)
    }
  }
}

export function LatexPreview() {
  const { activeLatex, activeAst, activePageId, parameterValues } = useAppStore()
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!ref.current) return
    renderDocument(ref.current, activeLatex, activeAst, activePageId, parameterValues)
  }, [activeLatex, activeAst, activePageId, parameterValues])

  return (
    <div className="flex h-full flex-col gap-2">
      <div className="flex items-center justify-between px-1">
        <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
          Vista previa
        </span>
      </div>
      <div
        ref={ref}
        className="min-h-0 flex-1 overflow-auto rounded-lg border bg-card p-5 text-sm shadow-sm"
      >
        <p className="text-muted-foreground italic">La preview aparecerá aquí…</p>
      </div>
    </div>
  )
}
