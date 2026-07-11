"""Motores STT enchufables (local-first, gratis)."""

from lablog.voice.engines.base import EngineInfo, SttEngine, TranscriptResult
from lablog.voice.engines.registry import (
    default_server_engine_id,
    get_engine,
    list_engines,
    register_engine,
    transcribe_audio,
    unregister_engine,
)

__all__ = [
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
