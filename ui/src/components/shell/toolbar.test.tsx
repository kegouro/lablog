import { render } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'

import { useAppStore } from '@/stores/app-store'

const { appendText, resetTranscript } = vi.hoisted(() => ({
  appendText: vi.fn(() => Promise.resolve()),
  resetTranscript: vi.fn(),
}))

vi.mock('@/hooks/use-speech', () => ({
  useSpeechRecognition: vi.fn(() => ({
    listening: false,
    supported: true,
    transcript: '',
    error: null,
    start: vi.fn(),
    stop: vi.fn(),
    resetTranscript,
  })),
}))

vi.mock('@/lib/api', () => ({
  appendText,
}))

import { Toolbar } from './toolbar'
import { useSpeechRecognition } from '@/hooks/use-speech'

const mockUseSpeech = vi.mocked(useSpeechRecognition)

describe('Toolbar dictation', () => {
  beforeEach(() => {
    appendText.mockClear()
    resetTranscript.mockClear()
    mockUseSpeech.mockReturnValue({
      listening: false,
      supported: true,
      transcript: '',
      error: null,
      start: vi.fn(),
      stop: vi.fn(),
      resetTranscript,
    })
  })

  it('appends dictated text once and resets transcript when listening stops', async () => {
    useAppStore.setState({ activePageId: 'page-1', activeLatex: '' })

    const { rerender } = render(<Toolbar onCreatePage={vi.fn()} />)

    // Simulate speech result arriving and then stopping.
    mockUseSpeech.mockReturnValue({
      listening: false,
      supported: true,
      transcript: 'hola mundo',
      error: null,
      start: vi.fn(),
      stop: vi.fn(),
      resetTranscript,
    })
    rerender(<Toolbar onCreatePage={vi.fn()} />)

    expect(appendText).toHaveBeenCalledTimes(1)
    expect(appendText).toHaveBeenCalledWith('page-1', 'hola mundo. ')
    expect(resetTranscript).toHaveBeenCalledTimes(1)

    // Re-rendering with the same transcript must not append again.
    rerender(<Toolbar onCreatePage={vi.fn()} />)
    expect(appendText).toHaveBeenCalledTimes(1)
  })
})
