import { ArrowDown, ArrowUp, Replace, Search, X } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { getPage, replacePageLatex } from '@/lib/api'
import { parseLatex } from '@/lib/latex-parser'
import { useAppStore } from '@/stores/app-store'

function countLines(text: string) {
  return text.split('\n').length
}

function escapeHtml(text: string) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
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

const CLOSERS: Record<string, string> = { '{': '}', '(': ')', '[': ']', '$': '$' }

export function LatexEditor() {
  const {
    activePageId,
    activeLatex,
    setActiveLatex,
    setActiveAst,
    parameterHints,
    setInsertAtCursor,
    setFlushSave,
  } = useAppStore()
  const [status, setStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const gutterRef = useRef<HTMLDivElement>(null)
  const overlayRef = useRef<HTMLDivElement>(null)

  // Historial undo/redo (cubre tipeo e inserciones programáticas).
  const valueRef = useRef('')
  const undoRef = useRef<string[]>([])
  const redoRef = useRef<string[]>([])
  const lastPushRef = useRef(0)

  // Buscar / reemplazar
  const [findOpen, setFindOpen] = useState(false)
  const [findQuery, setFindQuery] = useState('')
  const [replaceText, setReplaceText] = useState('')
  const findInputRef = useRef<HTMLInputElement>(null)

  const resetHistory = (value: string) => {
    valueRef.current = value
    undoRef.current = []
    redoRef.current = []
    lastPushRef.current = 0
  }

  useEffect(() => {
    if (!activePageId) {
      setActiveLatex('')
      setActiveAst(undefined)
      setStatus('idle')
      resetHistory('')
      return
    }
    setStatus('idle')
    getPage(activePageId)
      .then((page) => {
        setActiveLatex(page.latex)
        setActiveAst(page.ast)
        resetHistory(page.latex)
      })
      .catch(() => {
        setActiveLatex('')
        setActiveAst(undefined)
        resetHistory('')
      })
  }, [activePageId, setActiveLatex, setActiveAst])

  const save = useCallback(
    async (latex: string) => {
      if (!activePageId) return
      setStatus('saving')
      try {
        const result = await replacePageLatex(activePageId, latex)
        setActiveAst(result.ast)
        setStatus('saved')
      } catch {
        setStatus('error')
      }
    },
    [activePageId, setActiveAst],
  )

  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const scheduleSave = useCallback(
    (latex: string) => {
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current)
      saveTimerRef.current = setTimeout(() => {
        saveTimerRef.current = null
        void save(latex)
      }, 600)
    },
    [save],
  )

  const flushSave = useCallback(async () => {
    if (saveTimerRef.current) {
      clearTimeout(saveTimerRef.current)
      saveTimerRef.current = null
      await save(valueRef.current)
    }
  }, [save])

  useEffect(() => {
    setFlushSave(flushSave)
    return () => setFlushSave(null)
  }, [flushSave, setFlushSave])

  const applyValue = useCallback(
    (value: string, caret?: number) => {
      valueRef.current = value
      setActiveLatex(value)
      setActiveAst(parseLatex(value))
      setStatus('saving')
      scheduleSave(value)
      if (caret != null) {
        requestAnimationFrame(() => {
          const ta = textareaRef.current
          if (ta) {
            ta.focus()
            ta.setSelectionRange(caret, caret)
          }
        })
      }
    },
    [setActiveLatex, setActiveAst, scheduleSave],
  )

  const commit = useCallback(
    (value: string, caret?: number) => {
      // Empuja el estado previo al stack de undo, coalescido por ráfagas de tipeo.
      const now = Date.now()
      if (now - lastPushRef.current >= 600 || undoRef.current.length === 0) {
        undoRef.current.push(valueRef.current)
        if (undoRef.current.length > 200) undoRef.current.shift()
      }
      lastPushRef.current = now
      redoRef.current = []
      applyValue(value, caret)
    },
    [applyValue],
  )

  const undo = useCallback(() => {
    if (undoRef.current.length === 0) return
    const prev = undoRef.current.pop() as string
    redoRef.current.push(valueRef.current)
    lastPushRef.current = 0
    applyValue(prev)
  }, [applyValue])

  const redo = useCallback(() => {
    if (redoRef.current.length === 0) return
    const next = redoRef.current.pop() as string
    undoRef.current.push(valueRef.current)
    lastPushRef.current = 0
    applyValue(next)
  }, [applyValue])

  const handleChange = (value: string) => commit(value)

  const findNext = useCallback(
    (forward = true) => {
      const ta = textareaRef.current
      if (!ta || !findQuery) return
      const hay = ta.value.toLowerCase()
      const needle = findQuery.toLowerCase()
      let idx: number
      if (forward) {
        idx = hay.indexOf(needle, ta.selectionEnd)
        if (idx === -1) idx = hay.indexOf(needle, 0) // wrap
      } else {
        idx = hay.lastIndexOf(needle, Math.max(0, ta.selectionStart - 1))
        if (idx === -1) idx = hay.lastIndexOf(needle)
      }
      if (idx === -1) return
      ta.focus()
      ta.setSelectionRange(idx, idx + findQuery.length)
    },
    [findQuery],
  )

  const replaceCurrent = useCallback(() => {
    const ta = textareaRef.current
    if (!ta || !findQuery) return
    const sel = ta.value.slice(ta.selectionStart, ta.selectionEnd)
    if (sel.toLowerCase() === findQuery.toLowerCase()) {
      const caret = ta.selectionStart + replaceText.length
      const next = ta.value.slice(0, ta.selectionStart) + replaceText + ta.value.slice(ta.selectionEnd)
      commit(next, caret)
      requestAnimationFrame(() => findNext(true))
    } else {
      findNext(true)
    }
  }, [findQuery, replaceText, commit, findNext])

  const replaceAll = useCallback(() => {
    if (!findQuery) return
    const re = new RegExp(findQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi')
    const next = valueRef.current.replace(re, replaceText)
    if (next !== valueRef.current) commit(next)
  }, [findQuery, replaceText, commit])

  const matchCount = useMemo(() => {
    if (!findQuery) return 0
    const re = new RegExp(findQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi')
    return (activeLatex.match(re) || []).length
  }, [activeLatex, findQuery])

  const openFind = useCallback(() => {
    const ta = textareaRef.current
    const sel = ta ? ta.value.slice(ta.selectionStart, ta.selectionEnd) : ''
    if (sel && !sel.includes('\n')) setFindQuery(sel)
    setFindOpen(true)
    requestAnimationFrame(() => findInputRef.current?.select())
  }, [])

  // Inserta/envuelve en la selección actual del textarea.
  const replaceSelection = useCallback(
    (before: string, after = '', placeholder = '') => {
      const ta = textareaRef.current
      if (!ta) return
      const start = ta.selectionStart
      const end = ta.selectionEnd
      const value = ta.value
      const selected = value.slice(start, end) || placeholder
      const inserted = before + selected + after
      const next = value.slice(0, start) + inserted + value.slice(end)
      // Selección: si había texto, cursor tras el cierre; si no, dentro.
      const caret = start + before.length + selected.length
      commit(next, caret)
    },
    [commit],
  )

  // Registro para que paneles de símbolos/snippets inserten en el cursor.
  useEffect(() => {
    setInsertAtCursor((text: string) => replaceSelection(text))
    return () => setInsertAtCursor(null)
  }, [replaceSelection, setInsertAtCursor])

  // Resincroniza el baseline de undo si activeLatex cambia por fuera (dictado).
  useEffect(() => {
    if (activeLatex !== valueRef.current) valueRef.current = activeLatex
  }, [activeLatex])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    const ta = e.currentTarget
    const mod = e.metaKey || e.ctrlKey

    if (mod && e.key.toLowerCase() === 'z') {
      e.preventDefault()
      if (e.shiftKey) redo()
      else undo()
      return
    }
    if (mod && e.key.toLowerCase() === 'y') {
      e.preventDefault()
      redo()
      return
    }
    if (mod && (e.key.toLowerCase() === 'f' || e.key.toLowerCase() === 'h')) {
      e.preventDefault()
      openFind()
      return
    }
    if (e.key === 'Escape' && findOpen) {
      setFindOpen(false)
      return
    }
    if (e.key === 'Tab') {
      e.preventDefault()
      replaceSelection('  ')
      return
    }
    if (mod && e.key.toLowerCase() === 'b') {
      e.preventDefault()
      replaceSelection('\\textbf{', '}', 'texto')
      return
    }
    if (mod && e.key.toLowerCase() === 'i') {
      e.preventDefault()
      replaceSelection('\\textit{', '}', 'texto')
      return
    }
    if (mod && e.key.toLowerCase() === 'e') {
      e.preventDefault()
      replaceSelection('$', '$', 'x')
      return
    }
    // Auto-cierre de delimitadores al rodear una selección.
    if (CLOSERS[e.key] && ta.selectionStart !== ta.selectionEnd) {
      e.preventDefault()
      replaceSelection(e.key, CLOSERS[e.key])
    }
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

        {findOpen && (
          <div className="flex flex-wrap items-center gap-1.5 rounded-lg border bg-card/80 p-1.5 shadow-sm">
            <div className="relative">
              <Search className="absolute left-2 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
              <Input
                ref={findInputRef}
                value={findQuery}
                onChange={(e) => setFindQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    findNext(!e.shiftKey)
                  } else if (e.key === 'Escape') {
                    setFindOpen(false)
                  }
                }}
                placeholder="Buscar…"
                className="h-7 w-40 pl-7 text-xs"
              />
            </div>
            <span className="min-w-10 text-center text-[10px] tabular-nums text-muted-foreground">
              {matchCount}
            </span>
            <Button variant="ghost" size="icon" className="size-7" title="Anterior" onClick={() => findNext(false)}>
              <ArrowUp className="size-3.5" />
            </Button>
            <Button variant="ghost" size="icon" className="size-7" title="Siguiente (Enter)" onClick={() => findNext(true)}>
              <ArrowDown className="size-3.5" />
            </Button>
            <div className="relative">
              <Replace className="absolute left-2 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={replaceText}
                onChange={(e) => setReplaceText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    replaceCurrent()
                  } else if (e.key === 'Escape') {
                    setFindOpen(false)
                  }
                }}
                placeholder="Reemplazar…"
                className="h-7 w-40 pl-7 text-xs"
              />
            </div>
            <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={replaceCurrent}>
              Uno
            </Button>
            <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={replaceAll}>
              Todo
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="ml-auto size-7"
              title="Cerrar (Esc)"
              onClick={() => setFindOpen(false)}
            >
              <X className="size-3.5" />
            </Button>
          </div>
        )}

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
            onKeyDown={handleKeyDown}
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
