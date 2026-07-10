import { Play, RefreshCw, Wand2, X } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import {
  applyDiagramParams,
  diagramSimulateSource,
  insertCell,
  replacePageLatex,
  type DiagramExpandResult,
} from '@/lib/api'
import { useAppStore, type ParameterHint } from '@/stores/app-store'

const PLACEHOLDER_RE = /\{\{(\w+)\}\}/g

const COLOR_BADGE: Record<string, string> = {
  amber: 'bg-amber-400/20 text-amber-900 dark:text-amber-100 border-amber-400/40',
  sky: 'bg-sky-400/20 text-sky-900 dark:text-sky-100 border-sky-400/40',
  rose: 'bg-rose-400/20 text-rose-900 dark:text-rose-100 border-rose-400/40',
  emerald: 'bg-emerald-400/20 text-emerald-900 dark:text-emerald-100 border-emerald-400/40',
  violet: 'bg-violet-400/20 text-violet-900 dark:text-violet-100 border-violet-400/40',
}

function colorBadge(color?: string) {
  return COLOR_BADGE[color ?? ''] ?? 'bg-muted text-foreground border-border'
}

function logSliderPos(value: number, min: number, max: number): number {
  const a = Math.log(Math.max(min, 1e-30))
  const b = Math.log(Math.max(max, min * 1.0001))
  const v = Math.log(Math.max(value, min))
  return Math.round(((v - a) / (b - a)) * 1000)
}

function logSliderValue(pos: number, min: number, max: number): number {
  const a = Math.log(Math.max(min, 1e-30))
  const b = Math.log(Math.max(max, min * 1.0001))
  return Math.exp(a + (pos / 1000) * (b - a))
}

function hintsFromExpand(
  result: DiagramExpandResult,
): Record<string, ParameterHint> {
  const hints: Record<string, ParameterHint> = {}
  for (const p of result.param_specs) {
    hints[p.id] = {
      description: p.description,
      default: String(result.params[p.id] ?? p.value),
      color: p.highlight?.color ?? 'amber',
      unit: p.unit || undefined,
      min: p.min ?? undefined,
      max: p.max ?? undefined,
      scale: p.scale,
      highlightLine: p.highlight?.line ?? undefined,
      highlightTikz: p.highlight?.tikz ?? undefined,
      highlightLatex: p.highlight?.latex ?? undefined,
    }
  }
  return hints
}

/** Localiza la línea del parámetro en el LaTeX (editor + gutter). */
function findParamLine(
  latex: string,
  name: string,
  hint?: ParameterHint,
): number | null {
  if (hint?.highlightLine != null && hint.highlightLine > 0) {
    return hint.highlightLine
  }
  const lines = latex.split('\n')
  const paramRe = new RegExp(`%\\s*lablog-param:\\s*${name}\\s*=`)
  for (let i = 0; i < lines.length; i++) {
    if (paramRe.test(lines[i])) return i + 1
  }
  if (hint?.highlightTikz) {
    const nameRe = new RegExp(`name\\s*=\\s*${hint.highlightTikz}\\b`)
    for (let i = 0; i < lines.length; i++) {
      if (nameRe.test(lines[i])) return i + 1
    }
  }
  if (hint?.highlightLatex) {
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes(hint.highlightLatex)) return i + 1
    }
  }
  return null
}

function highlightLegend(hint?: ParameterHint): string | null {
  if (!hint) return null
  const parts: string[] = []
  if (hint.highlightTikz) parts.push(`nodo ${hint.highlightTikz}`)
  if (hint.highlightLine != null) parts.push(`L${hint.highlightLine}`)
  else if (hint.highlightLatex) parts.push(`“${hint.highlightLatex}”`)
  if (parts.length === 0) return null
  return `Resalta: ${parts.join(' · ')}`
}

export function ParametersPanel() {
  const activeLatex = useAppStore((s) => s.activeLatex)
  const setActiveLatex = useAppStore((s) => s.setActiveLatex)
  const activePageId = useAppStore((s) => s.activePageId)
  const togglePanel = useAppStore((s) => s.togglePanel)
  const parameterHints = useAppStore((s) => s.parameterHints)
  const parameterValues = useAppStore((s) => s.parameterValues)
  const setParameterValue = useAppStore((s) => s.setParameterValue)
  const setParameterHints = useAppStore((s) => s.setParameterHints)
  const activeDiagramPresetId = useAppStore((s) => s.activeDiagramPresetId)
  const setActiveDiagramPresetId = useAppStore((s) => s.setActiveDiagramPresetId)
  const discardPendingSave = useAppStore((s) => s.discardPendingSave)
  const setActiveVersion = useAppStore((s) => s.setActiveVersion)
  const setActiveAst = useAppStore((s) => s.setActiveAst)
  const setPanel = useAppStore((s) => s.setPanel)

  const [busy, setBusy] = useState(false)
  const [hydrating, setHydrating] = useState(false)

  const hasDiagramMarkers = useMemo(
    () => /%\s*lablog-diagram:/.test(activeLatex) || /%\s*lablog-param:/.test(activeLatex),
    [activeLatex],
  )

  const placeholderMatches = useMemo(() => {
    const seen = new Set<string>()
    const result: { name: string; count: number }[] = []
    for (const m of activeLatex.matchAll(PLACEHOLDER_RE)) {
      const name = m[1]
      if (!seen.has(name)) {
        seen.add(name)
        result.push({ name, count: 1 })
      } else {
        const item = result.find((r) => r.name === name)
        if (item) item.count++
      }
    }
    return result
  }, [activeLatex])

  /** Unión de placeholders {{}} y hints de diagrama (ya horneados). */
  const paramEntries = useMemo(() => {
    const byName = new Map<string, { name: string; count: number; source: 'placeholder' | 'diagram' }>()
    for (const m of placeholderMatches) {
      byName.set(m.name, { name: m.name, count: m.count, source: 'placeholder' })
    }
    for (const name of Object.keys(parameterHints)) {
      if (!byName.has(name)) {
        byName.set(name, { name, count: 1, source: 'diagram' })
      }
    }
    return [...byName.values()]
  }, [placeholderMatches, parameterHints])

  const isDiagramMode =
    hasDiagramMarkers || Boolean(activeDiagramPresetId) || paramEntries.some((p) => p.source === 'diagram')

  // Hidrata sliders al abrir una página que ya tiene lablog-diagram.
  useEffect(() => {
    if (!hasDiagramMarkers) return
    if (Object.keys(parameterHints).length > 0) return
    if (hydrating) return
    let cancelled = false
    setHydrating(true)
    applyDiagramParams(activeLatex)
      .then((result) => {
        if (cancelled) return
        const hints = hintsFromExpand(result)
        setParameterHints(hints)
        for (const [k, v] of Object.entries(result.params)) {
          setParameterValue(k, String(v))
        }
        setActiveDiagramPresetId(result.preset_id)
      })
      .catch(() => {
        /* sin preset o red caída: panel vacío es aceptable */
      })
      .finally(() => {
        if (!cancelled) setHydrating(false)
      })
    return () => {
      cancelled = true
    }
    // Solo al detectar markers sin hints; no re-hidratar en cada keystroke.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasDiagramMarkers, activePageId])

  const updateValue = (name: string, value: string) => {
    setParameterValue(name, value)
  }

  const collectNumericParams = useCallback((): Record<string, number> => {
    const out: Record<string, number> = {}
    for (const { name } of paramEntries) {
      const raw = parameterValues[name] ?? parameterHints[name]?.default
      if (raw == null || raw === '') continue
      const n = Number(raw)
      if (!Number.isNaN(n)) out[name] = n
    }
    return out
  }, [paramEntries, parameterValues, parameterHints])

  const bakePlaceholders = async () => {
    discardPendingSave?.()
    let next = activeLatex
    for (const { name } of placeholderMatches) {
      const value = parameterValues[name] ?? parameterHints[name]?.default ?? `{{${name}}}`
      next = next.replaceAll(`{{${name}}}`, value)
    }
    setActiveLatex(next)
    if (activePageId) {
      const version = useAppStore.getState().activeVersion || undefined
      const result = await replacePageLatex(activePageId, next, version)
      setActiveAst(result.ast)
      setActiveVersion(result.version)
    }
  }

  const reapplyDiagram = async (withSim: boolean) => {
    if (!activePageId) {
      toast.info('Selecciona una página primero')
      return
    }
    setBusy(true)
    try {
      discardPendingSave?.()
      const params = collectNumericParams()
      const applied = await applyDiagramParams(
        activeLatex,
        params,
        activeDiagramPresetId ?? undefined,
      )
      setActiveLatex(applied.document_latex)
      const version = useAppStore.getState().activeVersion || undefined
      const page = await replacePageLatex(activePageId, applied.document_latex, version)
      setActiveAst(page.ast)
      setActiveVersion(page.version)
      setActiveDiagramPresetId(applied.preset_id)
      const hints = hintsFromExpand(applied)
      setParameterHints(hints)
      for (const [k, v] of Object.entries(applied.params)) {
        setParameterValue(k, String(v))
      }

      if (withSim && applied.has_simulation) {
        const sim = await diagramSimulateSource(applied.preset_id, applied.params)
        await insertCell(activePageId, {
          cell_id: crypto.randomUUID(),
          language: 'python',
          source: sim.source,
        })
        setPanel('cells', true)
        toast.success('Diagrama actualizado + nueva celda de simulación')
      } else {
        toast.success(`Diagrama actualizado (${applied.title})`)
      }
    } catch (err) {
      console.error(err)
      toast.error('No se pudo reaplicar el diagrama')
    } finally {
      setBusy(false)
    }
  }

  const onPrimaryAction = async () => {
    if (placeholderMatches.length > 0 && !hasDiagramMarkers) {
      await bakePlaceholders()
      toast.success('Valores congelados')
      return
    }
    if (isDiagramMode) {
      await reapplyDiagram(false)
      return
    }
    await bakePlaceholders()
  }

  return (
    <Card className="m-2 border-0 shadow-none">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div>
          <CardTitle className="text-sm font-semibold">Parámetros</CardTitle>
          <p className="text-[10px] text-muted-foreground">
            {isDiagramMode
              ? 'Ajusta el diagrama y reaplica (TikZ + lablog-param)'
              : 'Edita los valores de los snippets'}
          </p>
        </div>
        <Button variant="ghost" size="icon" className="size-7" onClick={() => togglePanel('parameters')}>
          <X className="size-4" />
        </Button>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {paramEntries.length === 0 ? (
          <div className="py-6 text-center text-xs text-muted-foreground">
            {hydrating
              ? 'Cargando parámetros del diagrama…'
              : 'No hay parámetros editables en el texto actual.'}
          </div>
        ) : (
          <>
            <div className="flex flex-col gap-2">
              {paramEntries.map(({ name, count, source }) => {
                const hint = parameterHints[name]
                const badge = colorBadge(hint?.color)
                const goToLine = useAppStore.getState().goToLine
                const setHighlightLine = useAppStore.getState().setHighlightLine
                const numVal = Number(parameterValues[name] ?? hint?.default ?? '')
                const showRange =
                  hint?.min != null && hint?.max != null && !Number.isNaN(numVal)
                const legend = highlightLegend(hint)
                const focusEditor = () => {
                  const line = findParamLine(activeLatex, name, hint)
                  if (line != null) {
                    goToLine?.(line)
                    setHighlightLine(line)
                  }
                }
                return (
                  <div
                    key={name}
                    className="rounded-lg border bg-card p-2 transition-shadow focus-within:ring-1 focus-within:ring-primary/40"
                    onFocus={focusEditor}
                  >
                    <div className="mb-1.5 flex items-center gap-2">
                      <span className={`rounded border px-1.5 py-0.5 text-[10px] font-medium ${badge}`}>
                        {name}
                        {hint?.unit ? ` · ${hint.unit}` : ''}
                      </span>
                      <span className="text-[10px] text-muted-foreground">
                        {source === 'placeholder' ? `×${count}` : 'diagrama'}
                      </span>
                      <button
                        type="button"
                        className="ml-auto text-[10px] underline decoration-dotted text-muted-foreground"
                        onClick={focusEditor}
                      >
                        {hint?.highlightLine != null
                          ? `L${hint.highlightLine}`
                          : hint?.highlightTikz
                            ? hint.highlightTikz
                            : 'ir'}
                      </button>
                    </div>
                    {hint?.description ? (
                      <p className="mb-1 text-[10px] leading-tight text-muted-foreground">
                        {hint.description}
                      </p>
                    ) : null}
                    {legend ? (
                      <p className="mb-1.5 text-[10px] font-medium text-muted-foreground/90">
                        {legend}
                      </p>
                    ) : null}
                    <Input
                      type="text"
                      value={parameterValues[name] ?? hint?.default ?? ''}
                      onChange={(e) => updateValue(name, e.target.value)}
                      onFocus={focusEditor}
                      className="h-8 text-xs"
                      placeholder={`Valor para ${name}`}
                    />
                    {showRange && (
                      <>
                        <input
                          type="range"
                          className="mt-2 w-full accent-primary"
                          min={hint.scale === 'log' ? 0 : hint.min!}
                          max={hint.scale === 'log' ? 1000 : hint.max!}
                          step={hint.scale === 'log' ? 1 : undefined}
                          value={
                            hint.scale === 'log'
                              ? logSliderPos(numVal, hint.min!, hint.max!)
                              : numVal
                          }
                          onChange={(e) => {
                            const raw = Number(e.target.value)
                            const v =
                              hint.scale === 'log'
                                ? logSliderValue(raw, hint.min!, hint.max!)
                                : raw
                            updateValue(name, String(v))
                          }}
                          onPointerDown={focusEditor}
                        />
                        <p className="mt-0.5 text-[10px] text-muted-foreground">
                          Rango {hint.min} … {hint.max}
                          {hint.scale === 'log' ? ' (log)' : ''}
                        </p>
                      </>
                    )}
                  </div>
                )
              })}
            </div>
            <div className="flex flex-col gap-1.5">
              <Button
                size="sm"
                className="gap-2 text-xs"
                disabled={busy}
                onClick={() => void onPrimaryAction()}
              >
                {isDiagramMode ? (
                  <>
                    <RefreshCw className={`size-3.5 ${busy ? 'animate-spin' : ''}`} />
                    Reaplicar diagrama
                  </>
                ) : (
                  <>
                    <Wand2 className="size-3.5" />
                    Congelar valores
                  </>
                )}
              </Button>
              {isDiagramMode && (
                <Button
                  size="sm"
                  variant="outline"
                  className="gap-2 text-xs"
                  disabled={busy}
                  onClick={() => void reapplyDiagram(true)}
                >
                  <Play className="size-3.5" />
                  Reaplicar + sim
                </Button>
              )}
            </div>
            <p className="text-[10px] text-muted-foreground">
              {isDiagramMode
                ? 'Reaplica regenera el TikZ con los sliders y actualiza % lablog-param. “+ sim” inserta una celda Jupyter nueva.'
                : '"Congelar" reemplaza los placeholders por los valores actuales en el editor y en el guardado.'}
            </p>
          </>
        )}
      </CardContent>
    </Card>
  )
}
