"""Utilidades de audio opcionales (CLI / prototipos).

El path web no usa esto: el navegador envía WAV y ``engines.whisper``
transcribe. ``sounddevice`` solo se necesita para grabar desde el servidor.
"""

from __future__ import annotations

import tempfile
import wave
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np


def save_wav(audio: np.ndarray, path: Path, sr: int = 16000) -> None:
    import numpy as np

    peak = float(np.max(np.abs(audio))) or 1.0
    pcm = (audio / peak * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


def record(duration: float = 5.0, sr: int = 16000) -> np.ndarray:
    """Graba desde el mic del servidor (requiere sounddevice)."""
    import sounddevice as sd

    print(f"Grabando {duration:.1f}s...")
    audio = sd.rec(int(duration * sr), samplerate=sr, channels=1, dtype="float32")
    sd.wait()
    return np.squeeze(audio)  # type: ignore[no-any-return]


def listen(duration: float = 5.0, language: str | None = None) -> str:
    """Graba + transcribe con el motor Whisper local."""
    from lablog.voice.engines import transcribe_audio

    audio = record(duration)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "voice.wav"
        save_wav(audio, path)
        result = transcribe_audio(
            path.read_bytes(),
            filename="voice.wav",
            language=language,
        )
        return result.text
