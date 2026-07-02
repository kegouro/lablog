import type { LatexSymbol, Page, Snippet, VaultFile } from '@/types'

const API_BASE = '/api/v1'

async function fetchJson<T>(input: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${input}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => 'Unknown error')
    throw new Error(`${res.status}: ${text}`)
  }
  return res.json() as Promise<T>
}

export async function listPages(): Promise<Page[]> {
  const raw = await fetchJson<Array<{ page_id: string; title: string; project_id: string | null; updated_at: string }>>('/pages')
  return raw.map((p) => ({
    id: p.page_id,
    title: p.title,
    project_id: p.project_id,
    updated_at: p.updated_at,
    latex: '',
  }))
}

export async function createPage(title = 'Sin título', projectId?: string): Promise<Page> {
  const raw = await fetchJson<{ page_id: string; title: string; project_id: string | null; updated_at: string }>('/pages', {
    method: 'POST',
    body: JSON.stringify({ title, project_id: projectId || null }),
  })
  return {
    id: raw.page_id,
    title: raw.title,
    project_id: raw.project_id,
    updated_at: raw.updated_at,
    latex: '',
  }
}

export async function updatePage(pageId: string, data: { title?: string; project_id?: string | null }): Promise<void> {
  await fetchJson(`/pages/${pageId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export async function deletePage(pageId: string): Promise<void> {
  await fetchJson(`/pages/${pageId}`, { method: 'DELETE' })
}

export async function getPage(pageId: string): Promise<Page> {
  const detail = await fetchJson<{
    page_id: string
    title: string
    latex: string
    ast: Page['ast']
  }>(`/pages/${pageId}`)
  return {
    id: detail.page_id,
    title: detail.title,
    project_id: null,
    latex: detail.latex,
    ast: detail.ast,
    updated_at: new Date().toISOString(),
  }
}

export async function getLatex(pageId: string): Promise<string> {
  const res = await fetchJson<{ latex: string }>(`/pages/${pageId}/latex`)
  return res.latex
}

export async function appendText(pageId: string, text: string, position = -1): Promise<void> {
  await fetchJson(`/pages/${pageId}/text`, {
    method: 'POST',
    body: JSON.stringify({ text, position }),
  })
}

export async function replacePageLatex(
  pageId: string,
  latex: string,
): Promise<{ status: string; latex: string; ast: Page['ast'] }> {
  return fetchJson(`/pages/${pageId}/replace`, {
    method: 'POST',
    body: JSON.stringify({ latex }),
  })
}

export async function insertMath(pageId: string, latex: string, mode: 'inline' | 'display'): Promise<void> {
  await fetchJson(`/pages/${pageId}/math`, {
    method: 'POST',
    body: JSON.stringify({ latex, mode }),
  })
}

export interface Cell {
  cell_id: string
  language: string
  source: string
  output: string
  figure_path: string | null
}

export async function listCells(pageId: string): Promise<Cell[]> {
  return fetchJson(`/pages/${pageId}/cells`)
}

export async function insertCell(pageId: string, cell: Omit<Cell, 'output' | 'figure_path'>): Promise<void> {
  await fetchJson(`/pages/${pageId}/cells`, {
    method: 'POST',
    body: JSON.stringify(cell),
  })
}

export async function updateCell(pageId: string, cellId: string, cell: { language: string; source: string }): Promise<void> {
  await fetchJson(`/pages/${pageId}/cells/${cellId}/update`, {
    method: 'POST',
    body: JSON.stringify(cell),
  })
}

export async function executeCell(pageId: string, cellId: string): Promise<Cell & { status: string; figure_paths: string[] }> {
  return fetchJson(`/pages/${pageId}/cells/${cellId}/execute`, { method: 'POST' })
}

export async function deleteCell(pageId: string, cellId: string): Promise<void> {
  await fetchJson(`/pages/${pageId}/cells/${cellId}`, { method: 'DELETE' })
}

export async function moveCell(pageId: string, cellId: string, newIndex: number): Promise<void> {
  await fetchJson(`/pages/${pageId}/cells/${cellId}/move`, {
    method: 'POST',
    body: JSON.stringify({ new_index: newIndex }),
  })
}

export async function exportPages(): Promise<{ path: string }> {
  return fetchJson('/export', { method: 'POST' })
}

export async function sendVoice(pageId: string, text: string): Promise<{ status: string; intent: string }> {
  return fetchJson(`/pages/${pageId}/voice`, {
    method: 'POST',
    body: JSON.stringify({ text }),
  })
}

export async function listVaultFiles(): Promise<VaultFile[]> {
  return fetchJson('/vault')
}

export async function uploadVaultFile(file: File): Promise<VaultFile> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${API_BASE}/vault`, { method: 'POST', body: form })
  if (!res.ok) {
    const text = await res.text().catch(() => 'Unknown error')
    throw new Error(`${res.status}: ${text}`)
  }
  return res.json() as Promise<VaultFile>
}

export async function getVaultFile(fileId: string): Promise<VaultFile & { deletion_phrase: string }> {
  return fetchJson(`/vault/${fileId}`)
}

export async function previewVaultFile(fileId: string): Promise<{
  type: string
  mime_type?: string
  content?: string
  rows?: string[][]
  path?: string
}> {
  return fetchJson(`/vault/${fileId}/preview`)
}

export function vaultFileDownloadUrl(fileId: string): string {
  return `/api/v1/vault/${fileId}/download`
}

export async function requestVaultDeletion(fileId: string): Promise<{ scheduled_for_deletion_at: string }> {
  return fetchJson(`/vault/${fileId}/delete-request`, { method: 'POST' })
}

export async function cancelVaultDeletion(fileId: string): Promise<void> {
  await fetchJson(`/vault/${fileId}/cancel-delete`, { method: 'POST' })
}

export async function forceDeleteVaultFile(fileId: string, phrase: string): Promise<void> {
  await fetchJson(`/vault/${fileId}/force-delete`, {
    method: 'POST',
    body: JSON.stringify({ phrase }),
  })
}

export async function listSnippets(): Promise<Snippet[]> {
  return fetchJson('/snippets')
}

export async function renderSnippet(snippetId: string, values: Record<string, number | string>): Promise<string> {
  const res = await fetchJson<{ code: string }>(`/snippets/${snippetId}/render`, {
    method: 'POST',
    body: JSON.stringify({ values }),
  })
  return res.code
}

export async function listSymbols(category?: string): Promise<LatexSymbol[]> {
  const query = category ? `?category=${encodeURIComponent(category)}` : ''
  return fetchJson(`/latex-symbols${query}`)
}

export async function listFavorites(): Promise<string[]> {
  return fetchJson('/latex-symbols/favorites')
}

export async function addFavorite(symbolId: string): Promise<void> {
  await fetchJson(`/latex-symbols/favorites/${symbolId}`, { method: 'POST' })
}

export async function removeFavorite(symbolId: string): Promise<void> {
  await fetchJson(`/latex-symbols/favorites/${symbolId}`, { method: 'DELETE' })
}

export async function exportPage(pageId: string, format: string): Promise<Blob> {
  const res = await fetch(`${API_BASE}/pages/${pageId}/export/${format}`)
  if (!res.ok) {
    const text = await res.text().catch(() => 'Unknown error')
    throw new Error(`${res.status}: ${text}`)
  }
  return res.blob()
}

export interface PdfError {
  message: string
  source_line: number | null
  ref: string | null
  kind: string | null
}

export class PdfCompileError extends Error {
  status: number
  errors: PdfError[]

  constructor(status: number, message: string, errors: PdfError[] = []) {
    super(message)
    this.status = status
    this.errors = errors
  }
}

export interface PdfEngineStatus {
  binary_ready: boolean
  bundle_warmed: boolean
  managed: boolean
  installed_version: string | null
  target_version: string
  update_available: boolean
}

export async function pdfEngineStatus(): Promise<PdfEngineStatus> {
  return fetchJson('/pdf/engine-status')
}

export async function installPdfEngine(force = false): Promise<{ installed: boolean; warmed: boolean; message: string }> {
  return fetchJson(`/pdf/install${force ? '?force=true' : ''}`, { method: 'POST' })
}

export interface HistoryEvent {
  index: number
  type: string
  timestamp: string
  summary: string
}

interface PageDetailWire {
  page_id: string
  title: string
  latex: string
  ast: Page['ast']
}

function detailToPage(d: PageDetailWire): Page {
  return {
    id: d.page_id,
    title: d.title,
    project_id: null,
    latex: d.latex,
    ast: d.ast,
    updated_at: new Date().toISOString(),
  }
}

export async function getHistory(pageId: string): Promise<HistoryEvent[]> {
  return fetchJson(`/pages/${pageId}/history`)
}

export async function getPageAt(pageId: string, index: number): Promise<Page> {
  return detailToPage(await fetchJson<PageDetailWire>(`/pages/${pageId}/at/${index}`))
}

export async function restoreVersion(pageId: string, index: number): Promise<Page> {
  return detailToPage(
    await fetchJson<PageDetailWire>(`/pages/${pageId}/restore/${index}`, { method: 'POST' }),
  )
}

export async function compilePdf(pageId: string): Promise<Blob> {
  const res = await fetch(`${API_BASE}/pages/${pageId}/export/pdf`)
  if (res.ok) return res.blob()
  let detail: { errors?: PdfError[] } = {}
  try {
    const body = await res.json()
    detail = body.detail ?? body
  } catch {
    // sin cuerpo JSON
  }
  const msg =
    res.status === 422 ? 'Errores de compilación LaTeX'
    : res.status === 504 ? 'La compilación superó el tiempo límite'
    : res.status === 503 ? 'Motor PDF (Tectonic) no disponible'
    : `Error ${res.status}`
  throw new PdfCompileError(res.status, msg, detail.errors ?? [])
}
