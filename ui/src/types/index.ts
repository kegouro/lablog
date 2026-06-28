export interface CellNode {
  type: 'cell'
  cell_id: string
  language: string
  source: string
  output: string
  figure_path: string | null
}

export interface Page {
  id: string
  title: string
  project_id: string | null
  latex: string
  updated_at: string
  ast?: (CellNode | { type: string; text?: string; latex?: string; mode?: string })[]
}

export interface VaultFile {
  id: string
  name: string
  mime_type: string
  size: number
  uploaded_at: string
  status: 'active' | 'pending_deletion'
  scheduled_for_deletion_at: string | null
}

export interface SnippetParameter {
  name: string
  default: number | string
  min?: number
  max?: number
  step?: number
  description?: string
  unit?: string
}

export interface Snippet {
  id: string
  name: string
  description: string
  category: string
  template: string
  parameters: SnippetParameter[]
  tags: string[]
}

export interface LatexSymbol {
  id: string
  char: string
  latex: string
  category: string
  description: string
}
