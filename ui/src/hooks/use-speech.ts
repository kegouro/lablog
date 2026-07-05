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

interface SpeechHook {
  listening: boolean
  supported: boolean
  transcript: string
  error: string | null
  start: () => void
  stop: () => void
  resetTranscript: () => void
}

// ponytail: tope de sesión; el reconocedor puede colgarse sin emitir onend.
const MAX_SESSION_MS = 120_000

export function useSpeechRecognition(): SpeechHook {
  const [listening, setListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [error, setError] = useState<string | null>(null)
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const pendingFinalRef = useRef('')
  const generationRef = useRef(0)

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
      setListening(true)
      setError(null)
    }

    recognition.onend = () => {
      setListening(false)
      if (timerRef.current) clearTimeout(timerRef.current)
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
      setListening(false)
    }

    recognition.onresult = (event) => {
      const generation = generationRef.current
      let final = ''
      let interim = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        if (result.isFinal) {
          final += result[0].transcript
        } else {
          interim += result[0].transcript
        }
      }
      if (final) {
        pendingFinalRef.current += final
        setTranscript((prev) => {
          if (generation !== generationRef.current) return prev
          return prev + final
        })
      }
      if (interim) {
        setTranscript((prev) => {
          if (generation !== generationRef.current) return prev
          const trimmed = interim.trim()
          const base = prev.endsWith(trimmed) ? prev : prev + interim
          return base
        })
      }
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
    pendingFinalRef.current = ''
    setTranscript('')
  }, [])

  const start = useCallback(() => {
    resetTranscript()
    setError(null)
    try {
      recognitionRef.current?.start()
      if (timerRef.current) clearTimeout(timerRef.current)
      timerRef.current = setTimeout(() => {
        try {
          recognitionRef.current?.stop()
        } catch {
          // ignore
        }
        setListening(false)
      }, MAX_SESSION_MS)
    } catch {
      setError('No se pudo iniciar el dictado')
    }
  }, [resetTranscript])

  const stop = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current)
    try {
      recognitionRef.current?.stop()
    } catch {
      // ignore
    }
    setListening(false)
  }, [])

  return { listening, supported, transcript, error, start, stop, resetTranscript }
}
