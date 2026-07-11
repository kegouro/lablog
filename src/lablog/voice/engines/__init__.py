"""Motores STT enchufables (local-first, gratis)."""

from lablog.voice.engines.base import (
    WHISPER_MODEL_CHOICES,
    EngineInfo,
    SttEngine,
    TranscriptResult,
)
from lablog.voice.engines.registry import (
    default_server_engine_id,
    get_engine,
    list_engines,
    register_engine,
    transcribe_audio,
    unregister_engine,
)

__all__ = [
    "WHISPER_MODEL_CHOICES",
    "EngineInfo",
    "SttEngine",
    "TranscriptResult",
    "default_server_engine_id",
    "get_engine",
    "list_engines",
    "register_engine",
    "transcribe_audio",
    "unregister_engine",
]
