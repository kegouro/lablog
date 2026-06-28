"""Transcripción de audio a texto usando faster-whisper."""

from __future__ import annotations

import argparse
from pathlib import Path

from faster_whisper import WhisperModel


def transcribe(
    audio_path: Path,
    model_size: str = "tiny",
    device: str = "cpu",
    compute_type: str = "int8",
    language: str = "es",
) -> str:
    """Transcribe un archivo de audio a texto plano."""
    print(f"🧠 Cargando modelo Whisper '{model_size}' ({device}, {compute_type})...")
    model = WhisperModel(model_size, device=device, compute_type=compute_type)

    print("📝 Transcribiendo...")
    segments, info = model.transcribe(
        str(audio_path),
        language=language,
        task="transcribe",
        vad_filter=True,
    )

    text = " ".join(segment.text.strip() for segment in segments)
    print(f"🌐 Idioma detectado: {info.language} (probabilidad {info.language_probability:.2f})")
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description="Transcribe audio a texto.")
    parser.add_argument("audio", type=Path, help="Archivo de audio")
    parser.add_argument("--model", "-m", type=str, default="tiny", help="Tamaño del modelo Whisper")
    parser.add_argument("--language", "-l", type=str, default="es", help="Idioma del audio")
    args = parser.parse_args()

    text = transcribe(args.audio, model_size=args.model, language=args.language)
    print(f"\n📢 Transcripción:\n{text}")


if __name__ == "__main__":
    main()
