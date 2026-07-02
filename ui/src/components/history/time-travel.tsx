import { Clock, GitCompare, RotateCcw, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Slider } from '@/components/ui/slider'
import { getHistory, getPageAt, restoreVersion, type HistoryEvent } from '@/lib/api'
import { diffLines } from '@/lib/diff'
import { renderDocument } from '@/lib/latex-render'
import { useAppStore } from '@/stores/app-store'
import type { Page } from '@/types'

interface TimeTravelOverlayProps {
  pageId: string
  onClose: () => void
}

export function TimeTravelOverlay({ pageId, onClose }: TimeTravelOverlayProps) {
  const { parameterValues, activeLatex, setActiveLatex, setActiveAst, flushSave } = useAppStore()
  const [history, setHistory] = useState<HistoryEvent[]>([])
  const [index, setIndex] = useState(0)
  const [snapshot, setSnapshot] = useState<Page | null>(null)
  const [restoring, setRestoring] = useState(false)
  const [showDiff, setShowDiff] = useState(false)
  const pendingIndexRef = useRef(0)
  const scrubTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    return () => {
      if (scrubTimerRef.current) clearTimeout(scrubTimerRef.current)
    }
  }, [])

  useEffect(() => {
    getHistory(pageId)
      .then((h) => {
        setHistory(h)
        const last = Math.max(0, h.length - 1)
        setIndex(last)
        pendingIndexRef.current = last
        return getPageAt(pageId, last)
      })
      .then(setSnapshot)
      .catch(() => toast.error('No se pudo cargar la historia'))
  }, [pageId])

  const scrub = (k: number) => {
    setIndex(k)
    if (scrubTimerRef.current) clearTimeout(scrubTimerRef.current)
    scrubTimerRef.current = setTimeout(async () => {
      pendingIndexRef.current = k
      try {
        const page = await getPageAt(pageId, k)
        if (pendingIndexRef.current === k) setSnapshot(page)
      } catch {
        toast.error('No se pudo cargar esa versión')
      }
    }, 200)
  }

  const handleRestore = async () => {
    setRestoring(true)
    try {
      if (flushSave) await flushSave()
      const page = await restoreVersion(pageId, index)
      setActiveLatex(page.latex)
      setActiveAst(page.ast)
      toast.success(`Versión del evento ${index} restaurada`)
      onClose()
    } catch {
      toast.error('No se pudo restaurar')
    } finally {
      setRestoring(false)
    }
  }

  const selected = history[index]
  const html = snapshot ? renderDocument(snapshot.ast, pageId, parameterValues) : ''

  return (
    <div className="absolute inset-0 z-40 flex flex-col rounded-lg border bg-card shadow-lg">
      <div className="flex items-center justify-between border-b px-3 py-1.5">
        <span className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
          <Clock className="size-3.5" /> Historia
        </span>
        <Button variant="ghost" size="icon" className="size-6" onClick={onClose} title="Cerrar">
          <X className="size-3.5" />
        </Button>
      </div>

      <div className="flex min-h-0 flex-1">
        <ScrollArea className="w-56 shrink-0 border-r">
          <ul className="p-1.5 text-xs">
            {history.map((e) => (
              <li key={e.index}>
                <button
                  type="button"
                  onClick={() => scrub(e.index)}
                  className={`w-full rounded px-2 py-1 text-left transition-colors ${
                    e.index === index ? 'bg-primary/15 text-primary' : 'hover:bg-muted'
                  }`}
                >
                  <span className="font-mono">{e.index}</span> · {e.type.replace(/_/g, ' ')}
                  {e.summary && (
                    <span className="block truncate text-muted-foreground">{e.summary}</span>
                  )}
                </button>
              </li>
            ))}
          </ul>
        </ScrollArea>
        {showDiff && snapshot ? (
          <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
            <p className="shrink-0 px-3 pt-2 text-[10px] text-muted-foreground">
              Cambios desde esta versión hasta el estado actual
            </p>
            <div className="min-w-0 flex-1 overflow-auto p-3 font-mono text-xs leading-5">
              {(() => {
                const diff = diffLines(snapshot.latex, activeLatex)
                if (!diff) return <p className="text-muted-foreground">Documento muy grande para diff.</p>
                return diff.map((l, idx) => (
                  <div
                    key={idx}
                    className={
                      l.kind === 'add'
                        ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
                        : l.kind === 'del'
                          ? 'bg-rose-500/15 text-rose-700 dark:text-rose-300 line-through decoration-1'
                          : 'text-muted-foreground'
                    }
                  >
                    <span className="select-none pr-2">{l.kind === 'add' ? '+' : l.kind === 'del' ? '−' : ' '}</span>
                    {l.text || ' '}
                  </div>
                ))
              })()}
            </div>
          </div>
        ) : (
          <div
            className="min-w-0 flex-1 overflow-auto p-4 text-sm"
            dangerouslySetInnerHTML={{ __html: html }}
          />
        )}
      </div>

      <div className="flex items-center gap-3 border-t px-3 py-2">
        <Slider
          value={[index]}
          min={0}
          max={Math.max(0, history.length - 1)}
          step={1}
          onValueChange={([v]) => scrub(v)}
          className="flex-1"
        />
        <span className="w-40 shrink-0 text-right text-[10px] tabular-nums text-muted-foreground">
          {history.length > 0 ? `evento ${index + 1}/${history.length}` : '—'}
          {selected && ` · ${new Date(selected.timestamp).toLocaleString()}`}
        </span>
        <Button
          variant={showDiff ? 'secondary' : 'outline'}
          size="sm"
          className="h-7 gap-1.5 text-xs"
          onClick={() => setShowDiff((v) => !v)}
        >
          <GitCompare className="size-3.5" />
          Diff
        </Button>
        <Button size="sm" className="h-7 gap-1.5 text-xs" disabled={restoring} onClick={handleRestore}>
          <RotateCcw className="size-3.5" />
          Restaurar
        </Button>
      </div>
    </div>
  )
}
