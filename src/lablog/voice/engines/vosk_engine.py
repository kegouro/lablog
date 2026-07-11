"""Motor STT local con Vosk (gratis, ligero, offline).

Instalación:
    pip install "jose-labarca-lablog[voice]"

Modelo (español small ~40 MB), primera vez:
    lablog voice setup-vosk
    # o POST /api/v1/voice/engines/vosk/setup

Variables:
    LABLOG_VOSK_MODEL_PATH   default: ~/.lablog/models/vosk-model-small-es-0.42
"""

from __future__ import annotations

import json
import logging
import wave
from io import BytesIO
from pathlib import Path

from lablog.config import settings
from lablog.voice.engines.base import EngineInfo, TranscriptResult

logger = logging.getLogger(__name__)

_ENGINE_ID = "vosk"

# Modelo oficial pequeño en español (Alphacephei / Vosk).
DEFAULT_VOSK_MODEL_NAME = "vosk-model-small-es-0.42"
DEFAULT_VOSK_MODEL_URL = (
    "https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip"
)


class VoskSttEngine:
    """Vosk offline — más ligero que Whisper en CPU."""

    def __init__(self) -> None:
        self._model: object | None = None

    @property
    def id(self) -> str:
        return _ENGINE_ID

    @property
    def label(self) -> str:
        return "Vosk local (ligero)"

    @property
    def kind(self) -> str:
        return "local"

    @property
    def description(self) -> str:
        return (
            "Transcripción offline con Vosk. Gratis, sin API keys. "
            "Más liviano y rápido en CPU que Whisper; un poco menos preciso."
        )

    def model_path(self) -> Path:
        return Path(settings.vosk_model_path).expanduser().resolve()

    def available(self) -> bool:
        try:
            import vosk  # noqa: F401
        except ImportError:
            return False
        path = self.model_path()
        # Un modelo válido tiene am/ o conf/ o similar.
        return path.is_dir() and any(path.iterdir())

    def info(self) -> EngineInfo:
        ok = self.available()
        return EngineInfo(
            id=self.id,
            label=self.label,
            kind=self.kind,
            available=ok,
            description=self.description,
            requires_extra=None if ok else "voice",
            options={
                "model_path": str(self.model_path()),
                "model_name": DEFAULT_VOSK_MODEL_NAME,
                "setup_endpoint": "/api/v1/voice/engines/vosk/setup",
                "needs_setup": not ok,
            },
        )

    def _load_model(self) -> object:
        if self._model is not None:
            return self._model
        if not self.available():
            raise RuntimeError(
                "Vosk no listo. Instala el extra [voice] y descarga el modelo: "
                "POST /api/v1/voice/engines/vosk/setup  o  lablog voice setup-vosk"
            )
        from vosk import Model

        logger.info("Cargando Vosk model path=%s", self.model_path())
        self._model = Model(str(self.model_path()))
        return self._model

    def transcribe(
        self,
        audio: bytes,
        *,
        filename: str = "audio.wav",
        language: str | None = None,
        model: str | None = None,  # noqa: ARG002 — API común; Vosk usa path fijo
    ) -> TranscriptResult:
        if not audio:
            raise ValueError("audio vacío")

        pcm, sample_rate = _pcm_mono_16le(audio, filename)
        if sample_rate not in (8000, 16000, 32000, 44100, 48000):
            raise ValueError(f"sample rate no soportado por Vosk: {sample_rate}")

        # Vosk rinde mejor a 16 kHz; re-sample simple si hace falta.
        if sample_rate != 16000:
            pcm = _resample_pcm16(pcm, sample_rate, 16000)
            sample_rate = 16000

        from vosk import KaldiRecognizer, SetLogLevel

        SetLogLevel(-1)
        vosk_model = self._load_model()
        rec = KaldiRecognizer(vosk_model, sample_rate)
        rec.SetWords(False)

        # Chunks de ~0.25 s
        frame = sample_rate // 4 * 2  # bytes (16-bit mono)
        for i in range(0, len(pcm), frame):
            rec.AcceptWaveform(pcm[i : i + frame])
        final = json.loads(rec.FinalResult())
        text = str(final.get("text") or "").strip()
        return TranscriptResult(
            text=text,
            engine=self.id,
            language=language or "es",
            meta={"model_path": str(self.model_path())},
        )


def setup_vosk_model(*, force: bool = False) -> dict[str, object]:
    """Descarga y descomprime el modelo small-es si falta.

    Gratis (Alphacephei). Idempotente salvo ``force=True``.
    """
    import shutil
    import tempfile
    import urllib.request
    import zipfile

    try:
        import vosk  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            'Paquete vosk no instalado. pip install "jose-labarca-lablog[voice]"'
        ) from exc

    target = Path(settings.vosk_model_path).expanduser().resolve()
    if target.is_dir() and any(target.iterdir()) and not force:
        return {
            "status": "ok",
            "path": str(target),
            "downloaded": False,
            "message": "modelo ya presente",
        }

    target.parent.mkdir(parents=True, exist_ok=True)
    url = settings.vosk_model_url or DEFAULT_VOSK_MODEL_URL
    logger.info("Descargando modelo Vosk desde %s", url)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        zip_path = tmp_path / "vosk-model.zip"
        urllib.request.urlretrieve(url, zip_path)  # noqa: S310 — URL de confianza configurable
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_path)
        # El zip trae un directorio raíz con el nombre del modelo.
        extracted = [p for p in tmp_path.iterdir() if p.is_dir()]
        if not extracted:
            raise RuntimeError("ZIP de Vosk sin directorio de modelo")
        src = extracted[0]
        if target.exists():
            shutil.rmtree(target)
        shutil.move(str(src), str(target))

    return {
        "status": "ok",
        "path": str(target),
        "downloaded": True,
        "message": f"modelo listo en {target}",
    }


def _pcm_mono_16le(audio: bytes, filename: str) -> tuple[bytes, int]:
    """Extrae PCM s16le mono de un WAV; si no es WAV, error claro."""
    suffix = Path(filename).suffix.lower()
    if suffix and suffix not in {".wav", ".wave"}:
        # Intentamos igual por si el cliente mandó WAV con otro nombre.
        pass
    try:
        with wave.open(BytesIO(audio), "rb") as wf:
            channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            rate = wf.getframerate()
            nframes = wf.getnframes()
            raw = wf.readframes(nframes)
    except wave.Error as exc:
        raise ValueError(
            "Vosk requiere WAV PCM. Usa el grabador de lablog (WAV 16 kHz) "
            f"o convierte el audio. Detalle: {exc}"
        ) from exc

    if sampwidth != 2:
        raise ValueError(f"Vosk requiere 16-bit PCM (sampwidth=2), got {sampwidth}")
    if channels == 1:
        return raw, rate
    if channels == 2:
        # Downmix estéreo → mono
        import array

        samples = array.array("h")
        samples.frombytes(raw)
        mono = array.array("h")
        for i in range(0, len(samples), 2):
            left = samples[i]
            right = samples[i + 1] if i + 1 < len(samples) else left
            mono.append(int((left + right) / 2))
        return mono.tobytes(), rate
    raise ValueError(f"canales no soportados: {channels}")


def _resample_pcm16(pcm: bytes, from_sr: int, to_sr: int) -> bytes:
    import array

    if from_sr == to_sr:
        return pcm
    samples = array.array("h")
    samples.frombytes(pcm)
    ratio = from_sr / to_sr
    new_len = max(1, int(len(samples) / ratio))
    out = array.array("h")
    for i in range(new_len):
        idx = i * ratio
        i0 = int(idx)
        i1 = min(i0 + 1, len(samples) - 1)
        frac = idx - i0
        v = samples[i0] * (1 - frac) + samples[i1] * frac
        out.append(int(v))
    return out.tobytes()
