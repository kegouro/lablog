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

vi.mock('@/hooks/use-speech', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/hooks/use-speech')>()
  return {
    ...actual,
    useSpeechRecognition: vi.fn(() => ({
      phase: 'idle',
      listening: false,
      supported: true,
      transcript: '',
      interimTranscript: '',
      error: null,
      start: vi.fn(),
      stop: vi.fn(),
      completeProcessing,
      resetTranscript: vi.fn(),
    })),
  }
})

vi.mock('@/lib/api', () => ({
  sendVoice,
  getPage,
}))

import { useSpeechRecognition } from '@/hooks/use-speech'

import { Toolbar } from './toolbar'

const mockUseSpeech = vi.mocked(useSpeechRecognition)

describe('Toolbar dictation', () => {
  beforeEach(() => {
    sendVoice.mockClear()
    getPage.mockClear()
    completeProcessing.mockClear()
    mockUseSpeech.mockReturnValue({
      phase: 'idle',
      listening: false,
      supported: true,
      transcript: '',
      interimTranscript: '',
      error: null,
      start: vi.fn(),
      stop: vi.fn(),
      completeProcessing,
      resetTranscript: vi.fn(),
    })
  })

  it('saves dictated text via /voice only in processing phase and completes FSM', async () => {
    useAppStore.setState({ activePageId: 'page-1', activeLatex: '', flushSave: null })

    const { rerender } = render(<Toolbar onCreatePage={vi.fn()} />)

    mockUseSpeech.mockReturnValue({
      phase: 'processing',
      listening: false,
      supported: true,
      transcript: 'hola mundo',
      interimTranscript: '',
      error: null,
      start: vi.fn(),
      stop: vi.fn(),
      completeProcessing,
      resetTranscript: vi.fn(),
    })
    rerender(<Toolbar onCreatePage={vi.fn()} />)

    await waitFor(() => expect(sendVoice).toHaveBeenCalledTimes(1))
    expect(sendVoice).toHaveBeenCalledWith('page-1', 'hola mundo')
    await waitFor(() => expect(getPage).toHaveBeenCalledWith('page-1'))
    await waitFor(() => expect(completeProcessing).toHaveBeenCalled())

    // Same processing cycle must not double-send (processingRef).
    rerender(<Toolbar onCreatePage={vi.fn()} />)
    expect(sendVoice).toHaveBeenCalledTimes(1)
  })

  it('ignores transcript while still listening', async () => {
    useAppStore.setState({ activePageId: 'page-1', activeLatex: '' })
    mockUseSpeech.mockReturnValue({
      phase: 'listening',
      listening: true,
      supported: true,
      transcript: 'parcial',
      interimTranscript: 'par',
      error: null,
      start: vi.fn(),
      stop: vi.fn(),
      completeProcessing,
      resetTranscript: vi.fn(),
    })
    render(<Toolbar onCreatePage={vi.fn()} />)
    await new Promise((r) => setTimeout(r, 50))
    expect(sendVoice).not.toHaveBeenCalled()
  })

  it('skips empty or noise-only transcripts', async () => {
    useAppStore.setState({ activePageId: 'page-1', activeLatex: '' })
    mockUseSpeech.mockReturnValue({
      phase: 'processing',
      listening: false,
      supported: true,
      transcript: '  ',
      interimTranscript: '',
      error: null,
      start: vi.fn(),
      stop: vi.fn(),
      completeProcessing,
      resetTranscript: vi.fn(),
    })
    render(<Toolbar onCreatePage={vi.fn()} />)
    await waitFor(() => expect(completeProcessing).toHaveBeenCalled())
    expect(sendVoice).not.toHaveBeenCalled()
  })
})
