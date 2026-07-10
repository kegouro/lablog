export interface CompletionItem {
  label: string
  insert: string
  kind: string
  detail: string
}

const API_BASE = '/api/v1'

export async function fetchSuggestions(prefix: string): Promise<CompletionItem[]> {
  const q = encodeURIComponent(prefix)
  const res = await fetch(`${API_BASE}/suggest?q=${q}&limit=30`)
  if (!res.ok) return []
  return (await res.json()) as CompletionItem[]
}

/** Prefijo tras la última `\` sin espacios (para trigger de autocomplete). */
export function completionPrefix(text: string, caret: number): string | null {
  const before = text.slice(0, caret)
  const m = before.match(/\\([A-Za-z]*)$/)
  if (!m) return null
  return m[1]
}
