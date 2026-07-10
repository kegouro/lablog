"""Catálogo de plantillas LaTeX (SSOT para API, CLI y UI)."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class LatexTemplate:
    id: str
    name: str
    description: str
    content: str


_TEMPLATES: list[LatexTemplate] = [
    LatexTemplate(
        id="lab-report-physics",
        name="Informe de laboratorio (física)",
        description="Objetivo, montaje, datos con siunitx, celda python y conclusión",
        content=r"""\documentclass[11pt]{article}
\usepackage[margin=2.5cm]{geometry}
\usepackage{fontspec}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{siunitx}
\usepackage{booktabs}
\usepackage{hyperref}

\title{Informe de laboratorio: \textit{título del experimento}}
\author{Nombre Apellido}
\date{\today}

\begin{document}
\maketitle

\section{Objetivo}
Describir en una frase qué se mide y por qué.

\section{Montaje y método}
Diagrama del aparato y protocolo de medición.

\section{Datos}
\begin{table}[h]
  \centering
  \begin{tabular}{S[table-format=1.2] S[table-format=2.1]}
    \toprule
    {$t$ (\si{\second})} & {$v$ (\si{\metre\per\second})} \\
    \midrule
    0.10 & 1.0 \\
    0.20 & 2.1 \\
    \bottomrule
  \end{tabular}
  \caption{Mediciones brutas.}
\end{table}

\begin{python}
# Ajuste lineal de ejemplo
import numpy as np
t = np.array([0.10, 0.20])
v = np.array([1.0, 2.1])
a, b = np.polyfit(t, v, 1)
print(f"pendiente ≈ {a:.3f} m/s²")
\end{python}

\section{Incertidumbre}
Propagación y comparación con valor de referencia.

\section{Conclusión}
¿Se cumplió el objetivo? Limitaciones y mejoras.

\end{document}
""",
    ),
    LatexTemplate(
        id="em-notes",
        name="Notas de clase E&M",
        description="Maxwell, nomenclatura y entornos align",
        content=r"""\documentclass[11pt]{article}
\usepackage[margin=2.5cm]{geometry}
\usepackage{fontspec}
\usepackage{amsmath,amssymb}
\usepackage{hyperref}

\title{Notas de Electromagnetismo}
\author{Nombre Apellido}
\date{\today}

\begin{document}
\maketitle

\section{Ecuaciones de Maxwell (forma diferencial)}
\begin{align}
  \nabla \cdot \mathbf{E} &= \frac{\rho}{\varepsilon_0} \\
  \nabla \cdot \mathbf{B} &= 0 \\
  \nabla \times \mathbf{E} &= -\frac{\partial \mathbf{B}}{\partial t} \\
  \nabla \times \mathbf{B}
    &= \mu_0\mathbf{J}
     + \mu_0\varepsilon_0\frac{\partial \mathbf{E}}{\partial t}
\end{align}

\section{Nomenclatura}
\begin{itemize}
  \item $\mathbf{E}$: campo eléctrico
  \item $\mathbf{B}$: campo magnético
  \item $\rho$: densidad de carga
\end{itemize}

\section{Ejercicio del día}


\end{document}
""",
    ),
    LatexTemplate(
        id="experiment-diary",
        name="Diario de experimento",
        description="Fecha, hipótesis, protocolo, observaciones y vault",
        content=r"""\documentclass[11pt]{article}
\usepackage[margin=2.5cm]{geometry}
\usepackage{fontspec}
\usepackage{amsmath}
\usepackage{hyperref}

\title{Diario de experimento}
\author{Nombre Apellido}
\date{\today}

\begin{document}
\maketitle

\section{Contexto}
Fecha / instrumento / muestra.

\section{Hipótesis}


\section{Protocolo}
\begin{enumerate}
  \item Preparación
  \item Adquisición
  \item Control
\end{enumerate}

\section{Observaciones}
% Adjunta capturas al vault y referencia vault://...

\begin{python}
# Notas numéricas rápidas
print("run ok")
\end{python}

\section{Siguiente paso}


\end{document}
""",
    ),
    LatexTemplate(
        id="thesis-chapter",
        name="Capítulo de tesis parcial",
        description="Estructura de capítulo con abstract y secciones profundas",
        content=r"""\documentclass[11pt]{article}
\usepackage[margin=2.5cm]{geometry}
\usepackage{fontspec}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{hyperref}

\title{Capítulo: \textit{título}}
\author{Nombre Apellido}
\date{\today}

\begin{document}
\maketitle

\begin{abstract}
Resumen del capítulo (media página).
\end{abstract}

\section{Introducción y estado del arte}

\subsection{Trabajo previo}

\section{Formulación}
\begin{equation}
  \mathcal{L} = T - V
\end{equation}

\section{Resultados preliminares}

\section{Discusión}

\section{Conclusiones parciales}

\end{document}
""",
    ),
    LatexTemplate(
        id="articulo",
        name="Artículo científico",
        description="article · abstract, secciones y matemática",
        content=r"""\documentclass[11pt]{article}
\usepackage[margin=2.5cm]{geometry}
\usepackage{fontspec}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{hyperref}

\title{Título del trabajo}
\author{Nombre Apellido}
\date{\today}

\begin{document}
\maketitle

\begin{abstract}
Resumen del trabajo en un párrafo.
\end{abstract}

\section{Introducción}
El contexto y la motivación. Una ecuación inline: $E = mc^2$.

\section{Método}
\begin{equation}
  F = ma
\end{equation}

\section{Resultados}

\section{Conclusiones}

\end{document}
""",
    ),
]


def list_templates() -> list[LatexTemplate]:
    return list(_TEMPLATES)


def get_template(template_id: str) -> LatexTemplate | None:
    for t in _TEMPLATES:
        if t.id == template_id:
            return t
    return None


def templates_as_dicts() -> list[dict[str, str]]:
    return [asdict(t) for t in _TEMPLATES]
