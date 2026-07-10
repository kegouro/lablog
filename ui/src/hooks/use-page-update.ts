import { useCallback, useEffect, useRef, useState } from 'react'

import { updatePageRaw } from '@/lib/api'
import type { Page } from '@/types'

interface UsePageUpdateResult {
  status: 'idle' | 'saving' | 'saved' | 'error'
  updateRaw: (raw: string) => void
  flush: () => Promise<Page | undefined>
}

const DEBOUNCE_MS = 300

export function usePageUpdate(
  pageId: string | null,
  onUpdate?: (page: Page) => void,
): UsePageUpdateResult {
  const [status, setStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const pendingRef = useRef<string | null>(null)
  /** Descarta respuestas de saves obsoletos si el usuario siguió escribiendo. */
  const genRef = useRef(0)

  // Cancela cualquier guardado pendiente cuando cambia la página activa.
  useEffect(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current)
      timerRef.current = null
    }
    pendingRef.current = null
    genRef.current += 1
    setStatus('idle')
  }, [pageId])

  const save = useCallback(
    async (raw: string): Promise<Page | undefined> => {
      if (!pageId) return
      const gen = genRef.current
      setStatus('saving')
      try {
        const page = await updatePageRaw(pageId, raw)
        // Si el draft local ya es más nuevo, no pisar AST/versión con respuesta vieja.
        if (gen !== genRef.current || pendingRef.current !== null) {
          return page
        }
        setStatus('saved')
        onUpdate?.(page)
        return page
      } catch {
        if (gen === genRef.current) setStatus('error')
      }
    },
    [pageId, onUpdate],
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
        if (toSave != null) void save(toSave)
      }, DEBOUNCE_MS)
    },
    [save],
  )

  const flush = useCallback(async (): Promise<Page | undefined> => {
    if (timerRef.current) {
      clearTimeout(timerRef.current)
      timerRef.current = null
    }
    const raw = pendingRef.current
    pendingRef.current = null
    if (raw != null) return save(raw)
  }, [save])

  return { status, updateRaw, flush }
}
