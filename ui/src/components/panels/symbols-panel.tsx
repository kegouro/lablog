import { Search, Star, X } from 'lucide-react'
import { useMemo, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useAppStore } from '@/stores/app-store'

const CATEGORIES = ['all', 'greek', 'operators', 'arrows', 'relations', 'delimiters', 'accents']

export function SymbolsPanel() {
  const {
    symbols,
    favorites,
    setFavorites,
    togglePanel,
    setActiveLatex,
    activeLatex,
  } = useAppStore()
  const [category, setCategory] = useState('all')
  const [query, setQuery] = useState('')
  const [mode, setMode] = useState<'all' | 'favorites'>('all')

  const filtered = useMemo(() => {
    let list = symbols
    if (mode === 'favorites') {
      list = list.filter((s) => favorites.includes(s.id))
    }
    if (category !== 'all') {
      list = list.filter((s) => s.category === category)
    }
    if (query.trim()) {
      const q = query.toLowerCase()
      list = list.filter(
        (s) =>
          s.latex.toLowerCase().includes(q) ||
          s.description.toLowerCase().includes(q) ||
          s.category.toLowerCase().includes(q),
      )
    }
    return list
  }, [symbols, favorites, mode, category, query])

  const insert = (latex: string) => {
    setActiveLatex(activeLatex + latex)
  }

  const toggleFavorite = (id: string) => {
    const next = new Set(favorites)
    if (next.has(id)) {
      next.delete(id)
    } else {
      next.add(id)
    }
    setFavorites(Array.from(next))
  }

  return (
    <Card className="m-2 border-0 shadow-none">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-semibold">Símbolos LaTeX</CardTitle>
        <Button variant="ghost" size="icon" className="size-7" onClick={() => togglePanel('symbols')}>
          <X className="size-4" />
        </Button>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className="flex gap-1">
          <Button
            variant={mode === 'all' ? 'secondary' : 'ghost'}
            size="sm"
            className="h-7 flex-1 text-xs"
            onClick={() => setMode('all')}
          >
            Todos
          </Button>
          <Button
            variant={mode === 'favorites' ? 'secondary' : 'ghost'}
            size="sm"
            className="h-7 flex-1 gap-1 text-xs"
            onClick={() => setMode('favorites')}
          >
            <Star className="size-3" />
            Favoritos
            <span className="rounded-full bg-muted px-1.5 py-0 text-[10px]">{favorites.length}</span>
          </Button>
        </div>

        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Buscar símbolo…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="h-8 bg-muted/40 pl-8 text-xs"
          />
        </div>

        <div className="flex flex-wrap gap-1">
          {CATEGORIES.map((c) => (
            <Button
              key={c}
              variant={category === c ? 'secondary' : 'ghost'}
              size="sm"
              className="h-6 text-[10px] capitalize"
              onClick={() => setCategory(c)}
            >
              {c}
            </Button>
          ))}
        </div>

        <div className="grid grid-cols-5 gap-1">
          {filtered.slice(0, 100).map((symbol) => (
            <div
              key={symbol.id}
              className="group relative flex aspect-square cursor-pointer items-center justify-center rounded-md border text-lg hover:border-primary hover:bg-muted"
              onClick={() => insert(symbol.latex)}
              title={`${symbol.latex} — ${symbol.description}`}
            >
              {symbol.char}
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  toggleFavorite(symbol.id)
                }}
                className="absolute right-0.5 top-0.5 opacity-0 transition-opacity group-hover:opacity-100"
              >
                <Star
                  className={`size-3 ${favorites.includes(symbol.id) ? 'fill-amber-400 text-amber-400' : 'text-muted-foreground'}`}
                />
              </button>
            </div>
          ))}
        </div>

        {filtered.length === 0 && (
          <p className="text-center text-xs text-muted-foreground">
            {mode === 'favorites' ? 'Aún no tienes favoritos' : 'Sin coincidencias'}
          </p>
        )}
      </CardContent>
    </Card>
  )
}
