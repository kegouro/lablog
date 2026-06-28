"""Audio: grabación y transcripción con Whisper."""

from __future__ import annotations

import tempfile
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel


def record(duration: float = 5.0, sr: int = 16000) -> np.ndarray:
    print(f"Grabando {duration:.1f}s...")
    audio = sd.rec(int(duration * sr), samplerate=sr, channels=1, dtype="float32")
    sd.wait()
    return np.squeeze(audio)  # type: ignore[no-any-return]


def save_wav(audio: np.ndarray, path: Path, sr: int = 16000) -> None:
    audio = (audio / np.max(np.abs(audio)) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(audio.tobytes())


def transcribe(path: Path, model_size: str = "tiny", language: str = "es") -> str:
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(path), language=language, task="transcribe", vad_filter=True)
    return " ".join(s.text.strip() for s in segments)


def listen(duration: float = 5.0, model_size: str = "tiny", language: str = "es") -> str:
    audio = record(duration)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "voice.wav"
        save_wav(audio, path)
        return transcribe(path, model_size, language)
