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

  // Cancela cualquier guardado pendiente cuando cambia la página activa.
  useEffect(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current)
      timerRef.current = null
    }
    pendingRef.current = null
    setStatus('idle')
  }, [pageId])

  const save = useCallback(
    async (raw: string): Promise<Page | undefined> => {
      if (!pageId) return
      setStatus('saving')
      try {
        const page = await updatePageRaw(pageId, raw)
        setStatus('saved')
        onUpdate?.(page)
        return page
      } catch {
        setStatus('error')
      }
    },
    [pageId, onUpdate],
  )

  const updateRaw = useCallback(
    (raw: string) => {
      pendingRef.current = raw
      if (timerRef.current) clearTimeout(timerRef.current)
      setStatus('saving')
      timerRef.current = setTimeout(() => {
        timerRef.current = null
        void save(raw)
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
