import type { Page } from '@/types'

// Lenguajes que lablog ejecuta como celdas. Cualquier otro \begin{...}
// (align, equation, itemize, figure, …) es LaTeX normal: se preserva como
// texto y lo renderiza el preview. Debe coincidir con CODE_ENVIRONMENTS del backend.
const CODE_ENVIRONMENTS = new Set([
  'python', 'py', 'code', 'sage', 'julia', 'r', 'octave', 'bash', 'sh',
])

function extractOption(options: string, key: string): string | undefined {
  const pattern = new RegExp(`\\b${key}\\s*=\\s*([^,\\]]+)`, 'g')
  const m = pattern.exec(options)
  return m ? m[1].trim() : undefined
}

export function parseLatex(source: string): NonNullable<Page['ast']> {
  const ast: NonNullable<Page['ast']> = []
  let remaining = source
  let cellCounter = 0

  const cellPattern = /\\begin\{([a-zA-Z0-9_]+)\}\s*\[(.*?)\](.*?)\\end\{\1\}/gs
  const cellPatternNoOpts = /\\begin\{([a-zA-Z0-9_]+)\}(.*?)\\end\{\1\}/gs
  const displayBlockPattern = /\$\$([\s\S]*?)\$\$/gs
  const displayBracketPattern = /\\\[(.*?)\\\]/gs
  const inlineMathPattern = /\$(.*?)\$/gs

  while (remaining) {
    const matches: Array<{
      start: number
      end: number
      node: NonNullable<Page['ast']>[number]
    }> = []

    for (const m of remaining.matchAll(cellPattern)) {
      if (m.index == null) continue
      if (!CODE_ENVIRONMENTS.has(m[1])) continue
      matches.push({
        start: m.index,
        end: m.index + m[0].length,
        node: {
          type: 'cell',
          cell_id: extractOption(m[2], 'label') || extractOption(m[2], 'id') || '',
          language: m[1],
          source: m[3].trim(),
          output: '',
          figure_path: null,
        },
      })
    }

    if (matches.length === 0) {
      for (const m of remaining.matchAll(cellPatternNoOpts)) {
        if (m.index == null) continue
        if (!CODE_ENVIRONMENTS.has(m[1])) continue
        matches.push({
          start: m.index,
          end: m.index + m[0].length,
          node: {
            type: 'cell',
            cell_id: '',
            language: m[1],
            source: m[2].trim(),
            output: '',
            figure_path: null,
          },
        })
      }
    }

    for (const m of remaining.matchAll(displayBlockPattern)) {
      if (m.index == null) continue
      matches.push({
        start: m.index,
        end: m.index + m[0].length,
        node: { type: 'math', latex: m[1].trim(), mode: 'display' },
      })
    }

    for (const m of remaining.matchAll(displayBracketPattern)) {
      if (m.index == null) continue
      matches.push({
        start: m.index,
        end: m.index + m[0].length,
        node: { type: 'math', latex: m[1].trim(), mode: 'display' },
      })
    }

    for (const m of remaining.matchAll(inlineMathPattern)) {
      if (m.index == null) continue
      matches.push({
        start: m.index,
        end: m.index + m[0].length,
        node: { type: 'math', latex: m[1].trim(), mode: 'inline' },
      })
    }

    if (matches.length === 0) {
      ast.push({ type: 'text', text: remaining })
      break
    }

    matches.sort((a, b) => a.start - b.start)
    const { start, end, node } = matches[0]

    if (node.type === 'cell') {
      const cellNode = node as { cell_id: string }
      if (!cellNode.cell_id) {
        cellCounter += 1
        cellNode.cell_id = `cell_${cellCounter}`
      }
    }

    if (start > 0) {
      ast.push({ type: 'text', text: remaining.slice(0, start) })
    }

    ast.push(node)
    remaining = remaining.slice(end)
  }

  return ast
}
