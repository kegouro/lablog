# Prototipo 0 · Voz → LaTeX

Pipeline independiente que demuestra la killer feature de lablog: convertir dictado de voz en código LaTeX estructurado.

## Arquitectura de capas

```
[Micrófono / Texto]
        │
        ▼
[STT]              faster-whisper (local)
        │
        ▼
[Intent Parser]    detecta jerga matemática
        │
        ▼
[Translation]      Ollama → OpenAI → reglas
        │
        ▼
[LaTeX en consola]
```

## Requisitos

- Python 3.11+
- Entorno virtual con dependencias instaladas desde `pyproject.toml`
- (Opcional) Ollama corriendo localmente para mejor calidad
- (Opcional) `OPENAI_API_KEY` en `.env` para fallback de pago

## Uso

### Modo texto (sin micrófono)

```bash
python prototypes/voice_to_latex/voice_to_latex.py \
  --text "integral de cero a infinito de e a la menos x cuadrado dx"
```

### Modo voz

```bash
python prototypes/voice_to_latex/voice_to_latex.py --duration 5
```

### Demo con frases de prueba

```bash
python prototypes/voice_to_latex/demo_text.py
```

## Estado

El traductor por reglas maneja frases comunes. Para producción, se usará un LLM local (Ollama) con prompt estricto, manteniendo el fallback por reglas para offline rápido.
