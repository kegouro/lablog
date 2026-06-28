"""Catálogo de snippets parametrizados para celdas Jupyter y TikZ."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class Parameter(BaseModel):
    name: str
    default: float | int | str = 0
    min: float | int | None = None
    max: float | int | None = None
    step: float | int | None = None
    description: str = ""
    unit: str = ""


class Snippet(BaseModel):
    id: str
    name: str
    category: Literal["matplotlib", "tikz", "python"]
    description: str
    template: str
    parameters: list[Parameter]
    tags: list[str] = []

    @classmethod
    def catalog(cls) -> list[Snippet]:
        return _CATALOG


def render_snippet(snippet: Snippet, values: dict[str, Any]) -> str:
    defaults = {p.name: p.default for p in snippet.parameters}
    defaults.update(values)
    return snippet.template.format(**defaults)


def find_snippet(snippet_id: str) -> Snippet | None:
    return next((s for s in _CATALOG if s.id == snippet_id), None)


def _p(
    name: str,
    default: Any,
    description: str,
    min: Any = None,
    max: Any = None,
    step: Any = None,
    unit: str = "",
) -> Parameter:
    return Parameter(
        name=name,
        default=default,
        description=description,
        min=min,
        max=max,
        step=step,
        unit=unit,
    )


_CATALOG: list[Snippet] = [
    Snippet(
        id="line_plot",
        name="Gráfico de líneas",
        category="matplotlib",
        description="Línea entre dos puntos.",
        template="""import matplotlib.pyplot as plt
plt.figure()
plt.plot([{x0}, {x1}], [{y0}, {y1}], marker='o')
plt.xlabel('{xlabel}')
plt.ylabel('{ylabel}')
plt.title('{title}')
plt.grid(True)
""",
        parameters=[
            _p("x0", 0, "Coordenada x inicial", -100, 100, 1),
            _p("x1", 10, "Coordenada x final", -100, 100, 1),
            _p("y0", 0, "Coordenada y inicial", -100, 100, 1),
            _p("y1", 10, "Coordenada y final", -100, 100, 1),
            _p("xlabel", "x", "Etiqueta eje x"),
            _p("ylabel", "y", "Etiqueta eje y"),
            _p("title", "Línea", "Título del gráfico"),
        ],
    ),
    Snippet(
        id="scatter_plot",
        name="Diagrama de dispersión",
        category="matplotlib",
        description="Nube de puntos aleatorios.",
        template="""import matplotlib.pyplot as plt
import numpy as np
plt.figure()
np.random.seed({seed})
x = np.random.normal({mean}, {std}, {n})
y = np.random.normal({mean}, {std}, {n})
plt.scatter(x, y, alpha={alpha})
plt.xlabel('{xlabel}')
plt.ylabel('{ylabel}')
plt.title('{title}')
""",
        parameters=[
            _p("n", 100, "Número de puntos", 10, 10000, 10),
            _p("mean", 0, "Media", -50, 50, 1),
            _p("std", 1, "Desviación estándar", 0.1, 20, 0.1),
            _p("seed", 42, "Semilla aleatoria", 0, 10000, 1),
            _p("alpha", 0.6, "Transparencia", 0.0, 1.0, 0.05),
            _p("xlabel", "x", "Etiqueta eje x"),
            _p("ylabel", "y", "Etiqueta eje y"),
            _p("title", "Dispersión", "Título"),
        ],
    ),
    Snippet(
        id="histogram",
        name="Histograma",
        category="matplotlib",
        description="Histograma de datos aleatorios.",
        template="""import matplotlib.pyplot as plt
import numpy as np
plt.figure()
np.random.seed({seed})
data = np.random.normal({mean}, {std}, {n})
plt.hist(data, bins={bins}, edgecolor='black')
plt.xlabel('{xlabel}')
plt.ylabel('{ylabel}')
plt.title('{title}')
""",
        parameters=[
            _p("n", 1000, "Número de muestras", 10, 100000, 10),
            _p("mean", 0, "Media", -50, 50, 1),
            _p("std", 1, "Desviación estándar", 0.1, 20, 0.1),
            _p("bins", 30, "Número de bins", 2, 200, 1),
            _p("seed", 42, "Semilla", 0, 10000, 1),
            _p("xlabel", "valor", "Etiqueta eje x"),
            _p("ylabel", "frecuencia", "Etiqueta eje y"),
            _p("title", "Histograma", "Título"),
        ],
    ),
    Snippet(
        id="tikz_function",
        name="Gráfico de función (TikZ)",
        category="tikz",
        description="Gráfico de una función cuadrática en TikZ.",
        template="""\\begin{{tikzpicture}}
\\draw[->] (-{xmax},0) -- ({xmax},0) node[right] {{$x$}};
\\draw[->] (0,-{ymax}) -- (0,{ymax}) node[above] {{$y$}};
\\draw[domain=-{xmax}:{xmax}, samples={samples}, thick, {color}]
    plot (\\x, {{\\a*(\\x)^2 + \\b*\\x + \\c}});
\\end{{tikzpicture}}
""",
        parameters=[
            _p("a", 1, "Coeficiente cuadrático", -10, 10, 0.1),
            _p("b", 0, "Coeficiente lineal", -10, 10, 0.1),
            _p("c", 0, "Término constante", -10, 10, 0.1),
            _p("xmax", 3, "Límite eje x", 1, 20, 1),
            _p("ymax", 5, "Límite eje y", 1, 50, 1),
            _p("samples", 50, "Puntos de muestreo", 10, 500, 10),
            _p("color", "blue", "Color de la curva"),
        ],
    ),
    Snippet(
        id="tikz_free_body",
        name="Diagrama de cuerpo libre (TikZ)",
        category="tikz",
        description="Bloque con fuerzas.",
        template="""\\begin{{tikzpicture}}
\\draw[thick] (-1,-0.5) rectangle (1,0.5);
\\draw[->, red, thick] (0,0) -- ({fx},0) node[below] {{$F_x$}};
\\draw[->, blue, thick] (0,0) -- (0,{fy}) node[left] {{$F_y$}};
\\draw[->, green!60!black, thick]
    (0,0) -- ({gx},{gy}) node[right] {{$\\vec{{g}}$}};
\\end{{tikzpicture}}
""",
        parameters=[
            _p("fx", 2, "Fuerza horizontal", -5, 5, 0.1, "N"),
            _p("fy", 1.5, "Fuerza vertical", -5, 5, 0.1, "N"),
            _p("gx", 0, "Gravedad x", -2, 2, 0.1, "m/s²"),
            _p("gy", -1.5, "Gravedad y", -3, 0, 0.1, "m/s²"),
        ],
    ),
    Snippet(
        id="bar_plot",
        name="Gráfico de barras",
        category="matplotlib",
        description="Barras comparativas.",
        template="""import matplotlib.pyplot as plt
labels = ['{label1}', '{label2}', '{label3}']
values = [{v1}, {v2}, {v3}]
plt.figure()
plt.bar(labels, values, color='{color}')
plt.ylabel('{ylabel}')
plt.title('{title}')
plt.grid(axis='y')
""",
        parameters=[
            _p("label1", "A", "Etiqueta 1"),
            _p("label2", "B", "Etiqueta 2"),
            _p("label3", "C", "Etiqueta 3"),
            _p("v1", 3, "Valor 1"),
            _p("v2", 7, "Valor 2"),
            _p("v3", 5, "Valor 3"),
            _p("ylabel", "Magnitud", "Etiqueta eje y"),
            _p("title", "Barras", "Título"),
            _p("color", "steelblue", "Color de las barras"),
        ],
        tags=["plot"],
    ),
    Snippet(
        id="fit_line",
        name="Ajuste lineal",
        category="matplotlib",
        description="Regresión lineal con numpy.",
        template="""import numpy as np
import matplotlib.pyplot as plt
x = np.array([{x0}, {x1}, {x2}, {x3}])
y = np.array([{y0}, {y1}, {y2}, {y3}])
coeffs = np.polyfit(x, y, 1)
x_fit = np.linspace(x.min(), x.max(), 100)
y_fit = np.polyval(coeffs, x_fit)
plt.figure()
plt.scatter(x, y, label='Datos')
plt.plot(x_fit, y_fit, color='{color}', label=f'y = {coeffs[0]:.2f}x + {coeffs[1]:.2f}')
plt.xlabel('{xlabel}')
plt.ylabel('{ylabel}')
plt.title('{title}')
plt.legend()
""",
        parameters=[
            _p("x0", 1, "x₀"),
            _p("x1", 2, "x₁"),
            _p("x2", 3, "x₂"),
            _p("x3", 4, "x₃"),
            _p("y0", 2, "y₀"),
            _p("y1", 3, "y₁"),
            _p("y2", 5, "y₂"),
            _p("y3", 4, "y₃"),
            _p("xlabel", "x", "Etiqueta eje x"),
            _p("ylabel", "y", "Etiqueta eje y"),
            _p("title", "Ajuste lineal", "Título"),
            _p("color", "red", "Color de la recta"),
        ],
        tags=["fit", "regression"],
    ),
    Snippet(
        id="simple_table",
        name="Tabla simple (LaTeX)",
        category="tikz",
        description="Tabla básica con booktabs.",
        template="""\\\\begin{{table}}[h]
  \\centering
  \\begin{{tabular}}{{ {cols} }}
    \\toprule
    {header} \\\\
    \\midrule
    {row1} \\\\
    {row2} \\\\
    {row3} \\\\
    \\bottomrule
  \\end{{tabular}}
  \\caption{{{caption}}}
\\end{{table}}
""",
        parameters=[
            _p("cols", "ccc", "Alineación de columnas"),
            _p("header", "A & B & C", "Encabezado"),
            _p("row1", "1 & 2 & 3", "Fila 1"),
            _p("row2", "4 & 5 & 6", "Fila 2"),
            _p("row3", "7 & 8 & 9", "Fila 3"),
            _p("caption", "Mi tabla", "Pie de tabla"),
        ],
        tags=["table"],
    ),
    Snippet(
        id="ode_solve",
        name="Resolver EDO (SciPy)",
        category="python",
        description="Integra una ecuación diferencial ordinaria.",
        template="""from scipy.integrate import solve_ivp
import numpy as np
import matplotlib.pyplot as plt

def model(t, y):
    return {k} * y

sol = solve_ivp(model, [{t0}, {tf}], [{y0}], dense_output=True)
t = np.linspace({t0}, {tf}, 300)
plt.figure()
plt.plot(t, sol.sol(t).T)
plt.xlabel('t')
plt.ylabel('y')
plt.title('{title}')
""",
        parameters=[
            _p("k", -0.5, "Constante del modelo", -10, 10, 0.1),
            _p("t0", 0, "Tiempo inicial"),
            _p("tf", 10, "Tiempo final"),
            _p("y0", 1, "Condición inicial"),
            _p("title", "Solución EDO", "Título"),
        ],
        tags=["ode", "scipy"],
    ),
    Snippet(
        id="energy_equation",
        name="Ecuación de energía",
        category="tikz",
        description="Ecuación de conservación de energía.",
        template="""$$E = mc^2 + \\frac{{1}}{{2}}mv^2 + mgh$$
Donde $m = {m}\\,{m_unit}$, $v = {v}\\,{v_unit}$ y $h = {h}\\,{h_unit}$.
""",
        parameters=[
            _p("m", 1, "Masa", 0, 1000, 0.1, "kg"),
            _p("v", 3, "Velocidad", 0, 1000, 0.1, "m/s"),
            _p("h", 10, "Altura", 0, 10000, 0.1, "m"),
            _p("m_unit", "kg", "Unidad de masa"),
            _p("v_unit", "m/s", "Unidad de velocidad"),
            _p("h_unit", "m", "Unidad de altura"),
        ],
        tags=["physics"],
    ),
]

