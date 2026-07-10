import { render, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAppStore } from '@/stores/app-store'

const { replacePageLatex, completeProcessing } = vi.hoisted(() => ({
  replacePageLatex: vi.fn(() =>
    Promise.resolve({ status: 'ok', latex: '', ast: [], version: 2 }),
  ),
  completeProcessing: vi.fn(),
}))

vi.mock('@/hooks/use-speech', () => ({
  useSpeechRecognition: vi.fn(() => ({
    phase: 'idle',
    listening: false,
    supported: true,
    transcript: '',
    error: null,
    start: vi.fn(),
    stop: vi.fn(),
    completeProcessing,
    resetTranscript: vi.fn(),
  })),
}))

vi.mock('@/lib/api', () => ({
  replacePageLatex,
}))

import { useSpeechRecognition } from '@/hooks/use-speech'

import { Toolbar } from './toolbar'

const mockUseSpeech = vi.mocked(useSpeechRecognition)

describe('Toolbar dictation', () => {
  beforeEach(() => {
    replacePageLatex.mockClear()
    completeProcessing.mockClear()
    mockUseSpeech.mockReturnValue({
      phase: 'idle',
      listening: false,
      supported: true,
      transcript: '',
      error: null,
      start: vi.fn(),
      stop: vi.fn(),
      completeProcessing,
      resetTranscript: vi.fn(),
    })
  })

  it('saves dictated text only in processing phase and completes FSM', async () => {
    useAppStore.setState({ activePageId: 'page-1', activeLatex: '' })

    const { rerender } = render(<Toolbar onCreatePage={vi.fn()} />)

    mockUseSpeech.mockReturnValue({
      phase: 'processing',
      listening: false,
      supported: true,
      transcript: 'hola mundo',
      error: null,
      start: vi.fn(),
      stop: vi.fn(),
      completeProcessing,
      resetTranscript: vi.fn(),
    })
    rerender(<Toolbar onCreatePage={vi.fn()} />)

    await waitFor(() => expect(replacePageLatex).toHaveBeenCalledTimes(1))
    expect(replacePageLatex).toHaveBeenCalledWith('page-1', 'hola mundo. ')
    await waitFor(() => expect(completeProcessing).toHaveBeenCalled())

    // Same processing cycle must not double-append (processingRef).
    rerender(<Toolbar onCreatePage={vi.fn()} />)
    expect(replacePageLatex).toHaveBeenCalledTimes(1)
  })

  it('ignores transcript while still listening', async () => {
    useAppStore.setState({ activePageId: 'page-1', activeLatex: '' })
    mockUseSpeech.mockReturnValue({
      phase: 'listening',
      listening: true,
      supported: true,
      transcript: 'parcial',
      error: null,
      start: vi.fn(),
      stop: vi.fn(),
      completeProcessing,
      resetTranscript: vi.fn(),
    })
    render(<Toolbar onCreatePage={vi.fn()} />)
    await new Promise((r) => setTimeout(r, 50))
    expect(replacePageLatex).not.toHaveBeenCalled()
  })
})
