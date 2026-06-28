"""Tabla de símbolos LaTeX y almacenamiento de favoritos."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from lablog.config import settings


@dataclass
class Symbol:
    id: str
    char: str
    latex: str
    category: str
    description: str = ""


_SYMBOLS: list[Symbol] = [
    Symbol("alpha", "α", "\\alpha", "greek", "Alfa"),
    Symbol("beta", "β", "\\beta", "greek", "Beta"),
    Symbol("gamma", "γ", "\\gamma", "greek", "Gamma"),
    Symbol("delta", "δ", "\\delta", "greek", "Delta"),
    Symbol("epsilon", "ε", "\\epsilon", "greek", "Épsilon"),
    Symbol("theta", "θ", "\\theta", "greek", "Theta"),
    Symbol("lambda", "λ", "\\lambda", "greek", "Lambda"),
    Symbol("mu", "μ", "\\mu", "greek", "Mu"),
    Symbol("pi", "π", "\\pi", "greek", "Pi"),
    Symbol("sigma", "σ", "\\sigma", "greek", "Sigma"),
    Symbol("omega", "ω", "\\omega", "greek", "Omega"),
    Symbol("Omega_cap", "Ω", "\\Omega", "greek", "Omega mayúscula"),
    Symbol("infty", "∞", "\\infty", "operators", "Infinito"),
    Symbol("int", "∫", "\\int", "operators", "Integral"),
    Symbol("sum", "∑", "\\sum", "operators", "Sumatoria"),
    Symbol("prod", "∏", "\\prod", "operators", "Productorio"),
    Symbol("partial", "∂", "\\partial", "operators", "Derivada parcial"),
    Symbol("nabla", "∇", "\\nabla", "operators", "Nabla"),
    Symbol("pm", "±", "\\pm", "operators", "Más menos"),
    Symbol("cdot", "·", "\\cdot", "operators", "Producto punto"),
    Symbol("times", "×", "\\times", "operators", "Producto cruz"),
    Symbol("leq", "≤", "\\leq", "operators", "Menor o igual"),
    Symbol("geq", "≥", "\\geq", "operators", "Mayor o igual"),
    Symbol("neq", "≠", "\\neq", "operators", "Distinto"),
    Symbol("approx", "≈", "\\approx", "operators", "Aproximadamente"),
    Symbol("equiv", "≡", "\\equiv", "operators", "Equivalente"),
    Symbol("rightarrow", "→", "\\rightarrow", "arrows", "Flecha derecha"),
    Symbol("leftarrow", "←", "\\leftarrow", "arrows", "Flecha izquierda"),
    Symbol("Rightarrow", "⇒", "\\Rightarrow", "arrows", "Flecha doble derecha"),
    Symbol("Leftarrow", "⇐", "\\Leftarrow", "arrows", "Flecha doble izquierda"),
    Symbol("vec", "→", "\\vec{}", "accents", "Vector"),
    Symbol("hat", "^", "\\hat{}", "accents", "Sombreado"),
    Symbol("bar", "‾", "\\bar{}", "accents", "Barra"),
    Symbol("dot", "˙", "\\dot{}", "accents", "Punto (derivada)"),
    Symbol("ddot", "¨", "\\ddot{}", "accents", "Doble punto"),
    Symbol("sqrt", "√", "\\sqrt{}", "functions", "Raíz cuadrada"),
    Symbol("frac", "⁄", "\\frac{}{}", "functions", "Fracción"),
    Symbol("lim", "lim", "\\lim", "functions", "Límite"),
    Symbol("sin", "sin", "\\sin", "functions", "Seno"),
    Symbol("cos", "cos", "\\cos", "functions", "Coseno"),
    Symbol("tan", "tan", "\\tan", "functions", "Tangente"),
    Symbol("log", "log", "\\log", "functions", "Logaritmo"),
    Symbol("exp", "exp", "\\exp", "functions", "Exponencial"),
]


def list_symbols(category: str | None = None) -> list[Symbol]:
    if category:
        return [s for s in _SYMBOLS if s.category == category]
    return _SYMBOLS.copy()


def find_symbol(symbol_id: str) -> Symbol | None:
    return next((s for s in _SYMBOLS if s.id == symbol_id), None)


class FavoritesStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path or settings.data_dir / "favorites.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def list_favorites(self) -> list[str]:
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return list(data.get("symbols", []))

    def add(self, symbol_id: str) -> None:
        favorites = self.list_favorites()
        if symbol_id not in favorites:
            favorites.append(symbol_id)
        self._save(favorites)

    def remove(self, symbol_id: str) -> None:
        favorites = [s for s in self.list_favorites() if s != symbol_id]
        self._save(favorites)

    def _save(self, favorites: list[str]) -> None:
        self.path.write_text(json.dumps({"symbols": favorites}), encoding="utf-8")
