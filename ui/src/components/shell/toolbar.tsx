import { FlaskConical, Mic, MicOff, Plus } from 'lucide-react'
import { useEffect, useRef } from 'react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { useSpeechRecognition } from '@/hooks/use-speech'
import { replacePageLatex } from '@/lib/api'
import { useAppStore } from '@/stores/app-store'

import { ExportMenu } from './export-menu'
import { SettingsDialog } from './settings-dialog'
import { TemplatesMenu } from './templates-menu'
import { ThemeToggle } from './theme-toggle'

interface ToolbarProps {
  onCreatePage: () => void
}

export function Toolbar({ onCreatePage }: ToolbarProps) {
  const labMode = useAppStore((s) => s.labMode)
  const setLabMode = useAppStore((s) => s.setLabMode)
  const activePageId = useAppStore((s) => s.activePageId)
  const setActiveLatex = useAppStore((s) => s.setActiveLatex)
  const setActiveAst = useAppStore((s) => s.setActiveAst)
  const setActiveVersion = useAppStore((s) => s.setActiveVersion)
  const flushSave = useAppStore((s) => s.flushSave)
  const {
    phase,
    listening,
    supported,
    transcript,
    error,
    start,
    stop,
    completeProcessing,
  } = useSpeechRecognition()
  const processingRef = useRef(false)

  useEffect(() => {
    if (error) toast.error(error)
  }, [error])

  // Solo en phase === processing se consume el transcript (FSM).
  useEffect(() => {
    if (phase !== 'processing' || !activePageId || processingRef.current) return
    const text = transcript.trim()
    if (!text) {
      completeProcessing()
      return
    }
    processingRef.current = true
    const normalized = text.endsWith('.') || text.endsWith(' ') ? text : `${text}. `

    ;(async () => {
      try {
        if (flushSave) await flushSave()
        const currentLatex = useAppStore.getState().activeLatex
        const next = currentLatex ? `${currentLatex}\n${normalized}` : normalized
        setActiveLatex(next)
        const result = await replacePageLatex(activePageId, next)
        setActiveAst(result.ast)
        setActiveVersion(result.version)
      } catch {
        toast.error('No se pudo guardar el dictado')
      } finally {
        completeProcessing()
        processingRef.current = false
      }
    })()
  }, [
    phase,
    transcript,
    activePageId,
    setActiveLatex,
    setActiveAst,
    setActiveVersion,
    completeProcessing,
    flushSave,
  ])

  const handleDictate = () => {
    if (!supported) {
      toast.error('Tu navegador no soporta dictado por voz')
      return
    }
    if (listening) {
      stop()
    } else {
      if (!activePageId) {
        toast.info('Selecciona una página primero')
        return
      }
      start()
    }
  }

  return (
    <header className="flex h-12 shrink-0 items-center justify-between border-b bg-card/80 px-3 backdrop-blur">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" className="size-8" onClick={onCreatePage} title="Nueva página">
          <Plus className="size-4" />
        </Button>
        <Separator orientation="vertical" className="h-5" />
        <div className="flex items-center gap-1.5 pl-1">
          <div className="flex size-7 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
            <FlaskConical className="size-4" />
          </div>
          <span className="hidden font-semibold tracking-tight sm:inline">lablog</span>
        </div>
      </div>

      <div className="flex items-center gap-1 rounded-xl border bg-muted/40 p-1 shadow-sm">
        <Button
          variant={listening ? 'default' : 'ghost'}
          size="sm"
          onClick={handleDictate}
          className="gap-2 rounded-lg"
        >
          {listening ? <MicOff className="size-4 animate-pulse" /> : <Mic className="size-4" />}
          <span className="hidden sm:inline">{listening ? 'Detener' : 'Dictar'}</span>
        </Button>
        <TemplatesMenu />
        <ExportMenu />
        <Button
          variant={labMode ? 'secondary' : 'ghost'}
          size="sm"
          onClick={() => setLabMode(!labMode)}
          className="gap-2 rounded-lg"
        >
          <FlaskConical className="size-4" />
          <span className="hidden sm:inline">Laboratorio</span>
        </Button>
      </div>

      <div className="flex items-center gap-1">
        <SettingsDialog />
        <ThemeToggle />
      </div>
    </header>
  )
}
