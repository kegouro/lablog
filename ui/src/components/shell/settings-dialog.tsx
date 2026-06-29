import { Paintbrush, Palette, Type } from 'lucide-react'
import { useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Slider } from '@/components/ui/slider'
import { useAppStore } from '@/stores/app-store'

const ACCENTS = [
  { id: 'zinc', label: 'Zinc', value: '#6b7280' },
  { id: 'rose', label: 'Rosa', value: '#e11d48' },
  { id: 'blue', label: 'Azul', value: '#2563eb' },
  { id: 'emerald', label: 'Esmeralda', value: '#059669' },
  { id: 'violet', label: 'Violeta', value: '#7c3aed' },
  { id: 'amber', label: 'Ámbar', value: '#d97706' },
]

const PALETTES = [
  { id: 'original', label: 'Original', preview: 'bg-zinc-200 dark:bg-zinc-800' },
  { id: 'dracula', label: 'Dracula', preview: 'bg-[#282a36]' },
  { id: 'moka', label: 'Moka', preview: 'bg-[#f5f0e8] dark:bg-[#251e1b]' },
  { id: 'custom', label: 'Personalizado', preview: 'bg-gradient-to-br from-rose-300 via-sky-300 to-emerald-300' },
]

const CUSTOM_KEYS = [
  { key: '--background', label: 'Fondo' },
  { key: '--foreground', label: 'Texto' },
  { key: '--card', label: 'Tarjeta' },
  { key: '--primary', label: 'Primario' },
  { key: '--secondary', label: 'Secundario' },
  { key: '--muted', label: 'Muted' },
  { key: '--accent', label: 'Acento' },
  { key: '--border', label: 'Borde' },
]

function applyCustomColors(colors: Record<string, string>) {
  const root = document.documentElement
  for (const [key, value] of Object.entries(colors)) {
    if (value) root.style.setProperty(key, value)
    else root.style.removeProperty(key)
  }
}

export function SettingsDialog() {
  const {
    fontScale,
    setFontScale,
    accent,
    setAccent,
    palette,
    setPalette,
    customColors,
    setCustomColors,
  } = useAppStore()
  const [open, setOpen] = useState(false)
  const [draftColors, setDraftColors] = useState(customColors)

  // Sincroniza el borrador cuando los colores llegan desde localStorage (async).
  useEffect(() => {
    setDraftColors(customColors)
  }, [customColors])

  useEffect(() => {
    document.documentElement.style.fontSize = `${fontScale}%`
  }, [fontScale])

  useEffect(() => {
    if (accent === 'zinc') {
      document.documentElement.removeAttribute('data-accent')
    } else {
      document.documentElement.setAttribute('data-accent', accent)
    }
    localStorage.setItem('lablog-accent', accent)
  }, [accent])

  useEffect(() => {
    if (palette === 'custom') {
      document.documentElement.setAttribute('data-palette', 'custom')
      applyCustomColors(customColors)
    } else if (palette === 'original') {
      document.documentElement.removeAttribute('data-palette')
      applyCustomColors({})
    } else {
      document.documentElement.setAttribute('data-palette', palette)
      applyCustomColors({})
    }
    localStorage.setItem('lablog-palette', palette)
  }, [palette, customColors])

  useEffect(() => {
    localStorage.setItem('lablog-fontScale', String(fontScale))
  }, [fontScale])

  useEffect(() => {
    localStorage.setItem('lablog-custom-colors', JSON.stringify(customColors))
  }, [customColors])

  const updateColor = (key: string, value: string) => {
    const next = { ...draftColors, [key]: value }
    setDraftColors(next) // refleja lo que escribe el usuario
    // Solo persiste/aplica si es hex válido o vacío (no romper el CSS con basura).
    if (value === '' || /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.test(value)) {
      setCustomColors(next)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="ghost" size="icon" className="size-8" title="Preferencias">
          <Paintbrush className="size-4" />
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Preferencias</DialogTitle>
          <DialogDescription>Personaliza la apariencia y comodidad de lablog.</DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Type className="size-4 text-muted-foreground" />
              <label className="text-sm font-medium">Tamaño de fuente ({fontScale}%)</label>
            </div>
            <Slider
              value={[fontScale]}
              onValueChange={([v]) => setFontScale(v)}
              min={85}
              max={125}
              step={5}
            />
          </div>

          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Palette className="size-4 text-muted-foreground" />
              <label className="text-sm font-medium">Paleta</label>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {PALETTES.map((p) => (
                <button
                  key={p.id}
                  onClick={() => setPalette(p.id)}
                  className={`flex items-center gap-2 rounded-lg border p-2 text-left text-xs transition-all ${
                    palette === p.id ? 'border-primary bg-primary/10' : 'hover:bg-muted/50'
                  }`}
                >
                  <span className={`size-6 rounded-full border ${p.preview}`} />
                  <span className="font-medium">{p.label}</span>
                </button>
              ))}
            </div>
          </div>

          {palette === 'custom' && (
            <div className="space-y-3 rounded-lg border bg-muted/30 p-3">
              <p className="text-xs font-medium">Colores personalizados</p>
              <div className="grid grid-cols-2 gap-3">
                {CUSTOM_KEYS.map(({ key, label }) => (
                  <div key={key} className="space-y-1">
                    <label htmlFor={key} className="text-[10px] uppercase tracking-wider">
                      {label}
                    </label>
                    <div className="flex items-center gap-2">
                      <input
                        id={key}
                        type="color"
                        value={draftColors[key] || '#000000'}
                        onChange={(e) => updateColor(key, e.target.value)}
                        className="size-8 cursor-pointer rounded border bg-transparent p-0.5"
                      />
                      <Input
                        value={draftColors[key] || ''}
                        onChange={(e) => updateColor(key, e.target.value)}
                        placeholder="#rrggbb"
                        className="h-8 flex-1 text-xs"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="space-y-3">
            <label className="text-sm font-medium">Color de acento</label>
            <div className="flex flex-wrap gap-2">
              {ACCENTS.map((a) => (
                <button
                  key={a.id}
                  onClick={() => setAccent(a.id)}
                  className={`flex size-9 items-center justify-center rounded-full border-2 transition-all ${
                    accent === a.id ? 'border-foreground scale-110' : 'border-transparent hover:scale-105'
                  }`}
                  style={{ backgroundColor: a.value }}
                  title={a.label}
                >
                  {accent === a.id && <span className="text-xs font-bold text-white drop-shadow">✓</span>}
                </button>
              ))}
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
