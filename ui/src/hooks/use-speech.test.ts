import { act, renderHook, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'

import {
  buildFinalTranscript,
  dedupeSpeechText,
  useSpeechRecognition,
} from './use-speech'

class MockSpeechRecognition {
  continuous = false
  interimResults = false
  lang = ''
  maxAlternatives = 1
  onstart: (() => void) | null = null
  onend: (() => void) | null = null
  onerror: ((event: Event) => void) | null = null
  onresult: ((event: Event & { resultIndex: number; results: SpeechRecognitionResultList }) => void) | null =
    null
  startCount = 0

  start() {
    this.startCount += 1
    this.onstart?.()
  }

  stop() {
    this.onend?.()
  }

  abort() {
    this.onend?.()
  }
}

function makeFinal(text: string, confidence = 0.9): SpeechRecognitionResult {
  return Object.assign([{ transcript: text, confidence }], {
    isFinal: true,
    length: 1,
  }) as unknown as SpeechRecognitionResult
}

function makeInterim(text: string): SpeechRecognitionResult {
  return Object.assign([{ transcript: text, confidence: 0.5 }], {
    isFinal: false,
    length: 1,
  }) as unknown as SpeechRecognitionResult
}

function fireResult(
  recognition: MockSpeechRecognition,
  results: SpeechRecognitionResult[],
  resultIndex = 0,
) {
  const list = Object.assign([...results], { length: results.length }) as unknown as SpeechRecognitionResultList
  const event = new Event('result') as Event & {
    resultIndex: number
    results: SpeechRecognitionResultList
  }
  event.resultIndex = resultIndex
  event.results = list
  recognition.onresult?.(event)
}

describe('speech transcript helpers', () => {
  it('rebuilds finals without duplicating when resultIndex resets to 0', () => {
    // Simula el bug clásico de Chrome: re-envía todos los finals.
    const r1 = makeFinal('hola ')
    const r2 = makeFinal('mundo')
    expect(buildFinalTranscript(Object.assign([r1], { length: 1 }) as SpeechRecognitionResultList)).toBe(
      'hola',
    )
    expect(
      buildFinalTranscript(Object.assign([r1, r2], { length: 2 }) as SpeechRecognitionResultList),
    ).toBe('hola mundo')
  })

  it('dedupes stutter and repeated phrases', () => {
    expect(dedupeSpeechText('la la la energía')).toBe('la energía')
    expect(dedupeSpeechText('hola mundo hola mundo')).toBe('hola mundo')
    expect(dedupeSpeechText('  la   masa   ')).toBe('la masa')
  })
})

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
      configurable: true,
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
    act(() => {
      fireResult(recognition, [makeFinal('hola')])
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

  it('does not duplicate when the engine re-sends prior finals', async () => {
    const { result } = renderHook(() => useSpeechRecognition())
    act(() => {
      result.current.start()
    })
    await waitFor(() => expect(result.current.listening).toBe(true))

    const recognition = instances[0]
    const a = makeFinal('medida uno ')
    const b = makeFinal('medida dos')

    act(() => {
      fireResult(recognition, [a], 0)
    })
    expect(result.current.transcript).toBe('medida uno')

    // Re-envío de [a, b] con resultIndex=0 (bug típico si se hace append).
    act(() => {
      fireResult(recognition, [a, b], 0)
    })
    expect(result.current.transcript).toBe('medida uno medida dos')
    expect(result.current.transcript).not.toContain('medida uno medida uno')
  })

  it('auto-restarts on engine end while user still wants listening', async () => {
    const { result } = renderHook(() => useSpeechRecognition())
    act(() => {
      result.current.start()
    })
    await waitFor(() => expect(result.current.listening).toBe(true))

    const recognition = instances[0]
    const startsBefore = recognition.startCount

    // Corte del motor sin stop() del usuario.
    act(() => {
      recognition.onend?.()
    })

    await waitFor(() => expect(recognition.startCount).toBeGreaterThan(startsBefore))
    expect(result.current.phase).toBe('listening')
  })

  it('completeProcessing clears transcript without double-fire risk', async () => {
    const { result } = renderHook(() => useSpeechRecognition())
    act(() => {
      result.current.start()
    })
    await waitFor(() => expect(result.current.listening).toBe(true))

    const recognition = instances[0]
    act(() => {
      fireResult(recognition, [makeFinal('uno')])
    })

    act(() => {
      result.current.completeProcessing()
    })
    expect(result.current.transcript).toBe('')
    expect(result.current.phase).toBe('idle')
  })

  it('exposes interim hypothesis separately from finals', async () => {
    const { result } = renderHook(() => useSpeechRecognition())
    act(() => {
      result.current.start()
    })
    await waitFor(() => expect(result.current.listening).toBe(true))

    const recognition = instances[0]
    act(() => {
      fireResult(recognition, [makeFinal('hola '), makeInterim('mun')])
    })
    expect(result.current.transcript).toBe('hola')
    expect(result.current.interimTranscript).toContain('mun')
  })
})
