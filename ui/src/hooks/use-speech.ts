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
  length: number
  [index: number]: { transcript: string; confidence: number }
}

interface SpeechRecognitionInstance {
  continuous: boolean
  interimResults: boolean
  lang: string
  maxAlternatives: number
  onstart: (() => void) | null
  onend: (() => void) | null
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null
  onresult: ((event: SpeechRecognitionEvent) => void) | null
  start: () => void
  stop: () => void
  abort: () => void
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
  /** Texto final acumulado (solo resultados isFinal). */
  transcript: string
  /** Hipótesis en vivo (no se inserta hasta ser final). */
  interimTranscript: string
  error: string | null
  start: () => void
  stop: () => void
  /** Consume el transcript y vuelve a idle (transición processing → idle). */
  completeProcessing: () => void
  resetTranscript: () => void
}

const MAX_SESSION_MS = 120_000
/** Chrome corta continuous tras silencio; reintentamos un rato. */
const MAX_AUTORESTARTS = 40
/** Descarta resultados con confianza muy baja cuando el motor la reporta. */
const MIN_CONFIDENCE = 0.25

/**
 * Reconstruye el transcript final desde la lista completa de resultados.
 * Nunca hacer `prev + chunk`: varios motores re-envían resultados previos con
 * `resultIndex === 0` y eso produce verborrea (hola → hola hola → …).
 */
export function buildFinalTranscript(results: SpeechRecognitionResultList): string {
  let out = ''
  for (let i = 0; i < results.length; i++) {
    const result = results[i]
    if (!result?.isFinal) continue
    const alt = pickBestAlternative(result)
    if (!alt) continue
    out += alt
  }
  return collapseWhitespace(out)
}

export function buildInterimTranscript(results: SpeechRecognitionResultList): string {
  let out = ''
  for (let i = 0; i < results.length; i++) {
    const result = results[i]
    if (result?.isFinal) continue
    const alt = pickBestAlternative(result)
    if (!alt) continue
    out += alt
  }
  return collapseWhitespace(out)
}

function pickBestAlternative(result: SpeechRecognitionResult): string {
  let best = result[0]
  if (!best?.transcript) return ''
  // Prefer higher confidence when the engine exposes several alts.
  for (let i = 1; i < (result.length || 1); i++) {
    const cand = result[i]
    if (cand && typeof cand.confidence === 'number' && cand.confidence > (best.confidence ?? 0)) {
      best = cand
    }
  }
  if (typeof best.confidence === 'number' && best.confidence > 0 && best.confidence < MIN_CONFIDENCE) {
    return ''
  }
  return best.transcript
}

function collapseWhitespace(s: string): string {
  return s.replace(/\s+/g, ' ').trim()
}

/**
 * Colapsa repeticiones típicas del STT (stutter / re-decode):
 * "la la la energía" → "la energía"
 * "hola mundo hola mundo" → "hola mundo"
 */
export function dedupeSpeechText(text: string): string {
  let t = collapseWhitespace(text).trim()
  if (!t) return ''
  // Misma palabra 2+ veces seguidas.
  t = t.replace(/\b(\p{L}+(?:'\p{L}+)?)(?:\s+\1)+\b/giu, '$1')
  // Mismo bigrama/frase corta repetida (hasta 5 palabras).
  for (let n = 5; n >= 2; n--) {
    const parts = Array.from({ length: n }, () => String.raw`\p{L}+(?:'\p{L}+)?`).join(String.raw`\s+`)
    t = t.replace(new RegExp(String.raw`\b(${parts})(?:\s+\1)+\b`, 'giu'), '$1')
  }
  return collapseWhitespace(t).trim()
}

export function useSpeechRecognition(): SpeechHook {
  const [phase, setPhase] = useState<SpeechPhase>('idle')
  const [transcript, setTranscript] = useState('')
  const [interimTranscript, setInterimTranscript] = useState('')
  const [error, setError] = useState<string | null>(null)
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const generationRef = useRef(0)
  const phaseRef = useRef<SpeechPhase>('idle')
  const transcriptRef = useRef('')
  /** true solo cuando el usuario pulsó Detener (no en cortes del motor). */
  const userStoppedRef = useRef(false)
  const wantListenRef = useRef(false)
  const autoRestartsRef = useRef(0)

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
    recognition.maxAlternatives = 3
    recognition.lang = 'es-ES'

    recognition.onstart = () => {
      setPhase('listening')
      setError(null)
    }

    recognition.onend = () => {
      if (timerRef.current) clearTimeout(timerRef.current)

      // Corte del motor (silencio / límite interno): reanudar si el usuario
      // sigue en modo dictado. Sin esto Chrome termina a cada pausa y el
      // pipeline inserta basura parcial.
      if (wantListenRef.current && !userStoppedRef.current && autoRestartsRef.current < MAX_AUTORESTARTS) {
        autoRestartsRef.current += 1
        try {
          recognition.start()
          if (timerRef.current) clearTimeout(timerRef.current)
          timerRef.current = setTimeout(() => {
            userStoppedRef.current = true
            wantListenRef.current = false
            try {
              recognition.stop()
            } catch {
              // ignore
            }
          }, MAX_SESSION_MS)
          return
        } catch {
          // fall through → procesar lo acumulado
        }
      }

      wantListenRef.current = false
      setPhase(transcriptRef.current.trim() ? 'processing' : 'idle')
      setInterimTranscript('')
    }

    recognition.onerror = (event) => {
      // "no-speech" / "aborted" en reinicios automáticos no son errores fatales.
      if (event.error === 'aborted') {
        setError(null)
        return
      }
      if (event.error === 'no-speech') {
        // Silencio: si el usuario sigue dictando, onend reintentará.
        setError(null)
        return
      }
      if (event.error === 'not-allowed') {
        setError('Permiso de micrófono denegado')
        wantListenRef.current = false
        userStoppedRef.current = true
      } else if (event.error === 'network') {
        setError('Error de red del reconocimiento de voz')
        wantListenRef.current = false
      } else {
        setError(`Error de voz: ${event.error}`)
      }
      if (transcriptRef.current.trim() && (event.error === 'not-allowed' || event.error === 'network')) {
        setPhase('processing')
      } else if (!wantListenRef.current) {
        setPhase(transcriptRef.current.trim() ? 'processing' : 'idle')
      }
    }

    recognition.onresult = (event) => {
      const generation = generationRef.current
      if (generation !== generationRef.current) return

      // Reconstruir SIEMPRE desde todos los resultados de la sesión.
      const finals = buildFinalTranscript(event.results)
      const interim = buildInterimTranscript(event.results)
      const cleaned = dedupeSpeechText(finals)

      setTranscript(() => {
        if (generation !== generationRef.current) return transcriptRef.current
        transcriptRef.current = cleaned
        return cleaned
      })
      setInterimTranscript(interim)
    }

    recognitionRef.current = recognition

    return () => {
      wantListenRef.current = false
      userStoppedRef.current = true
      try {
        recognition.abort()
      } catch {
        try {
          recognition.stop()
        } catch {
          // ignore
        }
      }
    }
  }, [supported])

  const resetTranscript = useCallback(() => {
    generationRef.current += 1
    setTranscript('')
    setInterimTranscript('')
    transcriptRef.current = ''
  }, [])

  const completeProcessing = useCallback(() => {
    generationRef.current += 1
    setTranscript('')
    setInterimTranscript('')
    transcriptRef.current = ''
    setPhase('idle')
  }, [])

  const start = useCallback(() => {
    resetTranscript()
    setError(null)
    userStoppedRef.current = false
    wantListenRef.current = true
    autoRestartsRef.current = 0
    setPhase('listening')
    try {
      recognitionRef.current?.start()
      if (timerRef.current) clearTimeout(timerRef.current)
      timerRef.current = setTimeout(() => {
        // Límite duro de sesión: trata como stop del usuario.
        userStoppedRef.current = true
        wantListenRef.current = false
        try {
          recognitionRef.current?.stop()
        } catch {
          // ignore
        }
      }, MAX_SESSION_MS)
    } catch {
      setError('No se pudo iniciar el dictado')
      setPhase('idle')
      wantListenRef.current = false
    }
  }, [resetTranscript])

  const stop = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current)
    userStoppedRef.current = true
    wantListenRef.current = false
    const hasText = transcriptRef.current.trim().length > 0
    // Anticipar processing antes de onend para que el consumer no pierda el ciclo.
    setPhase(hasText ? 'processing' : 'idle')
    setInterimTranscript('')
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
    interimTranscript,
    error,
    start,
    stop,
    completeProcessing,
    resetTranscript,
  }
}
