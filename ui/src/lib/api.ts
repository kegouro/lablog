import type { AstNode, LatexSymbol, Page, Snippet, VaultFile } from '@/types'

const API_BASE = '/api/v1'

export class ApiError extends Error {
  readonly status: number
  readonly errorCode: string | null
  readonly detail: unknown

  constructor(status: number, message: string, errorCode: string | null = null, detail: unknown = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.errorCode = errorCode
    this.detail = detail
  }
}

function parseErrorBody(text: string): { message: string; errorCode: string | null; detail: unknown } {
  try {
    const json = JSON.parse(text) as { detail?: unknown }
    const detail = json.detail
    if (detail && typeof detail === 'object' && detail !== null && 'message' in detail) {
      const d = detail as { message?: string; error_code?: string }
      return {
        message: d.message ?? text,
        errorCode: d.error_code ?? null,
        detail,
      }
    }
    if (typeof detail === 'string') {
      return { message: detail, errorCode: null, detail }
    }
  } catch {
    // body no JSON
  }
  return { message: text || 'Unknown error', errorCode: null, detail: text }
}

async function fetchJson<T>(input: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${input}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => 'Unknown error')
    const parsed = parseErrorBody(text)
    throw new ApiError(res.status, parsed.message, parsed.errorCode, parsed.detail)
  }
  // 204 / cuerpo vacío: DELETE y similares no devuelven JSON.
  if (res.status === 204) {
    return undefined as T
  }
  const text = await res.text()
  if (!text.trim()) {
    return undefined as T
  }
  return JSON.parse(text) as T
}

interface PageDetailWire {
  page_id: string
  title: string
  project_id?: string | null
  latex: string
  raw: string
  ast: AstNode[]
  version: number
  updated_at?: string | null
}

function detailToPage(d: PageDetailWire): Page {
  return {
    id: d.page_id,
    title: d.title,
    project_id: d.project_id ?? null,
    latex: d.latex,
    raw: d.raw,
    ast: d.ast,
    version: d.version,
    updated_at: d.updated_at ?? new Date().toISOString(),
  }
}

export async function listPages(): Promise<Page[]> {
  const raw = await fetchJson<Array<{ page_id: string; title: string; project_id: string | null; updated_at: string }>>('/pages')
  return raw.map((p) => ({
    id: p.page_id,
    title: p.title,
    project_id: p.project_id,
    updated_at: p.updated_at,
    latex: '',
    raw: '',
    version: 0,
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
    raw: '',
    version: 0,
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
  return detailToPage(await fetchJson<PageDetailWire>(`/pages/${pageId}`))
}

export async function updatePageRaw(
  pageId: string,
  raw: string,
  version?: number | null,
): Promise<Page> {
  return detailToPage(
    await fetchJson<PageDetailWire>(`/pages/${pageId}`, {
      method: 'PUT',
      body: JSON.stringify({
        raw,
        ...(version != null ? { version } : {}),
      }),
    }),
  )
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
  version?: number | null,
): Promise<{ status: string; latex: string; ast: Page['ast']; version: number }> {
  const page = await updatePageRaw(pageId, latex, version)
  return { status: 'ok', latex: page.latex, ast: page.ast, version: page.version }
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
  output: string | null
  figure_path: string | null
  status?: 'idle' | 'running' | 'ok' | 'error'
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

export async function executeCell(
  pageId: string,
  cellId: string,
): Promise<Cell & { status: string; figure_paths: string[] }> {
  const cell = await fetchJson<Cell & { status?: string }>(
    `/pages/${pageId}/cells/${cellId}/execute`,
    { method: 'POST' },
  )
  return {
    ...cell,
    status: cell.status ?? 'ok',
    figure_paths: cell.figure_path ? [cell.figure_path] : [],
  }
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

export interface DiagramPresetSummary {
  preset_id: string
  version: number
  kind: string
  title: string
  summary: string
  category: string
  tags: string[]
  param_ids: string[]
  has_simulation: boolean
}

export interface DiagramExpandResult {
  preset_id: string
  version: number
  kind: string
  title: string
  latex: string
  params: Record<string, number>
  param_specs: Array<{
    id: string
    label: string
    description: string
    value: number
    unit: string
    min: number | null
    max: number | null
    scale: 'linear' | 'log'
    highlight: { tikz?: string | null; latex?: string | null; line?: number | null; color?: string }
  }>
  has_simulation: boolean
  highlight_param?: string | null
  supports_pyspice?: boolean
}

export async function listDiagramPresets(): Promise<DiagramPresetSummary[]> {
  return fetchJson('/diagrams/presets')
}

export async function expandDiagramPreset(
  presetId: string,
  params?: Record<string, number>,
  opts?: { highlightParam?: string | null },
): Promise<DiagramExpandResult> {
  return fetchJson(`/diagrams/presets/${presetId}/expand`, {
    method: 'POST',
    body: JSON.stringify({
      params: params ?? null,
      highlight_param: opts?.highlightParam ?? null,
    }),
  })
}

export async function diagramSimulateSource(
  presetId: string,
  params?: Record<string, number>,
  opts?: { preferPyspice?: boolean },
): Promise<{ source: string; language: string; backend: string; params: Record<string, number> }> {
  return fetchJson(`/diagrams/presets/${presetId}/simulate-source`, {
    method: 'POST',
    body: JSON.stringify({
      params: params ?? null,
      prefer_pyspice: opts?.preferPyspice ?? false,
    }),
  })
}

export interface DiagramApplyResult extends DiagramExpandResult {
  document_latex: string
  highlight_param?: string | null
  supports_pyspice?: boolean
}

/** Reexpande un preset embebido (o forzado) y devuelve el LaTeX completo de la página. */
export async function applyDiagramParams(
  latex: string,
  params?: Record<string, number>,
  presetId?: string | null,
  opts?: { highlightParam?: string | null },
): Promise<DiagramApplyResult> {
  return fetchJson('/diagrams/apply', {
    method: 'POST',
    body: JSON.stringify({
      latex,
      params: params ?? null,
      preset_id: presetId ?? null,
      highlight_param: opts?.highlightParam ?? null,
    }),
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

export async function getVaultFile(fileId: string): Promise<VaultFile> {
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

export async function requestVaultDeletion(
  fileId: string,
): Promise<{ scheduled_for_deletion_at: string; deletion_phrase: string }> {
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
  editor_line?: number | null
  ref: string | null
  kind: string | null
  severity?: string | null
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
