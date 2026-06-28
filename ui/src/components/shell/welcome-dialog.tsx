import { BookOpen, Check, FlaskConical, Sparkles, X } from 'lucide-react'
import { useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { useAppStore } from '@/stores/app-store'

const STEPS = [
  {
    icon: BookOpen,
    title: 'Escribe LaTeX en vivo',
    text: 'Editor con números de línea, autoguardado y vista previa KaTeX al instante.',
  },
  {
    icon: FlaskConical,
    title: 'Bóveda y celdas ejecutables',
    text: 'Arrastra archivos a la bóveda y ejecuta código Python/Julia dentro de tus notas.',
  },
  {
    icon: Sparkles,
    title: 'Productividad sin fricción',
    text: 'Snippets, símbolos favoritos, dictado por voz y temas personalizables.',
  },
]

export function WelcomeDialog() {
  const { setPanel } = useAppStore()
  const [open, setOpen] = useState(false)

  useEffect(() => {
    const dismissed = localStorage.getItem('lablog-welcome-dismissed')
    if (dismissed !== 'true') {
      setOpen(true)
    }
  }, [])

  const dismiss = (permanent: boolean) => {
    if (permanent) {
      localStorage.setItem('lablog-welcome-dismissed', 'true')
    }
    setOpen(false)
  }

  const startTour = () => {
    dismiss(false)
    setPanel('tutorials', true)
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm">
              <BookOpen className="size-5" />
            </div>
            <div>
              <DialogTitle className="text-xl">Bienvenido a lablog</DialogTitle>
              <DialogDescription className="text-sm">
                Tu bitácora científica con superpoderes.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-3 py-2">
          <p className="text-sm leading-relaxed text-muted-foreground">
            <strong>lablog</strong> es un editor de LaTeX pensado para investigadores, estudiantes y curiosos:
            escribe fórmulas, guarda figuras en una bóveda segura, reutiliza snippets y ejecuta celdas de código
            sin salir de tu flujo. Nació para ser más cómodo que Overleaf, más limpio que TeXmacs y más tuyo
            que cualquier editor genérico.
          </p>
          <p className="text-xs italic text-muted-foreground">
            Hecho con cuidado por <strong>José Labarca Baeza</strong>.
          </p>

          <div className="grid gap-2">
            {STEPS.map((step) => (
              <div
                key={step.title}
                className="flex items-start gap-3 rounded-lg border p-3 transition-colors hover:bg-muted/40"
              >
                <div className="flex size-8 shrink-0 items-center justify-center rounded-md bg-secondary text-secondary-foreground">
                  <step.icon className="size-4" />
                </div>
                <div>
                  <p className="text-sm font-medium">{step.title}</p>
                  <p className="text-xs text-muted-foreground">{step.text}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <DialogFooter className="flex-col gap-2 sm:flex-row">
          <Button variant="outline" size="sm" className="gap-2" onClick={() => dismiss(true)}>
            <X className="size-4" />
            No volver a mostrar
          </Button>
          <Button variant="secondary" size="sm" className="gap-2" onClick={startTour}>
            <Sparkles className="size-4" />
            Ver tutoriales
          </Button>
          <Button size="sm" className="gap-2" onClick={() => dismiss(false)}>
            <Check className="size-4" />
            Empezar a escribir
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
