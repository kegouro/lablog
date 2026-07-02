import type { LatexSymbol, Page, Snippet, VaultFile } from '@/types'
import { create } from 'zustand'

export type PanelId = 'vault' | 'snippets' | 'symbols' | 'cells' | 'output' | 'tutorials' | 'parameters'

export interface ParameterHint {
  description: string
  default: string
  color: string
}

interface AppState {
  pages: Page[]
  activePageId: string | null
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
  vaultFiles: VaultFile[]
  snippets: Snippet[]
  symbols: LatexSymbol[]
  favorites: string[]
  isRecording: boolean
  transcription: string
  parameterHints: Record<string, ParameterHint>
  parameterValues: Record<string, string>
  /** Registrado por el editor: inserta texto en la posición del cursor. */
  insertAtCursor: ((text: string) => void) | null
  /** Registrado por el editor: fuerza el guardado inmediato si hay cambios pendientes. */
  flushSave: (() => Promise<void>) | null
  setPages: (pages: Page[]) => void
  setActivePageId: (id: string | null) => void
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
  setVaultFiles: (files: VaultFile[]) => void
  setSnippets: (snippets: Snippet[]) => void
  setSymbols: (symbols: LatexSymbol[]) => void
  setFavorites: (favorites: string[]) => void
  setRecording: (recording: boolean) => void
  setTranscription: (text: string) => void
  setParameterHints: (hints: Record<string, ParameterHint>) => void
  setParameterValue: (name: string, value: string) => void
  clearParameters: () => void
  setInsertAtCursor: (fn: ((text: string) => void) | null) => void
  setFlushSave: (fn: (() => Promise<void>) | null) => void
}

function persist(key: string, value: string): void {
  try {
    localStorage.setItem(key, value)
  } catch {
    // localStorage no disponible (navegación privada)
  }
}

export const useAppStore = create<AppState>((set) => ({
  pages: [],
  activePageId: null,
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
  },
  labMode: false,
  theme: 'dark',
  accent: 'zinc',
  palette: 'original',
  customColors: {},
  fontScale: 100,
  vaultFiles: [],
  snippets: [],
  symbols: [],
  favorites: [],
  isRecording: false,
  transcription: '',
  parameterHints: {},
  parameterValues: {},
  insertAtCursor: null,
  flushSave: null,
  setPages: (pages) => set({ pages }),
  setActivePageId: (id) => set({ activePageId: id }),
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
  clearParameters: () => set({ parameterHints: {}, parameterValues: {} }),
  setInsertAtCursor: (insertAtCursor) => set({ insertAtCursor }),
  setFlushSave: (flushSave) => set({ flushSave }),
}))
