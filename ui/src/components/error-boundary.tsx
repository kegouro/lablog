import { Component, type ErrorInfo, type ReactNode } from 'react'

import { Button } from '@/components/ui/button'

interface Props {
  children: ReactNode
  /** Clave de remount: al cambiar (p.ej. version de página) se limpia el error. */
  resetKey?: string | number | null
  label?: string
  onReset?: () => void
}

interface State {
  error: Error | null
  prevResetKey: Props['resetKey']
}

/**
 * Aísla fallos de render (KaTeX, celdas, etc.) sin tumbar el shell.
 * `resetKey` debe ligarse a la versión del documento del backend.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null, prevResetKey: this.props.resetKey }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { error }
  }

  static getDerivedStateFromProps(props: Props, state: State): Partial<State> | null {
    if (props.resetKey !== state.prevResetKey) {
      return { error: null, prevResetKey: props.resetKey }
    }
    return null
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('[ErrorBoundary]', this.props.label ?? 'panel', error, info.componentStack)
  }

  private handleReset = () => {
    this.setState({ error: null })
    this.props.onReset?.()
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex h-full min-h-[8rem] flex-col items-center justify-center gap-3 p-6 text-center">
          <p className="text-sm font-semibold text-destructive">
            {this.props.label ?? 'Panel'} falló al renderizar
          </p>
          <p className="max-w-sm font-mono text-xs text-muted-foreground">
            {this.state.error.message}
          </p>
          <Button size="sm" variant="outline" onClick={this.handleReset}>
            Reintentar / recargar desde servidor
          </Button>
        </div>
      )
    }
    return this.props.children
  }
}
