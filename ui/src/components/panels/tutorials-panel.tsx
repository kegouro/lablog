import { BookOpen, ChevronRight, FileText, Image, Lightbulb, Mic, Palette, Sigma, X } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useAppStore } from '@/stores/app-store'

const TUTORIALS = [
  {
    id: 'first-page',
    icon: FileText,
    title: 'Crea tu primera página',
    steps: [
      'Haz clic en el + del panel izquierdo o presiona Ctrl+K.',
      'Escribe un título y empieza a escribir LaTeX.',
      'El autoguardado se encarga del resto.',
    ],
  },
  {
    id: 'formulas',
    icon: Sigma,
    title: 'Escribe fórmulas',
    steps: [
      'Inline: escribe $E = mc^2$.',
      'Display: usa $$...$$ o \\[...\\].',
      'La preview se actualiza mientras escribes.',
    ],
  },
  {
    id: 'snippets',
    icon: Lightbulb,
    title: 'Usa snippets',
    steps: [
      'Abre el panel de Snippets desde la barra superior.',
      'Elige una plantilla y haz clic en Insertar.',
      'Personaliza el contenido a tu gusto.',
    ],
  },
  {
    id: 'symbols',
    icon: Sigma,
    title: 'Símbolos favoritos',
    steps: [
      'Abre el panel Símbolos.',
      'Filtra por categoría.',
      'Haz clic en una estrella para guardar favoritos.',
    ],
  },
  {
    id: 'vault',
    icon: Image,
    title: 'Guarda archivos en la bóveda',
    steps: [
      'Arrastra imágenes o archivos al panel Bóveda.',
      'Solicita borrado seguro cuando ya no los necesites.',
      'Los archivos se mantienen locales.',
    ],
  },
  {
    id: 'voice',
    icon: Mic,
    title: 'Dictado por voz',
    steps: [
      'Presiona Dictar en la barra superior.',
      'Habla claramente.',
      'La transcripción se inserta en tu página.',
    ],
  },
  {
    id: 'theme',
    icon: Palette,
    title: 'Personaliza el aspecto',
    steps: [
      'Abre Configuración (rueda dentada).',
      'Cambia entre claro, oscuro o sistema.',
      'Elige un color de acento y ajusta el tamaño de fuente.',
    ],
  },
]

export function TutorialsPanel() {
  const { togglePanel } = useAppStore()

  return (
    <Card className="m-2 border-0 shadow-none">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div className="flex items-center gap-2">
          <BookOpen className="size-4 text-primary" />
          <CardTitle className="text-sm font-semibold">Tutoriales</CardTitle>
        </div>
        <Button variant="ghost" size="icon" className="size-7" onClick={() => togglePanel('tutorials')}>
          <X className="size-4" />
        </Button>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {TUTORIALS.map((t) => (
          <div
            key={t.id}
            className="group rounded-lg border p-3 transition-colors hover:border-primary/40 hover:bg-muted/30"
          >
            <div className="flex items-center gap-2">
              <div className="flex size-7 items-center justify-center rounded-md bg-secondary text-secondary-foreground">
                <t.icon className="size-4" />
              </div>
              <p className="text-sm font-medium">{t.title}</p>
              <ChevronRight className="ml-auto size-4 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
            </div>
            <ul className="mt-2 space-y-1 pl-9">
              {t.steps.map((step, i) => (
                <li key={i} className="text-xs text-muted-foreground">
                  • {step}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
