/**
 * Captura de micrófono → WAV PCM 16 kHz mono.
 *
 * Formato simple que faster-whisper entiende sin depender de ffmpeg
 * en el servidor para el caso común.
 */

const TARGET_SR = 16_000

export interface WavRecorder {
  start: () => Promise<void>
  stop: () => Promise<Blob>
  /** true mientras graba */
  readonly recording: boolean
}

export function createWavRecorder(): WavRecorder {
  let mediaStream: MediaStream | null = null
  let context: AudioContext | null = null
  let processor: ScriptProcessorNode | null = null
  let source: MediaStreamAudioSourceNode | null = null
  let chunks: Float32Array[] = []
  let recording = false
  let inputSampleRate = TARGET_SR

  return {
    get recording() {
      return recording
    },

    async start() {
      if (recording) return
      chunks = []
      mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      })
      const Ctx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
      context = new Ctx()
      inputSampleRate = context.sampleRate
      source = context.createMediaStreamSource(mediaStream)
      // ScriptProcessor está deprecado pero es el más portable sin AudioWorklet bundle.
      processor = context.createScriptProcessor(4096, 1, 1)
      processor.onaudioprocess = (ev) => {
        if (!recording) return
        const input = ev.inputBuffer.getChannelData(0)
        chunks.push(new Float32Array(input))
      }
      source.connect(processor)
      processor.connect(context.destination)
      recording = true
    },

    async stop() {
      recording = false
      try {
        processor?.disconnect()
        source?.disconnect()
      } catch {
        // ignore
      }
      processor = null
      source = null
      if (context) {
        try {
          await context.close()
        } catch {
          // ignore
        }
      }
      context = null
      mediaStream?.getTracks().forEach((t) => t.stop())
      mediaStream = null

      const merged = mergeFloat32(chunks)
      chunks = []
      const resampled = downsample(merged, inputSampleRate, TARGET_SR)
      return encodeWav(resampled, TARGET_SR)
    },
  }
}

function mergeFloat32(parts: Float32Array[]): Float32Array {
  const total = parts.reduce((n, p) => n + p.length, 0)
  const out = new Float32Array(total)
  let offset = 0
  for (const p of parts) {
    out.set(p, offset)
    offset += p.length
  }
  return out
}

/** Downsample lineal barato a TARGET_SR. */
export function downsample(input: Float32Array, fromSr: number, toSr: number): Float32Array {
  if (fromSr === toSr || input.length === 0) return input
  const ratio = fromSr / toSr
  const newLen = Math.max(1, Math.round(input.length / ratio))
  const out = new Float32Array(newLen)
  for (let i = 0; i < newLen; i++) {
    const idx = i * ratio
    const i0 = Math.floor(idx)
    const i1 = Math.min(i0 + 1, input.length - 1)
    const frac = idx - i0
    out[i] = input[i0] * (1 - frac) + input[i1] * frac
  }
  return out
}

/** Codifica PCM float [-1,1] a WAV 16-bit LE. */
export function encodeWav(samples: Float32Array, sampleRate: number): Blob {
  const buffer = new ArrayBuffer(44 + samples.length * 2)
  const view = new DataView(buffer)

  writeString(view, 0, 'RIFF')
  view.setUint32(4, 36 + samples.length * 2, true)
  writeString(view, 8, 'WAVE')
  writeString(view, 12, 'fmt ')
  view.setUint32(16, 16, true) // PCM chunk size
  view.setUint16(20, 1, true) // PCM
  view.setUint16(22, 1, true) // mono
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * 2, true) // byte rate
  view.setUint16(32, 2, true) // block align
  view.setUint16(34, 16, true) // bits
  writeString(view, 36, 'data')
  view.setUint32(40, samples.length * 2, true)

  let offset = 44
  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1, Math.min(1, samples[i] ?? 0))
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true)
    offset += 2
  }
  return new Blob([buffer], { type: 'audio/wav' })
}

function writeString(view: DataView, offset: number, str: string) {
  for (let i = 0; i < str.length; i++) {
    view.setUint8(offset + i, str.charCodeAt(i))
  }
}
