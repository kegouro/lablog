import { afterEach, describe, expect, it, vi } from 'vitest'

import { deleteCell, deletePage } from './api'

describe('fetchJson empty-body responses', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('resolves DELETE 204 without parsing JSON', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 204,
      text: async () => '',
      headers: { get: () => null },
    })
    vi.stubGlobal('fetch', fetchMock)

    await expect(deletePage('aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee')).resolves.toBeUndefined()
    await expect(
      deleteCell('aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'c1'),
    ).resolves.toBeUndefined()
    expect(fetchMock).toHaveBeenCalled()
  })
})
