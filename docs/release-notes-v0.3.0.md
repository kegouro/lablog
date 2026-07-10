# lablog v0.3.0

**Released:** 2026-07-10
**PyPI:** `jose-labarca-lablog==0.3.0`

## Highlights

lablog 0.3 turns the notebook into a **parameterized scientific workbench**:
diagrams you can dial, re-simulate, export to Jupyter, and personalize for the
bench, the paper, or the classroom.

### Diagram workbench
- 12 built-in presets (circuits, control, mechanics, optics, Feynman)
- Re-apply parameters without `{{}}` placeholders (`% lablog-param`)
- Dual highlight: editor line + colored Circuitikz/TikZ components in PDF
- Optional PySpice cells (RC, RLC, half-wave) with automatic numpy fallback

### Product polish
- UI density, editor font, Nord palette, reduced motion
- Profiles: Laboratorio / Paper / Docencia
- Configurable keyboard shortcuts
- Export **Notebook Jupyter (.ipynb)**
- Playwright smoke tests in CI

## Install

```bash
pip install -U "jose-labarca-lablog==0.3.0"
# optional SPICE:
pip install -U "jose-labarca-lablog[pyspice]"
```

```bash
lablog diagrams
uvicorn lablog.api:app --host 127.0.0.1 --port 8000
```

## Upgrade notes

- Preference localStorage keys are backward compatible.
- Diagram pages using `% lablog-diagram` rehydrate sliders automatically.
- PySpice remains optional; sim cells degrade gracefully without ngspice.

## Cite

See `CITATION.cff` (version 0.3.0).
