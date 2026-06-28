"""Detecta intención matemática en transcripciones de voz."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class IntentType(Enum):
    PLAIN_TEXT = "plain_text"
    MATH = "math"
    EQUATION = "equation"
    INTEGRAL = "integral"
    MATRIX = "matrix"
    SNIPPET = "snippet"
    COMMAND = "command"


@dataclass
class Intent:
    type: IntentType
    confidence: float
    matched_keywords: list[str]
    clean_text: str


MATH_KEYWORDS = {
    "integral": IntentType.INTEGRAL,
    "integrar": IntentType.INTEGRAL,
    "sumatoria": IntentType.MATH,
    "suma": IntentType.MATH,
    "límite": IntentType.MATH,
    "límite": IntentType.MATH,
    "matriz": IntentType.MATRIX,
    "vector": IntentType.MATH,
    "fracción": IntentType.MATH,
    "raíz": IntentType.MATH,
    "exponencial": IntentType.MATH,
    "logaritmo": IntentType.MATH,
    "seno": IntentType.MATH,
    "coseno": IntentType.MATH,
    "tangente": IntentType.MATH,
    "más o menos": IntentType.MATH,
    "subíndice": IntentType.MATH,
    "superíndice": IntentType.MATH,
    "ecuación": IntentType.EQUATION,
    "formula": IntentType.EQUATION,
    "fórmula": IntentType.EQUATION,
    "schrodinger": IntentType.SNIPPET,
    "schrödinger": IntentType.SNIPPET,
    "maxwell": IntentType.SNIPPET,
    "newton": IntentType.SNIPPET,
    "inserta": IntentType.COMMAND,
    "nueva página": IntentType.COMMAND,
    "guardar": IntentType.COMMAND,
}


def parse_intent(text: str) -> Intent:
    """Analiza el texto y detecta si contiene jerga matemática."""
    lower = text.lower()
    matched: list[str] = []
    detected_type = IntentType.PLAIN_TEXT
    max_confidence = 0.0

    for keyword, intent_type in MATH_KEYWORDS.items():
        if keyword in lower or re.search(r"\b" + re.escape(keyword) + r"\b", lower):
            matched.append(keyword)
            if intent_type.value != "plain_text":
                detected_type = intent_type
                max_confidence = max(max_confidence, 0.7)

    # Patrones numéricos con variables aumentan confianza matemática
    if re.search(r"\b[xyztv]\s*(igual|es|=)\s*\d", lower):
        if detected_type == IntentType.PLAIN_TEXT:
            detected_type = IntentType.MATH
        max_confidence = max(max_confidence, 0.6)

    if re.search(r"\b\d+\s*(más|menos|por|dividido|elevado)\s*\d+", lower):
        if detected_type == IntentType.PLAIN_TEXT:
            detected_type = IntentType.MATH
        max_confidence = max(max_confidence, 0.6)

    confidence = max_confidence if matched else 0.0
    if confidence == 0.0 and detected_type != IntentType.PLAIN_TEXT:
        confidence = 0.5

    return Intent(
        type=detected_type,
        confidence=confidence,
        matched_keywords=matched,
        clean_text=text.strip(),
    )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Detecta intención matemática en texto.")
    parser.add_argument("text", type=str, help="Texto a analizar")
    args = parser.parse_args()

    intent = parse_intent(args.text)
    print(f"Tipo: {intent.type.value}")
    print(f"Confianza: {intent.confidence:.2f}")
    print(f"Palabras clave: {intent.matched_keywords}")
    print(f"Texto: {intent.clean_text}")


if __name__ == "__main__":
    main()
