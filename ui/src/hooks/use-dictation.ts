/**
 * Hook unificado de dictado: elige motor (browser | whisper | …) y
 * expone la misma FSM que el toolbar ya consume.
 *
 * - browser: Web Speech API (cliente, gratis, impreciso)
 * - whisper: graba WAV → POST /voice (local, gratis, preciso; elige modelo)
 * - vosk: graba WAV → POST /voice (local, gratis, ligero)
 */
import { useCallback, useEffect, useRef, useState } from 'react'

import { listVoiceEngines, sendVoiceAudio, type VoiceEngineInfo } from '@/lib/api'
import { createWavRecorder, type WavRecorder } from '@/lib/voice/record-wav'
import type { VoiceEngineId } from '@/lib/voice/types'
import { useAppStore } from '@/stores/app-store'

import {
  dedupeSpeechText,
  useSpeechRecognition,
  type SpeechPhase,
} from './use-speech'

export type DictationPhase = SpeechPhase

export interface DictationHook {
  phase: DictationPhase
  listening: boolean
  supported: boolean
  transcript: string
  interimTranscript: string
  error: string | null
  engineId: VoiceEngineId
  engines: VoiceEngineInfo[]
  enginesLoading: boolean
  start: () => void
  stop: () => void
  completeProcessing: () => void
  /** Resultado listo para insertar (whisper rellena al parar; browser vía transcript). */
  pendingText: string
  /** Tras insertar con whisper, limpia el pending. */
  clearPending: () => void
  /** true si el motor actual es server-side (Whisper, etc.) */
  isServerEngine: boolean
}

export function useDictation(): DictationHook {
  const engineId = useAppStore((s) => s.voiceEngine)
  const whisperModel = useAppStore((s) => s.whisperModel)
  const [engines, setEngines] = useState<VoiceEngineInfo[]>([])
  const [enginesLoading, setEnginesLoading] = useState(true)
  const [serverPhase, setServerPhase] = useState<DictationPhase>('idle')
  const [serverError, setServerError] = useState<string | null>(null)
  const [pendingText, setPendingText] = useState('')
  const recorderRef = useRef<WavRecorder | null>(null)
  const pageIdRef = useRef<string | null>(null)

  const browser = useSpeechRecognition()
  const isServer = engineId !== 'browser'

  useEffect(() => {
    let cancelled = false
    setEnginesLoading(true)
    listVoiceEngines()
      .then((res) => {
        if (cancelled) return
        setEngines(res.engines)
      })
      .catch(() => {
        if (cancelled) return
        // Fallback mínimo si la API no responde.
        setEngines([
          {
            id: 'browser',
            label: 'Navegador (Web Speech)',
            kind: 'client',
            available: true,
            description: 'Dictado del navegador',
          },
        ])
      })
      .finally(() => {
        if (!cancelled) setEnginesLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const startServer = useCallback(async () => {
    setServerError(null)
    setPendingText('')
    setServerPhase('listening')
    try {
      const rec = createWavRecorder()
      recorderRef.current = rec
      await rec.start()
    } catch (err) {
      setServerPhase('idle')
      setServerError(
        err instanceof Error ? err.message : 'No se pudo acceder al micrófono',
      )
    }
  }, [])

  const stopServer = useCallback(async () => {
    const rec = recorderRef.current
    recorderRef.current = null
    if (!rec?.recording) {
      setServerPhase('idle')
      return
    }
    setServerPhase('processing')
    try {
      const blob = await rec.stop()
      if (blob.size < 1000) {
        setServerError('Grabación demasiado corta')
        setServerPhase('idle')
        return
      }
      const pageId = pageIdRef.current
      if (!pageId) {
        setServerError('Sin página activa')
        setServerPhase('idle')
        return
      }
      const res = await sendVoiceAudio(pageId, blob, {
        engine: engineId === 'browser' ? undefined : engineId,
        filename: 'dictation.wav',
        model: engineId === 'whisper' ? whisperModel : undefined,
      })
      const text = dedupeSpeechText(res.text || '')
      setPendingText(text)
      // processing se mantiene hasta que el toolbar complete (resync página).
      if (!res.inserted || !text) {
        setServerPhase('idle')
      }
    } catch (err) {
      setServerError(err instanceof Error ? err.message : 'Error al transcribir')
      setServerPhase('idle')
    }
  }, [engineId, whisperModel])

  const start = useCallback(() => {
    pageIdRef.current = useAppStore.getState().activePageId
    if (isServer) {
      void startServer()
    } else {
      browser.start()
    }
  }, [browser, isServer, startServer])

  const stop = useCallback(() => {
    if (isServer) {
      void stopServer()
    } else {
      browser.stop()
    }
  }, [browser, isServer, stopServer])

  const completeProcessing = useCallback(() => {
    if (isServer) {
      setPendingText('')
      setServerPhase('idle')
    } else {
      browser.completeProcessing()
    }
  }, [browser, isServer])

  const clearPending = useCallback(() => setPendingText(''), [])

  if (isServer) {
    return {
      phase: serverPhase,
      listening: serverPhase === 'listening',
      supported: typeof navigator !== 'undefined' && !!navigator.mediaDevices?.getUserMedia,
      transcript: pendingText,
      interimTranscript:
        serverPhase === 'listening'
          ? engineId === 'vosk'
            ? 'Grabando… (Vosk al soltar)'
            : `Grabando… (Whisper ${whisperModel} al soltar)`
          : '',
      error: serverError,
      engineId,
      engines,
      enginesLoading,
      start,
      stop,
      completeProcessing,
      pendingText,
      clearPending,
      isServerEngine: true,
    }
  }

  return {
    phase: browser.phase,
    listening: browser.listening,
    supported: browser.supported,
    transcript: browser.transcript,
    interimTranscript: browser.interimTranscript,
    error: browser.error,
    engineId,
    engines,
    enginesLoading,
    start,
    stop,
    completeProcessing,
    pendingText: browser.phase === 'processing' ? browser.transcript : '',
    clearPending: browser.completeProcessing,
    isServerEngine: false,
  }
}
