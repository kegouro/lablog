import type { LatexSymbol, Page, Snippet, VaultFile } from '@/types'
import { create } from 'zustand'

export type PanelId =
  | 'vault'
  | 'snippets'
  | 'symbols'
  | 'cells'
  | 'output'
  | 'tutorials'
  | 'parameters'
  | 'diagrams'

export interface ParameterHint {
  description: string
  default: string
  color: string
  unit?: string
  min?: number
  max?: number
  scale?: 'linear' | 'log'
  /** Línea 1-based en el editor LaTeX. */
  highlightLine?: number
  /** Nodo TikZ (`name=`) o etiqueta de esquema. */
  highlightTikz?: string
  /** Fragmento LaTeX a buscar al enfocar. */
  highlightLatex?: string
}

export type UiDensity = 'comfortable' | 'compact'
export type EditorFont = 'sans' | 'mono' | 'serif'

/** Preferencias de apariencia exportables/importables. */
export interface AppPreferences {
  version: 1
  accent: string
  palette: string
  customColors: Record<string, string>
  fontScale: number
  density: UiDensity
  editorFont: EditorFont
  reducedMotion: boolean
  labMode: boolean
}

interface AppState {
  pages: Page[]
  activePageId: string | null
  /** Versión del documento en el backend (para ErrorBoundary resetKey). */
  activeVersion: number
  activeLatex: string
  activeAst: Page['ast']
  searchQuery: string
  panels: Record<PanelId, boolean>
  labMode: boolean
  theme: 'dark' | 'light' | 'system'
  accent: string
  palette: string
  customColors: Record<string, string>
  fontScale: number
  density: UiDensity
  editorFont: EditorFont
  reducedMotion: boolean
  vaultFiles: VaultFile[]
  snippets: Snippet[]
  symbols: LatexSymbol[]
  favorites: string[]
  isRecording: boolean
  transcription: string
  parameterHints: Record<string, ParameterHint>
  parameterValues: Record<string, string>
  /** Preset de diagrama activo en la página (para re-aplicar desde Parámetros). */
  activeDiagramPresetId: string | null
  /** Parámetro enfocado para color TikZ en el PDF. */
  activeHighlightParam: string | null
  /** Registrado por el editor: inserta texto en la posición del cursor. */
  insertAtCursor: ((text: string) => void) | null
  /** Registrado por el editor: fuerza el guardado inmediato si hay cambios pendientes. */
  flushSave: (() => Promise<void>) | null
  /** Cancela autosave pendiente sin escribir (p.ej. tras congelar parámetros). */
  discardPendingSave: (() => void) | null
  /** Registrado por el editor: mueve el cursor a la línea indicada (1-based). */
  goToLine: ((line: number) => void) | null
  /** Línea resaltada en el gutter (error PDF, etc.). */
  highlightLine: number | null
  setPages: (pages: Page[]) => void
  setActivePageId: (id: string | null) => void
  setActiveVersion: (version: number) => void
  setActiveLatex: (latex: string) => void
  setActiveAst: (ast: Page['ast']) => void
  setSearchQuery: (q: string) => void
  togglePanel: (id: PanelId) => void
  setPanel: (id: PanelId, open: boolean) => void
  setLabMode: (active: boolean) => void
  setTheme: (theme: 'dark' | 'light' | 'system') => void
  setAccent: (accent: string) => void
  setPalette: (palette: string) => void
  setCustomColors: (colors: Record<string, string>) => void
  setFontScale: (scale: number) => void
  setDensity: (density: UiDensity) => void
  setEditorFont: (font: EditorFont) => void
  setReducedMotion: (on: boolean) => void
  exportPreferences: () => AppPreferences
  importPreferences: (prefs: Partial<AppPreferences>) => void
  setVaultFiles: (files: VaultFile[]) => void
  setSnippets: (snippets: Snippet[]) => void
  setSymbols: (symbols: LatexSymbol[]) => void
  setFavorites: (favorites: string[]) => void
  setRecording: (recording: boolean) => void
  setTranscription: (text: string) => void
  setParameterHints: (hints: Record<string, ParameterHint>) => void
  setParameterValue: (name: string, value: string) => void
  setActiveDiagramPresetId: (id: string | null) => void
  setActiveHighlightParam: (id: string | null) => void
  clearParameters: () => void
  setInsertAtCursor: (fn: ((text: string) => void) | null) => void
  setFlushSave: (fn: (() => Promise<void>) | null) => void
  setDiscardPendingSave: (fn: (() => void) | null) => void
  setGoToLine: (fn: ((line: number) => void) | null) => void
  setHighlightLine: (line: number | null) => void
}

function persist(key: string, value: string): void {
  try {
    localStorage.setItem(key, value)
  } catch {
    // localStorage no disponible (navegación privada)
  }
}

export const useAppStore = create<AppState>((set, get) => ({
  pages: [],
  activePageId: null,
  activeVersion: 0,
  activeLatex: '',
  activeAst: undefined,
  searchQuery: '',
  panels: {
    vault: true,
    snippets: false,
    symbols: false,
    cells: false,
    output: false,
    tutorials: false,
    parameters: false,
    diagrams: false,
  },
  labMode: false,
  theme: 'dark',
  accent: 'zinc',
  palette: 'original',
  customColors: {},
  fontScale: 100,
  density: 'comfortable',
  editorFont: 'mono',
  reducedMotion: false,
  vaultFiles: [],
  snippets: [],
  symbols: [],
  favorites: [],
  isRecording: false,
  transcription: '',
  parameterHints: {},
  parameterValues: {},
  activeDiagramPresetId: null,
  activeHighlightParam: null,
  insertAtCursor: null,
  flushSave: null,
  discardPendingSave: null,
  goToLine: null,
  highlightLine: null,
  setPages: (pages) => set({ pages }),
  setActivePageId: (id) => set({ activePageId: id, activeVersion: 0 }),
  setActiveVersion: (activeVersion) => set({ activeVersion }),
  setActiveLatex: (activeLatex) => set({ activeLatex }),
  setActiveAst: (activeAst) => set({ activeAst }),
  setSearchQuery: (searchQuery) => set({ searchQuery }),
  togglePanel: (id) =>
    set((state) => {
      const panels = { ...state.panels, [id]: !state.panels[id] }
      persist('lablog-panels', JSON.stringify(panels))
      return { panels }
    }),
  setPanel: (id, open) =>
    set((state) => {
      const panels = { ...state.panels, [id]: open }
      persist('lablog-panels', JSON.stringify(panels))
      return { panels }
    }),
  setLabMode: (active) => {
    persist('lablog-labMode', String(active))
    set({ labMode: active })
  },
  setTheme: (theme) => set({ theme }),
  setAccent: (accent) => set({ accent }),
  setPalette: (palette) => set({ palette }),
  setCustomColors: (customColors) => set({ customColors }),
  setFontScale: (fontScale) => set({ fontScale }),
  setDensity: (density) => {
    persist('lablog-density', density)
    set({ density })
  },
  setEditorFont: (editorFont) => {
    persist('lablog-editorFont', editorFont)
    set({ editorFont })
  },
  setReducedMotion: (reducedMotion) => {
    persist('lablog-reducedMotion', String(reducedMotion))
    set({ reducedMotion })
  },
  exportPreferences: (): AppPreferences => {
    const s = get()
    return {
      version: 1,
      accent: s.accent,
      palette: s.palette,
      customColors: s.customColors,
      fontScale: s.fontScale,
      density: s.density,
      editorFont: s.editorFont,
      reducedMotion: s.reducedMotion,
      labMode: s.labMode,
    }
  },
  importPreferences: (prefs) => {
    set((state) => {
      const next = { ...state }
      if (prefs.accent != null) next.accent = prefs.accent
      if (prefs.palette != null) next.palette = prefs.palette
      if (prefs.customColors != null) next.customColors = prefs.customColors
      if (prefs.fontScale != null) next.fontScale = prefs.fontScale
      if (prefs.density === 'comfortable' || prefs.density === 'compact') {
        next.density = prefs.density
      }
      if (prefs.editorFont === 'sans' || prefs.editorFont === 'mono' || prefs.editorFont === 'serif') {
        next.editorFont = prefs.editorFont
      }
      if (typeof prefs.reducedMotion === 'boolean') next.reducedMotion = prefs.reducedMotion
      if (typeof prefs.labMode === 'boolean') next.labMode = prefs.labMode
      persist('lablog-accent', next.accent)
      persist('lablog-palette', next.palette)
      persist('lablog-custom-colors', JSON.stringify(next.customColors))
      persist('lablog-fontScale', String(next.fontScale))
      persist('lablog-density', next.density)
      persist('lablog-editorFont', next.editorFont)
      persist('lablog-reducedMotion', String(next.reducedMotion))
      persist('lablog-labMode', String(next.labMode))
      return next
    })
  },
  setVaultFiles: (vaultFiles) => set({ vaultFiles }),
  setSnippets: (snippets) => set({ snippets }),
  setSymbols: (symbols) => set({ symbols }),
  setFavorites: (favorites) => set({ favorites }),
  setRecording: (isRecording) => set({ isRecording }),
  setTranscription: (transcription) => set({ transcription }),
  setParameterHints: (parameterHints) => set((state) => ({ parameterHints: { ...state.parameterHints, ...parameterHints } })),
  setParameterValue: (name, value) =>
    set((state) => ({
      parameterValues: { ...state.parameterValues, [name]: value },
    })),
  setActiveDiagramPresetId: (activeDiagramPresetId) => set({ activeDiagramPresetId }),
  setActiveHighlightParam: (activeHighlightParam) => set({ activeHighlightParam }),
  clearParameters: () =>
    set({
      parameterHints: {},
      parameterValues: {},
      activeDiagramPresetId: null,
      activeHighlightParam: null,
    }),
  setInsertAtCursor: (insertAtCursor) => set({ insertAtCursor }),
  setFlushSave: (flushSave) => set({ flushSave }),
  setDiscardPendingSave: (discardPendingSave) => set({ discardPendingSave }),
  setGoToLine: (goToLine) => set({ goToLine }),
  setHighlightLine: (highlightLine) => set({ highlightLine }),
}))
