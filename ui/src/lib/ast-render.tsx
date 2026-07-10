import 'katex/dist/katex.min.css'

import katex from 'katex'
import { memo, useEffect, useMemo, useRef } from 'react'

import type { AstNode, CellNode } from '@/types'

interface MathProps {
  latex: string
  displayMode: boolean
}

const MathNode = memo(function MathNode({ latex, displayMode }: MathProps) {
  const ref = useRef<HTMLSpanElement>(null)

  useEffect(() => {
    if (!ref.current) return
    try {
      katex.render(latex, ref.current, {
        throwOnError: false,
        displayMode,
        strict: 'ignore',
      })
    } catch {
      ref.current.textContent = latex
    }
  }, [latex, displayMode])

  return displayMode ? (
    <div className="my-2 block overflow-x-auto" ref={ref as React.RefObject<HTMLDivElement>} />
  ) : (
    <span ref={ref} />
  )
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

interface TextProps {
  text: string
}

/** Prosa con math inline $...$ / $$...$$ / \[...\] sin HTML crudo. */
const TextNodeView = memo(function TextNodeView({ text }: TextProps) {
  const parts = useMemo(() => splitProseMath(text), [text])
  if (!text.trim()) return null
  return (
    <div className="my-1.5 leading-relaxed whitespace-pre-wrap">
      {parts.map((p, i) =>
        p.kind === 'text' ? (
          <span key={i}>{p.value}</span>
        ) : (
          <MathNode key={i} latex={p.value} displayMode={p.display} />
        ),
      )}
    </div>
  )
})

type ProsePart =
  | { kind: 'text'; value: string }
  | { kind: 'math'; value: string; display: boolean }

function splitProseMath(text: string): ProsePart[] {
  const parts: ProsePart[] = []
  const re = /\$\$([\s\S]+?)\$\$|\\\[([\s\S]+?)\\\]|\$([^$\n]+?)\$/g
  let last = 0
  let m: RegExpExecArray | null
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) {
      parts.push({ kind: 'text', value: text.slice(last, m.index) })
    }
    if (m[1] != null) {
      parts.push({ kind: 'math', value: m[1].trim(), display: true })
    } else if (m[2] != null) {
      parts.push({ kind: 'math', value: m[2].trim(), display: true })
    } else if (m[3] != null) {
      parts.push({ kind: 'math', value: m[3].trim(), display: false })
    }
    last = m.index + m[0].length
  }
  if (last < text.length) {
    parts.push({ kind: 'text', value: text.slice(last) })
  }
  return parts.length ? parts : [{ kind: 'text', value: text }]
}

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

/** Render del AST del backend — una sola fuente de verdad para live preview. */
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
