/** Atajos de teclado: chord estilo `mod+k`, `mod+shift+d`. */

export type ShortcutAction =
  | 'commandPalette'
  | 'save'
  | 'toggleDiagrams'
  | 'toggleParameters'
  | 'toggleCells'
  | 'toggleLabMode'
  | 'newPage'

export const DEFAULT_SHORTCUTS: Record<ShortcutAction, string> = {
  commandPalette: 'mod+k',
  save: 'mod+s',
  toggleDiagrams: 'mod+shift+d',
  toggleParameters: 'mod+shift+p',
  toggleCells: 'mod+shift+c',
  toggleLabMode: 'mod+shift+l',
  newPage: 'mod+n',
}

export const SHORTCUT_LABELS: Record<ShortcutAction, string> = {
  commandPalette: 'Paleta de comandos',
  save: 'Guardar ahora',
  toggleDiagrams: 'Panel diagramas',
  toggleParameters: 'Panel parámetros',
  toggleCells: 'Panel celdas',
  toggleLabMode: 'Modo laboratorio',
  newPage: 'Nueva página',
}

const MOD_KEYS = new Set(['mod', 'cmd', 'meta', 'ctrl', 'control'])

/** True si el evento de teclado coincide con el chord. */
export function matchChord(e: KeyboardEvent, chord: string): boolean {
  const parts = chord
    .toLowerCase()
    .split('+')
    .map((p) => p.trim())
    .filter(Boolean)
  if (parts.length === 0) return false
  const key = parts[parts.length - 1]!
  const mods = parts.slice(0, -1)
  const wantMod = mods.some((m) => MOD_KEYS.has(m))
  const wantShift = mods.includes('shift')
  const wantAlt = mods.includes('alt') || mods.includes('option')
  const hasMod = e.metaKey || e.ctrlKey
  if (wantMod !== hasMod) return false
  if (wantShift !== e.shiftKey) return false
  if (wantAlt !== e.altKey) return false
  // Ignorar solo modificadores
  if (['control', 'meta', 'shift', 'alt'].includes(e.key.toLowerCase())) return false
  const pressed = e.key.length === 1 ? e.key.toLowerCase() : e.key.toLowerCase()
  return pressed === key || e.code.toLowerCase() === `key${key}`
}

/** Valida un chord simple (modificadores + una tecla). */
export function isValidChord(chord: string): boolean {
  const parts = chord
    .toLowerCase()
    .split('+')
    .map((p) => p.trim())
    .filter(Boolean)
  if (parts.length < 1) return false
  const key = parts[parts.length - 1]!
  if (key.length !== 1 && !['escape', 'enter', 'tab', 'space'].includes(key)) {
    return /^[a-z0-9]$/.test(key)
  }
  return true
}

export function formatChordForDisplay(chord: string): string {
  const isMac =
    typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform)
  return chord
    .split('+')
    .map((p) => {
      const x = p.trim().toLowerCase()
      if (x === 'mod' || x === 'cmd' || x === 'meta') return isMac ? '⌘' : 'Ctrl'
      if (x === 'ctrl' || x === 'control') return 'Ctrl'
      if (x === 'shift') return isMac ? '⇧' : 'Shift'
      if (x === 'alt' || x === 'option') return isMac ? '⌥' : 'Alt'
      return x.toUpperCase()
    })
    .join(isMac ? '' : '+')
}
