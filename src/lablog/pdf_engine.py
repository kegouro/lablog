"""Construye y compila documentos LaTeX reales con Tectonic (XeTeX)."""

from __future__ import annotations

import hashlib
import os
import platform
import re
import shutil
import tarfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from lablog.ast_nodes import CellNode, DocumentNode, MathNode, Node, TextNode
from lablog.config import settings
from lablog.latex_ast import serialize_ast

_PREAMBLE = (
    "\\documentclass{article}\n"
    "\\usepackage{geometry}\n"
    "\\usepackage{fontspec}\n"
    "\\usepackage{amsmath,amssymb}\n"
    "\\usepackage{graphicx}\n"
    "\\usepackage{fancyvrb}\n"
    "\\usepackage{hyperref}\n"  # debe ir último
    "\\begin{document}\n"
)

_LATEX_ESCAPES = {
    "\\": "\\textbackslash{}", "&": "\\&", "%": "\\%", "$": "\\$",
    "#": "\\#", "_": "\\_", "{": "\\{", "}": "\\}",
    "~": "\\textasciitilde{}", "^": "\\textasciicircum{}",
}


def _escape_latex(text: str) -> str:
    return "".join(_LATEX_ESCAPES.get(ch, ch) for ch in text)


def figure_basename(figure_path: str) -> str:
    return Path(figure_path).name


@dataclass
class SourceMarker:
    tex_line: int
    kind: str
    ref: str


@dataclass
class CompileError:
    message: str
    source_line: int | None = None
    ref: str | None = None
    kind: str | None = None


def _verbatim(body: str) -> str:
    return (
        "\\begin{Verbatim}[breaklines=true,breakanywhere=true]\n"
        f"{body}\n"
        "\\end{Verbatim}\n"
    )


def build_document(doc: DocumentNode, title: str) -> tuple[str, list[SourceMarker], list[str]]:
    parts: list[str] = []
    markers: list[SourceMarker] = []
    figures: list[str] = []

    def cur_line() -> int:
        return sum(p.count("\n") for p in parts) + 1

    parts.append(_PREAMBLE)
    if title:
        parts.append(f"\\title{{{_escape_latex(title)}}}\n\\maketitle\n")

    buffer: list[Node] = []

    def flush() -> None:
        if not buffer:
            return
        markers.append(SourceMarker(cur_line(), "text", "prose"))
        parts.append("% lablog-src: kind=text ref=prose\n")
        parts.append(serialize_ast(DocumentNode(children=list(buffer))) + "\n")
        buffer.clear()

    for node in doc.children:
        if isinstance(node, CellNode):
            flush()
            markers.append(SourceMarker(cur_line(), "cell", node.cell_id))
            parts.append(f"% lablog-src: kind=cell ref={node.cell_id}\n")
            parts.append(_verbatim(node.source))
            if node.output:
                parts.append(_verbatim(node.output))
            if node.figure_path:
                figures.append(node.figure_path)
                parts.append(
                    f"\\includegraphics[width=\\linewidth]{{{figure_basename(node.figure_path)}}}\n"
                )
        elif isinstance(node, (TextNode, MathNode)):
            buffer.append(node)

    flush()
    parts.append("\\end{document}\n")
    return "".join(parts), markers, figures


def parse_errors(log: str, markers: list[SourceMarker]) -> list[CompileError]:
    ordered = sorted(markers, key=lambda m: m.tex_line)
    errors: list[CompileError] = []
    for m in re.finditer(r"(?:main\.tex|\.tex)?:(\d+):\s*(.+)", log):
        line = int(m.group(1))
        message = m.group(2).strip()
        marker = None
        for mk in ordered:
            if mk.tex_line <= line:
                marker = mk
            else:
                break
        errors.append(
            CompileError(
                message=message,
                source_line=line,
                ref=marker.ref if marker else None,
                kind=marker.kind if marker else None,
            )
        )
    return errors


# Task 2: Tectonic binary acquisition
TECTONIC_VERSION = "0.15.0"
# Rellenar con los SHA256 reales de los assets de la release pineada
# https://github.com/tectonic-typesetting/tectonic/releases/tag/tectonic@0.15.0
TECTONIC_SHA256: dict[tuple[str, str], str] = {
    ("Darwin", "arm64"): "",
    ("Darwin", "x86_64"): "",
    ("Linux", "x86_64"): "",
    ("Windows", "AMD64"): "",
}
_ASSET = {
    ("Darwin", "arm64"): "tectonic-{v}-aarch64-apple-darwin.tar.gz",
    ("Darwin", "x86_64"): "tectonic-{v}-x86_64-apple-darwin.tar.gz",
    ("Linux", "x86_64"): "tectonic-{v}-x86_64-unknown-linux-gnu.tar.gz",
    ("Windows", "AMD64"): "tectonic-{v}-x86_64-pc-windows-msvc.zip",
}


def _platform_key() -> tuple[str, str]:
    return (platform.system(), platform.machine())


def _bin_dir() -> Path:
    d = settings.data_dir / "bin"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _cached_binary() -> Path | None:
    name = "tectonic.exe" if platform.system() == "Windows" else "tectonic"
    p = _bin_dir() / name
    return p if p.exists() else None


def engine_status() -> dict[str, bool]:
    binary_ready = tectonic_path(download=False) is not None
    cache_dir = Path(os.path.expanduser("~")) / ".cache" / "Tectonic"
    return {"binary_ready": binary_ready, "bundle_warmed": cache_dir.exists()}


def _download_binary() -> Path | None:
    key = _platform_key()
    sha = TECTONIC_SHA256.get(key)
    asset = _ASSET.get(key)
    if not sha or not asset:
        return None
    fname = asset.format(v=TECTONIC_VERSION)
    url = (
        "https://github.com/tectonic-typesetting/tectonic/releases/download/"
        f"tectonic%40{TECTONIC_VERSION}/{fname}"
    )
    archive = _bin_dir() / fname
    with urllib.request.urlopen(url, timeout=120) as resp:  # noqa: S310
        data = resp.read()
    if hashlib.sha256(data).hexdigest() != sha:
        return None
    archive.write_bytes(data)
    if fname.endswith(".tar.gz"):
        with tarfile.open(archive) as tf:
            tf.extractall(_bin_dir())  # noqa: S202
    archive.unlink(missing_ok=True)
    binary = _cached_binary()
    if binary:
        binary.chmod(0o755)
    return binary


def tectonic_path(*, download: bool = True) -> Path | None:
    found = shutil.which("tectonic")
    if found:
        return Path(found)
    cached = _cached_binary()
    if cached:
        return cached
    return _download_binary() if download else None
