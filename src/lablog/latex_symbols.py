"""Tabla de símbolos LaTeX (física/matemáticas) y favoritos."""

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


def _s(sid: str, char: str, latex: str, cat: str, desc: str = "") -> Symbol:
    return Symbol(sid, char, latex, cat, desc)


# Catálogo amplio para preview KaTeX + PDF (amsmath/amssymb/physics).
_SYMBOLS: list[Symbol] = [
    # --- Greek lower ---
    _s("alpha", "α", "\\alpha", "greek", "Alfa"),
    _s("beta", "β", "\\beta", "greek", "Beta"),
    _s("gamma", "γ", "\\gamma", "greek", "Gamma"),
    _s("delta", "δ", "\\delta", "greek", "Delta"),
    _s("epsilon", "ε", "\\epsilon", "greek", "Épsilon"),
    _s("varepsilon", "ε", "\\varepsilon", "greek", "Épsilon var"),
    _s("zeta", "ζ", "\\zeta", "greek", "Zeta"),
    _s("eta", "η", "\\eta", "greek", "Eta"),
    _s("theta", "θ", "\\theta", "greek", "Theta"),
    _s("vartheta", "ϑ", "\\vartheta", "greek", "Theta var"),
    _s("iota", "ι", "\\iota", "greek", "Iota"),
    _s("kappa", "κ", "\\kappa", "greek", "Kappa"),
    _s("lambda", "λ", "\\lambda", "greek", "Lambda"),
    _s("mu", "μ", "\\mu", "greek", "Mu"),
    _s("nu", "ν", "\\nu", "greek", "Nu"),
    _s("xi", "ξ", "\\xi", "greek", "Xi"),
    _s("pi", "π", "\\pi", "greek", "Pi"),
    _s("varpi", "ϖ", "\\varpi", "greek", "Pi var"),
    _s("rho", "ρ", "\\rho", "greek", "Rho"),
    _s("varrho", "ϱ", "\\varrho", "greek", "Rho var"),
    _s("sigma", "σ", "\\sigma", "greek", "Sigma"),
    _s("varsigma", "ς", "\\varsigma", "greek", "Sigma final"),
    _s("tau", "τ", "\\tau", "greek", "Tau"),
    _s("upsilon", "υ", "\\upsilon", "greek", "Upsilon"),
    _s("phi", "φ", "\\phi", "greek", "Phi"),
    _s("varphi", "ϕ", "\\varphi", "greek", "Phi var"),
    _s("chi", "χ", "\\chi", "greek", "Chi"),
    _s("psi", "ψ", "\\psi", "greek", "Psi"),
    _s("omega", "ω", "\\omega", "greek", "Omega"),
    # --- Greek upper ---
    _s("Gamma", "Γ", "\\Gamma", "greek", "Gamma mayúscula"),
    _s("Delta", "Δ", "\\Delta", "greek", "Delta mayúscula"),
    _s("Theta", "Θ", "\\Theta", "greek", "Theta mayúscula"),
    _s("Lambda", "Λ", "\\Lambda", "greek", "Lambda mayúscula"),
    _s("Xi", "Ξ", "\\Xi", "greek", "Xi mayúscula"),
    _s("Pi", "Π", "\\Pi", "greek", "Pi mayúscula"),
    _s("Sigma", "Σ", "\\Sigma", "greek", "Sigma mayúscula"),
    _s("Upsilon", "Υ", "\\Upsilon", "greek", "Upsilon mayúscula"),
    _s("Phi", "Φ", "\\Phi", "greek", "Phi mayúscula"),
    _s("Psi", "Ψ", "\\Psi", "greek", "Psi mayúscula"),
    _s("Omega", "Ω", "\\Omega", "greek", "Omega mayúscula"),
    # --- Operators / calculus ---
    _s("infty", "∞", "\\infty", "operators", "Infinito"),
    _s("int", "∫", "\\int", "operators", "Integral"),
    _s("iint", "∬", "\\iint", "operators", "Integral doble"),
    _s("iiint", "∭", "\\iiint", "operators", "Integral triple"),
    _s("oint", "∮", "\\oint", "operators", "Integral de contorno"),
    _s("sum", "∑", "\\sum", "operators", "Sumatoria"),
    _s("prod", "∏", "\\prod", "operators", "Productorio"),
    _s("coprod", "∐", "\\coprod", "operators", "Coproducto"),
    _s("partial", "∂", "\\partial", "operators", "Derivada parcial"),
    _s("nabla", "∇", "\\nabla", "operators", "Nabla / gradiente"),
    _s("pm", "±", "\\pm", "operators", "Más menos"),
    _s("mp", "∓", "\\mp", "operators", "Menos más"),
    _s("cdot", "·", "\\cdot", "operators", "Producto punto"),
    _s("times", "×", "\\times", "operators", "Producto cruz"),
    _s("ast", "∗", "\\ast", "operators", "Asterisco"),
    _s("star", "⋆", "\\star", "operators", "Estrella"),
    _s("circ", "∘", "\\circ", "operators", "Composición"),
    _s("bullet", "•", "\\bullet", "operators", "Viñeta"),
    _s("div", "÷", "\\div", "operators", "División"),
    _s("setminus", "∖", "\\setminus", "operators", "Diferencia de conjuntos"),
    _s("oplus", "⊕", "\\oplus", "operators", "Suma directa"),
    _s("ominus", "⊖", "\\ominus", "operators", "Menos en círculo"),
    _s("otimes", "⊗", "\\otimes", "operators", "Producto tensorial"),
    _s("oslash", "⊘", "\\oslash", "operators", "Slash en círculo"),
    _s("odot", "⊙", "\\odot", "operators", "Punto en círculo"),
    # --- Relations ---
    _s("leq", "≤", "\\leq", "relations", "Menor o igual"),
    _s("geq", "≥", "\\geq", "relations", "Mayor o igual"),
    _s("neq", "≠", "\\neq", "relations", "Distinto"),
    _s("approx", "≈", "\\approx", "relations", "Aproximadamente"),
    _s("equiv", "≡", "\\equiv", "relations", "Equivalente / idéntico"),
    _s("sim", "∼", "\\sim", "relations", "Similar"),
    _s("simeq", "≃", "\\simeq", "relations", "Semejante"),
    _s("cong", "≅", "\\cong", "relations", "Congruente"),
    _s("propto", "∝", "\\propto", "relations", "Proporcional"),
    _s("ll", "≪", "\\ll", "relations", "Mucho menor"),
    _s("gg", "≫", "\\gg", "relations", "Mucho mayor"),
    _s("prec", "≺", "\\prec", "relations", "Precede"),
    _s("succ", "≻", "\\succ", "relations", "Sucede"),
    _s("subset", "⊂", "\\subset", "relations", "Subconjunto"),
    _s("supset", "⊃", "\\supset", "relations", "Superconjunto"),
    _s("subseteq", "⊆", "\\subseteq", "relations", "Subconjunto o igual"),
    _s("supseteq", "⊇", "\\supseteq", "relations", "Superconjunto o igual"),
    _s("in", "∈", "\\in", "relations", "Pertenece"),
    _s("notin", "∉", "\\notin", "relations", "No pertenece"),
    _s("ni", "∋", "\\ni", "relations", "Contiene como elemento"),
    _s("perp", "⊥", "\\perp", "relations", "Perpendicular"),
    _s("parallel", "∥", "\\parallel", "relations", "Paralelo"),
    _s("mid", "∣", "\\mid", "relations", "Divide / dado que"),
    _s("models", "⊨", "\\models", "relations", "Modela / implica semántico"),
    # --- Sets / logic ---
    _s("emptyset", "∅", "\\emptyset", "sets", "Conjunto vacío"),
    _s("varnothing", "∅", "\\varnothing", "sets", "Vacío (var)"),
    _s("mathbbR", "ℝ", "\\mathbb{R}", "sets", "Reales"),
    _s("mathbbC", "ℂ", "\\mathbb{C}", "sets", "Complejos"),
    _s("mathbbN", "ℕ", "\\mathbb{N}", "sets", "Naturales"),
    _s("mathbbZ", "ℤ", "\\mathbb{Z}", "sets", "Enteros"),
    _s("mathbbQ", "ℚ", "\\mathbb{Q}", "sets", "Racionales"),
    _s("cup", "∪", "\\cup", "sets", "Unión"),
    _s("cap", "∩", "\\cap", "sets", "Intersección"),
    _s("vee", "∨", "\\vee", "sets", "O lógico"),
    _s("wedge", "∧", "\\wedge", "sets", "Y lógico"),
    _s("neg", "¬", "\\neg", "sets", "Negación"),
    _s("forall", "∀", "\\forall", "sets", "Para todo"),
    _s("exists", "∃", "\\exists", "sets", "Existe"),
    _s("nexists", "∄", "\\nexists", "sets", "No existe"),
    # --- Arrows ---
    _s("rightarrow", "→", "\\rightarrow", "arrows", "Flecha derecha"),
    _s("leftarrow", "←", "\\leftarrow", "arrows", "Flecha izquierda"),
    _s("leftrightarrow", "↔", "\\leftrightarrow", "arrows", "Flecha doble"),
    _s("Rightarrow", "⇒", "\\Rightarrow", "arrows", "Implica"),
    _s("Leftarrow", "⇐", "\\Leftarrow", "arrows", "Implicado por"),
    _s("Leftrightarrow", "⇔", "\\Leftrightarrow", "arrows", "Si y solo si"),
    _s("mapsto", "↦", "\\mapsto", "arrows", "Mapea a"),
    _s("to", "→", "\\to", "arrows", "A (límite)"),
    _s("longrightarrow", "⟶", "\\longrightarrow", "arrows", "Flecha larga"),
    _s("uparrow", "↑", "\\uparrow", "arrows", "Arriba"),
    _s("downarrow", "↓", "\\downarrow", "arrows", "Abajo"),
    _s("nearrow", "↗", "\\nearrow", "arrows", "Noreste"),
    _s("searrow", "↘", "\\searrow", "arrows", "Sureste"),
    # --- Accents ---
    _s("vec", "→x", "\\vec{}", "accents", "Vector"),
    _s("hat", "x̂", "\\hat{}", "accents", "Sombrero"),
    _s("bar", "x̄", "\\bar{}", "accents", "Barra"),
    _s("tilde", "x̃", "\\tilde{}", "accents", "Tilde"),
    _s("dot", "ẋ", "\\dot{}", "accents", "Punto (derivada)"),
    _s("ddot", "ẍ", "\\ddot{}", "accents", "Doble punto"),
    _s("overline", "x̄", "\\overline{}", "accents", "Sobrelínea"),
    _s("underline", "x̲", "\\underline{}", "accents", "Subrayado"),
    _s("mathbf", "x", "\\mathbf{}", "accents", "Negrita math"),
    _s("mathrm", "x", "\\mathrm{}", "accents", "Romano"),
    _s("mathcal", "X", "\\mathcal{}", "accents", "Caligráfico"),
    _s("mathfrak", "X", "\\mathfrak{}", "accents", "Fraktur"),
    # --- Functions ---
    _s("sqrt", "√", "\\sqrt{}", "functions", "Raíz"),
    _s("frac", "⁄", "\\frac{}{}", "functions", "Fracción"),
    _s("dfrac", "⁄", "\\dfrac{}{}", "functions", "Fracción display"),
    _s("lim", "lim", "\\lim", "functions", "Límite"),
    _s("sin", "sin", "\\sin", "functions", "Seno"),
    _s("cos", "cos", "\\cos", "functions", "Coseno"),
    _s("tan", "tan", "\\tan", "functions", "Tangente"),
    _s("cot", "cot", "\\cot", "functions", "Cotangente"),
    _s("sec", "sec", "\\sec", "functions", "Secante"),
    _s("csc", "csc", "\\csc", "functions", "Cosecante"),
    _s("arcsin", "arcsin", "\\arcsin", "functions", "Arcoseno"),
    _s("arccos", "arccos", "\\arccos", "functions", "Arcocoseno"),
    _s("arctan", "arctan", "\\arctan", "functions", "Arcotangente"),
    _s("sinh", "sinh", "\\sinh", "functions", "Seno hiperbólico"),
    _s("cosh", "cosh", "\\cosh", "functions", "Coseno hiperbólico"),
    _s("tanh", "tanh", "\\tanh", "functions", "Tangente hiperbólica"),
    _s("log", "log", "\\log", "functions", "Logaritmo"),
    _s("ln", "ln", "\\ln", "functions", "Logaritmo natural"),
    _s("exp", "exp", "\\exp", "functions", "Exponencial"),
    _s("det", "det", "\\det", "functions", "Determinante"),
    _s("dim", "dim", "\\dim", "functions", "Dimensión"),
    _s("ker", "ker", "\\ker", "functions", "Núcleo"),
    _s("tr", "tr", "\\mathrm{tr}", "functions", "Traza"),
    _s("Re", "Re", "\\mathrm{Re}", "functions", "Parte real"),
    _s("Im", "Im", "\\mathrm{Im}", "functions", "Parte imaginaria"),
    # --- Physics / quantum ---
    _s("hbar", "ℏ", "\\hbar", "physics", "h barra"),
    _s("ell", "ℓ", "\\ell", "physics", "ell cursiva"),
    _s("degree", "°", "^{\\circ}", "physics", "Grado"),
    _s("angstrom", "Å", "\\mathrm{\\AA}", "physics", "Ångström"),
    _s("ket", "|ψ⟩", "\\ket{}", "physics", "Ket (braket)"),
    _s("bra", "⟨ψ|", "\\bra{}", "physics", "Bra"),
    _s("braket", "⟨a|b⟩", "\\braket{}{}", "physics", "Braket"),
    _s("ketbra", "|a⟩⟨b|", "\\ketbra{}{}", "physics", "Ket-bra"),
    _s("expval", "⟨O⟩", "\\expval{}", "physics", "Valor esperado"),
    _s("cross", "×", "\\times", "physics", "Producto vectorial"),
    _s("dotp", "·", "\\cdot", "physics", "Producto escalar"),
    _s("grad", "∇", "\\nabla", "physics", "Gradiente"),
    _s("divop", "∇·", "\\nabla\\cdot", "physics", "Divergencia"),
    _s("curl", "∇×", "\\nabla\\times", "physics", "Rotacional"),
    _s("laplacian", "∇²", "\\nabla^2", "physics", "Laplaciano"),
    _s("dalembert", "□", "\\Box", "physics", "D'Alembertiano"),
    # --- Delimiters / misc ---
    _s("langle", "⟨", "\\langle", "delimiters", "Ángulo izq"),
    _s("rangle", "⟩", "\\rangle", "delimiters", "Ángulo der"),
    _s("lfloor", "⌊", "\\lfloor", "delimiters", "Suelo izq"),
    _s("rfloor", "⌋", "\\rfloor", "delimiters", "Suelo der"),
    _s("lceil", "⌈", "\\lceil", "delimiters", "Techo izq"),
    _s("rceil", "⌉", "\\rceil", "delimiters", "Techo der"),
    _s("vert", "|", "\\vert", "delimiters", "Barra vertical"),
    _s("Vert", "‖", "\\Vert", "delimiters", "Doble barra"),
    _s("ldots", "…", "\\ldots", "misc", "Puntos bajos"),
    _s("cdots", "⋯", "\\cdots", "misc", "Puntos centrados"),
    _s("vdots", "⋮", "\\vdots", "misc", "Puntos verticales"),
    _s("ddots", "⋱", "\\ddots", "misc", "Puntos diagonales"),
    _s("dots", "…", "\\dots", "misc", "Puntos"),
    _s("prime", "′", "'", "misc", "Prima"),
    _s("dagger", "†", "\\dagger", "misc", "Daga (adjunto)"),
    _s("ddagger", "‡", "\\ddagger", "misc", "Doble daga"),
    _s("clubsuit", "♣", "\\clubsuit", "misc", "Trébol"),
    _s("diamondsuit", "♦", "\\diamondsuit", "misc", "Diamante"),
    _s("heartsuit", "♥", "\\heartsuit", "misc", "Corazón"),
    _s("spadesuit", "♠", "\\spadesuit", "misc", "Pica"),
]


def list_symbols(category: str | None = None) -> list[Symbol]:
    if category:
        return [s for s in _SYMBOLS if s.category == category]
    return _SYMBOLS.copy()


def list_categories() -> list[str]:
    seen: list[str] = []
    for s in _SYMBOLS:
        if s.category not in seen:
            seen.append(s.category)
    return seen


def find_symbol(symbol_id: str) -> Symbol | None:
    return next((s for s in _SYMBOLS if s.id == symbol_id), None)


def all_latex_commands() -> list[str]:
    """Comandos únicos para autocompletado / tests de preview."""
    cmds: list[str] = []
    for s in _SYMBOLS:
        cmd = s.latex.split("{", 1)[0]
        if cmd.startswith("\\") and cmd not in cmds:
            cmds.append(cmd)
    return cmds


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
