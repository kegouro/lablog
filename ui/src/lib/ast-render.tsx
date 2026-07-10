import 'katex/dist/katex.min.css'

import katex from 'katex'
import { memo, useEffect, useMemo, useRef, useState } from 'react'

import {
  KATEX_MATH_ENVS,
  PDF_ONLY_ENVS,
  katexOptions,
} from '@/lib/katex-config'
import type { AstNode, CellNode } from '@/types'

interface MathProps {
  latex: string
  displayMode: boolean
}

const MathNode = memo(function MathNode({ latex, displayMode }: MathProps) {
  const ref = useRef<HTMLSpanElement>(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    if (!ref.current) return
    try {
      katex.render(latex, ref.current, katexOptions(displayMode))
      setFailed(false)
    } catch {
      ref.current.textContent = latex
      setFailed(true)
    }
  }, [latex, displayMode])

  const body = displayMode ? (
    <div
      className="my-2 block overflow-x-auto"
      ref={ref as React.RefObject<HTMLDivElement>}
    />
  ) : (
    <span ref={ref} />
  )

  if (failed && displayMode) {
    return (
      <div className="my-2 rounded border border-amber-500/40 bg-amber-500/5 p-2 text-xs">
        <p className="mb-1 text-amber-700 dark:text-amber-300">
          KaTeX no pudo renderizar este bloque — prueba Compilar PDF.
        </p>
        {body}
      </div>
    )
  }
  return body
})

interface CellProps {
  cell: CellNode
  pageId: string | null
}

const CellNodeView = memo(function CellNodeView({ cell, pageId }: CellProps) {
  const figureSrc =
    cell.figure_path && pageId
      ? `/api/v1/pages/${pageId}/cells/${encodeURIComponent(cell.cell_id)}/figure`
      : null

  return (
    <div className="my-3 rounded-lg border bg-muted/30 p-3">
      <div className="mb-2 flex items-center justify-between text-[10px] uppercase tracking-wider text-muted-foreground">
        <span>Celda {cell.language}</span>
        {cell.status === 'error' && <span className="text-destructive">error</span>}
        {cell.status === 'ok' && <span className="text-emerald-600">ok</span>}
      </div>
      <pre className="mb-2 max-h-24 overflow-auto rounded bg-muted p-2 text-xs font-mono whitespace-pre-wrap">
        {cell.source}
      </pre>
      {cell.output && (
        <div className="rounded border bg-card p-2 text-xs">
          <p className="font-semibold text-muted-foreground">Output</p>
          <pre className="whitespace-pre-wrap font-mono">{cell.output}</pre>
        </div>
      )}
      {figureSrc && (
        <img
          src={figureSrc}
          alt="figura"
          className="mt-2 max-h-48 rounded border object-contain"
          loading="lazy"
        />
      )}
    </div>
  )
})

const PdfOnlyBlock = memo(function PdfOnlyBlock({
  env,
  body,
}: {
  env: string
  body: string
}) {
  return (
    <div className="my-3 rounded-lg border border-dashed border-primary/40 bg-primary/5 p-3">
      <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-primary">
        {env} · vista previa PDF
      </p>
      <p className="mb-2 text-xs text-muted-foreground">
        Tablas, TikZ y diagramas de Feynman se ven al compilar con Tectonic (paquetes
        booktabs, tikz, tikz-feynman, …).
      </p>
      <pre className="max-h-40 overflow-auto rounded bg-muted/60 p-2 text-[11px] font-mono whitespace-pre-wrap">
        {`\\begin{${env}}${body}\\end{${env}}`}
      </pre>
    </div>
  )
})

type ProsePart =
  | { kind: 'text'; value: string }
  | { kind: 'math'; value: string; display: boolean }
  | { kind: 'pdf'; env: string; body: string }

/**
 * Parte prosa en: math display/inline, entornos KaTeX, entornos solo-PDF, texto.
 */
export function splitProseMath(text: string): ProsePart[] {
  const parts: ProsePart[] = []
  // Entornos \begin{env}...\end{env} (no code cells: los filtra el backend).
  const envRe =
    /\\begin\{([a-zA-Z*]+)\}([\s\S]*?)\\end\{\1\}|\$\$([\s\S]+?)\$\$|\\\[([\s\S]+?)\\\]|\$([^$\n]+?)\$/g
  let last = 0
  let m: RegExpExecArray | null
  while ((m = envRe.exec(text)) !== null) {
    if (m.index > last) {
      parts.push({ kind: 'text', value: text.slice(last, m.index) })
    }
    if (m[1] != null) {
      const env = m[1]
      const body = m[2] ?? ''
      const base = env.replace(/\*$/, '')
      if (KATEX_MATH_ENVS.has(env) || KATEX_MATH_ENVS.has(base)) {
        // KaTeX espera el entorno completo para align/matrix.
        parts.push({
          kind: 'math',
          value: `\\begin{${env}}${body}\\end{${env}}`,
          display: true,
        })
      } else if (PDF_ONLY_ENVS.has(env) || PDF_ONLY_ENVS.has(base)) {
        parts.push({ kind: 'pdf', env, body })
      } else {
        // Entorno desconocido: intentar como math display, si falla se verá el fallback.
        parts.push({
          kind: 'math',
          value: `\\begin{${env}}${body}\\end{${env}}`,
          display: true,
        })
      }
    } else if (m[3] != null) {
      parts.push({ kind: 'math', value: m[3].trim(), display: true })
    } else if (m[4] != null) {
      parts.push({ kind: 'math', value: m[4].trim(), display: true })
    } else if (m[5] != null) {
      parts.push({ kind: 'math', value: m[5].trim(), display: false })
    }
    last = m.index + m[0].length
  }
  if (last < text.length) {
    parts.push({ kind: 'text', value: text.slice(last) })
  }
  return parts.length ? parts : [{ kind: 'text', value: text }]
}

const TextNodeView = memo(function TextNodeView({ text }: { text: string }) {
  const parts = useMemo(() => splitProseMath(text), [text])
  if (!text.trim()) return null
  return (
    <div className="my-1.5 leading-relaxed whitespace-pre-wrap">
      {parts.map((p, i) => {
        if (p.kind === 'text') return <span key={i}>{p.value}</span>
        if (p.kind === 'pdf') return <PdfOnlyBlock key={i} env={p.env} body={p.body} />
        return <MathNode key={i} latex={p.value} displayMode={p.display} />
      })}
    </div>
  )
})

interface AstNodeProps {
  node: AstNode
  pageId: string | null
}

const AstNodeView = memo(function AstNodeView({ node, pageId }: AstNodeProps) {
  switch (node.type) {
    case 'text':
      return <TextNodeView text={node.text} />
    case 'math':
      return <MathNode latex={node.latex} displayMode={node.mode === 'display'} />
    case 'cell':
      return <CellNodeView cell={node} pageId={pageId} />
    case 'section':
      return (
        <section className="my-3">
          <h3 className="mb-1 text-base font-semibold">{node.title}</h3>
          {node.children?.map((child, i) => (
            <AstNodeView key={i} node={child} pageId={pageId} />
          ))}
        </section>
      )
    default:
      return null
  }
})

interface AstRendererProps {
  ast: AstNode[] | undefined
  pageId?: string | null
}

/** Render del AST del backend — SSOT del live preview. */
export const AstRenderer = memo(function AstRenderer({
  ast,
  pageId = null,
}: AstRendererProps) {
  if (!ast?.length) {
    return (
      <p className="px-2 py-6 text-center text-sm text-muted-foreground">
        Escribe LaTeX para ver la vista previa en vivo.
      </p>
    )
  }
  return (
    <div className="px-1 py-2">
      {ast.map((node, i) => (
        <AstNodeView key={`${node.type}-${i}`} node={node} pageId={pageId} />
      ))}
    </div>
  )
})
