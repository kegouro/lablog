import 'katex/dist/katex.min.css'

import katex from 'katex'
import { useEffect, useRef } from 'react'

import type { AstNode, CellNode } from '@/types'

interface MathProps {
  latex: string
  displayMode: boolean
}

function MathNode({ latex, displayMode }: MathProps) {
  const ref = useRef<HTMLSpanElement>(null)

  useEffect(() => {
    if (!ref.current) return
    try {
      katex.render(latex, ref.current, {
        throwOnError: false,
        displayMode,
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
}

interface CellProps {
  cell: CellNode
  pageId: string | null
}

function CellNodeView({ cell, pageId }: CellProps) {
  return (
    <div className="my-3 rounded-lg border bg-muted/30 p-3">
      <div className="mb-2 flex items-center justify-between text-[10px] uppercase tracking-wider text-muted-foreground">
        <span>Celda {cell.language}</span>
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
      {cell.figure_path && pageId && (
        <img
          src={`/api/v1/pages/${pageId}/cells/${cell.cell_id}/figure`}
          alt="figura"
          className="mt-2 max-h-48 rounded border object-contain"
        />
      )}
    </div>
  )
}

interface TextProps {
  text: string
}

function TextNodeView({ text }: TextProps) {
  if (!text.trim()) return null
  return (
    <p className="my-1.5 leading-relaxed whitespace-pre-wrap">
      {text}
    </p>
  )
}

interface AstNodeProps {
  node: AstNode
  pageId: string | null
}

function AstNodeView({ node, pageId }: AstNodeProps) {
  switch (node.type) {
    case 'text':
      return <TextNodeView text={node.text} />
    case 'math':
      return <MathNode latex={node.latex} displayMode={node.mode === 'display'} />
    case 'cell':
      return <CellNodeView cell={node} pageId={pageId} />
    default:
      return null
  }
}

interface AstRendererProps {
  ast?: AstNode[]
  pageId?: string | null
}

export function AstRenderer({ ast, pageId = null }: AstRendererProps) {
  if (!ast || ast.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
        <div className="rounded-full bg-muted p-4 text-2xl">👀</div>
        <div className="max-w-xs space-y-1">
          <h3 className="font-semibold">Vista previa en vivo</h3>
          <p className="text-sm text-muted-foreground">
            Escribe LaTeX en el editor. Soporta{' '}
            <code className="rounded bg-muted px-1 text-xs">$...$</code>,{' '}
            <code className="rounded bg-muted px-1 text-xs">$$...$$</code> y{' '}
            <code className="rounded bg-muted px-1 text-xs">\\[...\\]</code>.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-1">
      {ast.map((node, index) => (
        <AstNodeView key={`${node.type}-${index}`} node={node} pageId={pageId} />
      ))}
    </div>
  )
}
