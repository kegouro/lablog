/**
 * Configuración KaTeX compartida: macros de física/math + entornos soportados.
 * Lo que KaTeX no puede (tikz, tabular complejo, feynman) se degrada al PDF.
 */

import type { KatexOptions } from 'katex'

/** Macros estilo physics/braket para live preview. */
export const KATEX_MACROS: Record<string, string> = {
  '\\R': '\\mathbb{R}',
  '\\C': '\\mathbb{C}',
  '\\N': '\\mathbb{N}',
  '\\Z': '\\mathbb{Z}',
  '\\Q': '\\mathbb{Q}',
  '\\dd': '\\mathrm{d}',
  '\\dv': '\\frac{\\mathrm{d}#1}{\\mathrm{d}#2}',
  '\\pdv': '\\frac{\\partial #1}{\\partial #2}',
  '\\abs': '\\left|#1\\right|',
  '\\norm': '\\left\\lVert#1\\right\\rVert',
  '\\bra': '\\left\\langle#1\\right|',
  '\\ket': '\\left|#1\\right\\rangle',
  '\\braket': '\\left\\langle#1\\middle|#2\\right\\rangle',
  '\\ketbra': '\\left|#1\\right\\rangle\\left\\langle#2\\right|',
  '\\expval': '\\left\\langle#1\\right\\rangle',
  '\\order': '\\mathcal{O}\\left(#1\\right)',
  '\\vb': '\\mathbf{#1}',
  '\\va': '\\vec{#1}',
  '\\grad': '\\nabla',
  '\\div': '\\nabla\\cdot',
  '\\curl': '\\nabla\\times',
  '\\laplacian': '\\nabla^2',
  '\\Tr': '\\mathrm{Tr}',
  '\\Re': '\\mathrm{Re}',
  '\\Im': '\\mathrm{Im}',
}

/** Entornos que KaTeX renderiza bien en display mode. */
export const KATEX_MATH_ENVS = new Set([
  'equation',
  'equation*',
  'align',
  'align*',
  'aligned',
  'gather',
  'gather*',
  'multline',
  'multline*',
  'split',
  'matrix',
  'pmatrix',
  'bmatrix',
  'Bmatrix',
  'vmatrix',
  'Vmatrix',
  'smallmatrix',
  'cases',
  'rcases',
  'array',
])

/**
 * Entornos de documento / diagramas: no van a KaTeX.
 * Se muestran como bloque «compilar PDF».
 */
export const PDF_ONLY_ENVS = new Set([
  'tabular',
  'tabular*',
  'table',
  'table*',
  'longtable',
  'tikzpicture',
  'tikz',
  'feynmandiagram',
  'fmffile',
  'fmfgraph',
  'fmfgraph*',
  'circuitikz',
  'axis', // pgfplots
  'figure',
  'figure*',
  'minipage',
  'center',
  'flushleft',
  'flushright',
  'enumerate',
  'itemize',
  'description',
  'verbatim',
  'lstlisting',
  'minted',
])

export function katexOptions(displayMode: boolean): KatexOptions {
  return {
    throwOnError: false,
    displayMode,
    strict: 'ignore',
    trust: false,
    macros: KATEX_MACROS,
    output: 'html',
  }
}
