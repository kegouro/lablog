import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { Textarea } from '@/components/ui/textarea'
import { getPage, replacePageLatex } from '@/lib/api'
import { useAppStore } from '@/stores/app-store'

function debounce<T extends (...args: never[]) => void>(fn: T, ms: number) {
  let timer: ReturnType<typeof setTimeout>
  return (...args: Parameters<T>) => {
    clearTimeout(timer)
    timer = setTimeout(() => fn(...args), ms)
  }
}

function countLines(text: string) {
  return text.split('\n').length
}

function escapeHtml(text: string) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

const PARAM_COLORS = [
  'bg-rose-400/30 text-rose-900 dark:text-rose-100 border-rose-400/40',
  'bg-sky-400/30 text-sky-900 dark:text-sky-100 border-sky-400/40',
  'bg-emerald-400/30 text-emerald-900 dark:text-emerald-100 border-emerald-400/40',
  'bg-amber-400/30 text-amber-900 dark:text-amber-100 border-amber-400/40',
  'bg-violet-400/30 text-violet-900 dark:text-violet-100 border-violet-400/40',
  'bg-pink-400/30 text-pink-900 dark:text-pink-100 border-pink-400/40',
]

function colorForName(name: string) {
  let hash = 0
  for (const ch of name) hash = (hash * 31 + ch.charCodeAt(0)) >>> 0
  return PARAM_COLORS[hash % PARAM_COLORS.length]
}

function buildOverlayHtml(text: string, hints: Record<string, { description: string }>) {
  const escaped = escapeHtml(text)
  return escaped.replace(/\{\{(\w+)\}\}/g, (_, name) => {
    const hint = hints[name]
    const colorClass = colorForName(name)
    const title = hint?.description ?? `Parámetro ${name}`
    return `<span class="inline rounded border px-1 py-0.5 text-xs font-medium ${colorClass}" title="${escapeHtml(title)}" data-param="${name}">{{${name}}}</span>`
  })
}

export function LatexEditor() {
  const {
    activePageId,
    activeLatex,
    setActiveLatex,
    setActiveAst,
    parameterHints,
  } = useAppStore()
  const [status, setStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const gutterRef = useRef<HTMLDivElement>(null)
  const overlayRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!activePageId) {
      setActiveLatex('')
      setActiveAst(undefined)
      setStatus('idle')
      return
    }
    setStatus('idle')
    getPage(activePageId)
      .then((page) => {
        setActiveLatex(page.latex)
        setActiveAst(page.ast)
      })
      .catch(() => {
        setActiveLatex('')
        setActiveAst(undefined)
      })
  }, [activePageId, setActiveLatex, setActiveAst])

  const save = useCallback(
    async (latex: string) => {
      if (!activePageId) return
      setStatus('saving')
      try {
        await replacePageLatex(activePageId, latex)
        setStatus('saved')
      } catch {
        setStatus('error')
      }
    },
    [activePageId],
  )

  const debouncedSave = useMemo(() => debounce(save, 900), [save])

  const handleChange = (value: string) => {
    setActiveLatex(value)
    setStatus('saving')
    debouncedSave(value)
  }

  const syncScroll = () => {
    if (textareaRef.current && gutterRef.current) {
      gutterRef.current.scrollTop = textareaRef.current.scrollTop
    }
    if (textareaRef.current && overlayRef.current) {
      overlayRef.current.scrollTop = textareaRef.current.scrollTop
      overlayRef.current.scrollLeft = textareaRef.current.scrollLeft
    }
  }

  const lines = useMemo(
    () => Array.from({ length: countLines(activeLatex) }, (_, i) => i + 1),
    [activeLatex],
  )

  const overlayHtml = useMemo(
    () => buildOverlayHtml(activeLatex, parameterHints),
    [activeLatex, parameterHints],
  )

  if (!activePageId) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 p-6 text-center">
        <div className="rounded-full bg-muted p-4">
          <span className="text-2xl">📝</span>
        </div>
        <div className="max-w-xs space-y-1">
          <h3 className="font-semibold">Nada seleccionado</h3>
          <p className="text-sm text-muted-foreground">
            Crea una página desde la barra lateral o pulsa <kbd className="rounded border px-1 text-xs">Ctrl+K</kbd> para buscar.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col gap-2">
        <div className="flex items-center justify-between px-1">
          <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
            Editor LaTeX
          </span>
          <div className="flex items-center gap-3">
            <span className="text-[10px] text-muted-foreground">
              {countLines(activeLatex)} líneas · {activeLatex.length} caracteres
            </span>
            <span
              className={`text-[10px] font-medium uppercase tracking-wider transition-colors ${
                status === 'error'
                  ? 'text-destructive'
                  : status === 'saved'
                    ? 'text-emerald-500'
                    : status === 'saving'
                      ? 'text-muted-foreground'
                      : 'text-transparent'
              }`}
            >
              {status === 'error' ? 'Error al guardar' : status === 'saved' ? 'Guardado' : status === 'saving' ? 'Guardando…' : '·'}
            </span>
          </div>
        </div>

        <div className="relative flex min-h-0 flex-1 overflow-hidden rounded-lg border bg-card/50 shadow-sm">
          <div
            ref={gutterRef}
            className="pointer-events-none absolute bottom-0 left-0 top-0 z-10 w-10 select-none overflow-hidden border-r bg-muted/30 py-3 pr-2 text-right font-mono text-xs leading-6 text-muted-foreground/60"
          >
            {lines.map((n) => (
              <div key={n}>{n}</div>
            ))}
          </div>

          {/* Overlay de parámetros resaltados */}
          <div
            ref={overlayRef}
            className="absolute inset-0 z-20 overflow-hidden whitespace-pre-wrap break-words py-3 pl-12 pr-4 font-mono text-sm leading-6"
            aria-hidden="true"
          >
            <div
              className="pointer-events-none"
              dangerouslySetInnerHTML={{ __html: overlayHtml }}
            />
          </div>

          <Textarea
            ref={textareaRef}
            value={activeLatex}
            onChange={(e) => handleChange(e.target.value)}
            onScroll={syncScroll}
            className="relative z-30 h-full flex-1 resize-none overflow-auto rounded-none border-0 bg-transparent py-3 pl-12 pr-4 font-mono text-sm leading-6 text-foreground shadow-none focus-visible:ring-0"
            placeholder="Escribe tu bitácora en LaTeX...\n\section{Introducción}\nLa energía se conserva: $E = mc^2$."
            spellCheck={false}
            autoComplete="off"
            autoCorrect="off"
            autoCapitalize="off"
          />
        </div>
      </div>
  )
}
