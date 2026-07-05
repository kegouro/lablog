import {
  Download,
  FileArchive,
  FileCode,
  FileImage,
  FileSpreadsheet,
  FileText,
  FileType,
  Trash2,
  Upload,
  X,
} from 'lucide-react'
import { useRef, useState } from 'react'

import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  cancelVaultDeletion,
  previewVaultFile,
  requestVaultDeletion,
  uploadVaultFile,
  vaultFileDownloadUrl,
} from '@/lib/api'
import { useAppStore } from '@/stores/app-store'

interface PreviewState {
  fileId: string
  type: string
  content?: string
  rows?: string[][]
  path?: string
  mime_type?: string
}

const FORMATS: Record<string, string> = {
  'text/plain': 'txt',
  'text/markdown': 'md',
  'text/csv': 'csv',
  'application/pdf': 'pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
  'application/msword': 'doc',
}

function fileBadge(mime: string) {
  return FORMATS[mime] ?? mime.split('/')[1] ?? 'file'
}

function fileIcon(mime: string) {
  if (mime.startsWith('image/')) return FileImage
  if (mime === 'text/csv' || mime.includes('spreadsheet')) return FileSpreadsheet
  if (mime === 'application/pdf') return FileType
  if (mime.includes('word')) return FileText
  if (mime === 'text/plain' || mime === 'text/markdown') return FileCode
  return FileArchive
}

export function VaultPanel() {
  const vaultFiles = useAppStore((s) => s.vaultFiles)
  const setVaultFiles = useAppStore((s) => s.setVaultFiles)
  const togglePanel = useAppStore((s) => s.togglePanel)
  const [dragging, setDragging] = useState(false)
  const [preview, setPreview] = useState<PreviewState | null>(null)
  const [loadingPreview, setLoadingPreview] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleUpload = async (file: File) => {
    try {
      const uploaded = await uploadVaultFile(file)
      setVaultFiles([uploaded, ...vaultFiles])
    } catch (err) {
      console.error(err)
      toast.error('No se pudo subir el archivo')
    } finally {
      // Permite re-subir el mismo archivo (el input no dispara onChange si no cambia).
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) await handleUpload(file)
  }

  const handleDelete = async (id: string) => {
    try {
      await requestVaultDeletion(id)
      setVaultFiles(
        vaultFiles.map((f) => (f.id === id ? { ...f, status: 'pending_deletion' as const } : f)),
      )
      if (preview?.fileId === id) setPreview(null)
    } catch (err) {
      console.error(err)
      toast.error('No se pudo programar el borrado')
    }
  }

  const handleCancelDelete = async (id: string) => {
    try {
      await cancelVaultDeletion(id)
      setVaultFiles(
        vaultFiles.map((f) =>
          f.id === id ? { ...f, status: 'active' as const, scheduled_for_deletion_at: null } : f,
        ),
      )
    } catch (err) {
      console.error(err)
      toast.error('No se pudo restaurar el archivo')
    }
  }

  const handlePreview = async (file: { id: string; mime_type: string }) => {
    setLoadingPreview(file.id)
    try {
      const data = await previewVaultFile(file.id)
      setPreview({ fileId: file.id, ...data })
    } finally {
      setLoadingPreview(null)
    }
  }

  const selectedFile = vaultFiles.find((f) => f.id === preview?.fileId)

  return (
    <Card className="m-2 border-0 shadow-none">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-semibold">Bóveda</CardTitle>
        <Button variant="ghost" size="icon" className="size-7" onClick={() => togglePanel('vault')}>
          <X className="size-4" />
        </Button>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div
          onClick={() => inputRef.current?.click()}
          onDrop={handleDrop}
          onDragOver={(e) => {
            e.preventDefault()
            setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          className={[
            'cursor-pointer rounded-xl border-2 border-dashed p-4 text-center text-xs transition-all duration-200',
            dragging ? 'border-primary bg-primary/5 scale-[1.02]' : 'border-muted-foreground/25 hover:border-primary/40 hover:bg-muted/30',
          ].join(' ')}
        >
          <Upload className="mx-auto mb-1 size-4 text-muted-foreground" />
          Arrastra un archivo o haz clic para subir
          <input
            ref={inputRef}
            type="file"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) handleUpload(file)
            }}
          />
        </div>

        <div className="flex flex-col gap-1.5">
          {vaultFiles.map((file) => {
            const Icon = fileIcon(file.mime_type)
            const active = preview?.fileId === file.id
            return (
              <div
                key={file.id}
                className={[
                  'group flex items-center gap-2 rounded-xl border p-2 text-xs transition-all duration-200',
                  active ? 'border-primary/50 bg-primary/5' : 'hover:bg-muted/40',
                ].join(' ')}
              >
                <button
                  type="button"
                  onClick={() => handlePreview(file)}
                  className="flex flex-1 items-center gap-2 overflow-hidden text-left"
                >
                  <Icon className="size-4 shrink-0 text-muted-foreground" />
                  <div className="min-w-0">
                    <p className="truncate font-medium">{file.name}</p>
                    <p className="text-muted-foreground">
                      {file.status === 'pending_deletion'
                        ? 'pendiente de borrado'
                        : `${fileBadge(file.mime_type)} · ${formatBytes(file.size)}`}
                    </p>
                  </div>
                </button>
                {file.status === 'active' ? (
                  <Button variant="ghost" size="icon" className="size-6 opacity-60 group-hover:opacity-100" onClick={() => handleDelete(file.id)}>
                    <Trash2 className="size-3" />
                  </Button>
                ) : (
                  <Button variant="ghost" size="sm" className="h-6 text-[10px]" onClick={() => handleCancelDelete(file.id)}>
                    Restaurar
                  </Button>
                )}
              </div>
            )
          })}
          {vaultFiles.length === 0 && (
            <p className="py-4 text-center text-xs text-muted-foreground">La bóveda está vacía</p>
          )}
        </div>

        {selectedFile && preview && (
          <div className="mt-1 overflow-hidden rounded-xl border bg-muted/20">
            <div className="flex items-center justify-between border-b bg-muted/40 px-3 py-2">
              <div className="min-w-0">
                <p className="truncate text-xs font-medium">{selectedFile.name}</p>
                <p className="text-[10px] text-muted-foreground">Vista previa</p>
              </div>
              <div className="flex items-center gap-1">
                <Button variant="ghost" size="icon" className="size-6" asChild>
                  <a href={vaultFileDownloadUrl(selectedFile.id)} download={selectedFile.name} title="Descargar">
                    <Download className="size-3.5" />
                  </a>
                </Button>
                <Button variant="ghost" size="icon" className="size-6" onClick={() => setPreview(null)}>
                  <X className="size-3.5" />
                </Button>
              </div>
            </div>
            <div className="max-h-96 overflow-auto p-2">
              {loadingPreview === selectedFile.id ? (
                <p className="py-8 text-center text-xs text-muted-foreground">Cargando vista previa…</p>
              ) : (
                <PreviewContent preview={preview} fileId={selectedFile.id} name={selectedFile.name} />
              )}
            </div>
          </div>
        )}

      </CardContent>
    </Card>
  )
}

function PreviewContent({ preview, fileId, name }: { preview: PreviewState; fileId: string; name: string }) {
  if (preview.type === 'text' || preview.type === 'markdown') {
    return (
      <pre className="whitespace-pre-wrap font-mono text-xs leading-relaxed">{preview.content}</pre>
    )
  }

  if (preview.type === 'csv' && preview.rows) {
    return (
      <div className="overflow-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b">
              {preview.rows[0]?.map((h, i) => (
                <th key={i} className="px-2 py-1 text-left font-semibold">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {preview.rows.slice(1).map((row, i) => (
              <tr key={i} className="border-b last:border-0">
                {row.map((cell, j) => (
                  <td key={j} className="px-2 py-1">{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  if (preview.type === 'pdf') {
    return (
      <div className="flex flex-col gap-2">
        <iframe
          src={vaultFileDownloadUrl(fileId)}
          title={name}
          className="h-80 w-full rounded-lg border"
        />
        <p className="text-center text-[10px] text-muted-foreground">
          Si no se muestra, usa el botón de descarga.
        </p>
      </div>
    )
  }

  if (preview.type === 'docx') {
    return (
      <pre className="whitespace-pre-wrap font-mono text-xs leading-relaxed">{preview.content}</pre>
    )
  }

  if (preview.type === 'image' && preview.path) {
    return (
      <img
        src={preview.path}
        alt={name}
        className="max-h-80 w-full rounded-lg object-contain"
      />
    )
  }

  return (
    <div className="flex flex-col items-center gap-2 py-6 text-center">
      <FileArchive className="size-8 text-muted-foreground" />
      <p className="text-xs text-muted-foreground">
        No hay vista previa para {preview.mime_type || 'este archivo'}.
      </p>
      <Button size="sm" variant="outline" asChild>
        <a href={vaultFileDownloadUrl(fileId)} download={name}>
          <Download className="mr-1 size-3.5" /> Descargar
        </a>
      </Button>
    </div>
  )
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}
