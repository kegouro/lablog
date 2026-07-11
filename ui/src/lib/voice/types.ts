/** Identificadores de motores de dictado (cliente + servidor). */
export type VoiceEngineId = 'browser' | 'whisper' | 'vosk' | (string & {})

/** Tamaños de modelo Whisper seleccionables en la UI. */
export type WhisperModelSize = 'tiny' | 'base' | 'small' | 'medium' | 'large-v3'

export const WHISPER_MODEL_SIZES: { id: WhisperModelSize; label: string; hint: string }[] = [
  { id: 'tiny', label: 'tiny', hint: '~75 MB · más rápido' },
  { id: 'base', label: 'base', hint: '~150 MB · equilibrado' },
  { id: 'small', label: 'small', hint: '~500 MB · más preciso' },
  { id: 'medium', label: 'medium', hint: '~1.5 GB · lento en CPU' },
  { id: 'large-v3', label: 'large-v3', hint: '~3 GB · máx. calidad' },
]

export interface VoiceEngineInfo {
  id: string
  label: string
  kind: 'local' | 'client' | string
  available: boolean
  description?: string
  requires_extra?: string | null
  options?: Record<string, unknown>
}

export interface TranscribeResult {
  status: string
  text: string
  engine: string
  language?: string | null
  meta?: Record<string, unknown>
}

export interface VoiceAudioInsertResult {
  status: string
  intent: string
  text: string
  engine?: string
  inserted: boolean
  language?: string | null
}
