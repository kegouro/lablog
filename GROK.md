# GROK session handoff — lablog

**Fecha:** 2026-07-11  
**Rama:** `main` (sync con `origin/main`)  
**Propósito:** contexto denso para reabrir el trabajo en lablog sin re-descubrir todo.

---

## Estado del producto (online)

| Superficie | Estado |
|------------|--------|
| Repo | https://github.com/kegouro/lablog |
| Docs/Pages | https://kegouro.github.io/lablog/ — landing con galería real + `notes.html` demo |
| PyPI | `jose-labarca-lablog==0.3.1` |
| Release | [v0.3.1](https://github.com/kegouro/lablog/releases/tag/v0.3.1) |
| Pharos landing | https://kegouro.github.io/ — lablog **Vivo**, PyPI v0.3.1 |
| Perfil GitHub | https://github.com/kegouro — tabla Pharos: lablog **✅ Vivo (v0.3.1)** (antes decía Próximamente) |
| Descripción repo | `lablog v0.3.1 — bitácora LaTeX-nativa…` (About / title) |

### Zenodo (otros proyectos Pharos — ya cableados)

| Proyecto | Versión | DOI |
|----------|---------|-----|
| spmkit | v0.1.4 | 10.5281/zenodo.21303280 |
| curvana | v0.1.2 | 10.5281/zenodo.21303284 |
| BeamLabStudio | v0.1.2 | 10.5281/zenodo.21303286 |
| Omniconvert | v1.0.1 | 10.5281/zenodo.21303287 |
| parcella | v0.1.1 | 10.5281/zenodo.21196991 |

**lablog en Zenodo:** pendiente de que el usuario active el repo en  
https://zenodo.org/account/settings/github/ → `kegouro/lablog` ON, y re-publique / sync del tag `v0.3.1`. Luego pegar DOI en `CITATION.cff` + badge README.

---

## Commits relevantes (esta arco)

| SHA | Qué |
|-----|-----|
| `4975b73` / PR #20 | Harden + README académico + screenshots reales |
| `e34ca65` / `a6d08c1` | Release prep v0.3.1 + badges |
| `3889cf9` | Pages landing con capturas UI |
| `78e4f8a` | Fix dictado: anti-verborrea Web Speech |
| `65c54b4` | STT modular: registry + Whisper local + browser |
| `8ef2061` | Vosk + selector tamaño Whisper en Preferencias |

Perfil Pharos: commit en `kegouro/kegouro` marcando lablog Vivo.  
Landing: `kegouro.github.io` card lablog actualizada.

---

## Stack y convenciones

- Backend: Python 3.11+, FastAPI, Pydantic, event sourcing JSONL, Jupyter client.
- Frontend: Vite, React 19, TS, Tailwind v4, shadcn, Zustand.
- Package managers: `uv` (Python), `npm` (UI).
- Event sourcing: append-only en `events.py`, proyección en `projector.py`. **No mutar AST desde API.**
- Paths vía `config.py`. API UI en `ui/src/lib/api.ts`. Store: `ui/src/stores/app-store.ts`.
- AI commits: `Co-Authored-By: Kimi Code <noreply@example.com>`
- Instrucciones agente: `Agents.md`

### Dev

```bash
source .venv/bin/activate
uvicorn lablog.api:app --host 127.0.0.1 --port 8000 --reload
cd ui && npm run dev

pytest -q
ruff check src tests
mypy -p lablog
cd ui && npm run build && npm run lint
```

---

## Hardening (v0.3.x) — ya en main

- OCC atómico en document replace (`expected_version` / 409).
- Autosave serializado + retry 409.
- Lab mode flush de celdas dirty al salir; insert/update/move devuelven `version`.
- `PageDetail` con `project_id` / `updated_at`.
- Snippets `fit_line` / `simple_table`; bounds título/project_id.
- Boot UI resiliente (`allSettled` etc.).

---

## Docs / capturas

- README EN + `README.es.md` (gemelos académicos).
- Capturas reales: `docs/assets/screenshots/*.png` (7).
- Script: `scripts/capture_ui_screenshots.mjs`.
- Pages: `scripts/build_demo_site.py` exporta landing marketing + `notes.html` + copia screenshots.
- Release notes: `docs/release-notes-v0.3.1.md`.

---

## Voz / STT — arquitectura actual (importante)

### Problema que se corrigió

El dictado del navegador era **inutilizable** por:

1. **Append ciego del transcript** — Chrome re-envía finales con `resultIndex=0` → duplicación explosiva (`hola` → `hola hola`…).
2. **Corte por silencio** → insertaba basura parcial sin que el usuario pulsara Detener.
3. **Reemplazos math agresivos** sobre prosa (`por` → `·`, etc.) en paths incorrectos.

### Capas

```
UI
  useDictation          # unifica engines
  use-speech            # Web Speech (browser), rebuild finales, auto-restart
  record-wav            # mic → WAV 16 kHz mono (sin ffmpeg server)
  Preferencias          # motor + modelo Whisper + setup Vosk

API
  GET  /voice/engines
  POST /voice/transcribe?engine=&model=&language=
  POST /pages/{id}/voice          # texto ya listo
  POST /pages/{id}/voice/audio    # audio → STT → insert
  POST /voice/engines/vosk/setup  # descarga modelo ES ~40MB

Backend voice/
  engines/base.py       # Protocol SttEngine, TranscriptResult, EngineInfo
  engines/registry.py   # register_engine / list / get / transcribe_audio
  engines/whisper.py    # faster-whisper; cache por tamaño de modelo
  engines/vosk_engine.py# Vosk ligero; setup_vosk_model()
  parser.py             # clean_dictation_text + intents → LaTeX
  audio.py              # utilidades CLI opcionales (sounddevice)
```

### Motores

| id | Dónde | Extra | Notas |
|----|--------|-------|--------|
| `browser` | cliente | no | Rápido, impreciso |
| `whisper` | server | `[voice]` | tiny/base/small/medium/large-v3 (UI) |
| `vosk` | server | `[voice]` | Ligero; necesita modelo descargado |

```bash
pip install "jose-labarca-lablog[voice]"
# o: uv sync --extra voice
lablog voice engines
lablog voice setup-vosk
```

Env (`.env.example`):

- `LABLOG_WHISPER_MODEL` (default `base`)
- `LABLOG_WHISPER_DEVICE` / `COMPUTE` / `LANGUAGE`
- `LABLOG_VOSK_MODEL_PATH` (default `~/.lablog/models/vosk-model-small-es-0.42`)
- `LABLOG_VOSK_MODEL_URL`
- `LABLOG_VOICE_MAX_UPLOAD_MB`

### UI preferencias

- Store: `voiceEngine` (`browser` \| `whisper` \| `vosk`), `whisperModel` (tamaños).
- Persistencia: `localStorage` keys `lablog-voiceEngine`, `lablog-whisperModel`.
- Setup Vosk: botón en Preferencias → `setupVoskModel()`.

### Extender con un motor nuevo

```python
from lablog.voice.engines import register_engine
register_engine(MyEngine())  # id propio, available(), transcribe(..., model=None)
```

---

## Feedback sincero (sesión) — no yes-man

**Fortalezas:** problema real (LaTeX lab local-first); event sourcing serio; empaque académico/Pharos; UI de herramienta.

**Debilidades / riesgos:**

- Audiencia aún ambigua (autor vs adopción externa).
- Superficie ancha (voz, diagramas, vault, OCC…) vs profundidad percibida.
- OCC/arquitectura buena no se vende sola: la UX de “nunca pierdo trabajo” debe ser obvia.
- Competencia = hábito (Overleaf+Jupyter), no otro ELN.
- Zenodo lablog incompleto vs hermanos.
- Monorepo mental pesado para un solo maintainer.
- STT browser sigue siendo mediocre; Whisper/Vosk lo hacen usable, no estenógrafo mágico.

**Condiciones para recomendar sin reservas:**

1. Onboarding in-app 10 min.
2. Tres flujos core perfectos (LaTeX, celda, export).
3. Promesa de datos explícita.
4. Un usuario externo real una semana.
5. DOI lablog.
6. Congelar features y matar fricción.
7. Decidir usuario principal.

---

## Pendiente / siguiente

- [ ] Usuario: activar Zenodo GitHub para `kegouro/lablog`, sync `v0.3.1`, pasar DOI.
- [ ] Probar en máquina real: `uv sync --extra voice`, Preferencias → Whisper/Vosk, dictar.
- [ ] Opcional: motor más (whisper.cpp, vosk otros idiomas).
- [ ] Opcional: usuario real 1 semana de lab → lista de fricciones.
- [ ] No reintroducir “Próximamente” en perfil/landing para lablog.

### Historial git residual (no es el título del repo)

Primer commit del repo: `Inicio — lablog (Pharos Project, próximamente)` — solo en historial.

---

## Archivos clave a tocar

| Área | Paths |
|------|--------|
| STT | `src/lablog/voice/engines/*`, `parser.py`, `api.py` voice routes |
| Dictado UI | `ui/src/hooks/use-dictation.ts`, `use-speech.ts`, `lib/voice/*`, toolbar, settings |
| Preferencias | `ui/src/stores/app-store.ts` (`voiceEngine`, `whisperModel`) |
| Config | `src/lablog/config.py`, `.env.example` |
| CLI voz | `lablog voice engines` / `setup-vosk` en `cli.py` |
| Pages demo | `scripts/build_demo_site.py` |
| Tests voz | `tests/test_voice_*.py`, `ui/src/hooks/use-speech.test.ts`, toolbar tests |

---

## Cómo retomar con Grok

Pegar o referenciar este archivo:

> Continúa desde `GROK.md` en lablog: contexto de v0.3.1, STT modular (browser/whisper/vosk), Zenodo pendiente, y la lista de pendientes.

O en la sesión:

```text
Lee GROK.md y Agents.md del repo lablog; retoma desde ahí.
```

---

*Generado al cerrar la sesión de polish/docs/voz. Actualizar este archivo cuando el estado online o la arquitectura de voz cambien de forma material.*
