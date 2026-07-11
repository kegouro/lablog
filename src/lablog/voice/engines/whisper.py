"""Motor STT local con faster-whisper (gratis, offline).

Instalación:
    pip install "jose-labarca-lablog[voice]"

Variables:
    LABLOG_WHISPER_MODEL     default: base
    LABLOG_WHISPER_DEVICE    default: cpu
    LABLOG_WHISPER_COMPUTE   default: int8
    LABLOG_WHISPER_LANGUAGE  default: es
"""

from __future__ import annotations

import logging
import tempfile
import threading
from pathlib import Path

from lablog.config import settings
from lablog.voice.engines.base import WHISPER_MODEL_CHOICES, EngineInfo, TranscriptResult

logger = logging.getLogger(__name__)

_ENGINE_ID = "whisper"


class WhisperSttEngine:
    """Whisper local vía faster-whisper.

    Cachea un modelo por tamaño (tiny/base/small/…) para poder cambiar
    desde la UI sin reiniciar el proceso.
    """

    def __init__(self) -> None:
        self._models: dict[str, object] = {}
        self._lock = threading.Lock()

    @property
    def id(self) -> str:
        return _ENGINE_ID

    @property
    def label(self) -> str:
        return f"Whisper local ({settings.whisper_model})"

    @property
    def kind(self) -> str:
        return "local"

    @property
    def description(self) -> str:
        return (
            "Transcripción offline con faster-whisper. "
            "Gratis, sin API keys. Elige el tamaño del modelo en Preferencias."
        )

    def available(self) -> bool:
        try:
            import faster_whisper  # noqa: F401
        except ImportError:
            return False
        return True

    def info(self) -> EngineInfo:
        return EngineInfo(
            id=self.id,
            label=self.label,
            kind=self.kind,
            available=self.available(),
            description=self.description,
            requires_extra="voice" if not self.available() else None,
            options={
                "models": list(WHISPER_MODEL_CHOICES),
                "default_model": settings.whisper_model,
                "device": settings.whisper_device,
                "compute": settings.whisper_compute,
            },
        )

    def _normalize_model(self, model: str | None) -> str:
        size = (model or settings.whisper_model).strip() or "base"
        if size not in WHISPER_MODEL_CHOICES:
            # Permitir IDs custom de HuggingFace, pero avisar en log.
            logger.warning("modelo Whisper no estándar: %s", size)
        return size

    def _load_model(self, size: str) -> object:
        cached = self._models.get(size)
        if cached is not None:
            return cached
        with self._lock:
            cached = self._models.get(size)
            if cached is not None:
                return cached
            from faster_whisper import WhisperModel

            logger.info(
                "Cargando Whisper model=%s device=%s compute=%s",
                size,
                settings.whisper_device,
                settings.whisper_compute,
            )
            loaded = WhisperModel(
                size,
                device=settings.whisper_device,
                compute_type=settings.whisper_compute,
            )
            self._models[size] = loaded
            return loaded

    def transcribe(
        self,
        audio: bytes,
        *,
        filename: str = "audio.wav",
        language: str | None = None,
        model: str | None = None,
    ) -> TranscriptResult:
        if not audio:
            raise ValueError("audio vacío")
        if not self.available():
            raise RuntimeError(
                'Motor Whisper no disponible. Instala: pip install "jose-labarca-lablog[voice]"'
            )

        size = self._normalize_model(model)
        lang = language or settings.whisper_language
        suffix = Path(filename).suffix.lower() or ".wav"
        if suffix not in {".wav", ".webm", ".ogg", ".mp3", ".m4a", ".mp4", ".flac", ".mpeg"}:
            suffix = ".wav"

        whisper_model = self._load_model(size)
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
            tmp.write(audio)
            tmp.flush()
            segments, info = whisper_model.transcribe(  # type: ignore[attr-defined]
                tmp.name,
                language=lang or None,
                task="transcribe",
                vad_filter=True,
                beam_size=5,
                condition_on_previous_text=False,
            )
            parts: list[str] = []
            for seg in segments:
                piece = (seg.text or "").strip()
                if piece:
                    parts.append(piece)
            text = " ".join(parts).strip()
            detected = getattr(info, "language", None)
            return TranscriptResult(
                text=text,
                engine=self.id,
                language=detected or lang,
                meta={
                    "model": size,
                    "language_probability": getattr(info, "language_probability", None),
                },
            )
