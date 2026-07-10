# Pgfplots / datos vivos → Jupyter (futuro)

Misma filosofía que Circuitikz: un diagrama **declarativo** en LaTeX se
convierte en un pipeline numérico editable.

## Idea

- Preset `xy_scatter_from_csv`: tabla en vault + pgfplots o matplotlib.
- Preset `bode_plot`: H(s) simbólica → `scipy.signal.bode`.
- Parámetros: `fmin`, `fmax`, `order`, con highlight en el eje del TikZ.

## Diferencia con Circuitikz

Aquí el “dibujo” a menudo es el **resultado** de la simulación (curva). Flujo:

1. Usuario elige preset “Bode 2º orden”.
2. Ajusta ζ, ωn.
3. Sim genera datos + figura.
4. Opcional: exportar datos a vault CSV y re-plot en PDF con pgfplots.

## Estado

Diseño only — implementación tras MVP de `rc_series_charge` en UI.
