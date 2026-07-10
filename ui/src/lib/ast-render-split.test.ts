import { describe, expect, it } from 'vitest'

import { splitProseMath } from './ast-render'

describe('splitProseMath', () => {
  it('extracts inline and display math', () => {
    const parts = splitProseMath('Hola $x^2$ y $$E=mc^2$$ fin')
    const kinds = parts.map((p) => p.kind)
    expect(kinds).toContain('math')
    expect(parts.some((p) => p.kind === 'math' && p.display === false)).toBe(true)
    expect(parts.some((p) => p.kind === 'math' && p.display === true)).toBe(true)
  })

  it('classifies pmatrix as KaTeX math env', () => {
    const parts = splitProseMath(
      String.raw`\begin{pmatrix} a & b \\ c & d \end{pmatrix}`,
    )
    expect(parts).toHaveLength(1)
    expect(parts[0].kind).toBe('math')
    if (parts[0].kind === 'math') {
      expect(parts[0].value).toContain('pmatrix')
      expect(parts[0].display).toBe(true)
    }
  })

  it('classifies align as math', () => {
    const parts = splitProseMath(
      String.raw`\begin{align} a &= b \\ c &= d \end{align}`,
    )
    expect(parts[0].kind).toBe('math')
  })

  it('classifies tabular as PDF-only', () => {
    const parts = splitProseMath(
      String.raw`\begin{tabular}{cc} a & b \\ c & d \end{tabular}`,
    )
    expect(parts[0].kind).toBe('pdf')
    if (parts[0].kind === 'pdf') {
      expect(parts[0].env).toBe('tabular')
    }
  })

  it('classifies tikzpicture as PDF-only (Feynman)', () => {
    const parts = splitProseMath(
      String.raw`\begin{tikzpicture}\draw (0,0)--(1,0);\end{tikzpicture}`,
    )
    expect(parts[0].kind).toBe('pdf')
    if (parts[0].kind === 'pdf') {
      expect(parts[0].env).toBe('tikzpicture')
    }
  })

  it('keeps plain prose', () => {
    const parts = splitProseMath('solo texto sin math')
    expect(parts).toEqual([{ kind: 'text', value: 'solo texto sin math' }])
  })
})
