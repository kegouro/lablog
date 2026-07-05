import { act, renderHook, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'

import { useSpeechRecognition } from './use-speech'

class MockSpeechRecognition {
  continuous = false
  interimResults = false
  lang = ''
  onstart: (() => void) | null = null
  onend: (() => void) | null = null
  onerror: ((event: Event) => void) | null = null
  onresult: ((event: Event & { resultIndex: number; results: SpeechRecognitionResultList }) => void) | null = null

  start() {
    this.onstart?.()
  }

  stop() {
    this.onend?.()
  }
}

describe('useSpeechRecognition', () => {
  let instances: MockSpeechRecognition[] = []

  beforeEach(() => {
    instances = []
    Object.defineProperty(globalThis, 'webkitSpeechRecognition', {
      value: function () {
        const instance = new MockSpeechRecognition()
        instances.push(instance)
        return instance
      },
      writable: true,
    })
  })

  it('exposes resetTranscript that clears the transcript', async () => {
    const { result } = renderHook(() => useSpeechRecognition())

    act(() => {
      result.current.start()
    })

    await waitFor(() => expect(result.current.listening).toBe(true))
    expect(instances).toHaveLength(1)

    const recognition = instances[0]
    const results = [
      [{ transcript: 'hola mundo', isFinal: true }],
    ] as unknown as SpeechRecognitionResultList
    const event = new Event('result') as Event & { resultIndex: number; results: SpeechRecognitionResultList }
    event.resultIndex = 0
    event.results = results

    act(() => {
      recognition.onresult?.(event)
    })

    expect(result.current.transcript).toBe('hola mundo')

    act(() => {
      result.current.resetTranscript()
    })

    expect(result.current.transcript).toBe('')
  })
})
