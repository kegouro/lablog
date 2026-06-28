import { useState } from 'react'
import {
  Archive,
  FileText,
  GraduationCap,
  Plus,
  Search,
  Sigma,
  SlidersHorizontal,
  Terminal,
  Trash2,
  Type,
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'
import { useAppStore, type PanelId } from '@/stores/app-store'

interface SidebarProps {
  onCreatePage: () => void
  onUpdatePage: (id: string, data: { title?: string; project_id?: string | null }) => void
  onDeletePage: (id: string) => void
}

const TOOLS: { id: PanelId; icon: React.ElementType; label: string }[] = [
  { id: 'vault', icon: Archive, label: 'Bóveda' },
  { id: 'snippets', icon: Type, label: 'Snippets' },
  { id: 'symbols', icon: Sigma, label: 'Símbolos' },
  { id: 'cells', icon: Terminal, label: 'Celdas' },
  { id: 'parameters', icon: SlidersHorizontal, label: 'Parámetros' },
  { id: 'tutorials', icon: GraduationCap, label: 'Tutoriales' },
]

export function Sidebar({ onCreatePage, onUpdatePage, onDeletePage }: SidebarProps) {
  const {
    pages,
    activePageId,
    setActivePageId,
    searchQuery,
    setSearchQuery,
    panels,
    setPanel,
  } = useAppStore()

  const [editingId, setEditingId] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState('')

  const filtered = pages.filter((p) =>
    p.title.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  const groups = filtered.reduce<Record<string, typeof filtered>>((acc, page) => {
    const key = page.project_id || 'Sin proyecto'
    acc[key] = acc[key] || []
    acc[key].push(page)
    return acc
  }, {})

  const isToolActive = (id: PanelId) => panels[id]

  const toggleTool = (id: PanelId) => {
    setPanel(id, !panels[id])
  }

  const startRename = (page: (typeof pages)[number]) => {
    setEditingId(page.id)
    setEditTitle(page.title)
  }

  const commitRename = (id: string) => {
    if (editTitle.trim()) {
      onUpdatePage(id, { title: editTitle.trim() })
    }
    setEditingId(null)
  }

  return (
    <aside className="flex w-64 shrink-0 flex-col border-r bg-card/80 backdrop-blur">
      <div className="flex items-center justify-between border-b px-3 py-2.5">
        <div className="flex items-center gap-2">
          <div className="flex size-7 items-center justify-center rounded-md bg-primary text-primary-foreground shadow-sm">
            <FileText className="size-4" />
          </div>
          <span className="font-bold tracking-tight">Páginas</span>
        </div>
        <Button variant="ghost" size="icon" className="size-7" onClick={onCreatePage} title="Nueva página">
          <Plus className="size-4" />
        </Button>
      </div>

      <div className="px-3 py-2.5">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Buscar páginas…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-8 bg-muted/40 pl-8 text-xs transition-colors focus-visible:bg-background"
          />
        </div>
      </div>

      <ScrollArea className="flex-1 px-2">
        <nav className="flex flex-col gap-3 py-1">
          {Object.entries(groups).map(([project, projectPages]) => (
            <div key={project}>
              <div className="px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/70">
                {project}
              </div>
              <div className="flex flex-col gap-0.5">
                {projectPages.map((page) => {
                  const isActive = activePageId === page.id
                  const isEditing = editingId === page.id
                  return (
                    <div
                      key={page.id}
                      className={cn(
                        'group relative flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-all duration-200',
                        isActive
                          ? 'bg-primary/15 text-primary shadow-sm'
                          : 'text-muted-foreground hover:bg-muted hover:text-foreground',
                      )}
                    >
                      {isActive && (
                        <span className="absolute left-0 top-1/2 h-5 w-1 -translate-y-1/2 rounded-r-full bg-primary" />
                      )}
                      <FileText
                        className={cn(
                          'size-4 shrink-0 transition-colors',
                          isActive ? 'text-primary' : 'text-muted-foreground/70 group-hover:text-foreground',
                        )}
                        onClick={() => setActivePageId(page.id)}
                      />
                      {isEditing ? (
                        <Input
                          autoFocus
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          onBlur={() => commitRename(page.id)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') commitRename(page.id)
                            if (e.key === 'Escape') setEditingId(null)
                          }}
                          className="h-6 py-0 text-xs"
                        />
                      ) : (
                        <button
                          type="button"
                          onClick={() => setActivePageId(page.id)}
                          onDoubleClick={() => startRename(page)}
                          className="flex-1 truncate text-left font-medium outline-none"
                        >
                          {page.title}
                        </button>
                      )}
                      <Button
                        variant="ghost"
                        size="icon"
                        className="size-6 opacity-0 group-hover:opacity-100"
                        onClick={() => {
                          if (window.confirm('¿Eliminar esta página?')) {
                            onDeletePage(page.id)
                          }
                        }}
                      >
                        <Trash2 className="size-3" />
                      </Button>
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
          {filtered.length === 0 && (
            <p className="px-2 py-4 text-center text-xs text-muted-foreground">
              {searchQuery ? 'Sin coincidencias' : 'Aún no hay páginas'}
            </p>
          )}
        </nav>
      </ScrollArea>

      <div className="border-t p-2">
        <div className="flex items-center justify-between gap-1">
          {TOOLS.map(({ id, icon: Icon, label }) => {
            const active = isToolActive(id)
            return (
              <button
                key={id}
                type="button"
                onClick={() => toggleTool(id)}
                title={label}
                className={cn(
                  'flex size-8 items-center justify-center rounded-lg transition-all duration-200 focus-visible:ring-2 focus-visible:ring-ring',
                  active
                    ? 'bg-primary/15 text-primary shadow-sm'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground hover:scale-105',
                )}
              >
                <Icon className="size-4" />
              </button>
            )
          })}
        </div>
      </div>
    </aside>
  )
}
