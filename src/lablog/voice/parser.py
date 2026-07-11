"""Intención y traducción por reglas de voz/texto a LaTeX."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Literal


class IntentType(Enum):
    TEXT = "text"
    MATH = "math"
    EQUATION = "equation"
    INTEGRAL = "integral"
    MATRIX = "matrix"


@dataclass
class Intent:
    type: IntentType
    confidence: float


@dataclass
class Translation:
    latex: str
    mode: Literal["inline", "display"]


KEYWORDS = {
    "integral": IntentType.INTEGRAL,
    "integrar": IntentType.INTEGRAL,
    "ecuación": IntentType.EQUATION,
    "formula": IntentType.EQUATION,
    "fórmula": IntentType.EQUATION,
    "matriz": IntentType.MATRIX,
}

# Rellenos típicos del STT en español — no merecen insertarse solos.
_FILLER_ONLY = re.compile(
    r"^(eh|ehm|mm+|hmm+|este|esta|esto|ah|ay|ok|okay|vale|bueno|pues|entonces)\.?$",
    re.IGNORECASE,
)


def clean_dictation_text(text: str) -> str:
    """Limpia basura típica del reconocimiento de voz antes de insertar.

    - Normaliza espacios
    - Colapsa palabras/frases repetidas (stutter del motor)
    - Quita rellenos solo-ruido
    """
    t = re.sub(r"\s+", " ", (text or "")).strip()
    if not t:
        return ""

    # Misma palabra 2+ veces: "la la la energía" → "la energía"
    t = re.sub(r"\b(\w+(?:'\w+)?)(?:\s+\1)+\b", r"\1", t, flags=re.IGNORECASE)

    # Mismo n-grama (2–5 palabras) repetido: "hola mundo hola mundo"
    for n in range(5, 1, -1):
        parts = r"\s+".join([r"\w+(?:'\w+)?" for _ in range(n)])
        t = re.sub(rf"\b({parts})(?:\s+\1)+\b", r"\1", t, flags=re.IGNORECASE)

    t = re.sub(r"\s+", " ", t).strip()

    # Puntuación duplicada del STT
    t = re.sub(r"([.!?])\1+", r"\1", t)
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)

    if _FILLER_ONLY.match(t):
        return ""

    # Muy corto o sin alfanuméricos → ruido del motor
    if len(t) < 2 or not re.search(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]", t):
        return ""

    return t


def parse_intent(text: str) -> Intent:
    lower = text.lower()
    matched = next((KEYWORDS[k] for k in KEYWORDS if k in lower), None)
    intent = matched or IntentType.TEXT
    confidence = 0.8 if matched else 0.0
    if re.search(r"\b[xyztv]\s*(igual|es|=)\s*\d", lower):
        intent = intent if intent != IntentType.TEXT else IntentType.MATH
        confidence = max(confidence, 0.6)
    return Intent(intent, confidence)


def translate(text: str, intent: IntentType) -> Translation:
    cleaned = clean_dictation_text(text)
    if intent == IntentType.TEXT:
        # Texto narrativo: NO aplicar reemplazos matemáticos agresivos
        # ("por" → · , "más" → +) que destrozan prosa científica.
        return Translation(latex=cleaned, mode="inline")

    latex = _normalize(cleaned)
    for pattern, repl in REPLACEMENTS:
        latex = re.sub(pattern, repl, latex, flags=re.IGNORECASE)
    latex = _balance_braces(latex)
    latex = re.sub(r"\s+", " ", latex).strip()
    mode: Literal["inline", "display"] = "display"
    if latex and not latex.startswith(("$", "\\[")):
        latex = f"\\[{latex}\\]"
    return Translation(latex=latex, mode=mode)


def _normalize(text: str) -> str:
    numbers = {
        "cero": "0",
        "uno": "1",
        "dos": "2",
        "tres": "3",
        "cuatro": "4",
        "cinco": "5",
        "seis": "6",
        "siete": "7",
        "ocho": "8",
        "nueve": "9",
        "diez": "10",
    }
    lower = text.lower()
    for word, digit in numbers.items():
        lower = re.sub(rf"\b{word}\b", digit, lower)
    return lower


REPLACEMENTS = [
    (r"ecuaci[oó]n de schr[oö]dinger", r"\\hat{H}\\psi = E\\psi"),
    (r"más o menos", r"\\pm"),
    (r"raíz cuadrada de ", r"\\sqrt{"),
    (r"fracción de ", r"\\frac{"),
    (r"integral de ", r"\\int "),
    (r"a la menos ", r"^{-"),
    (r"a la ", r"^{"),
    (r"al cuadrado", r"^{2}"),
    (r"al cubo", r"^{3}"),
    (r"elevado a la ", r"^{"),
    (r"subíndice ", r"_{"),
    (r"superíndice ", r"^{"),
    (r"dividido por ", r"/"),
    (r"dividido ", r"/"),
    (r"por ", r"\\cdot "),
    (r"más ", r"+ "),
    (r"menos ", r"- "),
    (r"es igual a ", r"= "),
    (r"igual a ", r"= "),
    (r"igual ", r"= "),
    (r"\bpi\b", r"\\pi"),
    (r"\balfa\b", r"\\alpha"),
    (r"\bbeta\b", r"\\beta"),
    (r"\bgamma\b", r"\\gamma"),
    (r"\bdelta\b", r"\\delta"),
    (r"\bsigma\b", r"\\sigma"),
    (r"\bomega\b", r"\\omega"),
    (r"\btheta\b", r"\\theta"),
    (r"\binfinito\b", r"\\infty"),
    (r"\bcuadrado\b", r"^{2}"),
    (r"\bcubo\b", r"^{3}"),
    (r"\bdx\b", r"\\, dx"),
    (r"\bdy\b", r"\\, dy"),
    (r"\bdt\b", r"\\, dt"),
]


def _balance_braces(latex: str) -> str:
    diff = latex.count("{") - latex.count("}")
    return latex + "}" * diff if diff > 0 else latex
