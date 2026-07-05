"""Integra el prototipo de voz con el Event Store y AST de lablog."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from lablog.event_store import EventStore
from lablog.events import Event, math_inserted, page_created, text_inserted
from lablog.latex_ast import serialize_ast
from lablog.projector import project

# Importar prototipo de voz (ruta relativa)
sys.path.insert(0, str(Path(__file__).parent))
from intent_parser import IntentType, parse_intent
from latex_translator import translate
from record import record_audio, save_wav
from transcribe import transcribe

_MATH_INTENTS = (
    IntentType.MATH,
    IntentType.INTEGRAL,
    IntentType.EQUATION,
    IntentType.SNIPPET,
    IntentType.MATRIX,
)


def get_store() -> EventStore:
    data_dir = Path.home() / ".lablog" / "events"
    return EventStore(data_dir)


def create_page(title: str) -> str:
    store = get_store()
    page_id = Event.__pydantic_fields__["id"].default_factory()  # type: ignore[arg-type]
    # Workaround: usar uuid directamente
    from uuid import uuid4

    page_id = str(uuid4())
    store.append(page_created(page_id=page_id, title=title))
    return page_id


def voice_to_event(
    page_id: str,
    duration: float = 5.0,
    model_size: str = "tiny",
    language: str = "es",
) -> Event:
    """Graba voz, la convierte a LaTeX y genera un evento para el AST."""
    print("=" * 60)
    print("🎙️  lablog · Voz → Evento → AST")
    print("=" * 60)

    audio = record_audio(duration=duration)

    with tempfile.TemporaryDirectory() as tmpdir:
        wav_path = Path(tmpdir) / "voice.wav"
        save_wav(audio, wav_path)

        text = transcribe(wav_path, model_size=model_size, language=language)
        print(f"\n📢 Transcripción: {text}")

        intent = parse_intent(text)
        print(f"🎯 Intención: {intent.type.value} (confianza {intent.confidence:.2f})")

        result = translate(text, intent.type.value)
        print(f"📝 Fuente: {result.source}")
        print(f"🧮 LaTeX: {result.latex}")

        if intent.type in _MATH_INTENTS:
            body, detected_mode = _extract_latex_body(result.latex)
            mode = detected_mode if result.mode == "display" else result.mode
            return math_inserted(page_id=page_id, ast_path="/document", latex=body, mode=mode)

        return text_inserted(page_id=page_id, position=-1, text=text)


def _extract_latex_body(latex: str) -> tuple[str, str]:
    """Separa el contenido LaTeX de sus delimitadores."""
    latex = latex.strip()
    if latex.startswith("\\[") and latex.endswith("\\]"):
        return latex[2:-2].strip(), "display"
    if latex.startswith("$") and latex.endswith("$"):
        return latex[1:-1].strip(), "inline"
    return latex, "inline"


def text_to_event(page_id: str, text: str) -> Event:
    """Convierte texto directamente a un evento."""
    intent = parse_intent(text)
    result = translate(text, intent.type.value)

    print(f"📝 Texto: {text}")
    print(f"🎯 Intención: {intent.type.value}")
    print(f"🧮 LaTeX: {result.latex}")

    if intent.type in _MATH_INTENTS:
        body, detected_mode = _extract_latex_body(result.latex)
        mode = detected_mode if result.mode == "display" else result.mode
        return math_inserted(page_id=page_id, ast_path="/document", latex=body, mode=mode)

    return text_inserted(page_id=page_id, position=-1, text=text)


def main() -> int:
    parser = argparse.ArgumentParser(description="Voz/Texto → Evento → AST")
    parser.add_argument("--page-id", "-p", type=str, help="ID de página existente")
    parser.add_argument(
        "--title", "-t", type=str, default="Bitácora de voz", help="Título para nueva página"
    )
    parser.add_argument("--text", type=str, help="Usar texto en vez de micrófono")
    parser.add_argument("--duration", "-d", type=float, default=5.0, help="Duración de grabación")
    parser.add_argument("--model", "-m", type=str, default="tiny", help="Modelo Whisper")
    parser.add_argument("--language", "-l", type=str, default="es", help="Idioma")
    args = parser.parse_args()

    store = get_store()

    if args.page_id:
        page_id = args.page_id
        existing = store.get_events(page_id)
        if not existing:
            print(f"Página {page_id} no encontrada.", file=sys.stderr)
            return 1
    else:
        page_id = create_page(args.title)
        print(f"📄 Nueva página creada: {page_id}")

    if args.text:
        event = text_to_event(page_id, args.text)
    else:
        event = voice_to_event(
            page_id=page_id,
            duration=args.duration,
            model_size=args.model,
            language=args.language,
        )

    store.append(event)
    print(f"✅ Evento guardado: {event.type}")

    projection = project(page_id, store.get_events(page_id))
    print("\n📄 Documento actual:")
    print(serialize_ast(projection.ast))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
