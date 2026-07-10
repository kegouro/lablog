import { useEffect, useState } from 'react'
import { toast } from 'sonner'

import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from '@/components/ui/command'
import {
  PREFERENCE_PROFILES,
  useAppStore,
  type PreferenceProfileId,
} from '@/stores/app-store'

export function CommandPalette() {
  const [open, setOpen] = useState(false)
  const pages = useAppStore((s) => s.pages)
  const activePageId = useAppStore((s) => s.activePageId)
  const setActivePageId = useAppStore((s) => s.setActivePageId)
  const setPanel = useAppStore((s) => s.setPanel)
  const setLabMode = useAppStore((s) => s.setLabMode)
  const flushSave = useAppStore((s) => s.flushSave)
  const applyPreferenceProfile = useAppStore((s) => s.applyPreferenceProfile)
  const exportPreferences = useAppStore((s) => s.exportPreferences)

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

  const close = () => setOpen(false)

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput placeholder="Buscar páginas, paneles, perfiles…" />
      <CommandList>
        <CommandEmpty>Sin resultados.</CommandEmpty>
        <CommandGroup heading="Páginas">
          {pages.map((page) => (
            <CommandItem
              key={page.id}
              value={page.title + ' ' + page.id}
              onSelect={() => {
                setActivePageId(page.id)
                close()
              }}
              className={activePageId === page.id ? 'bg-accent' : ''}
            >
              <span className="truncate">{page.title}</span>
            </CommandItem>
          ))}
        </CommandGroup>
        <CommandSeparator />
        <CommandGroup heading="Paneles">
          {(
            [
              ['vault', 'Bóveda'],
              ['diagrams', 'Diagramas'],
              ['parameters', 'Parámetros'],
              ['snippets', 'Snippets'],
              ['symbols', 'Símbolos'],
              ['cells', 'Celdas'],
              ['tutorials', 'Tutoriales'],
            ] as const
          ).map(([id, label]) => (
            <CommandItem
              key={id}
              value={`abrir ${label}`}
              onSelect={() => {
                setPanel(id, true)
                close()
              }}
            >
              Abrir {label}
            </CommandItem>
          ))}
        </CommandGroup>
        <CommandSeparator />
        <CommandGroup heading="Perfiles de UI">
          {(Object.keys(PREFERENCE_PROFILES) as PreferenceProfileId[]).map((id) => {
            const p = PREFERENCE_PROFILES[id]
            return (
              <CommandItem
                key={id}
                value={`perfil ${p.label} ${id}`}
                onSelect={() => {
                  applyPreferenceProfile(id)
                  toast.success(`Perfil «${p.label}» aplicado`)
                  close()
                }}
              >
                Perfil: {p.label}
              </CommandItem>
            )
          })}
          <CommandItem
            value="exportar preferencias"
            onSelect={() => {
              const blob = new Blob([JSON.stringify(exportPreferences(), null, 2)], {
                type: 'application/json',
              })
              const url = URL.createObjectURL(blob)
              const a = document.createElement('a')
              a.href = url
              a.download = 'lablog-preferences.json'
              a.click()
              URL.revokeObjectURL(url)
              toast.success('Preferencias exportadas')
              close()
            }}
          >
            Exportar preferencias JSON
          </CommandItem>
        </CommandGroup>
        <CommandSeparator />
        <CommandGroup heading="Modo">
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
              close()
            }}
          >
            Modo laboratorio
          </CommandItem>
          <CommandItem
            onSelect={() => {
              setLabMode(false)
              close()
            }}
          >
            Modo escritura
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  )
}
