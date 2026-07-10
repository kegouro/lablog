# Catálogo inicial de presets de diagramas

Lista de presets a implementar en fases. Cada uno debe cumplir el checklist de
`diagram-presets-and-parameters.md`.

## Circuitikz (prioridad alta)

### `rc_series_charge` — RC serie, carga
- **Parámetros**

| id | label | unit | min | max | scale | highlight | efecto |
|----|-------|------|-----|-----|-------|-----------|--------|
| R | Resistencia | Ω | 1 | 1e6 | log | nodo `R1` | ↑R → ↑τ=RC, menos corriente |
| C | Capacitancia | F | 1e-12 | 1e-3 | log | nodo `C1` | ↑C → ↑τ, más carga almacenada |
| V0 | Tensión fuente | V | 0.1 | 100 | linear | nodo `V1` | escala la asíntota de \(v_C\) |

- **Sim**: \(v_C(t)=V_0(1-e^{-t/RC})\), plot 0…5τ.
- **Didáctica**: laboratorio de constante de tiempo.

### `rlc_series_step` — RLC serie, escalón
| id | min | max | scale | notas |
|----|-----|-----|-------|-------|
| R | 0.1 | 1e5 | log | amortiguamiento |
| L | 1e-6 | 10 | log | |
| C | 1e-12 | 1e-3 | log | |
| V0 | 0.1 | 100 | linear | |

- **Sim**: ODE 2º orden; mostrar sub/crít/sobreamortiguado según ζ.
- **Highlight**: R, L, C y la malla.

### `voltage_divider` — Divisor resistivo
| id | description |
|----|-------------|
| R1 | Rama superior |
| R2 | Rama inferior |
| Vin | Entrada |

- **Sim**: \(V_{out}=V_{in} R_2/(R_1+R_2)\); barrido opcional de R2.
- **Rango** R: 1–1e7 Ω log.

### `wheatstone` — Puente de Wheatstone (solo DC)
- Params: R1–R4, Vex.
- Sim: tensiones de nodos (matriz conductancia 2×2).

### `half_wave_rectifier` — Rectificador media onda + C
- Params: Vpeak, f, Rload, C.
- Sim: numpy con diodo ideal; plot varios periodos.
- Backend ideal → PySpice en P3.

## TikZ Feynman (prioridad media)

### `qed_moller` — e⁻e⁻ → e⁻e⁻ (árbol)
- Params geométricos: `spread` (separación de legs), opcional `label_size`.
- Sin sim física real en MVP; botón “Simular” desactivado o toy matrix element.

### `z_ffbar` — Z → f f̄
- Params: solo etiquetas (f = e, μ, τ, q) como enum string.

## Bloques / control (prioridad media)

### `second_order_step` — 2º orden canónico
| id | label | min | max | description |
|----|-------|-----|-----|-------------|
| wn | ωₙ | 0.1 | 100 | frecuencia natural |
| zeta | ζ | 0.05 | 3 | amortiguamiento |
| K | ganancia | 0.1 | 10 | |

- **Sim**: `scipy.signal.step`.
- **Diagrama**: bloques TikZ K·wn²/(s²+2ζwn s+wn²).

### `pi_controller` — PI + planta 1er orden
- Params: Kp, Ki, tau_p, K_plant.
- Sim: respuesta a escalón en lazo cerrado.

## Mecánica (prioridad media)

### `mass_spring_damper`
| id | unit | min | max | scale |
|----|------|-----|-----|-------|
| m | kg | 0.01 | 100 | log |
| k | N/m | 0.1 | 1e5 | log |
| b | N·s/m | 0 | 1e3 | linear |
| x0 | m | -1 | 1 | linear |
| v0 | m/s | -10 | 10 | linear |

- Highlight: masa, resorte, amortiguador en el dibujo.

## Óptica (prioridad baja)

### `thin_lens`
- Params: f, do → di calculado (derived).
- Diagrama de rayos TikZ; sim = ecuación de lentes.

## Cómo añadir un preset (para contribuidores)

1. Crear `presets/<id>.json` (schema de `diagram-presets-and-parameters.md`).
2. Incluir `tikz_template` que compile con el preamble de `pdf_engine`.
3. Si hay sim: `sim_template` con bloque `LABLOG_PARAMS_*` y plot matplotlib.
4. Completar description + min/max + highlight en **cada** param.
5. Añadir miniatura PNG opcional en `docs/future-features/assets/`.
6. Test: expand params → parse LaTeX → (opcional) execute_cell en tmp.

## Naming

- `id`: `snake_case`, estable (no renombrar sin migración).
- Versión del preset en el JSON: `"version": 1` para evolucionar plantillas.
