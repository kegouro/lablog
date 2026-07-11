import { describe, expect, it } from 'vitest'

import { downsample, encodeWav } from './record-wav'

describe('record-wav helpers', () => {
  it('downsample halves length when rate doubles', () => {
    const input = new Float32Array([0, 0.5, 1, 0.5, 0, -0.5, -1, -0.5])
    const out = downsample(input, 32_000, 16_000)
    expect(out.length).toBe(4)
  })

  it('encodeWav produces a valid header', async () => {
    const samples = new Float32Array(1600)
    for (let i = 0; i < samples.length; i++) samples[i] = Math.sin(i / 10) * 0.2
    const blob = encodeWav(samples, 16_000)
    expect(blob.type).toBe('audio/wav')
    expect(blob.size).toBe(44 + samples.length * 2)
    const buf = new Uint8Array(await blob.arrayBuffer())
    const ascii = String.fromCharCode(...buf.slice(0, 4))
    expect(ascii).toBe('RIFF')
  })
})
