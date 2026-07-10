import { useCallback, useEffect, useRef, useState } from 'react'

interface SpeechRecognitionEvent extends Event {
  resultIndex: number
  results: SpeechRecognitionResultList
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string
}

interface SpeechRecognitionResultList {
  length: number
  [index: number]: SpeechRecognitionResult
}

interface SpeechRecognitionResult {
  isFinal: boolean
  [index: number]: { transcript: string }
}

interface SpeechRecognitionInstance {
  continuous: boolean
  interimResults: boolean
  lang: string
  onstart: (() => void) | null
  onend: (() => void) | null
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null
  onresult: ((event: SpeechRecognitionEvent) => void) | null
  start: () => void
  stop: () => void
}

interface SpeechRecognitionConstructor {
  new (): SpeechRecognitionInstance
}

interface SpeechWindow extends Window {
  SpeechRecognition?: SpeechRecognitionConstructor
  webkitSpeechRecognition?: SpeechRecognitionConstructor
}

/** FSM: idle → listening → processing → idle */
export type SpeechPhase = 'idle' | 'listening' | 'processing'

interface SpeechHook {
  phase: SpeechPhase
  listening: boolean
  supported: boolean
  transcript: string
  error: string | null
  start: () => void
  stop: () => void
  /** Consume el transcript y vuelve a idle (transición processing → idle). */
  completeProcessing: () => void
  resetTranscript: () => void
}

const MAX_SESSION_MS = 120_000

export function useSpeechRecognition(): SpeechHook {
  const [phase, setPhase] = useState<SpeechPhase>('idle')
  const [transcript, setTranscript] = useState('')
  const [error, setError] = useState<string | null>(null)
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const generationRef = useRef(0)
  const phaseRef = useRef<SpeechPhase>('idle')
  const transcriptRef = useRef('')

  phaseRef.current = phase
  transcriptRef.current = transcript

  const supported =
    typeof window !== 'undefined' &&
    ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)

  useEffect(() => {
    if (!supported) return

    const w = window as unknown as SpeechWindow
    const SR = w.SpeechRecognition ?? w.webkitSpeechRecognition
    if (!SR) return

    const recognition = new SR()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = 'es-ES'

    recognition.onstart = () => {
      setPhase('listening')
      setError(null)
    }

    recognition.onend = () => {
      if (timerRef.current) clearTimeout(timerRef.current)
      // stop() ya pudo poner processing; no bajar a idle si hay texto por consumir.
      if (phaseRef.current === 'listening') {
        if (transcriptRef.current.trim()) {
          setPhase('processing')
        } else {
          setPhase('idle')
        }
      }
    }

    recognition.onerror = (event) => {
      if (event.error === 'not-allowed') {
        setError('Permiso de micrófono denegado')
      } else if (event.error === 'no-speech') {
        setError('No se detectó voz')
      } else if (event.error === 'aborted') {
        setError(null)
      } else {
        setError(`Error: ${event.error}`)
      }
      setPhase('idle')
    }

    recognition.onresult = (event) => {
      const generation = generationRef.current
      let final = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        if (result.isFinal && result[0]?.transcript) {
          final += result[0].transcript
        }
      }
      if (!final) return
      setTranscript((prev) => {
        if (generation !== generationRef.current) return prev
        return prev + final
      })
    }

    recognitionRef.current = recognition

    return () => {
      try {
        recognition.stop()
      } catch {
        // ignore
      }
    }
  }, [supported])

  const resetTranscript = useCallback(() => {
    generationRef.current += 1
    setTranscript('')
  }, [])

  const completeProcessing = useCallback(() => {
    generationRef.current += 1
    setTranscript('')
    setPhase('idle')
  }, [])

  const start = useCallback(() => {
    resetTranscript()
    setError(null)
    setPhase('listening')
    try {
      recognitionRef.current?.start()
      if (timerRef.current) clearTimeout(timerRef.current)
      timerRef.current = setTimeout(() => {
        try {
          recognitionRef.current?.stop()
        } catch {
          // ignore
        }
      }, MAX_SESSION_MS)
    } catch {
      setError('No se pudo iniciar el dictado')
      setPhase('idle')
    }
  }, [resetTranscript])

  const stop = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current)
    const hasText = transcriptRef.current.trim().length > 0
    // Anticipar processing antes de onend para que el consumer no pierda el ciclo.
    setPhase(hasText ? 'processing' : 'idle')
    try {
      recognitionRef.current?.stop()
    } catch {
      // ignore
    }
  }, [])

  return {
    phase,
    listening: phase === 'listening',
    supported,
    transcript,
    error,
    start,
    stop,
    completeProcessing,
    resetTranscript,
  }
}
