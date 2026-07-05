import { X, Wand2 } from 'lucide-react'
import { useMemo } from 'react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { replacePageLatex } from '@/lib/api'
import { useAppStore } from '@/stores/app-store'

const PLACEHOLDER_RE = /\{\{(\w+)\}\}/g

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

  const bakeParameters = async () => {
    let next = activeLatex
    for (const { name } of matches) {
      const value = parameterValues[name] ?? parameterHints[name]?.default ?? `{{${name}}}`
      next = next.replaceAll(`{{${name}}}`, value)
    }
    setActiveLatex(next)
    if (activePageId) {
      await replacePageLatex(activePageId, next)
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
                const colorClass = hint?.color ?? 'bg-muted text-foreground border-border'
                return (
                  <div key={name} className="rounded-lg border bg-card p-2">
                    <div className="mb-1.5 flex items-center gap-2">
                      <span className={`rounded border px-1.5 py-0.5 text-[10px] font-medium ${colorClass}`}>
                        {name}
                      </span>
                      <span className="text-[10px] text-muted-foreground">×{count}</span>
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
