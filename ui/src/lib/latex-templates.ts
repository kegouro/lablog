export interface LatexTemplate {
  id: string
  name: string
  description: string
  content: string
}

export const LATEX_TEMPLATES: LatexTemplate[] = [
  {
    id: 'articulo',
    name: 'Artículo científico',
    description: 'article · abstract, secciones, matemática y figuras',
    content: `\\documentclass[11pt]{article}
\\usepackage[margin=2.5cm]{geometry}
\\usepackage{fontspec}
\\usepackage{amsmath,amssymb}
\\usepackage{graphicx}
\\usepackage{hyperref}

\\title{Título del trabajo}
\\author{Nombre Apellido}
\\date{\\today}

\\begin{document}
\\maketitle

\\begin{abstract}
Resumen del trabajo en un párrafo.
\\end{abstract}

\\section{Introducción}
El contexto y la motivación. Una ecuación inline: $E = mc^2$.

\\section{Método}
\\begin{equation}
  F = ma
\\end{equation}

\\section{Resultados}

\\section{Conclusiones}

\\end{document}
`,
  },
  {
    id: 'informe',
    name: 'Informe de laboratorio',
    description: 'article · siunitx y booktabs para datos y unidades',
    content: `\\documentclass[11pt]{article}
\\usepackage[margin=2.5cm]{geometry}
\\usepackage{fontspec}
\\usepackage{amsmath,amssymb}
\\usepackage{graphicx}
\\usepackage{siunitx}
\\usepackage{booktabs}
\\usepackage{hyperref}

\\title{Informe de laboratorio}
\\author{Nombre Apellido}
\\date{\\today}

\\begin{document}
\\maketitle

\\section{Objetivo}

\\section{Montaje y método}

\\section{Resultados}
\\begin{table}[h]
  \\centering
  \\begin{tabular}{S[table-format=1.2] S[table-format=2.1]}
    \\toprule
    {$t$ (\\si{\\second})} & {$v$ (\\si{\\metre\\per\\second})} \\\\
    \\midrule
    0.10 & 1.0 \\\\
    0.20 & 2.1 \\\\
    \\bottomrule
  \\end{tabular}
  \\caption{Mediciones.}
\\end{table}

La aceleración medida fue \\SI{9.81}{\\metre\\per\\second\\squared}.

\\section{Conclusión}

\\end{document}
`,
  },
  {
    id: 'tarea',
    name: 'Tarea de problemas',
    description: 'article · entornos problema/solución con amsthm',
    content: `\\documentclass[11pt]{article}
\\usepackage[margin=2.5cm]{geometry}
\\usepackage{fontspec}
\\usepackage{amsmath,amssymb,amsthm}
\\usepackage{enumitem}

\\newtheorem{problema}{Problema}
\\theoremstyle{remark}
\\newtheorem*{solucion}{Solución}

\\title{Tarea N}
\\author{Nombre Apellido}
\\date{\\today}

\\begin{document}
\\maketitle

\\begin{problema}
Enunciado del primer problema.
\\end{problema}

\\begin{solucion}
Desarrollo: $\\int_0^1 x\\,dx = \\tfrac{1}{2}$.
\\end{solucion}

\\end{document}
`,
  },
  {
    id: 'beamer',
    name: 'Presentación (Beamer)',
    description: 'beamer · portada y diapositivas de ejemplo',
    content: `\\documentclass{beamer}
\\usepackage{fontspec}
\\usepackage{amsmath}

\\title{Título de la presentación}
\\author{Nombre Apellido}
\\date{\\today}

\\begin{document}

\\frame{\\titlepage}

\\begin{frame}{Motivación}
  \\begin{itemize}
    \\item Primer punto.
    \\item Segundo punto.
  \\end{itemize}
\\end{frame}

\\begin{frame}{Resultado central}
  \\begin{equation}
    E = mc^2
  \\end{equation}
\\end{frame}

\\end{document}
`,
  },
  {
    id: 'carta',
    name: 'Carta formal',
    description: 'letter · remitente, destinatario y firma',
    content: `\\documentclass[11pt]{letter}
\\usepackage[margin=2.5cm]{geometry}
\\usepackage{fontspec}

\\signature{Nombre Apellido}
\\address{Tu dirección \\\\ Ciudad}

\\begin{document}
\\begin{letter}{Destinatario \\\\ Institución \\\\ Ciudad}

\\opening{Estimado/a:}

Cuerpo de la carta.

\\closing{Atentamente,}

\\end{letter}
\\end{document}
`,
  },
]
