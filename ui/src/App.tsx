import { useEffect } from 'react'

import { AppShell } from '@/components/shell/app-shell'
import { CommandPalette } from '@/components/shell/command-palette'
import { ThemeProvider } from '@/components/shell/theme-provider'
import { Toaster } from '@/components/ui/sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import { useAppStore } from '@/stores/app-store'

function AppInitializer() {
  const { setFontScale, setAccent, setPalette, setCustomColors } = useAppStore()

  useEffect(() => {
    const savedScale = localStorage.getItem('lablog-fontScale')
    const savedAccent = localStorage.getItem('lablog-accent')
    const savedPalette = localStorage.getItem('lablog-palette')
    const savedCustom = localStorage.getItem('lablog-custom-colors')
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
  }, [setFontScale, setAccent, setPalette, setCustomColors])

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
