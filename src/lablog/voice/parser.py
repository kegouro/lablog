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
    latex = _normalize(text)
    for pattern, repl in REPLACEMENTS:
        latex = re.sub(pattern, repl, latex, flags=re.IGNORECASE)
    latex = _balance_braces(latex)
    latex = re.sub(r"\s+", " ", latex).strip()
    mode: Literal["inline", "display"] = "display" if intent != IntentType.TEXT else "inline"
    if intent != IntentType.TEXT and not latex.startswith(("$", "\\[")):
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
