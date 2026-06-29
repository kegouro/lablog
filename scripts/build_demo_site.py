"""Build a demo lablog static site for the GitHub Pages workflow.

Seeds an ephemeral data directory with a representative page so the published
site has real content (the repository never carries personal notebooks), then
delegates to :func:`lablog.exporter.export_site`. Designed to be a single
``uv run python scripts/build_demo_site.py`` invocation in CI.
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from lablog.config import settings
from lablog.event_store import EventStore
from lablog.events import document_replaced, page_created
from lablog.exporter import export_site

DEMO_LATEX = r"""La energía total se conserva en un sistema \textbf{aislado}. Para un cuerpo
en caída libre con \textit{velocidad} $v$ y altura $h$:
$$E = \frac{1}{2} m v^{2} + m g h$$

\subsection{Sistema de ecuaciones}
\begin{align}
F &= m a \\
p &= m v \\
E_k &= \frac{p^{2}}{2 m}
\end{align}

\subsection{Pasos del experimento}
\begin{itemize}
\item Medir la masa $m$ del objeto.
\item Soltar desde una altura $h_{0} = 2.5$ m.
\item Registrar el tiempo $t$ de caída.
\end{itemize}

Matriz de rotación:
\[ R = \begin{pmatrix} \cos\theta & -\sin\theta \\ \sin\theta & \cos\theta \end{pmatrix} \]

\begin{python}[label=calc]
import numpy as np
print(np.sqrt(2 * 9.8 * 2.5))
\end{python}
"""

INTRO_LATEX = r"""Esta es una vista estática de lablog publicada con GitHub Pages. Muestra cómo
se renderiza un documento real con secciones, énfasis, listas, matemática
inline ($\nabla \cdot \mathbf{E} = \rho / \varepsilon_{0}$), entornos
matemáticos numerados y celdas de código.

La aplicación interactiva (editor, dictado por voz, ejecución de celdas)
corre localmente. Para probarla:

\begin{itemize}
\item Clona el repositorio.
\item Sigue las instrucciones del \textit{README}.
\item Abre la UI en tu navegador.
\end{itemize}
"""


def seed(store: EventStore, title: str, latex: str) -> str:
    page_id = str(uuid4())
    store.append(page_created(page_id=page_id, title=title))
    store.append(document_replaced(page_id=page_id, latex=latex))
    return page_id


def main() -> None:
    data_dir = Path("data").resolve()
    site_dir = Path("site").resolve()
    settings.data_dir = data_dir
    settings.site_dir = site_dir
    data_dir.mkdir(parents=True, exist_ok=True)

    store = EventStore(settings.event_dir)
    seed(store, "Bienvenido a lablog", INTRO_LATEX)
    seed(store, "Conservación de la energía", DEMO_LATEX)

    out = export_site(site_dir)
    print(f"Static site exported to {out}")


if __name__ == "__main__":
    main()
