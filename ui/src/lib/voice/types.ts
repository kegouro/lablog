/** Identificadores de motores de dictado (cliente + servidor). */
export type VoiceEngineId = 'browser' | 'whisper' | (string & {})

export interface VoiceEngineInfo {
  id: string
  label: string
  kind: 'local' | 'client' | string
  available: boolean
  description?: string
  requires_extra?: string | null
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
