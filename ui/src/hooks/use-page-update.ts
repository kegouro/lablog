import { useCallback, useEffect, useRef, useState } from 'react'

import { ApiError, updatePageRaw } from '@/lib/api'
import type { Page } from '@/types'

interface UsePageUpdateResult {
  status: 'idle' | 'saving' | 'saved' | 'error'
  updateRaw: (raw: string) => void
  flush: () => Promise<Page | undefined>
  /** Cancela debounce y descarta draft local (p.ej. tras congelar params). */
  discardPending: () => void
}

const DEBOUNCE_MS = 300

export function usePageUpdate(
  pageId: string | null,
  onUpdate?: (page: Page) => void,
  /** Versión del event log para optimistic concurrency (opcional). */
  getVersion?: () => number | undefined,
): UsePageUpdateResult {
  const [status, setStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const pendingRef = useRef<string | null>(null)
  const genRef = useRef(0)
  const inflightRef = useRef<Promise<Page | undefined> | null>(null)

  useEffect(() => {
    const previousPageId = pageId
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current)
        timerRef.current = null
      }
      const raw = pendingRef.current
      pendingRef.current = null
      genRef.current += 1
      if (raw != null && previousPageId) {
        const version = getVersion?.()
        void updatePageRaw(previousPageId, raw, version).catch((err) => {
          // Página eliminada / 409: no reintentar en unmount.
          if (err instanceof ApiError && (err.status === 404 || err.status === 409)) return
        })
      }
    }
  }, [pageId, getVersion])

  const save = useCallback(
    async (raw: string): Promise<Page | undefined> => {
      if (!pageId) return
      const gen = genRef.current
      setStatus('saving')
      const version = getVersion?.()
      const work = (async (): Promise<Page | undefined> => {
        try {
          const page = await updatePageRaw(pageId, raw, version)
          if (gen !== genRef.current || pendingRef.current !== null) {
            return page
          }
          setStatus('saved')
          onUpdate?.(page)
          return page
        } catch (err) {
          if (gen === genRef.current) {
            setStatus('error')
            // Re-encola el draft si el servidor falló (salvo conflicto de versión).
            if (!(err instanceof ApiError && err.status === 409)) {
              pendingRef.current = raw
            }
          }
          throw err
        }
      })()
      inflightRef.current = work
      try {
        return await work
      } finally {
        if (inflightRef.current === work) {
          inflightRef.current = null
        }
      }
    },
    [pageId, onUpdate, getVersion],
  )

  const updateRaw = useCallback(
    (raw: string) => {
      pendingRef.current = raw
      genRef.current += 1
      if (timerRef.current) clearTimeout(timerRef.current)
      setStatus('saving')
      const genAtSchedule = genRef.current
      timerRef.current = setTimeout(() => {
        timerRef.current = null
        if (genAtSchedule !== genRef.current) return
        const toSave = pendingRef.current
        pendingRef.current = null
        if (toSave != null) {
          void save(toSave).catch(() => {
            /* status ya es error */
          })
        }
      }, DEBOUNCE_MS)
    },
    [save],
  )

  const discardPending = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current)
      timerRef.current = null
    }
    pendingRef.current = null
    genRef.current += 1
  }, [])

  const flush = useCallback(async (): Promise<Page | undefined> => {
    if (timerRef.current) {
      clearTimeout(timerRef.current)
      timerRef.current = null
    }
    const raw = pendingRef.current
    pendingRef.current = null
    if (raw != null) {
      return save(raw)
    }
    if (inflightRef.current) {
      return inflightRef.current
    }
  }, [save])

  return { status, updateRaw, flush, discardPending }
}
