"""Graba audio del micrófono y lo guarda como WAV."""

from __future__ import annotations

import argparse
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd


def record_audio(
    duration: float = 5.0,
    sample_rate: int = 16000,
    channels: int = 1,
    dtype: str = "float32",
) -> np.ndarray:
    """Graba audio del micrófono por un tiempo determinado."""
    print(f"🎤 Grabando por {duration:.1f} segundos...")
    audio = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=channels,
        dtype=dtype,
    )
    sd.wait()
    print("✅ Grabación finalizada.")
    return np.squeeze(audio)


def save_wav(audio: np.ndarray, path: Path, sample_rate: int = 16000) -> None:
    """Guarda un array numpy como archivo WAV de 16 bits."""
    # Normalizar y convertir a int16
    audio = audio / np.max(np.abs(audio))
    audio_int16 = (audio * 32767).astype(np.int16)

    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())


def main() -> None:
    parser = argparse.ArgumentParser(description="Graba audio del micrófono.")
    parser.add_argument("--duration", "-d", type=float, default=5.0, help="Duración en segundos")
    parser.add_argument("--output", "-o", type=Path, default=Path("recording.wav"), help="Archivo de salida")
    args = parser.parse_args()

    audio = record_audio(duration=args.duration)
    save_wav(audio, args.output)
    print(f"💾 Audio guardado en: {args.output}")


if __name__ == "__main__":
    main()
