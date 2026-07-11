"""Tests del limpiador e intents de voz."""

from __future__ import annotations

from lablog.voice.parser import IntentType, clean_dictation_text, parse_intent, translate


def test_clean_collapses_repeated_words() -> None:
    assert clean_dictation_text("la la la energía se conserva") == "la energía se conserva"


def test_clean_collapses_repeated_phrases() -> None:
    assert clean_dictation_text("hola mundo hola mundo") == "hola mundo"
    assert clean_dictation_text("medida uno medida uno medida uno") == "medida uno"


def test_clean_rejects_filler_only() -> None:
    assert clean_dictation_text("eh") == ""
    assert clean_dictation_text("este") == ""
    assert clean_dictation_text("   ") == ""


def test_clean_normalizes_whitespace() -> None:
    assert clean_dictation_text("  la   masa  es  2  ") == "la masa es 2"


def test_translate_text_does_not_math_mangle_prose() -> None:
    # Antes: "por" → \cdot y "más" → + destrozaban prosa.
    out = translate("medimos más o menos por el método de Ohm", IntentType.TEXT)
    assert "\\cdot" not in out.latex
    assert out.latex.startswith("medimos")


def test_translate_math_still_replaces() -> None:
    out = translate("integral de x al cuadrado", IntentType.INTEGRAL)
    assert "\\int" in out.latex
    assert "^{2}" in out.latex


def test_parse_intent_integral() -> None:
    assert parse_intent("integral de cero a uno").type is IntentType.INTEGRAL
