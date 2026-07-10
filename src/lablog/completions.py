"""Sugerencias de autocompletado LaTeX (servidas al frontend)."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from lablog.latex_symbols import list_symbols


@dataclass(frozen=True)
class CompletionItem:
    label: str
    insert: str
    kind: str  # command | environment | symbol
    detail: str = ""


_COMMANDS: list[tuple[str, str, str]] = [
    ("\\section", "\\section{}", "Sección"),
    ("\\subsection", "\\subsection{}", "Subsección"),
    ("\\textbf", "\\textbf{}", "Negrita"),
    ("\\textit", "\\textit{}", "Cursiva"),
    ("\\emph", "\\emph{}", "Énfasis"),
    ("\\cite", "\\cite{}", "Cita"),
    ("\\ref", "\\ref{}", "Referencia"),
    ("\\eqref", "\\eqref{}", "Ref. ecuación"),
    ("\\label", "\\label{}", "Etiqueta"),
    ("\\includegraphics", "\\includegraphics[width=\\linewidth]{}", "Figura"),
    ("\\input", "\\input{}", "Incluir archivo/página"),
    ("\\frac", "\\frac{}{}", "Fracción"),
    ("\\sqrt", "\\sqrt{}", "Raíz"),
    ("\\sum", "\\sum_{i=1}^{n}", "Suma"),
    ("\\int", "\\int_{a}^{b}", "Integral"),
    ("\\partial", "\\partial", "Parcial"),
    ("\\nabla", "\\nabla", "Nabla"),
    ("\\cdot", "\\cdot", "Producto punto"),
    ("\\times", "\\times", "Producto cruz"),
    ("\\infty", "\\infty", "Infinito"),
    ("\\alpha", "\\alpha", "Alfa"),
    ("\\beta", "\\beta", "Beta"),
    ("\\gamma", "\\gamma", "Gamma"),
    ("\\delta", "\\delta", "Delta"),
    ("\\theta", "\\theta", "Theta"),
    ("\\lambda", "\\lambda", "Lambda"),
    ("\\mu", "\\mu", "Mu"),
    ("\\pi", "\\pi", "Pi"),
    ("\\sigma", "\\sigma", "Sigma"),
    ("\\omega", "\\omega", "Omega"),
    ("\\Omega", "\\Omega", "Omega mayúscula"),
    ("\\mathbb", "\\mathbb{}", "Blackboard bold"),
    ("\\mathrm", "\\mathrm{}", "Romano"),
    ("\\SI", "\\SI{}{}", "siunitx cantidad"),
    ("\\si", "\\si{}", "siunitx unidad"),
]

_ENVIRONMENTS: list[str] = [
    "equation",
    "align",
    "gather",
    "cases",
    "pmatrix",
    "bmatrix",
    "itemize",
    "enumerate",
    "figure",
    "table",
    "tabular",
    "python",
    "abstract",
]


def suggest(prefix: str, *, limit: int = 40) -> list[CompletionItem]:
    """Filtra sugerencias por prefijo (sin la barra invertida inicial opcional)."""
    p = prefix.lstrip("\\").lower()
    items: list[CompletionItem] = []

    for label, insert, detail in _COMMANDS:
        key = label.lstrip("\\").lower()
        if not p or key.startswith(p) or p in key:
            items.append(CompletionItem(label=label, insert=insert, kind="command", detail=detail))

    for env in _ENVIRONMENTS:
        if not p or env.startswith(p) or p in env:
            items.append(
                CompletionItem(
                    label=f"\\begin{{{env}}}",
                    insert=f"\\begin{{{env}}}\n\n\\end{{{env}}}",
                    kind="environment",
                    detail=f"Entorno {env}",
                )
            )

    for sym in list_symbols():
        key = sym.latex.lstrip("\\").lower()
        if not p or key.startswith(p) or p in key or p in sym.description.lower():
            items.append(
                CompletionItem(
                    label=sym.latex,
                    insert=sym.latex,
                    kind="symbol",
                    detail=sym.description or sym.char,
                )
            )

    # Preferencia: comandos, entornos, símbolos; recorta.
    order = {"command": 0, "environment": 1, "symbol": 2}
    items.sort(key=lambda x: (order.get(x.kind, 9), x.label))
    # Dedup por label
    seen: set[str] = set()
    unique: list[CompletionItem] = []
    for it in items:
        if it.label in seen:
            continue
        seen.add(it.label)
        unique.append(it)
        if len(unique) >= limit:
            break
    return unique


def suggest_as_dicts(prefix: str, limit: int = 40) -> list[dict[str, str]]:
    return [asdict(i) for i in suggest(prefix, limit=limit)]
