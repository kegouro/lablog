"""Convierte texto hablado a código LaTeX válido."""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass

import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


@dataclass
class TranslationResult:
    latex: str
    mode: str  # "inline", "display", "plain", "command"
    source: str  # "ollama", "openai", "rule"


SYSTEM_PROMPT = """Eres un asistente especializado en convertir dictado de voz de físicos experimentales a código LaTeX válido.

Reglas:
1. Responde SOLO con el código LaTeX, sin explicaciones, sin Markdown, sin comillas.
2. Si el texto es una ecuación, usa modo display: \\[ ... \\] o entorno equation.
3. Si es una fórmula dentro de una oración, usa $ ... $.
4. Si es texto plano sin matemáticas, devuélvelo tal cual.
5. Convierte palabras matemáticas a comandos LaTeX correctos:
   - "integral" -> \\int
   - "de cero a infinito" -> _0^\\infty
   - "más o menos" -> \\pm
   - "subíndice" -> _{}
   - "superíndice" -> ^{}
   - "fracción" -> \\frac{}{}
   - "raíz cuadrada" -> \\sqrt{}
   - "ecuación de Schrödinger" -> \\hat{H}\\psi = E\\psi
6. No incluyas \\begin{document}, preámbulos ni explicaciones.
7. Usa notación científica estándar.

Ejemplo:
Entrada: "integral de cero a infinito de e a la menos x cuadrado dx"
Salida: \\[\\int_0^\\infty e^{-x^2} \\, dx\\]
"""


def translate_with_ollama(text: str, intent_type: str) -> TranslationResult | None:
    """Traduce usando Ollama local."""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": f"{SYSTEM_PROMPT}\n\nEntrada: {text}\nSalida:",
                "stream": False,
                "options": {"temperature": 0.1},
            },
            timeout=60,
        )
        response.raise_for_status()
        latex = response.json()["response"].strip()
        return TranslationResult(latex=latex, mode=_infer_mode(latex, intent_type), source="ollama")
    except Exception:
        return None


def translate_with_openai(text: str, intent_type: str) -> TranslationResult | None:
    """Traduce usando OpenAI API como fallback."""
    if not OPENAI_API_KEY:
        return None
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                "temperature": 0.1,
            },
            timeout=60,
        )
        response.raise_for_status()
        latex = response.json()["choices"][0]["message"]["content"].strip()
        return TranslationResult(latex=latex, mode=_infer_mode(latex, intent_type), source="openai")
    except Exception as e:
        print(f"⚠️  OpenAI no disponible: {e}")
        return None


def translate_with_rules(text: str, intent_type: str) -> TranslationResult:
    """Fallback basado en reglas para el prototipo. Maneja frases comunes."""
    import re

    latex = text.lower().strip()

    # Convertir números escritos a dígitos antes de las plantillas
    number_map = {
        "cero": "0", "uno": "1", "dos": "2", "tres": "3", "cuatro": "4",
        "cinco": "5", "seis": "6", "siete": "7", "ocho": "8", "nueve": "9",
        "diez": "10",
    }
    for word, digit in number_map.items():
        latex = re.sub(rf"\b{word}\b", digit, latex)

    # Plantillas para frases matemáticas muy comunes
    templates = [
        (
            r"integral\s+de\s+(.+?)\s+a\s+(.+?)\s+de\s+(.+?)(?:\s+d([a-z]))?$",
            lambda m: (
                r"\\int_{" + _to_latex_expr(m.group(1)) + r"}^{" + _to_latex_expr(m.group(2)) + r"} " + _to_latex_expr(m.group(3)) + r" \\, d" + (m.group(4) or "x"),
                "display",
            ),
        ),
        (
            r"integral\s+de\s+(.+?)\s+de\s+(.+?)(?:\s+d([a-z]))?$",
            lambda m: (
                r"\\int_{" + _to_latex_expr(m.group(1)) + r"} " + _to_latex_expr(m.group(2)) + r" \\, d" + (m.group(3) or "x"),
                "display",
            ),
        ),
        (
            r"(?:la\s+)?ecuaci[oó]n\s+de\s+schr[oö]dinger",
            lambda _m: (r"\\hat{H}\\psi = E\\psi", "display"),
        ),
        (
            r"matriz\s+identidad\s+de\s+(\d+)\s+por\s+(\d+)",
            lambda m: (r"\\mathbf{I}_{" + m.group(1) + r" \\times " + m.group(2) + r"}", "inline"),
        ),
    ]

    for pattern, repl in templates:
        match = re.search(pattern, latex)
        if match:
            latex, mode = repl(match)
            if mode == "display":
                return TranslationResult(latex=f"\\[{latex}\\]", mode="display", source="rule")
            return TranslationResult(latex=f"${latex}$", mode="inline", source="rule")

    # Reemplazos por orden de prioridad (los más específicos primero)
    replacements = [
        (r"ecuación de schrödinger", r"\\hat{H}\\psi = E\\psi"),
        (r"ecuacion de schrodinger", r"\\hat{H}\\psi = E\\psi"),
        (r"más o menos", r"\\pm"),
        (r"mas o menos", r"\\pm"),
        (r"raíz cuadrada de ", r"\\sqrt{"),
        (r"raiz cuadrada de ", r"\\sqrt{"),
        (r"fracción de ", r"\\frac{"),
        (r"fraccion de ", r"\\frac{"),
        (r"integral de ", r"\\int "),
        (r"a la menos ", r"^{-"),
        (r"a la ", r"^{"),
        (r"al cuadrado", r"^{2}"),
        (r"al cubo", r"^{3}"),
        (r"elevado a la ", r"^{"),
        (r"subíndice ", r"_{"),
        (r"subindice ", r"_{"),
        (r"superíndice ", r"^{"),
        (r"superindice ", r"^{"),
        (r"dividido por ", r"/"),
        (r"dividido ", r"/"),
        (r"por ", r"\\cdot "),
        (r"más ", r"+ "),
        (r"menos ", r"- "),
        (r"es igual a ", r"= "),
        (r"igual a ", r"= "),
        (r"igual ", r"= "),
        (r"pi", r"\\pi"),
        (r"alfa", r"\\alpha"),
        (r"beta", r"\\beta"),
        (r"gamma", r"\\gamma"),
        (r"delta", r"\\delta"),
        (r"sigma", r"\\sigma"),
        (r"omega", r"\\omega"),
        (r"theta", r"\\theta"),
        (r"infinito", r"\\infty"),
        (r"cuadrado", r"^{2}"),
        (r"cubo", r"^{3}"),
        (r"dx", r"\\, dx"),
        (r"dy", r"\\, dy"),
        (r"dt", r"\\, dt"),
    ]

    for pattern, repl in replacements:
        latex = re.sub(pattern, repl, latex, flags=re.IGNORECASE)

    # Balanceo básico de llaves
    latex = _balance_braces(latex)

    # Limpieza de espacios múltiples
    latex = re.sub(r"\s+", " ", latex).strip()

    if intent_type in ("math", "integral", "equation"):
        if not latex.startswith("$") and not latex.startswith("\\["):
            latex = f"\\[{latex}\\]"

    return TranslationResult(latex=latex, mode=_infer_mode(latex, intent_type), source="rule")


def _to_latex_expr(expr: str) -> str:
    """Convierte una expresión simple a LaTeX."""
    import re

    expr = expr.strip()
    expr = re.sub(r"\bcero\b", r"0", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\buno\b", r"1", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\bdos\b", r"2", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\btres\b", r"3", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\bcuatro\b", r"4", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\bcinco\b", r"5", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\bseis\b", r"6", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\bsiete\b", r"7", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\bocho\b", r"8", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\bnueve\b", r"9", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\binfinito\b", r"\\infty", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\bpi\b", r"\\pi", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\bmenos\b", r"-", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\bmás\b", r"+", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\be\s+a\s+la\s+menos\s+([xtyz])\s+cuadrado", r"e^{-\1^{2}}", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\be\s+a\s+la\s+menos\s+(.+)", r"e^{-\1}", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\be\s+a\s+la\s+([xtyz])\s+cuadrado", r"e^{\1^{2}}", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\be\s+a\s+la\s+(.+)", r"e^{\1}", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\b([xtyz])\s+cuadrado", r"\1^{2}", expr, flags=re.IGNORECASE)
    return expr


def _balance_braces(latex: str) -> str:
    """Balancea llaves abiertas por los reemplazos."""
    open_count = latex.count("{")
    close_count = latex.count("}")
    if open_count > close_count:
        latex += "}" * (open_count - close_count)
    return latex


def _infer_mode(latex: str, intent_type: str) -> str:
    if latex.startswith("$") and latex.endswith("$"):
        return "inline"
    if latex.startswith("\\[") or latex.startswith("\\begin{equation}"):
        return "display"
    if intent_type in ("math", "integral", "equation"):
        return "display"
    return "plain"


def translate(text: str, intent_type: str = "math") -> TranslationResult:
    """Traduce texto hablado a LaTeX intentando Ollama, OpenAI y reglas."""
    result = translate_with_ollama(text, intent_type)
    if result:
        return result

    result = translate_with_openai(text, intent_type)
    if result:
        return result

    print("🔧 Usando traductor basado en reglas...")
    return translate_with_rules(text, intent_type)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convierte texto a LaTeX.")
    parser.add_argument("text", type=str, help="Texto hablado")
    parser.add_argument("--intent", "-i", type=str, default="math", help="Tipo de intención")
    args = parser.parse_args()

    result = translate(args.text, args.intent)
    print(f"\n📝 Fuente: {result.source}")
    print(f"📐 Modo: {result.mode}")
    print(f"🧮 LaTeX:\n{result.latex}")


if __name__ == "__main__":
    main()
