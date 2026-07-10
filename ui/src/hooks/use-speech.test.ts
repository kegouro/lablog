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

describe('useSpeechRecognition FSM', () => {
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

  it('transitions idle → listening → processing → idle', async () => {
    const { result } = renderHook(() => useSpeechRecognition())
    expect(result.current.phase).toBe('idle')

    act(() => {
      result.current.start()
    })
    await waitFor(() => expect(result.current.phase).toBe('listening'))

    const recognition = instances[0]
    const speechResult = Object.assign([{ transcript: 'hola' }], {
      isFinal: true,
      length: 1,
    }) as unknown as SpeechRecognitionResult
    const results = Object.assign([speechResult], { length: 1 }) as unknown as SpeechRecognitionResultList
    const event = new Event('result') as Event & { resultIndex: number; results: SpeechRecognitionResultList }
    event.resultIndex = 0
    event.results = results

    act(() => {
      recognition.onresult?.(event)
    })
    expect(result.current.transcript).toBe('hola')

    act(() => {
      result.current.stop()
    })
    expect(result.current.phase).toBe('processing')

    act(() => {
      result.current.completeProcessing()
    })
    expect(result.current.phase).toBe('idle')
    expect(result.current.transcript).toBe('')
  })

  it('completeProcessing clears transcript without double-fire risk', async () => {
    const { result } = renderHook(() => useSpeechRecognition())
    act(() => {
      result.current.start()
    })
    await waitFor(() => expect(result.current.listening).toBe(true))

    const recognition = instances[0]
    const speechResult = Object.assign([{ transcript: 'uno' }], {
      isFinal: true,
      length: 1,
    }) as unknown as SpeechRecognitionResult
    const results = Object.assign([speechResult], { length: 1 }) as unknown as SpeechRecognitionResultList
    const event = new Event('result') as Event & { resultIndex: number; results: SpeechRecognitionResultList }
    event.resultIndex = 0
    event.results = results
    act(() => {
      recognition.onresult?.(event)
    })

    act(() => {
      result.current.completeProcessing()
    })
    expect(result.current.transcript).toBe('')
    expect(result.current.phase).toBe('idle')
  })
})
