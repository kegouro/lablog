import { CircuitBoard, FlaskConical, Play, X } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  diagramSimulateSource,
  expandDiagramPreset,
  insertCell,
  listDiagramPresets,
  replacePageLatex,
  type DiagramPresetSummary,
} from '@/lib/api'
import { useAppStore, type ParameterHint } from '@/stores/app-store'

export function DiagramsPanel() {
  const togglePanel = useAppStore((s) => s.togglePanel)
  const activePageId = useAppStore((s) => s.activePageId)
  const setActiveLatex = useAppStore((s) => s.setActiveLatex)
  const setActiveAst = useAppStore((s) => s.setActiveAst)
  const setActiveVersion = useAppStore((s) => s.setActiveVersion)
  const setParameterHints = useAppStore((s) => s.setParameterHints)
  const setParameterValue = useAppStore((s) => s.setParameterValue)
  const setActiveDiagramPresetId = useAppStore((s) => s.setActiveDiagramPresetId)
  const clearParameters = useAppStore((s) => s.clearParameters)
  const setPanel = useAppStore((s) => s.setPanel)
  const discardPendingSave = useAppStore((s) => s.discardPendingSave)
  const flushSave = useAppStore((s) => s.flushSave)
  const goToLine = useAppStore((s) => s.goToLine)
  const setHighlightLine = useAppStore((s) => s.setHighlightLine)

  const [presets, setPresets] = useState<DiagramPresetSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState<string | null>(null)

  useEffect(() => {
    listDiagramPresets()
      .then(setPresets)
      .catch(() => toast.error('No se pudieron cargar los diagramas'))
      .finally(() => setLoading(false))
  }, [])

  const applyHints = useCallback(
    (result: Awaited<ReturnType<typeof expandDiagramPreset>>) => {
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
        setParameterValue(p.id, String(result.params[p.id] ?? p.value))
      }
      setParameterHints(hints)
      const firstLine = result.param_specs.find((p) => p.highlight?.line)?.highlight?.line
      if (firstLine) {
        goToLine?.(firstLine)
        setHighlightLine(firstLine)
      }
    },
    [setParameterHints, setParameterValue, goToLine, setHighlightLine],
  )

  const insertDiagram = async (presetId: string) => {
    if (!activePageId) {
      toast.info('Selecciona una página primero')
      return
    }
    setBusyId(presetId)
    try {
      if (flushSave) await flushSave()
      discardPendingSave?.()
      const result = await expandDiagramPreset(presetId)
      const current = useAppStore.getState().activeLatex
      const next = current.trim()
        ? `${current.trimEnd()}\n\n${result.latex}`
        : result.latex
      setActiveLatex(next)
      const version = useAppStore.getState().activeVersion || undefined
      const page = await replacePageLatex(activePageId, next, version)
      setActiveAst(page.ast)
      setActiveVersion(page.version)
      clearParameters()
      setActiveDiagramPresetId(presetId)
      applyHints(result)
      setPanel('parameters', true)
      toast.success(`Insertado: ${result.title}`)
    } catch (err) {
      console.error(err)
      toast.error('No se pudo insertar el diagrama')
    } finally {
      setBusyId(null)
    }
  }

  const insertAndSimulate = async (presetId: string) => {
    if (!activePageId) {
      toast.info('Selecciona una página primero')
      return
    }
    setBusyId(presetId)
    try {
      if (flushSave) await flushSave()
      discardPendingSave?.()
      const result = await expandDiagramPreset(presetId)
      const current = useAppStore.getState().activeLatex
      const next = current.trim()
        ? `${current.trimEnd()}\n\n${result.latex}`
        : result.latex
      setActiveLatex(next)
      const version = useAppStore.getState().activeVersion || undefined
      const page = await replacePageLatex(activePageId, next, version)
      setActiveAst(page.ast)
      setActiveVersion(page.version)
      clearParameters()
      setActiveDiagramPresetId(presetId)
      applyHints(result)

      const sim = await diagramSimulateSource(presetId, result.params)
      await insertCell(activePageId, {
        cell_id: crypto.randomUUID(),
        language: 'python',
        source: sim.source,
      })
      setPanel('cells', true)
      toast.success(`${result.title}: diagrama + celda de simulación`)
    } catch (err) {
      console.error(err)
      toast.error('No se pudo generar la simulación')
    } finally {
      setBusyId(null)
    }
  }

  const categoryLabel: Record<string, string> = {
    circuitos: 'Circuitos',
    control: 'Control',
    mecanica: 'Mecánica',
    particulas: 'Partículas',
    optica: 'Óptica',
    general: 'General',
  }

  const grouped = useMemo(() => {
    const map = new Map<string, DiagramPresetSummary[]>()
    for (const p of presets) {
      const cat = p.category || 'general'
      const list = map.get(cat) ?? []
      list.push(p)
      map.set(cat, list)
    }
    const order = ['circuitos', 'control', 'mecanica', 'particulas', 'optica', 'general']
    return [...map.entries()].sort(([a], [b]) => {
      const ia = order.indexOf(a)
      const ib = order.indexOf(b)
      return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib)
    })
  }, [presets])

  return (
    <Card className="m-2 border-0 shadow-none">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div>
          <CardTitle className="text-sm font-semibold">Diagramas</CardTitle>
          <p className="text-[10px] text-muted-foreground">
            Presets con parámetros y simulación Jupyter
          </p>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="size-7"
          onClick={() => togglePanel('diagrams')}
        >
          <X className="size-4" />
        </Button>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {loading && (
          <p className="py-6 text-center text-xs text-muted-foreground">Cargando catálogo…</p>
        )}
        {!loading && presets.length === 0 && (
          <p className="py-6 text-center text-xs text-muted-foreground">Sin presets</p>
        )}
        {grouped.map(([cat, items]) => (
          <div key={cat} className="flex flex-col gap-2">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
              {categoryLabel[cat] ?? cat}
            </p>
            {items.map((p) => (
              <div
                key={p.preset_id}
                className="rounded-xl border bg-muted/20 p-3 transition-colors hover:bg-muted/40"
              >
                <div className="mb-1 flex items-start gap-2">
                  <CircuitBoard className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-semibold">{p.title}</p>
                    <p className="text-[10px] text-muted-foreground">{p.summary}</p>
                    <p className="mt-1 text-[10px] text-muted-foreground">
                      {p.kind} · {p.param_ids.join(', ') || 'sin params'}
                      {p.has_simulation ? ' · sim' : ''}
                    </p>
                  </div>
                </div>
                <div className="mt-2 flex gap-1.5">
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-7 flex-1 gap-1 text-[10px]"
                    disabled={busyId === p.preset_id}
                    onClick={() => insertDiagram(p.preset_id)}
                  >
                    <FlaskConical className="size-3" />
                    Insertar
                  </Button>
                  {p.has_simulation && (
                    <Button
                      size="sm"
                      className="h-7 flex-1 gap-1 text-[10px]"
                      disabled={busyId === p.preset_id}
                      onClick={() => insertAndSimulate(p.preset_id)}
                    >
                      <Play className="size-3" />
                      + Sim
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
