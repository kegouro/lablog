import { useEffect } from 'react'

import { AppShell } from '@/components/shell/app-shell'
import { CommandPalette } from '@/components/shell/command-palette'
import { ThemeProvider } from '@/components/shell/theme-provider'
import { Toaster } from '@/components/ui/sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import { useAppStore } from '@/stores/app-store'

function AppInitializer() {
  const setFontScale = useAppStore((s) => s.setFontScale)
  const setAccent = useAppStore((s) => s.setAccent)
  const setPalette = useAppStore((s) => s.setPalette)
  const setCustomColors = useAppStore((s) => s.setCustomColors)
  const setLabMode = useAppStore((s) => s.setLabMode)
  const setPanel = useAppStore((s) => s.setPanel)

  useEffect(() => {
    let savedScale: string | null = null
    let savedAccent: string | null = null
    let savedPalette: string | null = null
    let savedCustom: string | null = null
    let savedLabMode: string | null = null
    let savedPanels: string | null = null
    try {
      savedScale = localStorage.getItem('lablog-fontScale')
      savedAccent = localStorage.getItem('lablog-accent')
      savedPalette = localStorage.getItem('lablog-palette')
      savedCustom = localStorage.getItem('lablog-custom-colors')
      savedLabMode = localStorage.getItem('lablog-labMode')
      savedPanels = localStorage.getItem('lablog-panels')
    } catch {
      // localStorage no disponible
    }
    if (savedScale) setFontScale(Number(savedScale))
    if (savedAccent) {
      setAccent(savedAccent)
      if (savedAccent === 'zinc') {
        document.documentElement.removeAttribute('data-accent')
      } else {
        document.documentElement.setAttribute('data-accent', savedAccent)
      }
    }
    if (savedPalette) setPalette(savedPalette)
    if (savedCustom) {
      try {
        setCustomColors(JSON.parse(savedCustom))
      } catch {
        // ignore
      }
    }
    if (savedLabMode === 'true') setLabMode(true)
    if (savedPanels) {
      try {
        const panels = JSON.parse(savedPanels) as Record<string, boolean>
        for (const [id, open] of Object.entries(panels)) {
          setPanel(id as Parameters<typeof setPanel>[0], open)
        }
      } catch {
        // ignore
      }
    }
  }, [setFontScale, setAccent, setPalette, setCustomColors, setLabMode, setPanel])

  return null
}

function App() {
  return (
    <ThemeProvider defaultTheme="dark" storageKey="lablog-theme" attribute="class" enableSystem>
      <TooltipProvider>
        <AppInitializer />
        <div className="h-screen w-screen overflow-hidden">
          <AppShell />
        </div>
        <Toaster position="bottom-right" />
        <CommandPalette />
      </TooltipProvider>
    </ThemeProvider>
  )
}

export default App
