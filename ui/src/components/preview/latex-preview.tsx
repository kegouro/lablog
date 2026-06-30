import 'katex/dist/katex.min.css'
import { useEffect, useMemo, useState } from 'react'

import { useDebouncedValue } from '@/hooks/use-debounced-value'
import { renderLatexToHtml } from '@/lib/latex-render'
import {
  compilePdf,
  installPdfEngine,
  pdfEngineStatus,
  PdfCompileError,
  type PdfEngineStatus,
  type PdfError,
} from '@/lib/api'
import { useAppStore } from '@/stores/app-store'
import type { CellNode, Page } from '@/types'
import { Button } from '@/components/ui/button'
import { Download, FileText, Loader2 } from 'lucide-react'
import { toast } from 'sonner'

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

function renderCell(cell: CellNode, pageId: string | null): string {
  const figureHtml =
    cell.figure_path && pageId
      ? `<img src="/api/v1/pages/${pageId}/cells/${cell.cell_id}/figure" alt="figura" class="mt-2 max-h-48 rounded border object-contain" />`
      : ''

  const outputHtml = cell.output
    ? `<div class="rounded border bg-card p-2 text-xs"><p class="font-semibold text-muted-foreground">Output</p><pre class="whitespace-pre-wrap font-mono">${escapeHtml(cell.output)}</pre></div>`
    : ''

  return `
    <div class="my-3 rounded-lg border bg-muted/30 p-3">
      <div class="mb-2 flex items-center justify-between text-[10px] uppercase tracking-wider text-muted-foreground">
        <span>Celda ${escapeHtml(cell.language)}</span>
      </div>
      <pre class="mb-2 max-h-24 overflow-auto rounded bg-muted p-2 text-xs font-mono">${escapeHtml(cell.source)}</pre>
      ${outputHtml}
      ${figureHtml}
    </div>
  `
}

function renderDocument(
  ast: Page['ast'],
  pageId: string | null,
  values: Record<string, string>,
): string {
  if (!ast || ast.length === 0) {
    return `
      <div class="flex h-full flex-col items-center justify-center gap-3 text-center">
        <div class="rounded-full bg-muted p-4 text-2xl">👀</div>
        <div class="max-w-xs space-y-1">
          <h3 class="font-semibold">Vista previa en vivo</h3>
          <p class="text-sm text-muted-foreground">
            Escribe LaTeX en el editor. Soporta <code class="rounded bg-muted px-1 text-xs">$...$</code>,
            <code class="rounded bg-muted px-1 text-xs">$$...$$</code> y
            <code class="rounded bg-muted px-1 text-xs">\\[...\\]</code>.
          </p>
        </div>
      </div>`
  }

  // Reconstruye el LaTeX de nodos texto+matemática contiguos y los renderiza
  // como un solo bloque, para que la matemática inline fluya dentro del párrafo
  // y los entornos (itemize, …) no lleguen fragmentados. Las celdas, que llevan
  // output/figura del AST, se renderizan aparte.
  let html = ''
  let buffer = ''
  const flush = () => {
    if (buffer.trim()) html += renderLatexToHtml(buffer, values)
    buffer = ''
  }
  for (const node of ast) {
    if (!node || typeof node !== 'object') continue
    if (node.type === 'cell') {
      flush()
      html += renderCell(node as CellNode, pageId)
    } else if (node.type === 'math') {
      const m = node as { latex?: string; mode?: string }
      const src = m.latex ?? ''
      buffer += m.mode === 'display' ? `\n\n\\[${src}\\]\n\n` : `$${src}$`
    } else if (node.type === 'text') {
      buffer += (node as { text?: string }).text ?? ''
    }
  }
  flush()
  return html
}

export function LatexPreview() {
  const { activeAst, activePageId, parameterValues } = useAppStore()
  const debouncedAst = useDebouncedValue(activeAst, 150)

  const [compiling, setCompiling] = useState(false)
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)
  const [errors, setErrors] = useState<PdfError[]>([])
  const [engine, setEngine] = useState<PdfEngineStatus | null>(null)
  const [installing, setInstalling] = useState(false)

  useEffect(() => {
    pdfEngineStatus().then(setEngine).catch(() => setEngine(null))
  }, [])

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

  const html = useMemo(
    () => renderDocument(debouncedAst, activePageId, parameterValues),
    [debouncedAst, activePageId, parameterValues],
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
      const blob = await compilePdf(activePageId)
      if (pdfUrl) URL.revokeObjectURL(pdfUrl)
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
          <span className="rounded bg-muted px-1.5 py-0.5 text-[9px] uppercase tracking-wider text-muted-foreground">
            Aproximada
          </span>
        </div>
        <Button variant="outline" size="sm" className="h-7 gap-1.5 text-xs" disabled={!activePageId || compiling} onClick={handleCompile}>
          {compiling ? <Loader2 className="size-3.5 animate-spin" /> : <FileText className="size-3.5" />}
          Compilar PDF
        </Button>
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
            {errors.map((e, i) => (
              <li key={i} className="font-mono">
                {e.kind === 'cell' ? `Celda ${e.ref}` : 'Documento'}
                {e.source_line != null ? ` · línea ${e.source_line}` : ''}: {e.message}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="relative min-h-0 flex-1">
        <div
          className="h-full overflow-auto rounded-lg border bg-card p-5 text-sm shadow-sm"
          dangerouslySetInnerHTML={{ __html: html }}
        />
        {pdfUrl && (
          <div className="absolute inset-0 z-30 flex flex-col bg-card">
            <div className="flex items-center justify-between border-b px-2 py-1">
              <span className="text-xs font-medium">PDF compilado</span>
              <div className="flex gap-1">
                <a className="text-xs underline" href={pdfUrl} download="lablog.pdf">Descargar</a>
                <button className="text-xs" onClick={() => { URL.revokeObjectURL(pdfUrl); setPdfUrl(null) }}>Cerrar</button>
              </div>
            </div>
            <iframe src={pdfUrl} title="PDF" className="min-h-0 flex-1" />
          </div>
        )}
      </div>
    </div>
  )
}
