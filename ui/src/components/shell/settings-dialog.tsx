import { Download, Keyboard, Paintbrush, Palette, Type, Upload } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'

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
import {
  DEFAULT_SHORTCUTS,
  SHORTCUT_LABELS,
  formatChordForDisplay,
  isValidChord,
  type ShortcutAction,
} from '@/lib/shortcuts'
import {
  PREFERENCE_PROFILES,
  useAppStore,
  type AppPreferences,
  type EditorFont,
  type PreferenceProfileId,
  type UiDensity,
} from '@/stores/app-store'

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
  { id: 'nord', label: 'Nord', preview: 'bg-[#5e81ac]' },
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
  const fontScale = useAppStore((s) => s.fontScale)
  const setFontScale = useAppStore((s) => s.setFontScale)
  const accent = useAppStore((s) => s.accent)
  const setAccent = useAppStore((s) => s.setAccent)
  const palette = useAppStore((s) => s.palette)
  const setPalette = useAppStore((s) => s.setPalette)
  const customColors = useAppStore((s) => s.customColors)
  const setCustomColors = useAppStore((s) => s.setCustomColors)
  const density = useAppStore((s) => s.density)
  const setDensity = useAppStore((s) => s.setDensity)
  const editorFont = useAppStore((s) => s.editorFont)
  const setEditorFont = useAppStore((s) => s.setEditorFont)
  const reducedMotion = useAppStore((s) => s.reducedMotion)
  const setReducedMotion = useAppStore((s) => s.setReducedMotion)
  const labMode = useAppStore((s) => s.labMode)
  const setLabMode = useAppStore((s) => s.setLabMode)
  const exportPreferences = useAppStore((s) => s.exportPreferences)
  const importPreferences = useAppStore((s) => s.importPreferences)
  const applyPreferenceProfile = useAppStore((s) => s.applyPreferenceProfile)
  const shortcuts = useAppStore((s) => s.shortcuts)
  const setShortcut = useAppStore((s) => s.setShortcut)
  const resetShortcuts = useAppStore((s) => s.resetShortcuts)
  const [open, setOpen] = useState(false)
  const [draftColors, setDraftColors] = useState(customColors)
  const fileRef = useRef<HTMLInputElement>(null)

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
    setDraftColors(next)
    if (value === '' || /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.test(value)) {
      setCustomColors(next)
    }
  }

  const downloadPrefs = () => {
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
  }

  const onImportFile = async (file: File) => {
    try {
      const text = await file.text()
      const data = JSON.parse(text) as Partial<AppPreferences>
      importPreferences(data)
      toast.success('Preferencias importadas')
    } catch {
      toast.error('JSON de preferencias inválido')
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="size-8"
          title="Preferencias"
          data-testid="settings-trigger"
          aria-label="Preferencias"
        >
          <Paintbrush className="size-4" />
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-md" data-testid="settings-dialog">
        <DialogHeader>
          <DialogTitle>Preferencias</DialogTitle>
          <DialogDescription>
            Apariencia, densidad, tipografía del editor y export/import.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Perfil rápido</label>
            <p className="text-[10px] text-muted-foreground">
              Un clic aplica densidad, fuente, acento y modo a la vez.
            </p>
            <div className="grid grid-cols-1 gap-2">
              {(Object.keys(PREFERENCE_PROFILES) as PreferenceProfileId[]).map((id) => {
                const p = PREFERENCE_PROFILES[id]
                return (
                  <button
                    key={id}
                    type="button"
                    onClick={() => {
                      applyPreferenceProfile(id)
                      toast.success(`Perfil «${p.label}» aplicado`)
                    }}
                    className="rounded-lg border p-2 text-left transition-colors hover:bg-muted/50"
                  >
                    <span className="text-xs font-semibold">{p.label}</span>
                    <span className="mt-0.5 block text-[10px] text-muted-foreground">
                      {p.description}
                    </span>
                  </button>
                )
              })}
            </div>
          </div>

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

          <div className="space-y-2">
            <label className="text-sm font-medium">Densidad de UI</label>
            <div className="grid grid-cols-2 gap-2">
              {(
                [
                  { id: 'comfortable' as UiDensity, label: 'Cómoda' },
                  { id: 'compact' as UiDensity, label: 'Compacta' },
                ] as const
              ).map((d) => (
                <button
                  key={d.id}
                  type="button"
                  onClick={() => setDensity(d.id)}
                  className={`rounded-lg border p-2 text-xs font-medium transition-all ${
                    density === d.id ? 'border-primary bg-primary/10' : 'hover:bg-muted/50'
                  }`}
                >
                  {d.label}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Fuente del editor LaTeX</label>
            <div className="grid grid-cols-3 gap-2">
              {(
                [
                  { id: 'mono' as EditorFont, label: 'Mono' },
                  { id: 'sans' as EditorFont, label: 'Sans' },
                  { id: 'serif' as EditorFont, label: 'Serif' },
                ] as const
              ).map((f) => (
                <button
                  key={f.id}
                  type="button"
                  onClick={() => setEditorFont(f.id)}
                  className={`rounded-lg border p-2 text-xs font-medium transition-all ${
                    editorFont === f.id ? 'border-primary bg-primary/10' : 'hover:bg-muted/50'
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={reducedMotion}
                onChange={(e) => setReducedMotion(e.target.checked)}
                className="size-3.5 accent-primary"
              />
              Reducir animaciones
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={labMode}
                onChange={async (e) => {
                  const next = e.target.checked
                  if (!next) {
                    const flushLab = useAppStore.getState().flushLabCells
                    if (flushLab) {
                      try {
                        await flushLab()
                      } catch {
                        /* best-effort */
                      }
                    }
                  }
                  setLabMode(next)
                }}
                className="size-3.5 accent-primary"
              />
              Modo laboratorio (layout denso)
            </label>
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
                  type="button"
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
                  type="button"
                  onClick={() => setAccent(a.id)}
                  className={`flex size-9 items-center justify-center rounded-full border-2 transition-all ${
                    accent === a.id ? 'border-foreground scale-110' : 'border-transparent hover:scale-105'
                  }`}
                  style={{ backgroundColor: a.value }}
                  title={a.label}
                >
                  {accent === a.id && (
                    <span className="text-xs font-bold text-white drop-shadow">✓</span>
                  )}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <Keyboard className="size-4 text-muted-foreground" />
                <label className="text-sm font-medium">Atajos</label>
              </div>
              <Button type="button" size="sm" variant="ghost" className="h-7 text-[10px]" onClick={resetShortcuts}>
                Restaurar
              </Button>
            </div>
            <p className="text-[10px] text-muted-foreground">
              Usa <code className="text-[10px]">mod</code> (= ⌘ en Mac / Ctrl en Windows). Ej:{' '}
              <code className="text-[10px]">mod+shift+d</code>
            </p>
            <div className="flex flex-col gap-1.5">
              {(Object.keys(DEFAULT_SHORTCUTS) as ShortcutAction[]).map((action) => {
                const value = shortcuts[action] ?? DEFAULT_SHORTCUTS[action]
                return (
                  <div key={action} className="flex items-center gap-2">
                    <span className="w-28 shrink-0 text-[10px] text-muted-foreground">
                      {SHORTCUT_LABELS[action]}
                    </span>
                    <Input
                      value={value}
                      onChange={(e) => {
                        const v = e.target.value.trim().toLowerCase()
                        if (v === '' || isValidChord(v)) setShortcut(action, v || DEFAULT_SHORTCUTS[action])
                      }}
                      className="h-7 flex-1 font-mono text-[10px]"
                      aria-label={SHORTCUT_LABELS[action]}
                    />
                    <span className="w-16 text-right text-[10px] text-muted-foreground">
                      {formatChordForDisplay(value)}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>

          <div className="flex gap-2">
            <Button type="button" size="sm" variant="outline" className="gap-1.5 text-xs" onClick={downloadPrefs}>
              <Download className="size-3.5" />
              Exportar
            </Button>
            <Button
              type="button"
              size="sm"
              variant="outline"
              className="gap-1.5 text-xs"
              onClick={() => fileRef.current?.click()}
            >
              <Upload className="size-3.5" />
              Importar
            </Button>
            <input
              ref={fileRef}
              type="file"
              accept="application/json,.json"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0]
                if (f) void onImportFile(f)
                e.target.value = ''
              }}
            />
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
