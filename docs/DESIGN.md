# lablog · Diseño Arquitectónico

> **Segundo cerebro científico**: bitácora de laboratorio con LaTeX en vivo, dictado de voz, ejecución integrada de código y bóveda segura de archivos.
> Parte del **Pharos Project**.

---

## 1. Visión

**lablog** no es solo un editor de LaTeX. Es un **acelerador de investigación** para físicos experimentales y científicos de laboratorio.

- **Overleaf** sirve para escribir el paper cuando el experimento ya terminó.
- **TeXstudio** sirve para editar LaTeX de forma tradicional.
- **lablog** acompaña al científico **durante el experimento**: con las manos ocupadas, guantes puestos, mirando un instrumento, dictando observaciones, ejecutando análisis de datos y preservando todo de forma inmutable.

### Propuesta de valor

1. **Voz → LaTeX estructurado**: no texto plano, sino ecuaciones y comandos insertados en el árbol del documento.
2. **Código vivo dentro del documento**: celdas Python/Julia/MATLAB ejecutables que generan resultados, tablas y figuras.
3. **Bóveda de archivos por página**: datos crudos, fotos, audio, scripts y más.
4. **Time-Travel con Event Sourcing**: historial inmutable, reproducibilidad y auditoría gratis.
5. **Exportación a paper**: cuando terminas, generas el paper sin reescribir nada.

---

## 2. Filosofía de diseño

### 2.1 Motor separado de la UI

El **engine** de lablog es independiente de cualquier interfaz. La UI se conecta vía API/WebSocket.

```
┌─────────────────────────────────────────────────────────────┐
│                         lablog UI                           │
│  (React / Tauri / Web / Terminal)                           │
└───────────────────────┬─────────────────────────────────────┘
                        │ API / WebSocket / EventBus
┌───────────────────────▼─────────────────────────────────────┐
│                      lablog Engine                          │
│  Python                                                     │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│  │ Event Store  │ │ LaTeX Engine │ │ Voice Engine         │ │
│  │ (Event       │ │ + AST        │ │ (STT → Intent → LLM) │ │
│  │  Sourcing)   │ │              │ │                      │ │
│  └──────────────┘ └──────────────┘ └──────────────────────┘ │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│  │ Vault Engine │ │ Plugin Bus   │ │ Export Engine        │ │
│  │ (seguridad)  │ │              │ │ (PDF / LaTeX / HTML) │ │
│  └──────────────┘ └──────────────┘ └──────────────────────┘ │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│  │ Time-Travel  │ │ Code Engine  │ │ Ingest Engine        │ │
│  │ (projections)│ │ (Jupyter)    │ │ (DataFrames)         │ │
│  └──────────────┘ └──────────────┘ └──────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Event Sourcing como núcleo

No guardamos el estado actual directamente. Guardamos una secuencia inmutable de eventos.

```json
[
  { "type": "page_created", "timestamp": "...", "payload": { "title": "SPM" } },
  { "type": "text_inserted", "timestamp": "...", "payload": { "pos": 14, "text": "\\int_0^1" } },
  { "type": "cell_executed", "timestamp": "...", "payload": { "cellId": "xyz", "output": "fig.png" } }
]
```

Beneficios:

- **Time-Travel gratis**: reproducir hasta cualquier punto en el tiempo.
- **Diff natural**: comparar listas de eventos.
- **Auditoría inmutable**: cada cambio queda registrado.
- **Colaboración P2P futura**: CRDTs y sincronización por eventos.

### 2.3 Modularidad extrema y plugins

Cada funcionalidad es un módulo con interfaz declarada. Los plugins se registran en el **Plugin Bus** y reaccionan a eventos.

### 2.4 Datos primero, nube opcional

Todo se guarda localmente en formatos abiertos. La sincronización en la nube es opcional y encriptada.

---

## 3. Componentes del sistema

### 3.1 Core Kernel + Event Store

Responsable de:

- Almacenar y reproducir eventos.
- Proyectar el estado actual de una página a partir de sus eventos.
- Gestionar proyectos, sesiones y configuración.

Conceptos clave:

- `Project`: agrupación de páginas.
- `Page`: entidad cuyo estado se calcula a partir de `Event[]`.
- `Event`: unidad inmutable del sistema.
- `Projection`: vista derivada del estado (render, bóveda, timeline).

### 3.2 LaTeX Engine con AST

El documento no se maneja como texto plano. Se parsea a un **AST (Abstract Syntax Tree)**:

- Inserciones de voz/código van al nodo correcto sin romper el documento.
- Se preserva formato, indentación y estructura.
- Soporta ecuaciones, figuras, tablas, referencias cruzadas y celdas ejecutables.

Ejemplo de AST simplificado:

```json
{
  "type": "document",
  "children": [
    { "type": "section", "title": "Setup" },
    { "type": "paragraph", "children": [...] },
    { "type": "math", "mode": "display", "latex": "\\int_0^\\infty e^{-x^2} dx" },
    { "type": "cell", "language": "python", "id": "xyz" }
  ]
}
```

### 3.3 Voice Engine (Voz → LaTeX)

Arquitectura por capas:

```
[Micrófono]
    │
    ▼
[Capa STT]              Whisper.cpp / Vosk / Whisper API
    │
    ▼
[Capa Intent Parser]    Detecta jerga matemática:
                        "integral", "ecuación de Schrödinger",
                        "más o menos", "subíndice", "matriz"
    │
    ▼
[Capa Structured       LLM local (Ollama Llama 3.2/8B)
 Translation]           o API (Claude/GPT)
    │
    ▼
[Capa AST Insertion]    Inserta el LaTeX generado en el nodo
                        correcto del árbol
```

Modos:

1. **Dictado normal**: transcribe texto plano en párrafos.
2. **Modo matemático**: la voz se traduce directamente a ecuaciones.
3. **Modo Dump**: grabación continua a borrador para depurar después.
4. **Modo Laboratorio**: interfaz reducida a botón gigante de grabación.

#### Prototipo 0

Un script independiente que:

1. Graba audio del micrófono.
2. Transcribe con Whisper.
3. Detecta intención matemática.
4. Pasa a un LLM local con prompt estricto.
5. Imprime el LaTeX en consola.

### 3.4 Code Engine (Jupyter como backend)

No reinventamos un intérprete. lablog es un cliente de Jupyter estilizado.

```latex
\begin{python}[label=fig:iv_curve]
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("vault://iv_data.csv")
plt.plot(df["V"], df["I"])
plt.xlabel("Voltaje (V)")
plt.ylabel("Corriente (A)")
\end{python}
```

Flujo:

1. El engine extrae el bloque.
2. Reemplaza `vault://...` por la ruta absoluta en disco.
3. Envía el código a un kernel de Jupyter vía `jupyter-client` (ZeroMQ).
4. Recibe el output (texto, tabla, imagen base64).
5. Inserta el resultado en el renderizado.
6. Emite evento `cell_executed` al Event Store.

Lenguajes iniciales: **Python**. Luego Julia, R, MATLAB.

### 3.5 Vault Engine (Bóveda)

Cada página tiene una bóveda para adjuntos.

- Indexación por hash.
- Previsualización nativa.
- Versionado opcional.

#### Eliminación segura

1. **Slider de destrucción**: arrastrar hasta el final.
2. **Confirmación con nombre** del archivo.
3. **Time-lock de 7 días**: recuperable durante ese periodo.
4. **Log de auditoría**.
5. **Modo ultra-seguro opcional**: triple contraseña para proyectos sensibles.

### 3.6 Time-Travel Engine

Cada evento del Event Store es un punto en el tiempo.

Funcionalidades:

- **Vista Timeline**: línea de tiempo visual.
- **Diff**: comparar proyecciones de dos instantes.
- **Blame**: ver cuándo cambió cada parte del documento.
- **Restaurar**: reproducir eventos hasta un punto dado.

### 3.7 Ingest Engine (DataFrames como ciudadanos de primera clase)

Al arrastrar un archivo a la bóveda, lablog lo inspecciona y sugiere acciones.

Ejemplo con CSV:

```json
{
  "type": "vault_file_added",
  "payload": {
    "file": "data.csv",
    "mimeType": "text/csv",
    "schema": { "V": "float", "I": "float" }
  }
}
```

Sugerencias:

- "¿Graficar?" → inserta celda Python:

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("vault://data.csv")
plt.plot(df["V"], df["I"])
plt.show()
```

- "¿Generar tabla LaTeX?" → usa `pgfplots` o `booktabs`.
- "¿Estadísticas descriptivas?" → celda con `df.describe()`.

### 3.8 Plugin Bus

Sistema de eventos tipado. Plugins reaccionan a eventos como:

- `page_created`, `text_inserted`, `cell_executed`
- `vault_file_added`, `vault_file_scheduled_for_deletion`
- `voice_transcription`, `voice_math_detected`

### 3.9 Export Engine

Exporta páginas o proyectos a:

- PDF (con LaTeX real).
- `.tex` autocontenido.
- HTML interactivo.
- Markdown.
- Jupyter notebook.
- `.lablog` (ZIP encriptado).

---

## 4. Modelo de datos basado en Event Sourcing

### Evento base

```json
{
  "id": "uuid",
  "type": "text_inserted",
  "timestamp": "2026-06-26T10:00:00Z",
  "actor": "user|plugin|system",
  "pageId": "uuid",
  "payload": {
    "pos": 42,
    "text": "\\int_0^\\infty"
  }
}
```

### Tipos de eventos principales

```yaml
page_created:
  payload: { title: string, projectId: uuid }

text_inserted:
  payload: { pos: int, text: string }

text_deleted:
  payload: { pos: int, length: int }

math_inserted:
  payload: { astPath: string, latex: string }

cell_inserted:
  payload: { cellId: uuid, language: string, source: string }

cell_executed:
  payload: { cellId: uuid, output: string, figurePath?: string }

vault_file_added:
  payload: { fileId: uuid, name: string, hash: string, schema?: object }

vault_file_scheduled_for_deletion:
  payload: { fileId: uuid, scheduledAt: datetime }

snapshot_requested:
  payload: { reason: string }
```

### Proyección

El estado actual de una página se obtiene aplicando todos sus eventos en orden:

```python
def project(page_id: str) -> Page:
    events = event_store.get_events(page_id)
    page = Page()
    for event in events:
        page.apply(event)
    return page
```

---

## 5. Flujos de usuario

### 5.1 Voz a LaTeX

```
[Usuario habla]
    │
    ▼
[STT: Whisper.cpp] → texto plano
    │
    ▼
[Intent Parser] → detecta matemática
    │
    ▼
[Structured Translation] → LLM local convierte a LaTeX
    │
    ▼
[AST Insertion] → inserta en el nodo correcto
    │
    ▼
[Event Store] → emite math_inserted
    │
    ▼
[Renderizado en vivo]
```

### 5.2 Celda ejecutable

```
[Usuario escribe \begin{python}...\end{python}]
    │
    ▼
[LaTeX Engine parsea AST]
    │
    ▼
[Code Engine extrae código]
    │
    ▼
[Reemplaza vault:// por path absoluto]
    │
    ▼
[Envía a kernel Jupyter vía jupyter-client]
    │
    ▼
[Recibe output]
    │
    ▼
[Emite cell_executed y renderiza]
```

### 5.3 Eliminación segura en bóveda

```
[Usuario solicita eliminar archivo]
    │
    ▼
[Slider de destrucción hasta el final]
    │
    ▼
[Confirmación escribiendo nombre del archivo]
    │
    ▼
[Archivo marcado con scheduledDeletionAt = ahora + 7 días]
    │
    ▼
[Evento vault_file_scheduled_for_deletion]
    │
    ▼
[Dentro de 7 días: posible recuperar]
[Después de 7 días: eliminación física + log]
```

---

## 6. Interfaz de usuario

### Layout normal

```
┌────────────────────────────────────────────────────────────────────┐
│  lablog · Proyecto: SPM  [🎤] [🧪 Modo Lab] [⏳ Timeline] [⚙️]      │
├──────────┬──────────────────────────┬──────────────────────────────┤
│          │                          │                              │
│ Páginas  │  Editor LaTeX / AST      │  Vista previa                │
│          │  (CodeMirror o Monaco)   │  (render + figuras)          │
│          │                          │                              │
│  ────────┼──────────────────────────┼──────────────────────────────┤
│  Bóveda  │  Vault                   │  Previsualización / Timeline │
│  +       │  · fig1.png              │                              │
│  ingest  │  · datos.csv             │                              │
│          │  · nota_voz.webm         │                              │
└──────────┴──────────────────────────┴──────────────────────────────┘
```

### Modo Laboratorio

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                    [ Vista previa en grande ]                │
│                                                             │
│                    Última transcripción:                    │
│                    "La corriente subió a 12.3 mA..."        │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│              [  🎤  GRABAR DUMP DE VOZ  🎤  ]               │
│                                                             │
│         [ Detener ]  [ Insertar borrador ]  [ Cancelar ]    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Vista Timeline

```
┌─────────────────────────────────────────────────────────────┐
│  Timeline de la página                                       │
│  ────────────────────────────────────────────────────────   │
│  09:42  ✏️  text_inserted en posición 42                     │
│  09:55  🐍  cell_executed: iv_curve → figura generada        │
│  10:10  📎  vault_file_added: datos.csv                      │
│  10:12  📊  ingest_suggestion_accepted: gráfico generado     │
│                                                             │
│  [Ver diff] [Restaurar] [Comparar con actual]               │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Stack tecnológico

### Engine (Python)

- **Python 3.11+** como lenguaje principal.
- **FastAPI** para API REST/WebSocket.
- **Event Store**: SQLite o archivo JSONL por página.
- **LaTeX AST**: `latex2py`/`pylatexenc` o parser propio.
- **STT**: `faster-whisper` o `whisper.cpp` vía bindings.
- **Intent / Translation**: Ollama con Llama 3.2/8B, o API remota.
- **Code execution**: `jupyter-client` conectado a kernels locales.
- **Vault**: sistema de archivos + SQLite para metadatos.

### UI

- **Tauri** (Rust) o **Electron** para escritorio.
- **React + TypeScript + Tailwind CSS**.
- **CodeMirror 6** para editor LaTeX.
- **KaTeX** para renderizado rápido.

### Comunicación

- WebSocket para eventos en tiempo real.
- HTTP API para operaciones puntuales.

---

## 8. Roadmap

### Fase 0 — Fundamentos del engine

- [ ] Setup del proyecto Python con `pyproject.toml`.
- [ ] Event Store básico (guardar y reproducir eventos JSONL).
- [ ] Proyección de página a partir de eventos.
- [ ] Parser LaTeX → AST mínimo.

### Fase 1 — Prototipo Voz a LaTeX

- [ ] Script independiente: micrófono → Whisper → LaTeX (consola).
- [ ] Intent parser para matemática.
- [ ] Structured translation con LLM local.
- [ ] Inserción simulada en AST.

### Fase 2 — Editor LaTeX en vivo

- [ ] UI con editor + preview.
- [ ] Sincronización bidireccional AST ↔ texto.
- [ ] Autocompletado y snippets.
- [ ] Exportar a PDF y `.tex`.

### Fase 3 — Code Engine con Jupyter

- [ ] Integración con `jupyter-client`.
- [ ] Celdas Python ejecutables.
- [ ] Reemplazo de `vault://` a path absoluto.
- [ ] Cacheo de outputs.

### Fase 4 — Vault e ingesta mágica

- [ ] Drag & drop de archivos.
- [ ] Previsualización nativa.
- [ ] Ingesta de CSV → celda Python o tabla LaTeX.
- [ ] Eliminación con slider + time-lock.

### Fase 5 — Time-Travel

- [ ] Vista Timeline.
- [ ] Diff entre snapshots.
- [ ] Blame y restauración.

### Fase 6 — Plugins y colaboración

- [ ] Sistema de plugins.
- [ ] Marketplace local.
- [ ] Sincronización P2P/encriptada.

---

## 9. Ideas de valor adicional

### Para físicos experimentales

- Plantillas de entrada: setup, medición, análisis, conclusión.
- Propagación de errores automática.
- Verificación dimensional de ecuaciones.
- Integración con instrumentos (osciloscopios, lock-ins).
- Timeline del experimento con fotos y notas de voz.
- Etiquetas de muestra y reactivos.

### Para productividad

- Modo focus.
- Recordatorios de voz vinculados a páginas.
- Búsqueda semántica.
- Tags inteligentes.
- Resumen con IA.

### Para seguridad

- Snapshots automáticos cada 5 minutos.
- Exportar proyecto como `.lablog` encriptado.
- Verificación de integridad por hash.
- Log de auditoría completo.

---

## 10. Diferenciación

| Característica | Overleaf | TeXstudio | lablog |
|---|---|---|---|
| Colaboración | ✅ | ❌ | ✅ (futuro) |
| LaTeX en vivo | ✅ | ✅ | ✅ |
| Voz → LaTeX estructurado | ❌ | ❌ | ✅ |
| Modo hands-free | ❌ | ❌ | ✅ |
| Celdas ejecutables | ❌ | ❌ | ✅ |
| Bóveda por página | ❌ | ❌ | ✅ |
| Event Sourcing / Time-Travel | ❌ | ❌ | ✅ |
| Ingesta mágica de datos | ❌ | ❌ | ✅ |
| Sin servidor propietario | ❌ | ✅ | ✅ |
| Plugins extensibles | ❌ | ❌ | ✅ |

---

## 11. Principios no negociables

1. Los datos del usuario nunca dependen de un servidor propietario.
2. El motor debe poder correr sin UI y ser testeable por CLI.
3. El estado se reconstruye a partir de eventos inmutables.
4. Todo formato de archivo es abierto o documentado.
5. La eliminación de archivos es intencionalmente difícil pero usable.
6. Los plugins nunca acceden a datos sin permiso explícito.
7. Todo resultado científico es reproducible y versionado.

---

## 12. Próximos pasos concretos

1. Inicializar proyecto Python con estructura de engine.
2. Implementar Event Store JSONL mínimo.
3. Construir Prototipo 0 de Voz → LaTeX.
4. Validar prototipo con frases matemáticas reales.
5. Integrar prototipo con el engine.

---

*Documento iniciado por José Labarca Baeza. Idea original con Vicente. Arquitectura técnica refinada con feedback de GLM 5.2.*
*USM · Valparaíso · Chile*
