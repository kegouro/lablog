"""Registro de motores STT.

Extender:
    from lablog.voice.engines.registry import register_engine
    register_engine(MyEngine())

Los engines se descubren por id. ``browser`` es solo informativo (corre en el cliente).
"""

from __future__ import annotations

from lablog.voice.engines.base import EngineInfo, SttEngine, TranscriptResult
from lablog.voice.engines.whisper import WhisperSttEngine

_ENGINES: dict[str, SttEngine] = {}
_DEFAULT_SERVER = "whisper"


def _browser_info() -> EngineInfo:
    return EngineInfo(
        id="browser",
        label="Navegador (Web Speech)",
        kind="client",
        available=True,
        description=(
            "Dictado del navegador (Chrome/Edge). Rápido, sin instalar nada; "
            "menos preciso. Corre 100% en el cliente."
        ),
        requires_extra=None,
    )


def register_engine(engine: SttEngine, *, replace: bool = False) -> None:
    """Registra un motor server-side. No uses id ``browser`` (reservado)."""
    if engine.id == "browser":
        raise ValueError("id 'browser' está reservado para el motor del cliente")
    if engine.id in _ENGINES and not replace:
        raise ValueError(f"motor ya registrado: {engine.id}")
    _ENGINES[engine.id] = engine


def unregister_engine(engine_id: str) -> None:
    _ENGINES.pop(engine_id, None)


def _ensure_builtins() -> None:
    if "whisper" not in _ENGINES:
        register_engine(WhisperSttEngine())


def list_engines() -> list[EngineInfo]:
    """Lista motores visibles (cliente + server)."""
    _ensure_builtins()
    infos = [_browser_info()]
    infos.extend(engine.info() for engine in _ENGINES.values())
    return infos


def get_engine(engine_id: str) -> SttEngine:
    """Devuelve un motor server-side o lanza KeyError / RuntimeError."""
    _ensure_builtins()
    if engine_id == "browser":
        raise RuntimeError(
            "El motor 'browser' corre en el cliente; no se invoca en el servidor."
        )
    try:
        return _ENGINES[engine_id]
    except KeyError as exc:
        known = ", ".join(sorted(_ENGINES)) or "(ninguno)"
        raise KeyError(f"motor desconocido: {engine_id}. Disponibles: {known}") from exc


def default_server_engine_id() -> str:
    _ensure_builtins()
    eng = _ENGINES.get(_DEFAULT_SERVER)
    if eng is not None and eng.available():
        return _DEFAULT_SERVER
    for eid, e in _ENGINES.items():
        if e.available():
            return eid
    return _DEFAULT_SERVER


def transcribe_audio(
    audio: bytes,
    *,
    engine_id: str | None = None,
    filename: str = "audio.wav",
    language: str | None = None,
) -> TranscriptResult:
    """Atajo: resuelve motor y transcribe."""
    eid = engine_id or default_server_engine_id()
    engine = get_engine(eid)
    if not engine.available():
        extra = engine.info().requires_extra or "voice"
        raise RuntimeError(
            f"Motor '{eid}' no disponible. "
            f'Instala: pip install "jose-labarca-lablog[{extra}]"'
        )
    return engine.transcribe(audio, filename=filename, language=language)
