import { describe, expect, it } from 'vitest'

import { cn } from './utils'

describe('cn', () => {
  it('merges class names', () => {
    expect(cn('foo', 'bar')).toBe('foo bar')
  })

  it('applies tailwind-merge to resolve conflicts', () => {
    expect(cn('px-2 px-4')).toBe('px-4')
  })

  it('ignores falsy values', () => {
    const disabled = false
    expect(cn('foo', disabled && 'bar', undefined, 'baz')).toBe('foo baz')
  })
})
