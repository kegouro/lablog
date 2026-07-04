import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { LatexEditor } from './latex-editor'

describe('LatexEditor', () => {
  it('renders the empty state when no page is active', () => {
    render(<LatexEditor />)
    expect(screen.getByText('Nada seleccionado')).toBeInTheDocument()
    expect(screen.getByText(/Crea una página desde la barra lateral/i)).toBeInTheDocument()
  })
})
