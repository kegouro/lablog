import { FlaskConical, Mic, MicOff, Plus } from 'lucide-react'
import { useEffect, useRef } from 'react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { useDictation } from '@/hooks/use-dictation'
import { dedupeSpeechText } from '@/hooks/use-speech'
import { getPage, sendVoice } from '@/lib/api'
import { useAppStore } from '@/stores/app-store'

import { ExportMenu } from './export-menu'
import { SettingsDialog } from './settings-dialog'
import { TemplatesMenu } from './templates-menu'
import { ThemeToggle } from './theme-toggle'

interface ToolbarProps {
  onCreatePage: () => void
}

/** Mínimo de caracteres útiles tras limpieza (evita insertar "eh", "a", …). */
const MIN_DICTATION_CHARS = 2

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
    interimTranscript,
    error,
    engineId,
    isServerEngine,
    start,
    stop,
    completeProcessing,
  } = useDictation()
  const processingRef = useRef(false)

  useEffect(() => {
    if (error) toast.error(error)
  }, [error])

  // Solo en phase === processing se consume el transcript (FSM).
  useEffect(() => {
    if (phase !== 'processing' || !activePageId || processingRef.current) return
    const text = dedupeSpeechText(transcript).trim()

    // Whisper ya insertó en el backend al parar; solo resync.
    if (isServerEngine) {
      processingRef.current = true
      ;(async () => {
        try {
          if (text) {
            const page = await getPage(activePageId)
            setActiveLatex(page.raw || page.latex)
            setActiveAst(page.ast)
            setActiveVersion(page.version)
            const preview = text.length > 80 ? `${text.slice(0, 80)}…` : text
            toast.success(`Whisper: ${preview}`)
          }
        } catch {
          toast.error('No se pudo actualizar tras el dictado')
        } finally {
          completeProcessing()
          processingRef.current = false
        }
      })()
      return
    }

    if (!text || text.length < MIN_DICTATION_CHARS) {
      if (text) toast.message('Dictado demasiado corto; no se insertó')
      completeProcessing()
      return
    }
    processingRef.current = true

    ;(async () => {
      try {
        if (flushSave) await flushSave()
        const res = await sendVoice(activePageId, text)
        const page = await getPage(activePageId)
        setActiveLatex(page.raw || page.latex)
        setActiveAst(page.ast)
        setActiveVersion(page.version)
        const preview = text.length > 80 ? `${text.slice(0, 80)}…` : text
        toast.success(
          res.intent && res.intent !== 'text'
            ? `Dictado (${res.intent}): ${preview}`
            : `Dictado: ${preview}`,
        )
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
    isServerEngine,
    setActiveLatex,
    setActiveAst,
    setActiveVersion,
    completeProcessing,
    flushSave,
  ])

  const handleDictate = () => {
    if (!supported) {
      toast.error(
        isServerEngine
          ? 'Micrófono no disponible en este navegador'
          : 'Tu navegador no soporta Web Speech (usa Chrome/Edge o Whisper/Vosk en Preferencias)',
      )
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
      toast.message(
        engineId === 'whisper'
          ? 'Grabando… Detener → Whisper'
          : engineId === 'vosk'
            ? 'Grabando… Detener → Vosk'
            : 'Escuchando… habla con claridad y pulsa Detener al terminar',
      )
    }
  }

  const livePreview = [transcript, interimTranscript].filter(Boolean).join(' ').trim()
  const engineLabel =
    engineId === 'whisper' ? 'Whisper' : engineId === 'vosk' ? 'Vosk' : 'Browser'

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

      <div className="flex max-w-[min(100%,42rem)] items-center gap-1 rounded-xl border bg-muted/40 p-1 shadow-sm">
        <Button
          variant={listening ? 'default' : 'ghost'}
          size="sm"
          onClick={handleDictate}
          className="gap-2 rounded-lg shrink-0"
          title={
            listening
              ? 'Detener dictado'
              : `Dictar (${engineLabel}) — cambia el motor en Preferencias`
          }
        >
          {listening ? <MicOff className="size-4 animate-pulse" /> : <Mic className="size-4" />}
          <span className="hidden sm:inline">{listening ? 'Detener' : 'Dictar'}</span>
        </Button>
        {(listening || phase === 'processing') && (
          <span
            className="hidden max-w-[18rem] truncate px-2 text-xs text-muted-foreground md:inline"
            title={livePreview || engineLabel}
          >
            {phase === 'processing'
              ? isServerEngine
                ? 'Transcribiendo…'
                : 'Insertando… '
              : `● ${engineLabel} `}
            {livePreview}
          </span>
        )}
        <TemplatesMenu />
        <ExportMenu />
        <Button
          variant={labMode ? 'secondary' : 'ghost'}
          size="sm"
          onClick={async () => {
            if (!labMode) {
              if (flushSave) {
                try {
                  await flushSave()
                } catch {
                  /* el backend puede fallar; el switch sigue */
                }
              }
            } else {
              const flushLab = useAppStore.getState().flushLabCells
              if (flushLab) {
                try {
                  await flushLab()
                } catch {
                  /* best-effort */
                }
              }
            }
            setLabMode(!labMode)
          }}
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
