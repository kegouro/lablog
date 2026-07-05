"""Pipeline completo: Voz → LaTeX."""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from intent_parser import parse_intent
from latex_translator import translate
from record import record_audio, save_wav
from transcribe import transcribe


def voice_to_latex(
    duration: float = 5.0,
    model_size: str = "tiny",
    language: str = "es",
) -> None:
    """Graba audio, transcribe, detecta intención y convierte a LaTeX."""
    print("=" * 60)
    print("🎙️  lablog · Prototipo 0: Voz → LaTeX")
    print("=" * 60)

    # 1. Grabar
    audio = record_audio(duration=duration)

    with tempfile.TemporaryDirectory() as tmpdir:
        wav_path = Path(tmpdir) / "voice.wav"
        save_wav(audio, wav_path)

        # 2. Transcribir
        text = transcribe(wav_path, model_size=model_size, language=language)
        print(f"\n📢 Transcripción: {text}")

        # 3. Detectar intención
        intent = parse_intent(text)
        print(f"\n🎯 Intención: {intent.type.value} (confianza {intent.confidence:.2f})")
        if intent.matched_keywords:
            print(f"🔑 Palabras clave: {', '.join(intent.matched_keywords)}")

        # 4. Traducir a LaTeX
        result = translate(text, intent.type.value)
        print(f"\n📝 Fuente de traducción: {result.source}")
        print(f"📐 Modo: {result.mode}")
        print(f"🧮 LaTeX generado:\n{result.latex}")


def text_to_latex(text: str, language: str = "es") -> None:
    """Modo texto: salta la grabación y va directo a intención + traducción."""
    print("=" * 60)
    print("🎙️  lablog · Prototipo 0: Texto → LaTeX")
    print("=" * 60)

    intent = parse_intent(text)
    print(f"📝 Texto: {text}")
    print(f"🎯 Intención: {intent.type.value} (confianza {intent.confidence:.2f})")
    if intent.matched_keywords:
        print(f"🔑 Palabras clave: {', '.join(intent.matched_keywords)}")

    result = translate(text, intent.type.value)
    print(f"\n📝 Fuente de traducción: {result.source}")
    print(f"📐 Modo: {result.mode}")
    print(f"🧮 LaTeX generado:\n{result.latex}")


def main() -> None:
    parser = argparse.ArgumentParser(description="lablog Prototipo 0: Voz/Texto → LaTeX")
    parser.add_argument("--text", "-t", type=str, help="Usar texto en vez de micrófono")
    parser.add_argument("--duration", "-d", type=float, default=5.0, help="Duración de grabación")
    parser.add_argument("--model", "-m", type=str, default="tiny", help="Modelo Whisper")
    parser.add_argument("--language", "-l", type=str, default="es", help="Idioma")
    args = parser.parse_args()

    if args.text:
        text_to_latex(args.text, language=args.language)
    else:
        voice_to_latex(
            duration=args.duration,
            model_size=args.model,
            language=args.language,
        )


if __name__ == "__main__":
    main()
