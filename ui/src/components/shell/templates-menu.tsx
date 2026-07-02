import { LayoutTemplate } from 'lucide-react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { replacePageLatex } from '@/lib/api'
import { LATEX_TEMPLATES } from '@/lib/latex-templates'
import { useAppStore } from '@/stores/app-store'

export function TemplatesMenu() {
  const { activePageId, activeLatex, setActiveLatex, setActiveAst, flushSave } = useAppStore()

  const applyTemplate = async (content: string) => {
    if (!activePageId) {
      toast.info('Selecciona una página primero')
      return
    }
    if (activeLatex.trim() && !window.confirm('¿Reemplazar el contenido actual con la plantilla?')) {
      return
    }
    try {
      if (flushSave) await flushSave()
      const result = await replacePageLatex(activePageId, content)
      setActiveLatex(result.latex)
      setActiveAst(result.ast)
      toast.success('Plantilla aplicada')
    } catch {
      toast.error('No se pudo aplicar la plantilla')
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm" className="gap-2 rounded-lg" disabled={!activePageId}>
          <LayoutTemplate className="size-4" />
          <span className="hidden sm:inline">Plantillas</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="center" className="w-72">
        {LATEX_TEMPLATES.map((t) => (
          <DropdownMenuItem key={t.id} onClick={() => applyTemplate(t.content)} className="flex flex-col items-start gap-0.5">
            <span className="font-medium">{t.name}</span>
            <span className="text-xs text-muted-foreground">{t.description}</span>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
