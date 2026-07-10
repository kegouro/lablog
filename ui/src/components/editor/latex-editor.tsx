import { ArrowDown, ArrowUp, Replace, Search, X } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { usePageUpdate } from '@/hooks/use-page-update'
import { getPage } from '@/lib/api'
import {
  completionPrefix,
  fetchSuggestions,
  type CompletionItem,
} from '@/lib/latex-completions'
import { useAppStore } from '@/stores/app-store'
import type { Page } from '@/types'

function countLines(text: string) {
  return text.split('\n').length
}

const PARAM_COLORS = [
  'bg-rose-400/30 text-rose-900 dark:text-rose-100 border-rose-400/40',
  'bg-sky-400/30 text-sky-900 dark:text-sky-100 border-sky-400/40',
  'bg-emerald-400/30 text-emerald-900 dark:text-emerald-100 border-emerald-400/40',
  'bg-amber-400/30 text-amber-900 dark:text-amber-100 border-amber-400/40',
  'bg-violet-400/30 text-violet-900 dark:text-violet-100 border-violet-400/40',
  'bg-pink-400/30 text-pink-900 dark:text-rose-100 border-pink-400/40',
]

function colorForName(name: string) {
  let hash = 0
  for (const ch of name) hash = (hash * 31 + ch.charCodeAt(0)) >>> 0
  return PARAM_COLORS[hash % PARAM_COLORS.length]
}

/** Overlay de parámetros como nodos React (sin HTML de usuario). */
function buildOverlayNodes(text: string, hints: Record<string, { description: string }>) {
  const parts: React.ReactNode[] = []
  const re = /\{\{(\w+)\}\}/g
  let last = 0
  let m: RegExpExecArray | null
  let i = 0
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) {
      parts.push(<span key={`t-${i++}`}>{text.slice(last, m.index)}</span>)
    }
    const name = m[1]
    const hint = hints[name]
    const colorClass = colorForName(name)
    const title = hint?.description ?? `Parámetro ${name}`
    parts.push(
      <span
        key={`p-${i++}`}
        className={`inline rounded border px-1 py-0.5 text-xs font-medium ${colorClass}`}
        title={title}
        data-param={name}
      >
        {`{{${name}}}`}
      </span>,
    )
    last = m.index + m[0].length
  }
  if (last < text.length) {
    parts.push(<span key={`t-${i++}`}>{text.slice(last)}</span>)
  }
  return parts
}

const CLOSERS: Record<string, string> = { '{': '}', '(': ')', '[': ']', '$': '$' }

export function LatexEditor() {
  const activePageId = useAppStore((s) => s.activePageId)
  const activeLatex = useAppStore((s) => s.activeLatex)
  const setActiveLatex = useAppStore((s) => s.setActiveLatex)
  const setActiveAst = useAppStore((s) => s.setActiveAst)
  const parameterHints = useAppStore((s) => s.parameterHints)
  const setInsertAtCursor = useAppStore((s) => s.setInsertAtCursor)
  const setFlushSave = useAppStore((s) => s.setFlushSave)
  const setDiscardPendingSave = useAppStore((s) => s.setDiscardPendingSave)
  const setGoToLine = useAppStore((s) => s.setGoToLine)

  const setActiveVersion = useAppStore((s) => s.setActiveVersion)

  const onUpdate = useCallback(
    (page: Page) => {
      setActiveAst(page.ast)
      setActiveVersion(page.version)
    },
    [setActiveAst, setActiveVersion],
  )

  const getVersion = useCallback(
    () => useAppStore.getState().activeVersion || undefined,
    [],
  )

  const { status, updateRaw, flush, discardPending } = usePageUpdate(
    activePageId,
    onUpdate,
    getVersion,
  )

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
  const [completions, setCompletions] = useState<CompletionItem[]>([])
  const [completionIndex, setCompletionIndex] = useState(0)
  const [completionOpen, setCompletionOpen] = useState(false)
  const completionTokenRef = useRef(0)

  const resetHistory = useCallback((value: string) => {
    valueRef.current = value
    undoRef.current = []
    redoRef.current = []
    lastPushRef.current = 0
  }, [])

  useEffect(() => {
    if (!activePageId) {
      setActiveLatex('')
      setActiveAst(undefined)
      setActiveVersion(0)
      resetHistory('')
      return
    }
    let cancelled = false
    const requestedId = activePageId
    getPage(requestedId)
      .then((page) => {
        if (cancelled || useAppStore.getState().activePageId !== requestedId) return
        setActiveLatex(page.latex)
        setActiveAst(page.ast)
        setActiveVersion(page.version)
        resetHistory(page.latex)
      })
      .catch(() => {
        if (cancelled || useAppStore.getState().activePageId !== requestedId) return
        setActiveLatex('')
        setActiveAst(undefined)
        setActiveVersion(0)
        resetHistory('')
      })
    return () => {
      cancelled = true
    }
  }, [activePageId, setActiveLatex, setActiveAst, setActiveVersion, resetHistory])

  const wrappedFlush = useCallback(async () => {
    await flush()
  }, [flush])

  useEffect(() => {
    setFlushSave(wrappedFlush)
    setDiscardPendingSave(discardPending)
    return () => {
      setFlushSave(null)
      setDiscardPendingSave(null)
    }
  }, [wrappedFlush, discardPending, setFlushSave, setDiscardPendingSave])

  const setHighlightLine = useAppStore((s) => s.setHighlightLine)
  const highlightLine = useAppStore((s) => s.highlightLine)

  const goToLine = useCallback(
    (line: number) => {
      const ta = textareaRef.current
      if (!ta) return
      const lines = ta.value.split('\n')
      const clamped = Math.max(1, Math.min(line, lines.length))
      const start = lines.slice(0, clamped - 1).reduce((n, l) => n + l.length + 1, 0)
      ta.focus()
      ta.setSelectionRange(start, start + (lines[clamped - 1]?.length ?? 0))
      ta.scrollTop = Math.max(0, (clamped - 3) * 24) // leading-6 = 24px por línea
      setHighlightLine(clamped)
      window.setTimeout(() => {
        if (useAppStore.getState().highlightLine === clamped) {
          setHighlightLine(null)
        }
      }, 2500)
    },
    [setHighlightLine],
  )

  useEffect(() => {
    setGoToLine(goToLine)
    return () => setGoToLine(null)
  }, [goToLine, setGoToLine])

  const applyValue = useCallback(
    (value: string, caret?: number) => {
      valueRef.current = value
      setActiveLatex(value)
      updateRaw(value)
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
    [setActiveLatex, updateRaw],
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

  const applyCompletion = useCallback(
    (item: CompletionItem) => {
      const ta = textareaRef.current
      if (!ta) return
      const caret = ta.selectionStart
      const value = ta.value
      const before = value.slice(0, caret)
      const m = before.match(/\\[A-Za-z]*$/)
      if (!m) return
      const start = caret - m[0].length
      const next = value.slice(0, start) + item.insert + value.slice(caret)
      const newCaret = start + item.insert.length
      commit(next, newCaret)
      setCompletionOpen(false)
      setCompletions([])
    },
    [commit],
  )

  const handleChange = (value: string) => {
    commit(value)
    const ta = textareaRef.current
    if (!ta) return
    const caret = ta.selectionStart
    const prefix = completionPrefix(value, caret)
    if (prefix === null) {
      setCompletionOpen(false)
      return
    }
    const token = ++completionTokenRef.current
    void fetchSuggestions(prefix).then((items) => {
      if (token !== completionTokenRef.current) return
      setCompletions(items)
      setCompletionIndex(0)
      setCompletionOpen(items.length > 0)
    })
  }

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

    if (completionOpen && completions.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setCompletionIndex((i) => (i + 1) % completions.length)
        return
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault()
        setCompletionIndex((i) => (i - 1 + completions.length) % completions.length)
        return
      }
      if (e.key === 'Enter' || e.key === 'Tab') {
        e.preventDefault()
        applyCompletion(completions[completionIndex] ?? completions[0])
        return
      }
      if (e.key === 'Escape') {
        e.preventDefault()
        setCompletionOpen(false)
        return
      }
    }

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

  const overlayNodes = useMemo(
    () => buildOverlayNodes(activeLatex, parameterHints),
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
            <div
              key={n}
              className={
                highlightLine === n
                  ? 'bg-destructive/25 font-semibold text-destructive'
                  : undefined
              }
            >
              {n}
            </div>
          ))}
        </div>

        {/* Overlay de parámetros resaltados */}
        <div
          ref={overlayRef}
          className="absolute inset-0 z-20 overflow-hidden whitespace-pre-wrap break-words py-3 pl-12 pr-4 font-mono text-sm leading-6"
          aria-hidden="true"
        >
          <div className="pointer-events-none text-transparent">{overlayNodes}</div>
        </div>

        <Textarea
          ref={textareaRef}
          value={activeLatex}
          onChange={(e) => handleChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onScroll={syncScroll}
          className="relative z-30 h-full flex-1 resize-none overflow-auto rounded-none border-0 bg-transparent py-3 pl-12 pr-4 font-mono text-sm leading-6 text-foreground shadow-none focus-visible:ring-0"
          placeholder="Escribe tu bitácora en LaTeX...\n\\section{Introducción}\nLa energía se conserva: $E = mc^2$."
          spellCheck={false}
          autoComplete="off"
          autoCorrect="off"
          autoCapitalize="off"
        />

        {completionOpen && completions.length > 0 && (
          <div className="absolute bottom-2 left-12 z-40 max-h-48 w-72 overflow-auto rounded-md border bg-popover p-1 text-xs shadow-lg">
            {completions.map((c, i) => (
              <button
                key={`${c.label}-${i}`}
                type="button"
                className={`flex w-full flex-col items-start rounded px-2 py-1 text-left ${
                  i === completionIndex ? 'bg-accent' : 'hover:bg-muted'
                }`}
                onMouseDown={(ev) => {
                  ev.preventDefault()
                  applyCompletion(c)
                }}
              >
                <span className="font-mono font-medium">{c.label}</span>
                <span className="text-[10px] text-muted-foreground">
                  {c.kind}
                  {c.detail ? ` · ${c.detail}` : ''}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
