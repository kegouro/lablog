"""Demo del pipeline de Voz/Texto → LaTeX usando frases de prueba."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TEST_PHRASES = [
    "integral de cero a infinito de e a la menos x cuadrado dx",
    "la ecuación de Schrödinger",
    "x más o menos 3 por y",
    "la matriz identidad de dos por dos",
    "raíz cuadrada de x al cuadrado más y al cuadrado",
    "el voltaje medido fue de 12.3 voltios",
]


def main() -> None:
    script = Path(__file__).parent / "voice_to_latex.py"
    python = sys.executable

    for phrase in TEST_PHRASES:
        print("\n" + "=" * 70)
        print(f"🗣️  Frase: {phrase}")
        print("=" * 70)
        subprocess.run([python, str(script), "--text", phrase], check=False)


if __name__ == "__main__":
    main()
