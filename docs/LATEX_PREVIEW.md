# Live preview LaTeX vs PDF (Tectonic)

lablog has **two** rendering paths. Knowing which one applies avoids confusion.

## Live preview (KaTeX, instant)

Source of truth: backend AST → `AstRenderer` (`ui/src/lib/ast-render.tsx`).

| Supported in live preview | Notes |
|---------------------------|--------|
| Inline `$...$`, display `$$...$$` / `\[...\]` | Always |
| Greek, operators, relations, arrows, accents | Catalog: `src/lablog/latex_symbols.py` (~190 symbols) |
| `equation`, `align`, `gather`, `multline` | Display math |
| `matrix`, `pmatrix`, `bmatrix`, `vmatrix`, `cases`, `array` | AMS matrices |
| Macros physics/braket | `\ket`, `\bra`, `\braket`, `\dv`, `\pdv`, `\R`, … (`katex-config.ts`) |

| **Not** in live preview (use **Compilar PDF**) | Why |
|-----------------------------------------------|-----|
| `tabular` / `table` / booktabs | Document layout, not math |
| `tikzpicture` / Feynman-style TikZ | Needs TikZ engine |
| `siunitx` numbers `\SI{...}` | Partial; prefer PDF |
| Full `\documentclass` packages | Raw Tectonic path |

Unsupported blocks show a dashed card: *«env · vista previa PDF»*.

## PDF compile (Tectonic / XeTeX)

Preamble (`pdf_engine._PREAMBLE`) loads scientific packages:

- `amsmath`, `amssymb`, `mathtools`, `bm`
- `booktabs`, `array`, `multirow`, `tabularx`, `siunitx`
- `physics`, `braket`
- `tikz` + libraries (arrows, decorations) for Feynman-like diagrams
- `graphicx`, `fvextra`, `hyperref`

Fixtures under `tests/fixtures/latex/`:

1. `01_characters.tex` — symbols & operators
2. `02_tables.tex` — booktabs + siunitx
3. `03_matrices.tex` — matrices & Maxwell align
4. `04_feynman.tex` — TikZ QED-style diagrams
5. `05_physics_packages.tex` — ket/bra, SI, EM
6. `06_full_document.tex` — full paper path

Run:

```bash
pytest tests/test_latex_fixtures.py -q
cd ui && npm test -- ast-render-split
```
