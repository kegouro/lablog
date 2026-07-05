import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi, beforeEach } from 'vitest'

import { useAppStore } from '@/stores/app-store'

vi.mock('@/lib/api', () => ({
  deleteCell: vi.fn(() => Promise.resolve()),
  executeCell: vi.fn(),
  getPage: vi.fn(),
  insertCell: vi.fn(() => Promise.resolve()),
  listCells: vi.fn(),
  moveCell: vi.fn(() => Promise.resolve()),
}))

import { executeCell, getPage, listCells } from '@/lib/api'
import { CellsPanel } from './cells-panel'

const mockExecuteCell = vi.mocked(executeCell)
const mockListCells = vi.mocked(listCells)
const mockGetPage = vi.mocked(getPage)

describe('CellsPanel', () => {
  beforeEach(() => {
    mockExecuteCell.mockReset()
    mockListCells.mockReset()
    mockGetPage.mockReset()
    useAppStore.setState({ activePageId: 'page-1' })
  })

  it('displays the backend error message when execution fails', async () => {
    mockListCells.mockResolvedValue([
      {
        cell_id: 'c1',
        language: 'python',
        source: '1/0',
        output: '',
        figure_path: null,
      },
    ])
    mockGetPage.mockResolvedValue({
      id: 'page-1',
      title: 'Página',
      project_id: null,
      latex: '',
      ast: [],
      updated_at: new Date().toISOString(),
    })
    mockExecuteCell.mockRejectedValue(new Error('division by zero'))

    render(<CellsPanel />)

    await waitFor(() => expect(mockListCells).toHaveBeenCalledWith('page-1'))

    const runButton = screen.getByTitle('Ejecutar celda')
    await userEvent.click(runButton)

    await waitFor(() => {
      expect(screen.getByText(/division by zero/i)).toBeInTheDocument()
    })
  })
})
