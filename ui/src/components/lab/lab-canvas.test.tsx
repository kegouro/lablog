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
    getPage: vi.fn(() =>
      Promise.resolve({
        id: 'page-1',
        title: 'T',
        project_id: null,
        latex: '',
        raw: '',
        ast: [],
        version: 2,
        updated_at: new Date().toISOString(),
      }),
    ),
    insertCell: vi.fn(() => Promise.resolve()),
    listCells: vi.fn(),
    moveCell: vi.fn(() => Promise.resolve()),
    updateCell: vi.fn(() => Promise.resolve({ version: 3 })),
  }
})

import { executeCell, getPage, listCells, updateCell } from '@/lib/api'
import { LabCanvas } from './lab-canvas'

const mockExecuteCell = vi.mocked(executeCell)
const mockListCells = vi.mocked(listCells)
const mockUpdateCell = vi.mocked(updateCell)
const mockGetPage = vi.mocked(getPage)

describe('LabCanvas', () => {
  beforeEach(() => {
    mockExecuteCell.mockReset()
    mockListCells.mockReset()
    mockUpdateCell.mockReset()
    mockUpdateCell.mockResolvedValue({ version: 3 })
    mockGetPage.mockClear()
    useAppStore.setState({ activePageId: 'page-1', labMode: true, flushLabCells: null })
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

  it('flushes dirty cell source when leaving lab without blur', async () => {
    mockListCells.mockResolvedValue([
      {
        cell_id: 'c1',
        language: 'python',
        source: 'print(1)',
        output: '',
        figure_path: null,
      },
    ])

    render(<LabCanvas />)
    await waitFor(() => expect(mockListCells).toHaveBeenCalledWith('page-1'))

    const ta = screen.getByPlaceholderText('# código Python')
    await userEvent.clear(ta)
    await userEvent.type(ta, 'print(42)')

    // Sin blur: el snapshot local está dirty.
    await userEvent.click(screen.getByRole('button', { name: /Volver al editor/i }))

    await waitFor(() => {
      expect(mockUpdateCell).toHaveBeenCalledWith('page-1', 'c1', {
        language: 'python',
        source: 'print(42)',
      })
    })
    expect(mockGetPage).toHaveBeenCalledWith('page-1')
    expect(useAppStore.getState().labMode).toBe(false)
  })
})
