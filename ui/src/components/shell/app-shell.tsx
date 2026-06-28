import { useEffect } from 'react'

import { LatexEditor } from '@/components/editor/latex-editor'
import { CellsPanel } from '@/components/panels/cells-panel'
import { ParametersPanel } from '@/components/panels/parameters-panel'
import { SnippetsPanel } from '@/components/panels/snippets-panel'
import { SymbolsPanel } from '@/components/panels/symbols-panel'
import { TutorialsPanel } from '@/components/panels/tutorials-panel'
import { VaultPanel } from '@/components/panels/vault-panel'
import { LatexPreview } from '@/components/preview/latex-preview'
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
  const store = useAppStore()

  useEffect(() => {
    async function load() {
      const [pages, vaultFiles, snippets, symbols, favorites] = await Promise.all([
        listPages(),
        listVaultFiles(),
        listSnippets(),
        listSymbols(),
        listFavorites(),
      ])
      store.setPages(pages)
      store.setVaultFiles(vaultFiles)
      store.setSnippets(snippets)
      store.setSymbols(symbols)
      store.setFavorites(favorites)
      if (pages.length > 0 && !store.activePageId) {
        store.setActivePageId(pages[0].id)
      }
    }
    load()
  }, [store])

  const refreshPages = async () => {
    const pages = await listPages()
    store.setPages(pages)
    if (pages.length > 0 && !pages.find((p) => p.id === store.activePageId)) {
      store.setActivePageId(pages[0].id)
    } else if (pages.length === 0) {
      store.setActivePageId(null)
    }
  }

  const handleCreatePage = async () => {
    try {
      const page = await createPage('Nueva página')
      store.setPages([page, ...store.pages])
      store.setActivePageId(page.id)
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
    store.panels.parameters ? 'parameters' :
    store.panels.tutorials ? 'tutorials' :
    store.panels.cells ? 'cells' :
    store.panels.snippets ? 'snippets' :
    store.panels.symbols ? 'symbols' :
    store.panels.vault ? 'vault' : null

  const PanelComponent = activePanel ? PANELS[activePanel] : null

  if (store.labMode) {
    return (
      <div className="flex h-full flex-col">
        <Toolbar onCreatePage={handleCreatePage} />
        <LabCanvas />
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
                  <LatexEditor />
                </div>
              </ScrollArea>
            </ResizablePanel>
            <ResizableHandle withHandle className="transition-colors hover:bg-primary/20" />
            <ResizablePanel defaultSize={45} minSize={25}>
              <ScrollArea className="h-full">
                <div className="h-[calc(100vh-3rem)] p-4">
                  <LatexPreview />
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
