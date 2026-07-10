import { Download, FileCode, FileImage, FileText, FileType2, Globe, Palette } from 'lucide-react'

import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { toast } from 'sonner'
import { compilePdf, exportPage, exportPages, replacePageLatex, PdfCompileError } from '@/lib/api'
import { useAppStore } from '@/stores/app-store'

const FORMATS = [
  { id: 'tex', label: 'LaTeX (.tex)', icon: FileCode },
  { id: 'txt', label: 'Texto plano (.txt)', icon: FileType2 },
  { id: 'pdf', label: 'PDF (.pdf)', icon: FileImage },
  { id: 'docx', label: 'Word (.docx)', icon: FileText },
  { id: 'canva', label: 'Canva-ready (.html)', icon: Palette },
  { id: 'site', label: 'Sitio estático (GitHub Pages)', icon: Globe },
]

export function ExportMenu() {
  const activePageId = useAppStore((s) => s.activePageId)
  const activeLatex = useAppStore((s) => s.activeLatex)
  const parameterValues = useAppStore((s) => s.parameterValues)
  const setActiveLatex = useAppStore((s) => s.setActiveLatex)
  const flushSave = useAppStore((s) => s.flushSave)

  const handleExport = async (format: string, _label: string) => {
    if (format === 'site') {
      try {
        if (flushSave) await flushSave()
        const result = await exportPages()
        toast.success(`Sitio exportado a ${result.path}`)
      } catch (err) {
        console.error(err)
        toast.error('Error al exportar el sitio estático')
      }
      return
    }

    if (!activePageId) return

    if (format === 'pdf') {
      try {
        if (flushSave) await flushSave()
        const blob = await compilePdf(activePageId)
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'lablog.pdf'
        document.body.appendChild(a)
        a.click()
        a.remove()
        URL.revokeObjectURL(url)
      } catch (err) {
        console.error(err)
        toast.error(err instanceof PdfCompileError ? err.message : 'Error al compilar PDF')
      }
      return
    }

    try {
      if (flushSave) await flushSave()
      // Congelar placeholders automáticamente antes de exportar
      const hasPlaceholders = /\{\{\w+\}\}/.test(activeLatex)
      let source = activeLatex
      if (hasPlaceholders) {
        source = activeLatex.replace(/\{\{(\w+)\}\}/g, (_, name) => parameterValues[name] ?? `{{${name}}}`)
        // Persiste primero; solo refleja en la UI si el servidor lo aceptó.
        const result = await replacePageLatex(activePageId, source)
        setActiveLatex(result.latex)
      }

      const blob = await exportPage(activePageId, format)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const ext = format === 'canva' ? 'html' : format
      a.download = `lablog_export.${ext}`
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
      if (hasPlaceholders) toast.success('Parámetros congelados y exportación lista')
    } catch (err) {
      console.error(err)
      toast.error('Error al exportar. Revisa que tengas pandoc y LaTeX instalados para PDF/Word.')
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className="hidden gap-2 sm:flex">
          <Download className="size-4" />
          Exportar
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {FORMATS.map((f) => (
          <DropdownMenuItem
            key={f.id}
            onClick={() => handleExport(f.id, f.label)}
            disabled={!activePageId}
            className="gap-2"
          >
            <f.icon className="size-4" />
            {f.label}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
