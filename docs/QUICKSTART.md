# lablog · Guía de 5 minutos

## 1. Instalar

```bash
pip install jose-labarca-lablog
# o desde el repo:
uv sync --extra dev
```

## 2. Arrancar

```bash
lablog serve
# UI: http://127.0.0.1:8000
```

App de escritorio (opcional):

```bash
pip install 'jose-labarca-lablog[desktop]'
lablog app
```

## 3. Primera página

1. **Nueva página** (barra superior o `Ctrl+K`).
2. **Plantillas** → *Informe de laboratorio (física)* o *Notas E&M*.
3. Edita LaTeX; la vista previa (KaTeX) actualiza al dejar de escribir ~300 ms.
4. Escribe `\` para **autocompletar** comandos y entornos (↑↓, Enter/Tab).

## 4. Compilar PDF real

1. Asegúrate de tener el motor (botón *Instalar motor* la primera vez).
2. **Compilar PDF**.
3. Si falla: haz click en **línea N** → el editor salta y resalta el gutter.

## 5. Celdas Python

```latex
\begin{python}
print(1 + 1)
\end{python}
```

Ejecuta desde el panel **Celdas** o el modo **Laboratorio**.

## 6. Multi-página (incluye)

En un documento raíz:

```latex
\input{page:<uuid-de-otra-pagina>}
```

Al compilar PDF se expanden los includes (sin ciclos; profundidad máxima 5).

## 7. CLI

```bash
lablog new --template=lab-report-physics --title="Lab 1"
lablog list-pages
lablog render <page_id>
```

## Más

- Historia / time-travel: botón **Historia** en la vista previa.
- Vault: panel lateral de adjuntos.
- Plan de producción: `docs/PRODUCTION_MASTER_PLAN.md`.
