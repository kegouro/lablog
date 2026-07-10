import 'katex/dist/katex.min.css'
import { useEffect, useMemo, useState } from 'react'

import { Button } from '@/components/ui/button'
import { TimeTravelOverlay } from '@/components/history/time-travel'
import { useDebouncedValue } from '@/hooks/use-debounced-value'
import {
  compilePdf,
  installPdfEngine,
  pdfEngineStatus,
  PdfCompileError,
  type PdfEngineStatus,
  type PdfError,
} from '@/lib/api'
import { AstRenderer } from '@/lib/ast-render'
import { useAppStore } from '@/stores/app-store'
import { Clock, Download, FileText, Loader2 } from 'lucide-react'
import { toast } from 'sonner'

export function LatexPreview() {
  const activeAst = useAppStore((s) => s.activeAst)
  const activeLatex = useAppStore((s) => s.activeLatex)
  const activePageId = useAppStore((s) => s.activePageId)
  const goToLine = useAppStore((s) => s.goToLine)
  const flushSave = useAppStore((s) => s.flushSave)
  const debouncedAst = useDebouncedValue(activeAst, 150)

  const [compiling, setCompiling] = useState(false)
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)
  const [errors, setErrors] = useState<PdfError[]>([])
  const [engine, setEngine] = useState<PdfEngineStatus | null>(null)
  const [installing, setInstalling] = useState(false)
  const [historyOpen, setHistoryOpen] = useState(false)

  useEffect(() => {
    pdfEngineStatus().then(setEngine).catch(() => setEngine(null))
  }, [])

  // Un solo dueño del blob URL: se revoca al reemplazarlo, cerrarlo o desmontar.
  useEffect(() => {
    return () => {
      if (pdfUrl) URL.revokeObjectURL(pdfUrl)
    }
  }, [pdfUrl])

  const handleInstall = async (force: boolean) => {
    setInstalling(true)
    try {
      const r = await installPdfEngine(force)
      toast[r.installed ? 'success' : 'error'](r.message)
      setEngine(await pdfEngineStatus())
    } catch {
      toast.error('No se pudo instalar el motor PDF')
    } finally {
      setInstalling(false)
    }
  }

  const isFullDoc = useMemo(
    () => /\\documentclass\b/.test(activeLatex) || /\\begin\s*\{\s*document\s*\}/.test(activeLatex),
    [activeLatex],
  )

  const handleCompile = async () => {
    if (!activePageId || compiling) return
    setErrors([])
    try {
      const st = await pdfEngineStatus()
      if (!st.binary_ready) toast.info('Primera vez: preparando el motor (~1 min)')
    } catch { /* sigue */ }
    setCompiling(true)
    try {
      if (flushSave) await flushSave()
      const blob = await compilePdf(activePageId)
      setPdfUrl(URL.createObjectURL(blob))
    } catch (e) {
      if (e instanceof PdfCompileError) setErrors(e.errors)
      toast.error(e instanceof Error ? e.message : 'Error al compilar')
    } finally {
      setCompiling(false)
    }
  }

  return (
    <div className="flex h-full flex-col gap-2">
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
            Vista previa
          </span>
          {isFullDoc && (
            <span className="rounded bg-muted px-1.5 py-0.5 text-[9px] uppercase tracking-wider text-muted-foreground">
              LaTeX completo
            </span>
          )}
        </div>
        <div className="flex items-center gap-1.5">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 gap-1.5 text-xs"
            disabled={!activePageId}
            onClick={() => { setPdfUrl(null); setHistoryOpen(true) }}
          >
            <Clock className="size-3.5" />
            Historia
          </Button>
          <Button variant="outline" size="sm" className="h-7 gap-1.5 text-xs" disabled={!activePageId || compiling} onClick={handleCompile}>
            {compiling ? <Loader2 className="size-3.5 animate-spin" /> : <FileText className="size-3.5" />}
            Compilar PDF
          </Button>
        </div>
      </div>

      {engine && !engine.binary_ready && (
        <div className="flex items-center justify-between gap-2 rounded-lg border border-primary/30 bg-primary/5 p-2 text-xs">
          <span className="text-muted-foreground">
            Motor PDF no instalado. Se descarga una vez (~20&nbsp;MB) y luego funciona sin conexión.
          </span>
          <Button size="sm" className="h-7 shrink-0 gap-1.5 text-xs" disabled={installing} onClick={() => handleInstall(false)}>
            {installing ? <Loader2 className="size-3.5 animate-spin" /> : <Download className="size-3.5" />}
            {installing ? 'Instalando…' : 'Instalar motor'}
          </Button>
        </div>
      )}

      {engine?.binary_ready && engine.update_available && (
        <div className="flex items-center justify-between gap-2 rounded-lg border border-amber-400/40 bg-amber-400/5 p-2 text-xs">
          <span className="text-muted-foreground">
            Motor instalado {engine.installed_version} · disponible {engine.target_version}.
          </span>
          <Button variant="outline" size="sm" className="h-7 shrink-0 gap-1.5 text-xs" disabled={installing} onClick={() => handleInstall(true)}>
            {installing ? <Loader2 className="size-3.5 animate-spin" /> : <Download className="size-3.5" />}
            Actualizar
          </Button>
        </div>
      )}

      {errors.length > 0 && (
        <div className="rounded-lg border border-destructive/40 bg-destructive/5 p-2 text-xs">
          <p className="mb-1 font-semibold text-destructive">Errores de compilación</p>
          <ul className="space-y-0.5">
            {errors.map((e, i) => {
              const jump = e.editor_line ?? (e.kind === 'raw' ? e.source_line : null)
              return (
                <li key={i} className="font-mono">
                  {jump != null ? (
                    <button
                      type="button"
                      className="underline decoration-dotted hover:text-destructive"
                      onClick={() => goToLine?.(jump)}
                    >
                      línea {jump}
                    </button>
                  ) : (
                    <span>
                      {e.kind === 'cell' ? `Celda ${e.ref}` : 'Documento'}
                      {e.source_line != null ? ` · tex:${e.source_line}` : ''}
                    </span>
                  )}
                  {e.severity === 'warning' ? ' [warn]' : ''}
                  : {e.message}
                </li>
              )
            })}
          </ul>
        </div>
      )}

      <div className="relative min-h-0 flex-1">
        <div className="h-full overflow-auto rounded-lg border bg-card p-5 text-sm shadow-sm">
          <AstRenderer ast={debouncedAst} pageId={activePageId} />
        </div>
        {pdfUrl && (
          <div className="absolute inset-0 z-30 flex flex-col bg-card">
            <div className="flex items-center justify-between border-b px-2 py-1">
              <span className="text-xs font-medium">PDF compilado</span>
              <div className="flex gap-1">
                <a className="text-xs underline" href={pdfUrl} download="lablog.pdf">Descargar</a>
                <button className="text-xs" onClick={() => setPdfUrl(null)}>Cerrar</button>
              </div>
            </div>
            <iframe src={pdfUrl} title="PDF" className="min-h-0 flex-1" />
          </div>
        )}
        {historyOpen && activePageId && (
          <TimeTravelOverlay pageId={activePageId} onClose={() => setHistoryOpen(false)} />
        )}
      </div>
    </div>
  )
}
