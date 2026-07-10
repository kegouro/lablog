# Circuitikz → simulación Jupyter (fácil)

## Visión

El usuario dibuja (o inserta un **preset**) un circuito en LaTeX con
**Circuitikz**. Con un comando o botón:

> **Simular circuito**

lablog:

1. Lee el diagrama y los **parámetros anotados**.
2. Genera una celda Jupyter (Python) con el modelo numérico listo.
3. Ejecuta (o deja listo para ejecutar) y opcionalmente pega la figura de
   resultados junto al circuito en la página.

Objetivo UX: **menos de 30 segundos** desde “preset RC serie” hasta ver
\(v_C(t)\) y la respuesta en frecuencia.

## Flujo de usuario

```
┌─────────────────┐     Simular      ┌──────────────────────┐
│  Circuitikz     │ ───────────────► │ Celda Python         │
│  (preset RC)    │                  │ (scipy/numpy/PySpice)│
│  + params       │ ◄── sliders ──── │ + plots matplotlib   │
└─────────────────┘                  └──────────────────────┘
         │                                      │
         └──────── Compilar PDF ────────────────┘
              (mismo R,C,V en diagrama y sim)
```

### Pasos concretos

1. Insertar preset: *Circuito RC serie (carga)*.
2. Ajustar sliders: `R ∈ [1 Ω, 1 MΩ]`, `C ∈ [1 pF, 1 mF]`, `V0 ∈ [0.1, 100] V`.
3. Highlight en rojo/ámbar: el resistor y el condensador en el TikZ, y las
   líneas `R = …` / `C = …` en el source LaTeX.
4. Clic **Simular** → se inserta (o actualiza) una celda:

   ```python
   # auto-generado por lablog · preset: rc_series_charge
   # No edites a mano los valores entre LABLOG_PARAMS; usa el panel.
   R = 1000.0   # ohm  [1, 1e6]
   C = 1e-6     # F    [1e-12, 1e-3]
   V0 = 5.0     # V    [0.1, 100]
   ...
   ```

5. La figura de salida se adjunta a la celda (path de figures ya soportado).

## Contrato de datos (fuente de verdad)

Cada diagrama parametrizable vive como:

```json
{
  "preset_id": "rc_series_charge",
  "kind": "circuitikz",
  "title": "RC serie — carga",
  "params": {
    "R": {
      "value": 1000,
      "unit": "ohm",
      "min": 1,
      "max": 1e6,
      "scale": "log",
      "label": "Resistencia",
      "description": "Limita la corriente de carga. Mayor R → constante de tiempo mayor (τ = RC).",
      "highlight": {
        "tikz_node": "R1",
        "latex_token": "R=\\SI{{{R}}{\\ohm}}"
      }
    },
    "C": { "...": "..." },
    "V0": { "...": "..." }
  },
  "tikz_template": "... circuitikz with {{R}} {{C}} ...",
  "sim_template": "python jinja or format string",
  "sim_backend": "numpy_ode | pyspice | lcapy"
}
```

- **tikz_template** → se renderiza a Circuitikz en la página.
- **sim_template** → se materializa en la celda Jupyter.
- **params.\*.highlight** → UI pinta nodo TikZ + span en el editor.

## Backends de simulación (prioridad)

| Prioridad | Backend | Cuándo |
|-----------|---------|--------|
| 1 | **numpy + scipy.integrate** | RC, RL, RLC lineales, sin dependencias pesadas |
| 2 | **lcapy** (si instalado) | redes simbólicas / s-domain |
| 3 | **PySpice / ngspice** | no lineales, conmutación, más realismo |

Default del producto: **numpy/scipy** embebido en el mismo kernel Jupyter que ya usa lablog. Sin instalar SPICE el usuario ya ve curvas.

## Anotaciones en el LaTeX (opcional, avanzado)

Para diagramas hechos a mano (no solo presets):

```latex
% lablog-param: id=R unit=ohm min=1 max=1e6 scale=log
% lablog-param: id=C unit=F min=1e-12 max=1e-3 scale=log
\begin{circuitikz}
  \draw (0,0) to[R, R=$R$, l^=$R$, n=R1] (2,0)
              to[C, C=$C$, n=C1] (2,-2)
  ...
\end{circuitikz}
% lablog-sim: preset=rc_series_charge
```

El parser (futuro) extrae comentarios `lablog-param` y el bloque circuitikz.

## API / eventos (borrador)

| Acción | Evento / endpoint |
|--------|-------------------|
| Insertar preset circuito | `snippet` o template page + `document_replaced` |
| Actualizar parámetro | `document_replaced` (tikz regenerado) + opcional `cell_updated` |
| Generar/actualizar sim | `cell_inserted` / `cell_updated` con source generado |
| Ejecutar | `POST .../cells/{id}/execute` (ya existe) |

No se inventa un store paralelo: los parámetros pueden ir en un sidecar JSON en
data dir o embebidos en comentarios del LaTeX (preferible para portabilidad).

## UX “muy fácil”

1. **Catálogo** en panel “Diagramas”: tarjetas con miniatura + 1 frase.
2. **Al insertar**: panel de parámetros se abre solo (reutilizar ParametersPanel).
3. **Highlight dual**: editor (línea/token) + preview (nodo resaltado).
4. **Botón único**: “Simular” = generar celda si no existe + execute.
5. **Errores de rango**: slider no sale de min/max; si se edita a mano el LaTeX
   fuera de rango → warning no bloqueante + clamp al simular.

## Seguridad

- Solo se ejecuta código de **plantillas firmadas** del catálogo (o diff mínimo
  de valores numéricos). No se evalúa TikZ arbitrario como Python.
- Si el usuario edita la celda a mano, se marca “desincronizada del preset”.

## Criterios de aceptación (MVP)

- [ ] Insertar preset RC serie sin escribir LaTeX a mano.
- [ ] Cambiar R y C con sliders actualiza el diagram y la celda.
- [ ] Highlight visible en resistor y en el source.
- [ ] Un clic produce plot de \(v_C(t)\) en < 2 s en máquina local típica.
- [ ] Compilar PDF sigue mostrando el circuito con valores actuales.
- [ ] Documentado el rango de cada parámetro en el panel (tooltip + pie).

## Fuera de MVP

- Extracción automática de topología Circuitikz genérica (netlist mágico).
- Multisim / SPICE GUI completa.
- Co-simulación en tiempo real con live sliders a 60 fps.
