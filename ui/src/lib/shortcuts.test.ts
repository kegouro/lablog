import { describe, expect, it } from 'vitest'

import { isValidChord, matchChord } from './shortcuts'

function keyEvent(partial: Partial<KeyboardEvent> & { key: string }): KeyboardEvent {
  return {
    key: partial.key,
    code: partial.code ?? `Key${partial.key.toUpperCase()}`,
    metaKey: partial.metaKey ?? false,
    ctrlKey: partial.ctrlKey ?? false,
    shiftKey: partial.shiftKey ?? false,
    altKey: partial.altKey ?? false,
  } as KeyboardEvent
}

describe('matchChord', () => {
  it('matches mod+k with meta', () => {
    expect(matchChord(keyEvent({ key: 'k', metaKey: true }), 'mod+k')).toBe(true)
  })
  it('matches mod+k with ctrl', () => {
    expect(matchChord(keyEvent({ key: 'k', ctrlKey: true }), 'mod+k')).toBe(true)
  })
  it('rejects without modifier', () => {
    expect(matchChord(keyEvent({ key: 'k' }), 'mod+k')).toBe(false)
  })
  it('matches mod+shift+d', () => {
    expect(
      matchChord(keyEvent({ key: 'd', metaKey: true, shiftKey: true }), 'mod+shift+d'),
    ).toBe(true)
  })
  it('rejects mod+shift+d without shift', () => {
    expect(matchChord(keyEvent({ key: 'd', metaKey: true }), 'mod+shift+d')).toBe(false)
  })
})

describe('isValidChord', () => {
  it('accepts mod+shift+p', () => {
    expect(isValidChord('mod+shift+p')).toBe(true)
  })
  it('rejects empty', () => {
    expect(isValidChord('')).toBe(false)
  })
})
