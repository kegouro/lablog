import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi, beforeEach } from 'vitest'

import { useAppStore } from '@/stores/app-store'

vi.mock('@/lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api')>()
  return {
    ...actual,
    deleteCell: vi.fn(() => Promise.resolve()),
    executeCell: vi.fn(),
    insertCell: vi.fn(() => Promise.resolve()),
    listCells: vi.fn(),
    moveCell: vi.fn(() => Promise.resolve()),
    updateCell: vi.fn(() => Promise.resolve()),
  }
})

import { executeCell, listCells } from '@/lib/api'
import { LabCanvas } from './lab-canvas'

const mockExecuteCell = vi.mocked(executeCell)
const mockListCells = vi.mocked(listCells)

describe('LabCanvas', () => {
  beforeEach(() => {
    mockExecuteCell.mockReset()
    mockListCells.mockReset()
    useAppStore.setState({ activePageId: 'page-1' })
  })

  it('renders markdown without executing inline HTML scripts', async () => {
    mockListCells.mockResolvedValue([
      {
        cell_id: 'c1',
        language: 'markdown',
        source: 'Hola <script>alert(1)</script> y $x^2$.',
        output: '',
        figure_path: null,
      },
    ])

    const { container } = render(<LabCanvas />)

    await waitFor(() => expect(mockListCells).toHaveBeenCalledWith('page-1'))

    expect(document.querySelector('script')).not.toBeInTheDocument()
    const paragraph = container.querySelector('p')
    expect(paragraph).not.toBeNull()
    expect(paragraph).toHaveTextContent(/Hola/)
    expect(paragraph).toHaveTextContent(/<script>alert\(1\)<\/script>/)
  })

  it('shows the backend error message when a python cell fails', async () => {
    mockListCells.mockResolvedValue([
      {
        cell_id: 'c1',
        language: 'python',
        source: '1/0',
        output: '',
        figure_path: null,
      },
    ])
    mockExecuteCell.mockRejectedValue(new Error('kernel timeout'))

    render(<LabCanvas />)

    await waitFor(() => expect(mockListCells).toHaveBeenCalledWith('page-1'))

    const runButton = screen.getByTitle('Ejecutar celda')
    await userEvent.click(runButton)

    await waitFor(() => {
      expect(screen.getByText(/kernel timeout/i)).toBeInTheDocument()
    })
  })
})
