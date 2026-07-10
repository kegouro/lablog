# Próximas features — lablog

Documentación de diseño (no implementación) para capacidades que maduran lablog
como **laboratorio vivo**: diagramas LaTeX/TikZ/Circuitikz ↔ celdas Jupyter
parametrizadas, con UX de presets, highlight y rangos seguros.

## Índice

| Doc | Qué describe |
|-----|----------------|
| [circuitikz-jupyter-simulation.md](./circuitikz-jupyter-simulation.md) | Circuitos Circuitikz → simulación SPICE/Python en notebook |
| [diagram-presets-and-parameters.md](./diagram-presets-and-parameters.md) | Presets de diagramas (cualquier tipo), parámetros, highlight, rangos |
| [diagram-catalog.md](./diagram-catalog.md) | Catálogo inicial de diagramas (circuitos, Feynman, bloques, mecánicos) |

## Principios de producto

1. **Fácil de usar**: un clic “Simular este diagrama” crea la celda Python lista.
2. **Presets, no formularios infinitos**: cada diagrama nace de una plantilla con
   3–8 parámetros de alto valor (R, L, C, V, ω…), no de 40 knobs.
3. **Transparencia**: cada parámetro tiene **qué hace**, **dónde se ve** (highlight
   en el LaTeX/TikZ y en el esquema), y **rango válido**.
4. **Bidireccionalidad suave**: cambiar un slider actualiza el LaTeX del diagrama
   *y* el código de simulación (misma fuente de verdad: un JSON de parámetros).
5. **PDF sigue siendo la verdad tipográfica**; Jupyter es la verdad numérica.

## Fuera de alcance de esta carpeta

- Implementación en código (API, UI, kernels).
- Sustituir Circuitikz/TikZ por un editor gráfico tipo draw.io.

## Estado

| Feature | Estado |
|---------|--------|
| Docs de diseño | ✅ esta carpeta |
| Parser de anotaciones de parámetros | 🔜 |
| Bridge Circuitikz → Python | 🔜 |
| Panel de presets + highlight | 🔜 |
| Export notebook (.ipynb) con celdas generadas | 🔜 |
