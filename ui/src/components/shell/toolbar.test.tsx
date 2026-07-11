import { render, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAppStore } from '@/stores/app-store'

const { sendVoice, getPage, completeProcessing } = vi.hoisted(() => ({
  sendVoice: vi.fn(() => Promise.resolve({ status: 'ok', intent: 'text' })),
  getPage: vi.fn(() =>
    Promise.resolve({
      id: 'page-1',
      title: 'T',
      project_id: null,
      latex: 'hola mundo',
      raw: 'hola mundo',
      updated_at: '',
      version: 2,
      ast: [],
    }),
  ),
  completeProcessing: vi.fn(),
}))

vi.mock('@/hooks/use-dictation', () => ({
  useDictation: vi.fn(() => ({
    phase: 'idle',
    listening: false,
    supported: true,
    transcript: '',
    interimTranscript: '',
    error: null,
    engineId: 'browser',
    engines: [],
    enginesLoading: false,
    start: vi.fn(),
    stop: vi.fn(),
    completeProcessing,
    pendingText: '',
    clearPending: vi.fn(),
    isServerEngine: false,
  })),
}))

vi.mock('@/hooks/use-speech', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/hooks/use-speech')>()
  return {
    ...actual,
  }
})

vi.mock('@/lib/api', () => ({
  sendVoice,
  getPage,
}))

import { useDictation } from '@/hooks/use-dictation'

import { Toolbar } from './toolbar'

const mockUseDictation = vi.mocked(useDictation)

describe('Toolbar dictation', () => {
  beforeEach(() => {
    sendVoice.mockClear()
    getPage.mockClear()
    completeProcessing.mockClear()
    mockUseDictation.mockReturnValue({
      phase: 'idle',
      listening: false,
      supported: true,
      transcript: '',
      interimTranscript: '',
      error: null,
      engineId: 'browser',
      engines: [],
      enginesLoading: false,
      start: vi.fn(),
      stop: vi.fn(),
      completeProcessing,
      pendingText: '',
      clearPending: vi.fn(),
      isServerEngine: false,
    })
  })

  it('saves dictated text via /voice only in processing phase and completes FSM', async () => {
    useAppStore.setState({ activePageId: 'page-1', activeLatex: '', flushSave: null })

    const { rerender } = render(<Toolbar onCreatePage={vi.fn()} />)

    mockUseDictation.mockReturnValue({
      phase: 'processing',
      listening: false,
      supported: true,
      transcript: 'hola mundo',
      interimTranscript: '',
      error: null,
      engineId: 'browser',
      engines: [],
      enginesLoading: false,
      start: vi.fn(),
      stop: vi.fn(),
      completeProcessing,
      pendingText: 'hola mundo',
      clearPending: vi.fn(),
      isServerEngine: false,
    })
    rerender(<Toolbar onCreatePage={vi.fn()} />)

    await waitFor(() => expect(sendVoice).toHaveBeenCalledTimes(1))
    expect(sendVoice).toHaveBeenCalledWith('page-1', 'hola mundo')
    await waitFor(() => expect(getPage).toHaveBeenCalledWith('page-1'))
    await waitFor(() => expect(completeProcessing).toHaveBeenCalled())

    rerender(<Toolbar onCreatePage={vi.fn()} />)
    expect(sendVoice).toHaveBeenCalledTimes(1)
  })

  it('ignores transcript while still listening', async () => {
    useAppStore.setState({ activePageId: 'page-1', activeLatex: '' })
    mockUseDictation.mockReturnValue({
      phase: 'listening',
      listening: true,
      supported: true,
      transcript: 'parcial',
      interimTranscript: 'par',
      error: null,
      engineId: 'browser',
      engines: [],
      enginesLoading: false,
      start: vi.fn(),
      stop: vi.fn(),
      completeProcessing,
      pendingText: '',
      clearPending: vi.fn(),
      isServerEngine: false,
    })
    render(<Toolbar onCreatePage={vi.fn()} />)
    await new Promise((r) => setTimeout(r, 50))
    expect(sendVoice).not.toHaveBeenCalled()
  })

  it('skips empty or noise-only transcripts for browser engine', async () => {
    useAppStore.setState({ activePageId: 'page-1', activeLatex: '' })
    mockUseDictation.mockReturnValue({
      phase: 'processing',
      listening: false,
      supported: true,
      transcript: '  ',
      interimTranscript: '',
      error: null,
      engineId: 'browser',
      engines: [],
      enginesLoading: false,
      start: vi.fn(),
      stop: vi.fn(),
      completeProcessing,
      pendingText: '',
      clearPending: vi.fn(),
      isServerEngine: false,
    })
    render(<Toolbar onCreatePage={vi.fn()} />)
    await waitFor(() => expect(completeProcessing).toHaveBeenCalled())
    expect(sendVoice).not.toHaveBeenCalled()
  })

  it('whisper path only resyncs page (already inserted server-side)', async () => {
    useAppStore.setState({ activePageId: 'page-1', activeLatex: '', flushSave: null })
    mockUseDictation.mockReturnValue({
      phase: 'processing',
      listening: false,
      supported: true,
      transcript: 'energía total',
      interimTranscript: '',
      error: null,
      engineId: 'whisper',
      engines: [],
      enginesLoading: false,
      start: vi.fn(),
      stop: vi.fn(),
      completeProcessing,
      pendingText: 'energía total',
      clearPending: vi.fn(),
      isServerEngine: true,
    })
    render(<Toolbar onCreatePage={vi.fn()} />)
    await waitFor(() => expect(getPage).toHaveBeenCalledWith('page-1'))
    expect(sendVoice).not.toHaveBeenCalled()
    await waitFor(() => expect(completeProcessing).toHaveBeenCalled())
  })
})
