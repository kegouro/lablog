import { Play, Plus, Trash2, X } from 'lucide-react'
import { useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { executeCell, insertCell, listCells } from '@/lib/api'
import { useAppStore } from '@/stores/app-store'

const LANGUAGES = [
  { id: 'python', label: 'Python' },
  { id: 'julia', label: 'Julia' },
]

export function CellsPanel() {
  const { activePageId, togglePanel } = useAppStore()
  const [cells, setCells] = useState<Array<{
    cell_id: string
    language: string
    source: string
    output: string
    figure_path: string | null
    status?: 'idle' | 'running' | 'ok' | 'error'
  }>>([])
  const [newSource, setNewSource] = useState('')
  const [newLang, setNewLang] = useState('python')

  useEffect(() => {
    if (!activePageId) {
      setCells([])
      return
    }
    listCells(activePageId).then(setCells)
  }, [activePageId])

  const addCell = async () => {
    if (!activePageId || !newSource.trim()) return
    const cell = {
      cell_id: crypto.randomUUID(),
      language: newLang,
      source: newSource,
    }
    await insertCell(activePageId, cell)
    setCells([...cells, { ...cell, output: '', figure_path: null }])
    setNewSource('')
  }

  const runCell = async (cellId: string) => {
    if (!activePageId) return
    setCells((prev) =>
      prev.map((c) => (c.cell_id === cellId ? { ...c, status: 'running' } : c)),
    )
    try {
      const result = await executeCell(activePageId, cellId)
      setCells((prev) =>
        prev.map((c) =>
          c.cell_id === cellId
            ? {
                ...c,
                output: result.output,
                figure_path: result.figure_paths[0] ?? null,
                status: result.status === 'ok' ? 'ok' : 'error',
              }
            : c,
        ),
      )
    } catch {
      setCells((prev) =>
        prev.map((c) => (c.cell_id === cellId ? { ...c, status: 'error', output: 'Error al ejecutar' } : c)),
      )
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

        {cells.map((cell) => (
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
                >
                  <Play className="size-3" />
                </Button>
                <Button variant="ghost" size="icon" className="size-6" disabled>
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
