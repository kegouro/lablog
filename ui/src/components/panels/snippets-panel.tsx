import { Check, Copy, FlaskConical, Image, X } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { replacePageLatex, renderSnippet } from '@/lib/api'
import { useAppStore } from '@/stores/app-store'
import type { Snippet, SnippetParameter } from '@/types'

const PARAM_COLORS = [
  'bg-rose-400/30 text-rose-700 border-rose-400/50',
  'bg-sky-400/30 text-sky-700 border-sky-400/50',
  'bg-emerald-400/30 text-emerald-700 border-emerald-400/50',
  'bg-amber-400/30 text-amber-700 border-amber-400/50',
  'bg-violet-400/30 text-violet-700 border-violet-400/50',
  'bg-pink-400/30 text-pink-700 border-pink-400/50',
]

function templateToPlaceholders(template: string) {
  return template.replace(/\{(\w+)\}/g, '{{$1}}')
}

function colorForIndex(index: number) {
  return PARAM_COLORS[index % PARAM_COLORS.length]
}

function ParameterField({
  param,
  value,
  onChange,
}: {
  param: SnippetParameter
  value: string
  onChange: (v: string) => void
}) {
  const numeric = param.min !== undefined || param.max !== undefined || param.step !== undefined
  const id = `param-${param.name}`
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <label htmlFor={id} className="text-xs font-medium">
          {param.name}
          {param.unit ? <span className="text-muted-foreground"> ({param.unit})</span> : null}
        </label>
      </div>
      {numeric ? (
        <div className="flex items-center gap-2">
          <Input
            id={id}
            type="number"
            min={param.min}
            max={param.max}
            step={param.step ?? 'any'}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className="h-8 text-xs"
          />
        </div>
      ) : (
        <Input
          id={id}
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="h-8 text-xs"
        />
      )}
      {param.description ? (
        <p className="text-[10px] text-muted-foreground">{param.description}</p>
      ) : null}
    </div>
  )
}

function SnippetCard({ snippet }: { snippet: Snippet }) {
  const activeLatex = useAppStore((s) => s.activeLatex)
  const setActiveLatex = useAppStore((s) => s.setActiveLatex)
  const activePageId = useAppStore((s) => s.activePageId)
  const setPanel = useAppStore((s) => s.setPanel)
  const setParameterHints = useAppStore((s) => s.setParameterHints)
  const setParameterValue = useAppStore((s) => s.setParameterValue)
  const insertAtCursor = useAppStore((s) => s.insertAtCursor)
  const [open, setOpen] = useState(false)
  const [copied, setCopied] = useState(false)
  const [preview, setPreview] = useState<string | null>(null)
  const [values, setValues] = useState<Record<string, string>>(() =>
    Object.fromEntries(snippet.parameters.map((p) => [p.name, String(p.default)])),
  )

  useEffect(() => {
    if (!open) {
      setPreview(null)
      return
    }
    let cancelled = false
    renderSnippet(snippet.id, values)
      .then((code) => {
        if (!cancelled) setPreview(code)
      })
      .catch(() => setPreview(null))
    return () => {
      cancelled = true
    }
  }, [open, snippet.id, values])

  const insert = async () => {
    const code = templateToPlaceholders(snippet.template)

    // Registrar hints y valores por defecto para el panel de parámetros
    const hints = Object.fromEntries(
      snippet.parameters.map((p, i) => [
        p.name,
        {
          description: p.description || `Valor para ${p.name}`,
          default: String(p.default),
          color: colorForIndex(i),
        },
      ]),
    )
    const defaults = Object.fromEntries(snippet.parameters.map((p) => [p.name, String(p.default)]))
    setParameterHints(hints)
    for (const [name, value] of Object.entries(defaults)) {
      setParameterValue(name, values[name] ?? value)
    }

    // Inserta en el cursor (el editor persiste); si no hay editor, añade al final.
    if (insertAtCursor) {
      insertAtCursor(code)
    } else {
      const next = activeLatex ? `${activeLatex}\n${code}` : code
      setActiveLatex(next)
      if (activePageId) await replacePageLatex(activePageId, next)
    }
    setOpen(false)
    setPanel('snippets', false)
    setPanel('parameters', true)
  }

  const copy = async () => {
    const code = templateToPlaceholders(snippet.template)
    await navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 1200)
  }

  return (
    <div className="rounded-xl border bg-card p-3 transition-all hover:border-primary/30 hover:shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="flex size-7 items-center justify-center rounded-md bg-muted text-muted-foreground">
            {snippet.category === 'tikz' ? <Image className="size-3.5" /> : <FlaskConical className="size-3.5" />}
          </div>
          <div>
            <p className="text-xs font-semibold">{snippet.name}</p>
            <p className="text-[10px] text-muted-foreground line-clamp-1">{snippet.description}</p>
          </div>
        </div>
        <div className="flex gap-0.5">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="ghost" size="icon" className="size-6" onClick={copy}>
                  {copied ? <Check className="size-3" /> : <Copy className="size-3" />}
                </Button>
              </TooltipTrigger>
              <TooltipContent side="top">Copiar código</TooltipContent>
            </Tooltip>
          </TooltipProvider>
          <Button variant="ghost" size="icon" className="size-6" onClick={() => setOpen(!open)}>
            {open ? <X className="size-3" /> : <span className="text-xs">▾</span>}
          </Button>
        </div>
      </div>

      {open && (
        <div className="mt-3 space-y-3 border-t pt-3">
          <div className="grid gap-2">
            {snippet.parameters.map((param) => (
              <ParameterField
                key={param.name}
                param={param}
                value={values[param.name] ?? String(param.default)}
                onChange={(v) => setValues((prev) => ({ ...prev, [param.name]: v }))}
              />
            ))}
          </div>
          {preview !== null && (
            <div className="rounded-md border bg-muted/40 p-2">
              <p className="mb-1 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Vista previa</p>
              <pre className="max-h-32 overflow-auto whitespace-pre-wrap text-[10px] font-mono">{preview}</pre>
            </div>
          )}
          <Button size="sm" className="w-full text-xs" onClick={insert}>
            Insertar en editor
          </Button>
        </div>
      )}
    </div>
  )
}

export function SnippetsPanel() {
  const snippets = useAppStore((s) => s.snippets)
  const togglePanel = useAppStore((s) => s.togglePanel)
  const searchQuery = useAppStore((s) => s.searchQuery)
  const setSearchQuery = useAppStore((s) => s.setSearchQuery)
  const [filter, setFilter] = useState<string>('all')

  const categories = useMemo(
    () => ['all', ...Array.from(new Set(snippets.map((s) => s.category)))],
    [snippets],
  )

  const filtered = useMemo(() => {
    const q = searchQuery.toLowerCase()
    return snippets.filter((s) => {
      const matchesCategory = filter === 'all' || s.category === filter
      const matchesSearch =
        s.name.toLowerCase().includes(q) ||
        s.description.toLowerCase().includes(q) ||
        s.tags.some((t) => t.toLowerCase().includes(q))
      return matchesCategory && matchesSearch
    })
  }, [snippets, filter, searchQuery])

  return (
    <Card className="m-2 border-0 shadow-none">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div>
          <CardTitle className="text-sm font-semibold">Snippets</CardTitle>
          <p className="text-[10px] text-muted-foreground">Plantillas parametrizadas</p>
        </div>
        <Button variant="ghost" size="icon" className="size-7" onClick={() => togglePanel('snippets')}>
          <X className="size-4" />
        </Button>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <Input
          placeholder="Buscar snippet…"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="h-8 text-xs"
        />
        <div className="flex flex-wrap gap-1">
          {categories.map((cat) => (
            <Button
              key={cat}
              variant={filter === cat ? 'secondary' : 'ghost'}
              size="sm"
              className="h-6 text-[10px] capitalize"
              onClick={() => setFilter(cat)}
            >
              {cat}
            </Button>
          ))}
        </div>
        <ScrollArea className="h-[calc(100vh-16rem)]">
          <div className="flex flex-col gap-2 pr-2">
            {filtered.map((snippet) => (
              <SnippetCard key={snippet.id} snippet={snippet} />
            ))}
            {filtered.length === 0 && (
              <p className="py-4 text-center text-xs text-muted-foreground">Sin coincidencias</p>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}
