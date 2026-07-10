import { afterEach, describe, expect, it, vi } from 'vitest'

import { deleteCell, deletePage, getPage } from './api'

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

  it('detailToPage preserves project_id and updated_at from wire', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      text: async () =>
        JSON.stringify({
          page_id: 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
          title: 'Optics',
          project_id: 'lab-1',
          latex: 'x',
          raw: 'x',
          ast: [],
          version: 3,
          updated_at: '2026-01-15T12:00:00Z',
        }),
      headers: { get: () => 'application/json' },
    })
    vi.stubGlobal('fetch', fetchMock)

    const page = await getPage('aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee')
    expect(page.project_id).toBe('lab-1')
    expect(page.updated_at).toBe('2026-01-15T12:00:00Z')
    expect(page.title).toBe('Optics')
    expect(page.version).toBe(3)
  })
})
