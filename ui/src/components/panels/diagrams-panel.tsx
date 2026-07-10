import { CircuitBoard, FlaskConical, Play, X } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import {
  diagramSimulateSource,
  expandDiagramPreset,
  getPage,
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
  const [query, setQuery] = useState('')

  useEffect(() => {
    listDiagramPresets()
      .then(setPresets)
      .catch(() => toast.error('No se pudieron cargar los diagramas'))
      .finally(() => setLoading(false))
  }, [])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return presets
    return presets.filter((p) => {
      const hay = [
        p.preset_id,
        p.title,
        p.summary,
        p.category,
        p.kind,
        ...p.tags,
        ...p.param_ids,
      ]
        .join(' ')
        .toLowerCase()
      return hay.includes(q)
    })
  }, [presets, query])

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
      const version = useAppStore.getState().activeVersion
      const page = await replacePageLatex(
        activePageId,
        next,
        typeof version === 'number' ? version : undefined,
      )
      setActiveLatex(page.latex)
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
      const version = useAppStore.getState().activeVersion
      const page = await replacePageLatex(
        activePageId,
        next,
        typeof version === 'number' ? version : undefined,
      )
      setActiveLatex(page.latex)
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
      // insertCell avanza la versión del event log; resincroniza OCC.
      const refreshed = await getPage(activePageId)
      setActiveLatex(refreshed.raw || refreshed.latex)
      setActiveAst(refreshed.ast)
      setActiveVersion(refreshed.version)
      setPanel('cells', true)
      toast.success(`${result.title}: diagrama + celda de simulación`)
    } catch (err) {
      console.error(err)
      toast.error('No se pudo generar la simulación')
    } finally {
      setBusyId(null)
    }
  }

  const insertPyspice = async (presetId: string) => {
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
      const version = useAppStore.getState().activeVersion
      const page = await replacePageLatex(
        activePageId,
        next,
        typeof version === 'number' ? version : undefined,
      )
      setActiveLatex(page.latex)
      setActiveAst(page.ast)
      setActiveVersion(page.version)
      clearParameters()
      setActiveDiagramPresetId(presetId)
      applyHints(result)
      const sim = await diagramSimulateSource(presetId, result.params, { preferPyspice: true })
      await insertCell(activePageId, {
        cell_id: crypto.randomUUID(),
        language: 'python',
        source: sim.source,
      })
      const refreshed = await getPage(activePageId)
      setActiveLatex(refreshed.raw || refreshed.latex)
      setActiveAst(refreshed.ast)
      setActiveVersion(refreshed.version)
      setPanel('cells', true)
      toast.success(`${result.title}: diagrama + sim PySpice (fallback numpy)`)
    } catch (err) {
      console.error(err)
      toast.error('No se pudo generar PySpice')
    } finally {
      setBusyId(null)
    }
  }

  const PYSPICE_IDS = new Set(['rc_series_charge', 'rlc_series_step', 'half_wave_rectifier'])

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
    for (const p of filtered) {
      const cat = p.category || 'general'
      const list = map.get(cat) ?? []
      list.push(p)
      map.set(cat, list)
    }
    const order = ['circuitos', 'control', 'mecanica', 'optica', 'particulas', 'general']
    return [...map.entries()].sort(([a], [b]) => {
      const ia = order.indexOf(a)
      const ib = order.indexOf(b)
      return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib)
    })
  }, [filtered])

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
        <Input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Buscar: rc, bode, lente, control…"
          className="h-8 text-xs"
          aria-label="Filtrar diagramas"
        />
        {loading && (
          <p className="py-6 text-center text-xs text-muted-foreground">Cargando catálogo…</p>
        )}
        {!loading && presets.length === 0 && (
          <p className="py-6 text-center text-xs text-muted-foreground">Sin presets</p>
        )}
        {!loading && presets.length > 0 && filtered.length === 0 && (
          <p className="py-4 text-center text-xs text-muted-foreground">
            Nada coincide con “{query.trim()}”
          </p>
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
                  {p.has_simulation && PYSPICE_IDS.has(p.preset_id) && (
                    <Button
                      size="sm"
                      variant="secondary"
                      className="h-7 flex-1 gap-1 text-[10px]"
                      disabled={busyId === p.preset_id}
                      onClick={() => insertPyspice(p.preset_id)}
                      title="Celda con PySpice si está instalado; si no, numpy"
                    >
                      SPICE
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
