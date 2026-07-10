# Presets de diagramas, parámetros, highlight y rangos

Aplica a **todos** los tipos de diagrama de lablog (no solo circuitos):
Circuitikz, TikZ Feynman, bloques de control, mecánicos, ópticos, etc.

## Idea central

Un **preset** es una plantilla con:

1. Dibujo LaTeX/TikZ/Circuitikz.
2. Lista pequeña de **parámetros** (3–8).
3. Opcionalmente un **backend de simulación** (Jupyter).
4. Metadatos de UI: labels, descripciones, rangos, escala, highlight.

El usuario no “programa el diagrama”: elige un preset y mueve knobs seguros.

## Esquema de un parámetro

```ts
type DiagramParam = {
  id: string                 // "R", "omega", "theta"
  label: string              // "Resistencia"
  description: string        // qué hace, en lenguaje de lab
  value: number | string
  unit?: string              // "ohm", "rad/s", "GeV"
  min?: number
  max?: number
  step?: number
  scale?: "linear" | "log"   // log para R, C, f
  precision?: number         // dígitos en UI
  highlight: {
    /** id de nodo/path en TikZ (name=) o selector lógico */
    tikz?: string
    /** fragmento o regex suave del source LaTeX a subrayar */
    latex?: string
    /** línea relativa en la plantilla (1-based) para gutter */
    line?: number
    /** color semántico */
    color?: "amber" | "sky" | "rose" | "emerald"
  }
  /** solo lectura en UI (calculado) */
  derived?: boolean
}
```

### Qué debe ver el usuario en cada parámetro

| Campo UI | Contenido |
|----------|-----------|
| Nombre | `label` + `unit` |
| Descripción | `description` (tooltip + texto bajo el slider) |
| Dónde actúa | mini-leyenda: “Resalta: R1 en el esquema · línea 12 del LaTeX” |
| Rango | `min`–`max` visibles; si `scale=log`, ticks log |
| Valor actual | input numérico + slider acoplados |
| Efecto al cambiar | preview del diagrama y, si hay sim, celda “dirty” hasta re-simular |

## Highlight (dónde se puede cambiar)

Al enfocar o arrastrar un parámetro:

1. **Editor LaTeX**: subrayado / fondo en el token (`R=\SI{1}{\kilo\ohm}`) y
   scroll a la línea (`goToLine` ya existe en el store).
2. **Preview PDF/TikZ**: si el preview es AST/KaTeX-only, mostrar badge
   “parámetro R”; en PDF recompilado, idealmente anotar con color (fase 2:
   reescribir nodos `draw[...]` con `color=lablogR`).
3. **Celda de simulación**: highlight de la línea `R = 1000.0  # ...`.

Sin ambigüedad: el mismo `param.id` enlaza las tres vistas.

## Rangos y validación

| Regla | Comportamiento |
|-------|----------------|
| Valor &lt; min o &gt; max | clamp al simular; warning en UI |
| `scale=log` y value ≤ 0 | rechazar; forzar min &gt; 0 |
| Edición manual del LaTeX | parse best-effort; si no se puede leer el valor, marcar param “manual” |
| Unidades | mostrar siempre la unidad del preset; no convertir sorpresas en v1 |

Ejemplos de rangos típicos (presets eléctricos):

| Parámetro | min | max | scale |
|-----------|-----|-----|-------|
| R | 1 Ω | 10 MΩ | log |
| C | 1 pF | 10 mF | log |
| L | 1 nH | 10 H | log |
| V / I | 0 (o 0.01) | 1e3 | linear o log |
| f, ω | 0.01 Hz | 10 GHz | log |
| duty cycle | 0 | 1 | linear |

## Plantilla TikZ / Circuitikz

Usar placeholders estables:

```latex
\begin{circuitikz}
  \draw (0,0) to[R, R={{R}}, l_=$R$, name=R1] (2,0)
              to[C, C={{C}}, name=C1] (2,-2) ...
\end{circuitikz}
```

Motor de expand: el mismo que snippets (`{{name}}`) ya usado en lablog.

## Plantilla de simulación

```python
# lablog-sim: preset={{preset_id}} version=1
# LABLOG_PARAMS_START
R = {{R}}  # {{R.unit}}  range [{{R.min}}, {{R.max}}]
C = {{C}}  # {{C.unit}}  range [{{C.min}}, {{C.max}}]
# LABLOG_PARAMS_END

import numpy as np
import matplotlib.pyplot as plt
# ... cuerpo del preset, solo usa R, C, ...
```

Al cambiar un slider, lablog **solo reescribe el bloque** entre
`LABLOG_PARAMS_START/END`, preservando ediciones del usuario fuera del bloque
si es posible; si el bloque está roto → regenerar celda completa con confirmación.

## Panel UI (mock de interacción)

```
┌─ Diagrama: RC serie ─────────────────────────┐
│ [Simular]  [Reset preset]  [Copiar params]   │
│                                              │
│ Resistencia R                    [1 kΩ]      │
│ ├─────────●──────────────────────┤  log      │
│ 1 Ω                          1 MΩ            │
│ Limita corriente; τ = RC.                    │
│ Resalta: nodo R1 · L12 del LaTeX             │
│                                              │
│ Capacitancia C                   [1 µF]      │
│ ...                                          │
└──────────────────────────────────────────────┘
```

Reutilizar `ParametersPanel` + hints de color existentes; ampliar con
`scale`, `min/max` y `highlight`.

## Tipos de diagrama soportados (mismo sistema de params)

| kind | Ejemplo preset | Sim backend típico |
|------|----------------|--------------------|
| `circuitikz` | RC, RLC, divisor, puente | numpy ODE / PySpice |
| `feynman_tikz` | s-channel, t-channel | (opcional) amplitudes toy |
| `block_diagram` | PI control, 2º orden | scipy.signal |
| `mechanics` | masa-resorte-amortiguador | ODE |
| `optics` | lente delgada, interferómetro | numpy |
| `generic_tikz` | solo parámetros geométricos | sin sim |

Si no hay `sim_template`, el preset es **solo visual** (sliders mueven el
dibujo). Sigue siendo útil para informes y PDF.

## Almacenamiento en el documento

Preferido (portable, un solo archivo de eventos):

```latex
% lablog-diagram: id=rc1 preset=rc_series_charge
% lablog-param: R=1000
% lablog-param: C=1e-6
% lablog-param: V0=5
\begin{circuitikz}
...
\end{circuitikz}
```

Alternativa: JSON en vault o data dir indexado por page_id + diagram_id
(mejor para binarios/miniaturas; peor para git diff).

## Criterios de calidad de un preset

- [ ] ≤ 8 parámetros; cada uno con description no vacía.
- [ ] min &lt; max; log solo si min &gt; 0.
- [ ] highlight.tikz o highlight.latex definido.
- [ ] Valores por defecto en el centro “didáctico” del rango (no en un extremo).
- [ ] Sim (si existe) termina en &lt; 2 s con defaults.
- [ ] PDF compile del tikz_template sin errores Tectonic.

## Fases de implementación

| Fase | Entrega |
|------|---------|
| P0 | JSON de presets + expand `{{params}}` en snippets/templates |
| P1 | Panel con sliders + highlight en editor |
| P2 | Generación de celda Jupyter + execute |
| P3 | Sync bidireccional robusta + “desync” detection |
| P4 | Catálogo grande + miniaturas + búsqueda |

## Relación con código actual

- Snippets/templates: `src/lablog/snippets.py`, `templates.py`, `ui` ParametersPanel.
- Celdas: `commands.execute_cell`, figures en `figures_dir`.
- Preview: KaTeX no pinta Circuitikz → card “PDF-only” ya prevista en
  `docs/LATEX_PREVIEW.md`; el highlight del esquema en live puede ser un
  SVG/annotación ligera hasta recompilar.
