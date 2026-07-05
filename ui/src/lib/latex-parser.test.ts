import { describe, expect, it } from 'vitest'

import { parseLatex } from './latex-parser'

describe('parseLatex', () => {
  it('returns a single text node for plain text', () => {
    const ast = parseLatex('Hola mundo')
    expect(ast).toHaveLength(1)
    expect(ast[0]).toEqual({ type: 'text', text: 'Hola mundo' })
  })

  it('parses inline math between single dollars', () => {
    const ast = parseLatex('Energía $E = mc^2$ total')
    expect(ast).toHaveLength(3)
    expect(ast[0]).toEqual({ type: 'text', text: 'Energía ' })
    expect(ast[1]).toEqual({ type: 'math', latex: 'E = mc^2', mode: 'inline' })
    expect(ast[2]).toEqual({ type: 'text', text: ' total' })
  })

  it('parses display math between double dollars', () => {
    const ast = parseLatex('$$\\sum_{i=1}^n i$$')
    expect(ast).toHaveLength(1)
    expect(ast[0]).toEqual({ type: 'math', latex: '\\sum_{i=1}^n i', mode: 'display' })
  })

  it('parses display math between backslash brackets', () => {
    const ast = parseLatex('\\[a^2 + b^2 = c^2\\]')
    expect(ast).toHaveLength(1)
    expect(ast[0]).toEqual({ type: 'math', latex: 'a^2 + b^2 = c^2', mode: 'display' })
  })

  it('extracts executable code cells', () => {
    const ast = parseLatex('\\begin{python}[label=uno]\n1 + 1\n\\end{python}')
    expect(ast).toHaveLength(1)
    expect(ast[0]).toMatchObject({
      type: 'cell',
      cell_id: 'uno',
      language: 'python',
      source: '1 + 1',
      output: '',
      figure_path: null,
    })
  })

  it('assigns an auto id to code cells without label', () => {
    const ast = parseLatex('\\begin{sage}\n2+2\n\\end{sage}')
    expect(ast[0]).toMatchObject({
      type: 'cell',
      cell_id: 'cell_1',
      language: 'sage',
      source: '2+2',
    })
  })

  it('ignores non-code environments and treats them as text', () => {
    const ast = parseLatex('\\begin{align}\nx &= y\n\\end{align}')
    expect(ast).toHaveLength(1)
    expect(ast[0]).toEqual({ type: 'text', text: '\\begin{align}\nx &= y\n\\end{align}' })
  })

  it('parses mixed cells with and without options in order', () => {
    const ast = parseLatex(
      '\\begin{python}[label=opt]\n1\n\\end{python}\n\\begin{python}\n2\n\\end{python}\n\\begin{python}[label=last]\n3\n\\end{python}',
    )
    expect(ast).toHaveLength(5)
    expect(ast[0]).toMatchObject({ type: 'cell', cell_id: 'opt', language: 'python', source: '1' })
    expect(ast[1]).toEqual({ type: 'text', text: '\n' })
    expect(ast[2]).toMatchObject({ type: 'cell', cell_id: 'cell_1', language: 'python', source: '2' })
    expect(ast[3]).toEqual({ type: 'text', text: '\n' })
    expect(ast[4]).toMatchObject({ type: 'cell', cell_id: 'last', language: 'python', source: '3' })
  })
})
