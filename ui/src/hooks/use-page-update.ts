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
  /** PUT en vuelo: flush debe esperarlo para no insertar celdas sobre un replace viejo. */
  const inflightRef = useRef<Promise<Page | undefined> | null>(null)
  const pageIdRef = useRef(pageId)
  pageIdRef.current = pageId

  // Al cambiar de página o desmontar: cancela debounce y persiste draft pendiente.
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
        void updatePageRaw(previousPageId, raw).catch(() => {
          // best-effort: no hay UI al desmontar
        })
      }
    }
  }, [pageId])

  const save = useCallback(
    async (raw: string): Promise<Page | undefined> => {
      if (!pageId) return
      const gen = genRef.current
      setStatus('saving')
      const work = (async (): Promise<Page | undefined> => {
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
          return undefined
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
    if (raw != null) {
      return save(raw)
    }
    // Espera el PUT ya enviado para que insertCell no pierda la carrera.
    if (inflightRef.current) {
      return inflightRef.current
    }
  }, [save])

  return { status, updateRaw, flush }
}
