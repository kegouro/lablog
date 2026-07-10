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

function conflictCurrent(err: unknown): number | null {
  if (!(err instanceof ApiError) || err.status !== 409) return null
  const d = err.detail
  if (d && typeof d === 'object' && d !== null && 'current' in d) {
    const cur = (d as { current?: unknown }).current
    if (typeof cur === 'number' && Number.isFinite(cur)) return cur
  }
  return null
}

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
          // Página eliminada: no reintentar en unmount.
          if (err instanceof ApiError && err.status === 404) return
          // 409: un reintento con la versión del servidor.
          const cur = conflictCurrent(err)
          if (cur != null) {
            void updatePageRaw(previousPageId, raw, cur).catch(() => {
              /* best-effort unmount */
            })
          }
        })
      }
    }
  }, [pageId, getVersion])

  const save = useCallback(
    async (raw: string): Promise<Page | undefined> => {
      if (!pageId) return

      // Serializa: espera al PUT anterior para no mandar dos veces la misma versión.
      const prev = inflightRef.current
      if (prev) {
        try {
          await prev
        } catch {
          /* el error ya se reportó */
        }
      }

      const gen = genRef.current
      setStatus('saving')
      // Versión fresca tras await del inflight (onUpdate pudo actualizar el store).
      const version = getVersion?.()

      const work = (async (): Promise<Page | undefined> => {
        try {
          let page: Page
          try {
            page = await updatePageRaw(pageId, raw, version)
          } catch (err) {
            const cur = conflictCurrent(err)
            if (cur == null) throw err
            // Un reintento con la versión actual del servidor.
            page = await updatePageRaw(pageId, raw, cur)
          }
          // Siempre refresca versión/AST aunque haya otro draft pendiente.
          onUpdate?.(page)
          if (gen !== genRef.current || pendingRef.current !== null) {
            setStatus('saving')
            return page
          }
          setStatus('saved')
          return page
        } catch (err) {
          if (gen === genRef.current) {
            setStatus('error')
            // Conserva el draft (incl. 409 sin reintento viable) para no perder texto.
            pendingRef.current = raw
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
    // Espera inflight antes de decidir si hay draft pendiente.
    if (inflightRef.current) {
      try {
        await inflightRef.current
      } catch {
        /* continue with pending draft */
      }
    }
    const raw = pendingRef.current
    pendingRef.current = null
    if (raw != null) {
      return save(raw)
    }
  }, [save])

  return { status, updateRaw, flush, discardPending }
}
