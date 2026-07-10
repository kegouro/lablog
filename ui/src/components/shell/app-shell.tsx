import { useEffect } from 'react'
import { useShallow } from 'zustand/react/shallow'

import { LatexEditor } from '@/components/editor/latex-editor'
import { ErrorBoundary } from '@/components/error-boundary'
import { CellsPanel } from '@/components/panels/cells-panel'
import { ParametersPanel } from '@/components/panels/parameters-panel'
import { SnippetsPanel } from '@/components/panels/snippets-panel'
import { SymbolsPanel } from '@/components/panels/symbols-panel'
import { TutorialsPanel } from '@/components/panels/tutorials-panel'
import { VaultPanel } from '@/components/panels/vault-panel'
import { LatexPreview } from '@/components/preview/latex-preview'
import { getPage } from '@/lib/api'
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/components/ui/resizable'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  createPage,
  deletePage,
  listFavorites,
  listPages,
  listSnippets,
  listSymbols,
  listVaultFiles,
  updatePage,
} from '@/lib/api'
import { useAppStore } from '@/stores/app-store'

import { LabCanvas } from '../lab/lab-canvas'
import { Sidebar } from './sidebar'
import { Toolbar } from './toolbar'
import { WelcomeDialog } from './welcome-dialog'

const PANELS: Record<string, React.FC> = {
  vault: VaultPanel,
  snippets: SnippetsPanel,
  symbols: SymbolsPanel,
  cells: CellsPanel,
  tutorials: TutorialsPanel,
  parameters: ParametersPanel,
}

export function AppShell() {
  const setPages = useAppStore((s) => s.setPages)
  const setVaultFiles = useAppStore((s) => s.setVaultFiles)
  const setSnippets = useAppStore((s) => s.setSnippets)
  const setSymbols = useAppStore((s) => s.setSymbols)
  const setFavorites = useAppStore((s) => s.setFavorites)
  const setActivePageId = useAppStore((s) => s.setActivePageId)
  const setActiveLatex = useAppStore((s) => s.setActiveLatex)
  const setActiveAst = useAppStore((s) => s.setActiveAst)
  const setActiveVersion = useAppStore((s) => s.setActiveVersion)
  const activePageId = useAppStore((s) => s.activePageId)
  const activeVersion = useAppStore((s) => s.activeVersion)
  const labMode = useAppStore((s) => s.labMode)
  const panels = useAppStore(useShallow((s) => s.panels))

  const reloadActivePage = async () => {
    const id = useAppStore.getState().activePageId
    if (!id) return
    try {
      const page = await getPage(id)
      setActiveLatex(page.raw || page.latex)
      setActiveAst(page.ast)
      setActiveVersion(page.version)
    } catch (err) {
      console.error(err)
    }
  }

  useEffect(() => {
    async function load() {
      const [pages, vaultFiles, snippets, symbols, favorites] = await Promise.all([
        listPages(),
        listVaultFiles(),
        listSnippets(),
        listSymbols(),
        listFavorites(),
      ])
      setPages(pages)
      setVaultFiles(vaultFiles)
      setSnippets(snippets)
      setSymbols(symbols)
      setFavorites(favorites)
      if (pages.length > 0 && !useAppStore.getState().activePageId) {
        setActivePageId(pages[0].id)
      }
    }
    load()
  }, [setPages, setVaultFiles, setSnippets, setSymbols, setFavorites, setActivePageId])

  const refreshPages = async () => {
    const pages = await listPages()
    setPages(pages)
    const currentActivePageId = useAppStore.getState().activePageId
    if (pages.length > 0 && !pages.find((p) => p.id === currentActivePageId)) {
      setActivePageId(pages[0].id)
    } else if (pages.length === 0) {
      setActivePageId(null)
    }
  }

  const handleCreatePage = async () => {
    try {
      const page = await createPage('Nueva página')
      setPages([page, ...useAppStore.getState().pages])
      setActivePageId(page.id)
    } catch (err) {
      console.error(err)
      alert('No se pudo crear la página. ¿Está corriendo el backend?')
    }
  }

  const handleUpdatePage = async (id: string, data: { title?: string; project_id?: string | null }) => {
    try {
      await updatePage(id, data)
      await refreshPages()
    } catch (err) {
      console.error(err)
      alert('No se pudo actualizar la página')
    }
  }

  const handleDeletePage = async (id: string) => {
    try {
      await deletePage(id)
      await refreshPages()
    } catch (err) {
      console.error(err)
      alert('No se pudo eliminar la página')
    }
  }

  const activePanel =
    panels.parameters ? 'parameters' :
    panels.tutorials ? 'tutorials' :
    panels.cells ? 'cells' :
    panels.snippets ? 'snippets' :
    panels.symbols ? 'symbols' :
    panels.vault ? 'vault' : null

  const PanelComponent = activePanel ? PANELS[activePanel] : null

  const boundaryKey = `${activePageId ?? 'none'}:${activeVersion}`

  if (labMode) {
    return (
      <div className="flex h-full flex-col">
        <Toolbar onCreatePage={handleCreatePage} />
        <ErrorBoundary
          label="Laboratorio"
          resetKey={boundaryKey}
          onReset={() => void reloadActivePage()}
        >
          <LabCanvas />
        </ErrorBoundary>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col">
      <Toolbar onCreatePage={handleCreatePage} />
      <div className="flex min-h-0 flex-1">
        <Sidebar
          onCreatePage={handleCreatePage}
          onUpdatePage={handleUpdatePage}
          onDeletePage={handleDeletePage}
        />
        <main className="relative flex min-h-0 flex-1">
          <ResizablePanelGroup orientation="horizontal" className="flex-1">
            <ResizablePanel defaultSize={55} minSize={30}>
              <ScrollArea className="h-full">
                <div className="h-[calc(100vh-3rem)] p-4">
                  <ErrorBoundary
                    label="Editor"
                    resetKey={boundaryKey}
                    onReset={() => void reloadActivePage()}
                  >
                    <LatexEditor />
                  </ErrorBoundary>
                </div>
              </ScrollArea>
            </ResizablePanel>
            <ResizableHandle withHandle className="transition-colors hover:bg-primary/20" />
            <ResizablePanel defaultSize={45} minSize={25}>
              <ScrollArea className="h-full">
                <div className="h-[calc(100vh-3rem)] p-4">
                  <ErrorBoundary
                    label="Vista previa"
                    resetKey={boundaryKey}
                    onReset={() => void reloadActivePage()}
                  >
                    <LatexPreview />
                  </ErrorBoundary>
                </div>
              </ScrollArea>
            </ResizablePanel>
          </ResizablePanelGroup>

          <aside
            className={[
              'absolute inset-y-0 right-0 z-20 w-80 border-l bg-card/95 backdrop-blur shadow-2xl',
              'transform transition-all duration-300 ease-[cubic-bezier(0.25,0.46,0.45,0.94)]',
              activePanel ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0 pointer-events-none',
            ].join(' ')}
          >
            <ScrollArea className="h-full">
              {PanelComponent && <PanelComponent />}
            </ScrollArea>
          </aside>
        </main>
      </div>
      <WelcomeDialog />
    </div>
  )
}
