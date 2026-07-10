import { LayoutTemplate } from 'lucide-react'
import { useEffect, useState } from 'react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { replacePageLatex } from '@/lib/api'
import { LATEX_TEMPLATES, type LatexTemplate } from '@/lib/latex-templates'
import { useAppStore } from '@/stores/app-store'

async function loadTemplates(): Promise<LatexTemplate[]> {
  try {
    const res = await fetch('/api/v1/templates')
    if (!res.ok) throw new Error('fail')
    const data: unknown = await res.json()
    return Array.isArray(data) ? (data as LatexTemplate[]) : LATEX_TEMPLATES
  } catch {
    return LATEX_TEMPLATES
  }
}

export function TemplatesMenu() {
  const activePageId = useAppStore((s) => s.activePageId)
  const activeLatex = useAppStore((s) => s.activeLatex)
  const setActiveLatex = useAppStore((s) => s.setActiveLatex)
  const setActiveAst = useAppStore((s) => s.setActiveAst)
  const setActiveVersion = useAppStore((s) => s.setActiveVersion)
  const flushSave = useAppStore((s) => s.flushSave)
  const [items, setItems] = useState<LatexTemplate[]>(LATEX_TEMPLATES)

  useEffect(() => {
    void loadTemplates().then(setItems)
  }, [])

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
      const version = useAppStore.getState().activeVersion
      const result = await replacePageLatex(
        activePageId,
        content,
        typeof version === 'number' ? version : undefined,
      )
      setActiveLatex(result.latex)
      setActiveAst(result.ast)
      setActiveVersion(result.version)
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
      <DropdownMenuContent align="center" className="w-80 max-h-96 overflow-auto">
        {items.map((t) => (
          <DropdownMenuItem
            key={t.id}
            onClick={() => applyTemplate(t.content)}
            className="flex flex-col items-start gap-0.5"
          >
            <span className="font-medium">{t.name}</span>
            <span className="text-xs text-muted-foreground">{t.description}</span>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
