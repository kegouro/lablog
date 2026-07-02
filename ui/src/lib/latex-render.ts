import katex from 'katex'

import type { CellNode, Page } from '@/types'

// Renderer LaTeX → HTML para el subconjunto común usado en una bitácora:
// matemática ($...$, $$...$$, \[...\], entornos align/equation/…) vía KaTeX,
// más estructura de prosa (secciones, énfasis, listas).
//
// ponytail: cubre el 90% de una bitácora científica, no LaTeX completo.
//   Para fidelidad total (figuras flotantes, bibliografía, refs numeradas)
//   el camino es compilar a PDF en el backend, no ampliar este archivo.

// Entornos matemáticos de nivel superior que pasamos enteros a KaTeX.
// matrix/cases/array NO van aquí: suelen ir anidados dentro de estos.
const MATH_ENVS = [
  'equation', 'equation*', 'align', 'align*', 'gather', 'gather*',
  'multline', 'multline*', 'flalign', 'flalign*', 'alignat', 'alignat*',
  'eqnarray', 'eqnarray*',
]

const MATH_ENV_ALT = MATH_ENVS.map((e) => e.replace('*', '\\*')).join('|')
const MATH_ENV_RE = new RegExp(`\\\\begin\\{(${MATH_ENV_ALT})\\}([\\s\\S]*?)\\\\end\\{\\1\\}`, 'g')

export function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

export function applyParameterValues(text: string, values: Record<string, string>): string {
  return text.replace(/\{\{(\w+)\}\}/g, (_, name) => values[name] ?? `{{${name}}}`)
}

function renderKatex(latex: string, displayMode: boolean): string {
  try {
    // throwOnError:false ya colorea en rojo errores de sintaxis dentro de KaTeX.
    return katex.renderToString(latex, { throwOnError: false, displayMode })
  } catch {
    // Fallo duro: muestra el origen con subrayado punteado en vez de romper.
    return `<span class="text-destructive underline decoration-dotted" title="Error de LaTeX">${escapeHtml(latex)}</span>`
  }
}

function renderInline(s: string): string {
  let prev = ''
  let out = s
  let guard = 0
  // Repetir para resolver anidación: \textbf{\emph{x}}
  while (out !== prev && guard++ < 6) {
    prev = out
    out = out
      .replace(/\\(?:textbf|textmd)\{([^{}]*)\}/g, '<strong>$1</strong>')
      .replace(/\\(?:textit|emph|textsl)\{([^{}]*)\}/g, '<em>$1</em>')
      .replace(/\\underline\{([^{}]*)\}/g, '<u>$1</u>')
      .replace(/\\(?:texttt|verb)\{([^{}]*)\}/g, '<code class="rounded bg-muted px-1 text-[0.85em]">$1</code>')
      .replace(/\\href\{([^{}]*)\}\{([^{}]*)\}/g, '<a class="text-primary underline" href="$1" target="_blank" rel="noreferrer">$2</a>')
      .replace(/\\url\{([^{}]*)\}/g, '<a class="text-primary underline" href="$1" target="_blank" rel="noreferrer">$1</a>')
  }
  return out
    .replace(/\\\\(\[[^\]]*\])?/g, '<br/>') // \\ y \\[2pt]
    .replace(/\\%/g, '%')
    .replace(/\\_/g, '_')
    .replace(/\\#/g, '#')
    .replace(/\\\$/g, '$')
    .replace(/\\\{/g, '{')
    .replace(/\\\}/g, '}')
    .replace(/~/g, '&nbsp;')
}

function renderItems(body: string): string {
  return body
    .split(/\\item\b/)
    .slice(1) // descarta lo previo al primer \item
    .map((chunk) => `<li>${renderInline(chunk.replace(/\n/g, ' ').trim())}</li>`)
    .join('')
}

// Procesa prosa (sin matemática: ya extraída como placeholders opacos).
function renderProse(text: string): string {
  let s = escapeHtml(text)

  // Comentarios de línea (no \%)
  s = s.replace(/(^|[^\\])%.*$/gm, '$1')

  // Listas (antes de partir en párrafos)
  s = s.replace(
    /\\begin\{itemize\}([\s\S]*?)\\end\{itemize\}/g,
    (_, body) => `<ul class="my-2 ml-5 list-disc space-y-1">${renderItems(body)}</ul>`,
  )
  s = s.replace(
    /\\begin\{enumerate\}([\s\S]*?)\\end\{enumerate\}/g,
    (_, body) => `<ol class="my-2 ml-5 list-decimal space-y-1">${renderItems(body)}</ol>`,
  )

  // Encabezados
  s = s.replace(/\\section\*?\{([^{}]*)\}/g, '<h2 class="mt-4 mb-2 text-xl font-bold tracking-tight">$1</h2>')
  s = s.replace(/\\subsection\*?\{([^{}]*)\}/g, '<h3 class="mt-3 mb-1.5 text-lg font-semibold">$1</h3>')
  s = s.replace(/\\subsubsection\*?\{([^{}]*)\}/g, '<h4 class="mt-2 mb-1 text-base font-semibold">$1</h4>')
  s = s.replace(/\\paragraph\*?\{([^{}]*)\}/g, '<span class="font-semibold">$1</span> ')

  // Comandos estructurales sin salida visible directa
  s = s.replace(
    /\\(maketitle|tableofcontents|centering|noindent|clearpage|newpage|bigskip|medskip|smallskip|hline|toprule|midrule|bottomrule)\b\*?/g,
    '',
  )

  // Párrafos por línea en blanco
  const blocks = s.split(/\n\s*\n/)
  let html = ''
  for (const raw of blocks) {
    const block = raw.trim()
    if (!block) continue
    if (/^<(h[1-6]|ul|ol|div|table)/.test(block)) {
      html += renderInline(block)
    } else {
      html += `<p class="my-1.5 leading-relaxed">${renderInline(block.replace(/\n/g, ' '))}</p>`
    }
  }
  return html
}

/** Renderiza un fragmento LaTeX (prosa + matemática) a HTML. */
export function renderLatexToHtml(source: string, values: Record<string, string> = {}): string {
  const input = applyParameterValues(source, values)
  if (!input.trim()) return ''

  // 1) Extrae TODA la matemática a placeholders opacos para que el split de
  //    prosa (párrafos, listas) no fragmente entornos ni rompa la línea en
  //    matemática inline. KaTeX produce HTML seguro; se reinyecta al final.
  const tokens: string[] = []
  const stash = (html: string): string => {
    tokens.push(html)
    return ` ${tokens.length - 1} `
  }

  const text = input
    .replace(/\$\$([\s\S]*?)\$\$/g, (_, m) =>
      stash(`<div class="my-2 block overflow-x-auto">${renderKatex(m.trim(), true)}</div>`),
    )
    .replace(/\\\[([\s\S]*?)\\\]/g, (_, m) =>
      stash(`<div class="my-2 block overflow-x-auto">${renderKatex(m.trim(), true)}</div>`),
    )
    .replace(MATH_ENV_RE, (m) =>
      stash(`<div class="my-2 block overflow-x-auto">${renderKatex(m.trim(), true)}</div>`),
    )
    .replace(/\$([^$\n][\s\S]*?)\$/g, (_, m) => stash(`<span>${renderKatex(m.trim(), false)}</span>`))
    .replace(/\\\(([\s\S]*?)\\\)/g, (_, m) => stash(`<span>${renderKatex(m.trim(), false)}</span>`))

  // 2) Renderiza la prosa y 3) reinyecta la matemática.
  const html = renderProse(text)
  return html.replace(/ (\d+) /g, (_, i) => tokens[Number(i)] ?? '')
}

export function renderCell(cell: CellNode, pageId: string | null): string {
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

export function renderDocument(
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
