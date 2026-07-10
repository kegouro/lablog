import { Play, Plus, Trash2, X } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { ApiError, deleteCell, executeCell, getPage, insertCell, listCells, moveCell } from '@/lib/api'
import { useAppStore } from '@/stores/app-store'

// Solo lenguajes que CodeEngine ejecuta hoy (python/py).
const LANGUAGES = [{ id: 'python', label: 'Python' }]

export function CellsPanel() {
  const activePageId = useAppStore((s) => s.activePageId)
  const togglePanel = useAppStore((s) => s.togglePanel)
  const setActiveAst = useAppStore((s) => s.setActiveAst)
  const setActiveLatex = useAppStore((s) => s.setActiveLatex)
  const setActiveVersion = useAppStore((s) => s.setActiveVersion)
  const flushSave = useAppStore((s) => s.flushSave)
  const [cells, setCells] = useState<Array<{
    cell_id: string
    language: string
    source: string
    output: string | null
    figure_path: string | null
    status?: 'idle' | 'running' | 'ok' | 'error'
  }>>([])
  const [newSource, setNewSource] = useState('')
  const [newLang, setNewLang] = useState('python')

  const refreshCells = useCallback(async () => {
    if (!activePageId) return
    try {
      const [cellList, page] = await Promise.all([listCells(activePageId), getPage(activePageId)])
      setCells(cellList)
      setActiveAst(page.ast)
      // Sincroniza el raw del editor para que el autosave no pise celdas nuevas.
      setActiveLatex(page.raw || page.latex)
      setActiveVersion(page.version)
    } catch (err) {
      console.error(err)
    }
  }, [activePageId, setActiveAst, setActiveLatex, setActiveVersion])

  useEffect(() => {
    if (!activePageId) {
      setCells([])
      return
    }
    void refreshCells()
  }, [activePageId, refreshCells])

  const addCell = async () => {
    if (!activePageId || !newSource.trim()) return
    try {
      if (flushSave) await flushSave()
      const cell = {
        cell_id: crypto.randomUUID(),
        language: newLang,
        source: newSource,
      }
      await insertCell(activePageId, cell)
      await refreshCells()
      setNewSource('')
    } catch (err) {
      console.error(err)
      alert(err instanceof Error ? err.message : 'No se pudo añadir la celda')
    }
  }

  const runCell = async (cellId: string) => {
    if (!activePageId) return
    if (flushSave) await flushSave()
    setCells((prev) =>
      prev.map((c) => (c.cell_id === cellId ? { ...c, status: 'running' } : c)),
    )
    try {
      await executeCell(activePageId, cellId)
      await refreshCells()
    } catch (err) {
      let message = err instanceof Error ? err.message : 'Error al ejecutar'
      if (err instanceof ApiError && err.errorCode === 'KERNEL_DEAD') {
        message = `Motor de cálculo no disponible. Reinicia el kernel.\n${err.message}`
      }
      setCells((prev) =>
        prev.map((c) => (c.cell_id === cellId ? { ...c, status: 'error', output: message } : c)),
      )
    }
  }

  const removeCell = async (cellId: string) => {
    if (!activePageId) return
    try {
      await deleteCell(activePageId, cellId)
      await refreshCells()
    } catch (err) {
      console.error(err)
      alert(err instanceof Error ? err.message : 'No se pudo eliminar la celda')
    }
  }

  const handleMove = async (cellId: string, direction: 'up' | 'down') => {
    if (!activePageId) return
    const index = cells.findIndex((c) => c.cell_id === cellId)
    if (index < 0) return
    const newIndex = direction === 'up' ? Math.max(0, index - 1) : Math.min(cells.length - 1, index + 1)
    if (newIndex === index) return
    try {
      await moveCell(activePageId, cellId, newIndex)
      await refreshCells()
    } catch (err) {
      console.error(err)
      alert(err instanceof Error ? err.message : 'No se pudo reordenar la celda')
    }
  }

  return (
    <Card className="m-2 border-0 shadow-none">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-semibold">Celdas ejecutables</CardTitle>
        <Button variant="ghost" size="icon" className="size-7" onClick={() => togglePanel('cells')}>
          <X className="size-4" />
        </Button>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {!activePageId && (
          <p className="text-center text-xs text-muted-foreground">Selecciona una página para añadir celdas.</p>
        )}

        {cells.map((cell, idx) => (
          <div key={cell.cell_id} className="rounded-lg border bg-muted/20 p-3">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                {cell.language}
              </span>
              <div className="flex gap-1">
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-6"
                  onClick={() => runCell(cell.cell_id)}
                  disabled={cell.status === 'running'}
                  title="Ejecutar celda"
                >
                  <Play className="size-3" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-6"
                  onClick={() => handleMove(cell.cell_id, 'up')}
                  disabled={idx === 0}
                  title="Mover arriba"
                >
                  ↑
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-6"
                  onClick={() => handleMove(cell.cell_id, 'down')}
                  disabled={idx === cells.length - 1}
                  title="Mover abajo"
                >
                  ↓
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-6 hover:text-destructive"
                  onClick={() => removeCell(cell.cell_id)}
                  title="Eliminar celda"
                >
                  <Trash2 className="size-3" />
                </Button>
              </div>
            </div>
            <pre className="mb-2 max-h-24 overflow-auto rounded bg-muted p-2 text-xs font-mono">{cell.source}</pre>
            {cell.output && (
              <div className="rounded border bg-card p-2 text-xs">
                <p className="font-semibold text-muted-foreground">Output</p>
                <pre className="whitespace-pre-wrap font-mono">{cell.output}</pre>
              </div>
            )}
            {cell.figure_path && (
              <img
                src={`/api/v1/pages/${activePageId}/cells/${cell.cell_id}/figure`}
                alt="figura"
                className="mt-2 max-h-40 rounded border object-contain"
              />
            )}
          </div>
        ))}

        {activePageId && (
          <div className="space-y-2">
            <Select value={newLang} onValueChange={setNewLang}>
              <SelectTrigger className="h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {LANGUAGES.map((l) => (
                  <SelectItem key={l.id} value={l.id}>
                    {l.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Textarea
              value={newSource}
              onChange={(e) => setNewSource(e.target.value)}
              placeholder={`import matplotlib.pyplot as plt\nplt.plot([1, 2, 3])`}
              className="min-h-[80px] font-mono text-xs"
            />
            <Button onClick={addCell} size="sm" className="w-full gap-1">
              <Plus className="size-4" />
              Añadir celda
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
