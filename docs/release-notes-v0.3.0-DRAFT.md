# lablog v0.3.0 — DRAFT (no tag aún)

**Estado:** borrador de notas para cuando se publique `v0.3.0`.
**No ejecutar** `git tag` / release workflow hasta confirmación explícita.

## Desde v0.2.1

### Diagramas
- Catálogo ampliado (12 presets: RC, divisor, RLC, Wheatstone, media onda, pasa-bajos, op-amp, MSD, 2º orden, PI, lente, Feynman)
- Re-aplicar parámetros desde panel sin placeholders `{{}}`
- Highlight editor (línea) + color TikZ/Circuitikz (`name=` + `color=`)
- Botón **SPICE** opcional (RC, RLC, media onda) con fallback numpy
- Extra: `pip install 'jose-labarca-lablog[pyspice]'` (+ ngspice del sistema)

### Producto UI
- Personalización: densidad, fuente editor, Nord, reduce motion
- Perfiles: Laboratorio / Paper / Docencia
- Atajos configurables (mod+s, paneles, lab mode, …)
- Export **Notebook Jupyter (.ipynb)**
- E2E Playwright smoke en CI

### Cómo publicar (cuando se apruebe)

1. Revisar `pyproject.toml` version → `0.3.0`
2. Renombrar este archivo a `release-notes-v0.3.0.md` (quitar DRAFT)
3. ```bash
   git tag -a v0.3.0 -m "lablog v0.3.0"
   git push origin v0.3.0
   ```
4. Confirmar PyPI trusted publisher (ver `docs/RELEASE.md`)

## Smoke post-release

```bash
pip install -U jose-labarca-lablog
lablog diagrams
lablog diagrams --expand rc_series_charge
```
