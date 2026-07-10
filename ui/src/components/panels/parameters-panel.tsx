import { X, Wand2 } from 'lucide-react'
import { useMemo } from 'react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { replacePageLatex } from '@/lib/api'
import { useAppStore } from '@/stores/app-store'

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

export function ParametersPanel() {
  const activeLatex = useAppStore((s) => s.activeLatex)
  const setActiveLatex = useAppStore((s) => s.setActiveLatex)
  const activePageId = useAppStore((s) => s.activePageId)
  const togglePanel = useAppStore((s) => s.togglePanel)
  const parameterHints = useAppStore((s) => s.parameterHints)
  const parameterValues = useAppStore((s) => s.parameterValues)
  const setParameterValue = useAppStore((s) => s.setParameterValue)

  const matches = useMemo(() => {
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

  const updateValue = (name: string, value: string) => {
    setParameterValue(name, value)
  }

  const discardPendingSave = useAppStore((s) => s.discardPendingSave)
  const setActiveVersion = useAppStore((s) => s.setActiveVersion)
  const setActiveAst = useAppStore((s) => s.setActiveAst)

  const bakeParameters = async () => {
    // Descarta autosave con placeholders sin hornear (evita carrera 300ms).
    discardPendingSave?.()
    let next = activeLatex
    for (const { name } of matches) {
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

  return (
    <Card className="m-2 border-0 shadow-none">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div>
          <CardTitle className="text-sm font-semibold">Parámetros</CardTitle>
          <p className="text-[10px] text-muted-foreground">Edita los valores de los snippets</p>
        </div>
        <Button variant="ghost" size="icon" className="size-7" onClick={() => togglePanel('parameters')}>
          <X className="size-4" />
        </Button>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {matches.length === 0 ? (
          <div className="py-6 text-center text-xs text-muted-foreground">
            No hay parámetros editables en el texto actual.
          </div>
        ) : (
          <>
            <div className="flex flex-col gap-2">
              {matches.map(({ name, count }) => {
                const hint = parameterHints[name]
                const badge = colorBadge(hint?.color)
                const goToLine = useAppStore.getState().goToLine
                const setHighlightLine = useAppStore.getState().setHighlightLine
                const numVal = Number(parameterValues[name] ?? hint?.default ?? '')
                const showRange =
                  hint?.min != null && hint?.max != null && !Number.isNaN(numVal)
                return (
                  <div key={name} className="rounded-lg border bg-card p-2">
                    <div className="mb-1.5 flex items-center gap-2">
                      <span className={`rounded border px-1.5 py-0.5 text-[10px] font-medium ${badge}`}>
                        {name}
                        {hint?.unit ? ` · ${hint.unit}` : ''}
                      </span>
                      <span className="text-[10px] text-muted-foreground">×{count}</span>
                      {hint?.highlightLine != null && (
                        <button
                          type="button"
                          className="ml-auto text-[10px] underline decoration-dotted text-muted-foreground"
                          onClick={() => {
                            goToLine?.(hint.highlightLine!)
                            setHighlightLine(hint.highlightLine!)
                          }}
                        >
                          L{hint.highlightLine}
                        </button>
                      )}
                    </div>
                    {hint?.description ? (
                      <p className="mb-1.5 text-[10px] leading-tight text-muted-foreground">
                        {hint.description}
                      </p>
                    ) : null}
                    <Input
                      type="text"
                      value={parameterValues[name] ?? hint?.default ?? ''}
                      onChange={(e) => updateValue(name, e.target.value)}
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
            <Button size="sm" className="gap-2 text-xs" onClick={bakeParameters}>
              <Wand2 className="size-3.5" />
              Congelar valores
            </Button>
            <p className="text-[10px] text-muted-foreground">
              "Congelar" reemplaza los placeholders por los valores actuales en el editor y en el guardado.
            </p>
          </>
        )}
      </CardContent>
    </Card>
  )
}
