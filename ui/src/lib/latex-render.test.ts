import katex from 'katex'
import { describe, expect, it, vi } from 'vitest'

import type { CellNode, Page } from '@/types'

import { renderDocument } from './latex-render'

describe('renderDocument', () => {
  it('renders empty state for empty AST', () => {
    const html = renderDocument([], null, {})
    expect(html).toContain('Vista previa en vivo')
  })

  it('renders AST with inline math and a code cell', () => {
    const ast: NonNullable<Page['ast']> = [
      { type: 'text', text: 'La energía es ' },
      { type: 'math', latex: 'E = mc^2', mode: 'inline' },
      { type: 'text', text: '.' },
      {
        type: 'cell',
        cell_id: 'c1',
        language: 'python',
        source: 'print(1)',
        output: '1',
        figure_path: null,
      } as CellNode,
    ]
    const html = renderDocument(ast, 'page-1', {})
    expect(html).toContain('La energía es')
    expect(html).toContain('katex')
    expect(html).toContain('print(1)')
    expect(html).toContain('Celda python')
    expect(html).toContain('1')
  })

  it('renders display math directly without reconstructing LaTeX', () => {
    const ast: NonNullable<Page['ast']> = [
      { type: 'math', latex: '\\sum_{i=1}^n i', mode: 'display' },
    ]
    const html = renderDocument(ast, null, {})
    expect(html).toContain('katex-display')
  })

  it('collects KaTeX parse errors when requested', () => {
    vi.spyOn(katex, 'renderToString').mockImplementationOnce(() => {
      throw new Error('parse error')
    })

    const ast: NonNullable<Page['ast']> = [
      { type: 'math', latex: '\\broken', mode: 'inline' },
    ]
    const errors: Array<{ latex: string; message: string }> = []
    renderDocument(ast, null, {}, errors)
    expect(errors.length).toBeGreaterThan(0)
    expect(errors[0].message).toContain('parse error')
  })
})
