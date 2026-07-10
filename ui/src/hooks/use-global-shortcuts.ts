import { useEffect } from 'react'
import { toast } from 'sonner'

import {
  DEFAULT_SHORTCUTS,
  matchChord,
  type ShortcutAction,
} from '@/lib/shortcuts'
import { createPage } from '@/lib/api'
import { useAppStore } from '@/stores/app-store'

/**
 * Atajos globales (fuera del editor cuando no está capturando input editable
 * salvo save / palette que sí se permiten).
 */
export function useGlobalShortcuts() {
  const shortcuts = useAppStore((s) => s.shortcuts)
  const togglePanel = useAppStore((s) => s.togglePanel)
  const setLabMode = useAppStore((s) => s.setLabMode)
  const labMode = useAppStore((s) => s.labMode)
  const flushSave = useAppStore((s) => s.flushSave)
  const setPages = useAppStore((s) => s.setPages)
  const setActivePageId = useAppStore((s) => s.setActivePageId)

  useEffect(() => {
    const chord = (action: ShortcutAction) =>
      shortcuts[action] || DEFAULT_SHORTCUTS[action]

    const onKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null
      const tag = target?.tagName?.toLowerCase()
      const inField =
        tag === 'input' ||
        tag === 'textarea' ||
        tag === 'select' ||
        target?.isContentEditable

      // En campos de texto solo permitimos palette y save.
      const allowInField = (action: ShortcutAction) =>
        action === 'commandPalette' || action === 'save'

      const run = (action: ShortcutAction, fn: () => void | Promise<void>) => {
        if (!matchChord(e, chord(action))) return false
        if (inField && !allowInField(action)) return false
        e.preventDefault()
        void fn()
        return true
      }

      if (
        run('commandPalette', () => {
          window.dispatchEvent(new CustomEvent('lablog:open-command-palette'))
        })
      ) {
        return
      }

      if (
        run('save', async () => {
          if (flushSave) {
            try {
              await flushSave()
              toast.success('Guardado')
            } catch {
              toast.error('No se pudo guardar')
            }
          } else {
            toast.info('Nada que guardar aún')
          }
        })
      ) {
        return
      }

      if (run('toggleDiagrams', () => togglePanel('diagrams'))) return
      if (run('toggleParameters', () => togglePanel('parameters'))) return
      if (run('toggleCells', () => togglePanel('cells'))) return
      if (
        run('toggleLabMode', async () => {
          if (labMode) {
            const flushLab = useAppStore.getState().flushLabCells
            if (flushLab) {
              try {
                await flushLab()
              } catch {
                /* best-effort */
              }
            }
            setLabMode(false)
          } else {
            if (flushSave) {
              try {
                await flushSave()
              } catch {
                /* best-effort */
              }
            }
            setLabMode(true)
          }
        })
      ) {
        return
      }

      if (
        run('newPage', async () => {
          try {
            const page = await createPage('Nueva página')
            const pages = useAppStore.getState().pages
            setPages([page, ...pages])
            setActivePageId(page.id)
            toast.success('Página creada')
          } catch {
            toast.error('No se pudo crear la página')
          }
        })
      ) {
        return
      }
    }

    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [
    shortcuts,
    flushSave,
    setLabMode,
    labMode,
    setPages,
    setActivePageId,
    togglePanel,
  ])
}
