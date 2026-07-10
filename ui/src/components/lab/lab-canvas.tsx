import katex from 'katex'
import {
  ChevronDown,
  ChevronUp,
  Code2,
  FileText,
  Play,
  Plus,
  RotateCcw,
  Trash2,
} from 'lucide-react'
import { Fragment, useEffect, useRef, useState, type ReactNode } from 'react'

import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import {
  ApiError,
  deleteCell,
  executeCell,
  insertCell,
  listCells,
  moveCell as moveCellApi,
  updateCell,
} from '@/lib/api'
import { useAppStore } from '@/stores/app-store'

type LabCell = {
  cell_id: string
  language: string
  source: string
  output: string | null
  figure_path: string | null
  status?: 'idle' | 'running' | 'ok' | 'error'
  collapsed?: boolean
}

const LANGUAGE_OPTIONS = [
  { value: 'python', label: 'Python' },
  { value: 'markdown', label: 'Texto / Markdown' },
  { value: 'latex', label: 'LaTeX' },
]

/** Preview markdown/texto sin HTML crudo: KaTeX en nodos React. */
function MarkdownPreview({ source }: { source: string }) {
  const lines = source.split('\n')
  return (
    <div className="prose prose-sm dark:prose-invert max-w-none">
      {lines.map((line, li) => {
        if (!line.trim()) return <div key={li} className="h-2" />
        const parts: ReactNode[] = []
        const re = /\$([^$]+)\$/g
        let last = 0
        let m: RegExpExecArray | null
        let pi = 0
        while ((m = re.exec(line)) !== null) {
          if (m.index > last) {
            parts.push(<Fragment key={`${li}-t-${pi++}`}>{line.slice(last, m.index)}</Fragment>)
          }
          const latex = m[1].trim()
          let html = ''
          try {
            html = katex.renderToString(latex, { throwOnError: false })
          } catch {
            html = ''
          }
          if (html) {
            parts.push(
              <span
                key={`${li}-m-${pi++}`}
                className="katex-inline"
                // KaTeX genera HTML confiable (no input de usuario crudo).
                dangerouslySetInnerHTML={{ __html: html }}
              />,
            )
          } else {
            parts.push(<Fragment key={`${li}-m-${pi++}`}>${latex}$</Fragment>)
          }
          last = m.index + m[0].length
        }
        if (last < line.length) {
          parts.push(<Fragment key={`${li}-t-${pi++}`}>{line.slice(last)}</Fragment>)
        }
        return (
          <p key={li} className="mb-2 leading-relaxed">
            {parts}
          </p>
        )
      })}
    </div>
  )
}

export function LabCanvas() {
  const activePageId = useAppStore((s) => s.activePageId)
  const setLabMode = useAppStore((s) => s.setLabMode)
  const [cells, setCells] = useState<LabCell[]>([])
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!activePageId) {
      setCells([])
      return
    }
    let cancelled = false
    const requestedId = activePageId
    setLoading(true)
    listCells(requestedId)
      .then((serverCells) => {
        if (cancelled || useAppStore.getState().activePageId !== requestedId) return
        setCells(
          serverCells.map((c) => ({
            ...c,
            status: (c.status as LabCell['status']) ?? 'idle',
            collapsed: false,
          })),
        )
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [activePageId])

  const addCell = async (language: string) => {
    if (!activePageId) return
    const cell: LabCell = {
      cell_id: crypto.randomUUID(),
      language,
      source: language === 'python' ? '# escribe tu código aquí\n' : '',
      output: '',
      figure_path: null,
      status: 'idle',
      collapsed: false,
    }
    try {
      await insertCell(activePageId, {
        cell_id: cell.cell_id,
        language: cell.language,
        source: cell.source,
      })
      setCells((prev) => [...prev, cell])
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)
    } catch (err) {
      console.error(err)
    }
  }

  const updateSource = (cellId: string, source: string) => {
    setCells((prev) => prev.map((c) => (c.cell_id === cellId ? { ...c, source } : c)))
  }

  const saveCell = async (cellId: string, language: string, source: string) => {
    if (!activePageId) return
    await updateCell(activePageId, cellId, { language, source })
  }

  const runCell = async (cellId: string) => {
    if (!activePageId) return
    const cell = cells.find((c) => c.cell_id === cellId)
    if (!cell) return
    await saveCell(cellId, cell.language, cell.source)
    setCells((prev) => prev.map((c) => (c.cell_id === cellId ? { ...c, status: 'running' } : c)))
    try {
      const result = await executeCell(activePageId, cellId)
      setCells((prev) =>
        prev.map((c) =>
          c.cell_id === cellId
            ? {
                ...c,
                output: result.output,
                figure_path: result.figure_paths[0] ?? null,
                status: result.status === 'ok' ? 'ok' : 'error',
              }
            : c,
        ),
      )
    } catch (err) {
      let message = err instanceof Error ? err.message : 'Error al ejecutar la celda'
      if (err instanceof ApiError && err.errorCode === 'KERNEL_DEAD') {
        message = `Motor de cálculo no disponible. Reinicia el kernel.\n${err.message}`
      }
      setCells((prev) =>
        prev.map((c) =>
          c.cell_id === cellId ? { ...c, status: 'error', output: message } : c,
        ),
      )
    }
  }

  const removeCell = async (cellId: string) => {
    if (!activePageId) return
    await deleteCell(activePageId, cellId)
    setCells((prev) => prev.filter((c) => c.cell_id !== cellId))
  }

  const moveCell = async (index: number, direction: -1 | 1) => {
    if (!activePageId) return
    const newIndex = index + direction
    if (newIndex < 0 || newIndex >= cells.length) return
    const cellId = cells[index].cell_id
    await moveCellApi(activePageId, cellId, newIndex)
    setCells((prev) => {
      const next = [...prev]
      const [moved] = next.splice(index, 1)
      next.splice(newIndex, 0, moved)
      return next
    })
  }

  const toggleCollapse = (cellId: string) => {
    setCells((prev) => prev.map((c) => (c.cell_id === cellId ? { ...c, collapsed: !c.collapsed } : c)))
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex items-center justify-between border-b px-4 py-2">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Code2 className="size-4" />
          <span>Laboratorio {activePageId ? '' : '— selecciona una página'}</span>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => addCell('python')}>
            <Plus className="mr-1 size-3.5" /> Python
          </Button>
          <Button variant="outline" size="sm" onClick={() => addCell('markdown')}>
            <FileText className="mr-1 size-3.5" /> Texto
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setLabMode(false)}>
            Volver al editor
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {!activePageId && (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-muted-foreground">
            <FileText className="size-8 opacity-50" />
            <p>Selecciona una página para empezar a experimentar.</p>
          </div>
        )}

        {activePageId && loading && (
          <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
            Cargando celdas…
          </div>
        )}

        <div className="mx-auto flex max-w-3xl flex-col gap-4">
          {cells.map((cell, index) => (
            <div
              key={cell.cell_id}
              className="group relative overflow-hidden rounded-2xl border bg-card shadow-sm transition-all duration-200 hover:shadow-md"
            >
              <div className="flex items-center justify-between border-b bg-muted/40 px-3 py-1.5">
                <div className="flex items-center gap-2">
                  <Select
                    value={cell.language}
                    onValueChange={(value) => {
                      setCells((prev) =>
                        prev.map((c) => (c.cell_id === cell.cell_id ? { ...c, language: value } : c)),
                      )
                      saveCell(cell.cell_id, value, cell.source)
                    }}
                  >
                    <SelectTrigger className="h-7 w-36 text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {LANGUAGE_OPTIONS.map((opt) => (
                        <SelectItem key={opt.value} value={opt.value} className="text-xs">
                          {opt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
                    {cell.status === 'running' ? 'ejecutando…' : cell.status === 'error' ? 'error' : cell.status === 'ok' ? 'listo' : ''}
                  </span>
                </div>
                <div className="flex items-center gap-0.5 opacity-80 transition-opacity group-hover:opacity-100">
                  <Button variant="ghost" size="icon" className="size-6" onClick={() => moveCell(index, -1)}>
                    <ChevronUp className="size-3.5" />
                  </Button>
                  <Button variant="ghost" size="icon" className="size-6" onClick={() => moveCell(index, 1)}>
                    <ChevronDown className="size-3.5" />
                  </Button>
                  <Button variant="ghost" size="icon" className="size-6" onClick={() => toggleCollapse(cell.cell_id)}>
                    {cell.collapsed ? <ChevronDown className="size-3.5" /> : <ChevronUp className="size-3.5" />}
                  </Button>
                  {cell.language === 'python' && (
                    <Button variant="ghost" size="icon" className="size-6" onClick={() => runCell(cell.cell_id)} disabled={cell.status === 'running'} title="Ejecutar celda">
                      <Play className="size-3.5" />
                    </Button>
                  )}
                  <Button variant="ghost" size="icon" className="size-6" onClick={() => removeCell(cell.cell_id)}>
                    <Trash2 className="size-3.5" />
                  </Button>
                </div>
              </div>

              {!cell.collapsed && (
                <div className="p-3">
                  <Textarea
                    value={cell.source}
                    onChange={(e) => updateSource(cell.cell_id, e.target.value)}
                    onBlur={() => saveCell(cell.cell_id, cell.language, cell.source)}
                    className="min-h-[80px] resize-y border-0 bg-transparent font-mono text-sm shadow-none focus-visible:ring-0"
                    spellCheck={false}
                    placeholder={cell.language === 'python' ? '# código Python' : 'Escribe texto o fórmulas $...$'}
                  />
                </div>
              )}

              {cell.language !== 'python' && !cell.collapsed && cell.source.trim() && (
                <div className="border-t bg-muted/20 px-3 py-2">
                  <MarkdownPreview source={cell.source} />
                </div>
              )}

              {cell.output && (
                <div className="border-t bg-muted/30 px-3 py-2">
                  <div className="mb-1 flex items-center gap-2">
                    <RotateCcw className="size-3 text-muted-foreground" />
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Output</span>
                  </div>
                  <pre className="whitespace-pre-wrap rounded-md bg-background p-2 font-mono text-xs">{cell.output}</pre>
                </div>
              )}

              {cell.figure_path && (
                <div className="border-t p-3">
                  <img
                    src={`/api/v1/pages/${activePageId}/cells/${cell.cell_id}/figure`}
                    alt="figura"
                    className="max-h-80 rounded-lg border object-contain shadow-sm"
                  />
                </div>
              )}
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
      </div>
    </div>
  )
}
