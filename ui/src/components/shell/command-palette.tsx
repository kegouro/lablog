import { useEffect, useState } from 'react'

import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from '@/components/ui/command'
import { useAppStore } from '@/stores/app-store'

export function CommandPalette() {
  const [open, setOpen] = useState(false)
  const pages = useAppStore((s) => s.pages)
  const activePageId = useAppStore((s) => s.activePageId)
  const setActivePageId = useAppStore((s) => s.setActivePageId)
  const setPanel = useAppStore((s) => s.setPanel)
  const setLabMode = useAppStore((s) => s.setLabMode)
  const flushSave = useAppStore((s) => s.flushSave)

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setOpen((prev) => !prev)
      }
    }
    document.addEventListener('keydown', down)
    return () => document.removeEventListener('keydown', down)
  }, [])

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput placeholder="Buscar páginas, comandos…" />
      <CommandList>
        <CommandEmpty>Sin resultados.</CommandEmpty>
        <CommandGroup heading="Páginas">
          {pages.map((page) => (
            <CommandItem
              key={page.id}
              value={page.title + ' ' + page.id}
              onSelect={() => {
                setActivePageId(page.id)
                setOpen(false)
              }}
              className={activePageId === page.id ? 'bg-accent' : ''}
            >
              <span className="truncate">{page.title}</span>
            </CommandItem>
          ))}
        </CommandGroup>
        <CommandSeparator />
        <CommandGroup heading="Vistas">
          <CommandItem onSelect={() => { setPanel('vault', true); setOpen(false) }}>Abrir bóveda</CommandItem>
          <CommandItem onSelect={() => { setPanel('snippets', true); setOpen(false) }}>Abrir snippets</CommandItem>
          <CommandItem onSelect={() => { setPanel('symbols', true); setOpen(false) }}>Abrir símbolos</CommandItem>
          <CommandItem
            onSelect={async () => {
              if (flushSave) {
                try {
                  await flushSave()
                } catch {
                  /* ignore */
                }
              }
              setLabMode(true)
              setOpen(false)
            }}
          >
            Modo laboratorio
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  )
}
