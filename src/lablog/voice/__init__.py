"""Pipeline de voz de lablog.

Capas:
- ``engines`` — STT modular (Whisper local, extensible)
- ``parser`` — limpieza + intents → LaTeX
"""

from lablog.voice.engines import (
    EngineInfo,
    TranscriptResult,
    list_engines,
    register_engine,
    transcribe_audio,
)
from lablog.voice.parser import (
    IntentType,
    clean_dictation_text,
    parse_intent,
    translate,
)

__all__ = [
    "EngineInfo",
    "IntentType",
    "TranscriptResult",
    "clean_dictation_text",
    "list_engines",
    "parse_intent",
    "register_engine",
    "transcribe_audio",
    "translate",
]
