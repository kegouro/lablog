"""Construye y compila documentos LaTeX reales con Tectonic (XeTeX)."""

from __future__ import annotations

import asyncio
import hashlib
import os
import platform
import re
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass, field
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
    "\\usepackage{fvextra}\n"  # Verbatim con breaklines/breakanywhere (extiende fancyvrb)
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
    editor_line: int | None = None


@dataclass
class CompileError:
    message: str
    source_line: int | None = None
    editor_line: int | None = None
    ref: str | None = None
    kind: str | None = None
    severity: str = "error"  # error | warning


def _verbatim(body: str) -> str:
    return (
        "\\begin{Verbatim}[breaklines=true,breakanywhere=true]\n"
        f"{body}\n"
        "\\end{Verbatim}\n"
    )


def _is_full_document(doc: DocumentNode) -> bool:
    """Documento LaTeX completo: el usuario trae su propio preámbulo."""
    return any(
        isinstance(node, TextNode) and "\\documentclass" in node.text
        for node in doc.children
    )


def _line_of_snippet(haystack: str, needle: str) -> int | None:
    if not needle.strip():
        return None
    idx = haystack.find(needle)
    if idx < 0:
        # Prueba primera línea no vacía del snippet
        first = next((ln for ln in needle.splitlines() if ln.strip()), "")
        if not first:
            return None
        idx = haystack.find(first)
        if idx < 0:
            return None
    return haystack.count("\n", 0, idx) + 1


def build_document(doc: DocumentNode, title: str) -> tuple[str, list[SourceMarker], list[str]]:
    if _is_full_document(doc):
        # Modo raw: la línea del .tex ES la línea del editor (mapeo 1:1).
        return serialize_ast(doc), [], []

    editor_src = serialize_ast(doc)
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
        snippet = serialize_ast(DocumentNode(children=list(buffer)))
        markers.append(
            SourceMarker(
                tex_line=cur_line(),
                kind="text",
                ref="prose",
                editor_line=_line_of_snippet(editor_src, snippet),
            )
        )
        parts.append("% lablog-src: kind=text ref=prose\n")
        parts.append(snippet + "\n")
        buffer.clear()

    for node in doc.children:
        if isinstance(node, CellNode):
            flush()
            markers.append(
                SourceMarker(
                    tex_line=cur_line(),
                    kind="cell",
                    ref=node.cell_id,
                    editor_line=_line_of_snippet(editor_src, node.source)
                    or _line_of_snippet(editor_src, "\\begin{python}"),
                )
            )
            parts.append(f"% lablog-src: kind=cell ref={node.cell_id}\n")
            parts.append(_verbatim(node.source))
            if node.output:
                parts.append(_verbatim(node.output))
            if node.figure_path:
                figures.append(node.figure_path)
                parts.append(
                    f"\\includegraphics[width=\\linewidth]{{{figure_basename(node.figure_path)}}}\n"
                )
        elif isinstance(node, TextNode | MathNode):
            buffer.append(node)

    flush()
    parts.append("\\end{document}\n")
    return "".join(parts), markers, figures


_BANG_RE = re.compile(r"^!\s*(.+)$")
_L_DOT_RE = re.compile(r"^l\.(\d+)\s*(.*)$")


def _nearest_marker(ordered: list[SourceMarker], line: int) -> SourceMarker | None:
    marker: SourceMarker | None = None
    for mk in ordered:
        if mk.tex_line <= line:
            marker = mk
        else:
            break
    return marker


def parse_errors(log: str, markers: list[SourceMarker]) -> list[CompileError]:
    """FSM línea-a-línea sobre el log de Tectonic/XeTeX.

    No depende de una única regex: acumula mensajes multi-línea tras ``!``.
    """
    ordered = sorted(markers, key=lambda m: m.tex_line)
    errors: list[CompileError] = []
    pending_msg: str | None = None
    pending_severity = "error"

    def emit(line: int | None, message: str, severity: str = "error") -> None:
        marker = _nearest_marker(ordered, line) if line is not None else None
        if marker is None and not markers:
            kind: str | None = "raw"
            editor_line = line  # 1:1 en modo documento completo
            ref = None
        elif marker is None:
            kind, editor_line, ref = None, None, None
        else:
            kind, editor_line, ref = marker.kind, marker.editor_line, marker.ref
            # En modo raw no hay markers; en wrapped usamos editor_line del marcador
            # o, si falta, no inventamos offset falso.
        if editor_line is None and not markers:
            editor_line = line
        kind_out = kind if kind is not None else ("raw" if not markers else None)
        errors.append(
            CompileError(
                message=message.strip() or "Error de compilación",
                source_line=line,
                editor_line=editor_line,
                ref=ref,
                kind=kind_out,
                severity=severity,
            )
        )

    for raw in log.splitlines():
        line = raw.rstrip()
        if not line:
            continue

        if line.startswith("!"):
            m = _BANG_RE.match(line)
            pending_msg = m.group(1).strip() if m else line[1:].strip()
            pending_severity = "error"
            continue

        if pending_msg is not None:
            m = _L_DOT_RE.match(line)
            if m:
                extra = m.group(2).strip()
                msg = f"{pending_msg} {extra}" if extra else pending_msg
                emit(int(m.group(1)), msg, pending_severity)
                pending_msg = None
                continue
            # Algunas líneas de contexto no llevan l.N; sigue acumulando una línea.
            if not line.startswith(" ") and ":" in line:
                m2 = re.search(r"(?:main\.tex|\.tex):(\d+):\s*(.+)", line)
                if m2:
                    combined = f"{pending_msg} {m2.group(2).strip()}"
                    emit(int(m2.group(1)), combined, pending_severity)
                    pending_msg = None
                    continue
            pending_msg = f"{pending_msg} {line.strip()}"
            continue

        m = re.search(r"(?:main\.tex|\.tex):(\d+):\s*(.+)", line)
        if m:
            msg = m.group(2).strip()
            sev = "warning" if msg.lower().startswith("warning") or "Warning" in line else "error"
            emit(int(m.group(1)), msg, sev)
            continue

        if line.lower().startswith("warning") or "LaTeX Warning" in line:
            # Warning sin número de línea: se emite igual.
            emit(None, line, "warning")

    if pending_msg is not None:
        emit(None, pending_msg, pending_severity)

    # Dedup por (line, message)
    seen: set[tuple[int | None, str]] = set()
    unique: list[CompileError] = []
    for e in errors:
        key = (e.source_line, e.message)
        if key in seen:
            continue
        seen.add(key)
        unique.append(e)
    return unique


# Tectonic binary acquisition.
# Versión pineada. No hay SHA256SUMS oficial publicado por upstream, así que la
# cadena de confianza es: TLS de GitHub + tag inmutable. Los hashes se calcularon
# descargando los assets oficiales de esta release.
TECTONIC_VERSION = "0.16.9"
TECTONIC_SHA256: dict[tuple[str, str], str] = {
    ("Darwin", "arm64"): "edb67c61aba768289f6da441c9e6f523cfaff4f8b2a5708523ef29c543f8e88e",
    ("Darwin", "x86_64"): "79d8839fa3594bfea9b2bf2ac0a0455bcc4d0de956a5e5c403107e9a72f79e86",
    ("Linux", "x86_64"): "f3c825128095dc3399ea11c08c18035b33050a216930c295c79e8eb11bd21de4",
    ("Windows", "AMD64"): "131a24604785a9600989a3d91225f597df52ac06f00aeffe86fd529f99ee5cdd",
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
    names = ("tectonic.exe", "tectonic") if platform.system() == "Windows" else ("tectonic",)
    for name in names:
        p = _bin_dir() / name
        if p.exists():
            return p
    return None


def _tectonic_cache_dir() -> Path:
    home = Path(os.path.expanduser("~"))
    system = platform.system()
    if system == "Darwin":
        return home / "Library" / "Caches" / "Tectonic"
    if system == "Windows":
        base = os.getenv("LOCALAPPDATA", str(home / "AppData" / "Local"))
        return Path(base) / "TectonicProject" / "Tectonic"
    return home / ".cache" / "Tectonic"


def installed_version(binary: Path) -> str | None:
    """Versión del binario (`tectonic --version` → '0.16.9'), o None si falla."""
    try:
        out = subprocess.run(  # noqa: S603
            [str(binary), "--version"], capture_output=True, text=True, timeout=10
        )
    except (OSError, subprocess.SubprocessError):
        return None
    m = re.search(r"(\d+\.\d+\.\d+)", out.stdout or out.stderr)
    return m.group(1) if m else None


def engine_status() -> dict[str, object]:
    binary = tectonic_path(download=False)
    on_path = shutil.which("tectonic") is not None
    managed = binary is not None and not on_path  # binario que gestionamos nosotros
    # Solo proponemos "actualizar" para el binario que gestionamos (no el del sistema).
    current = installed_version(binary) if (binary and managed) else None
    update_available = bool(managed and current and current != TECTONIC_VERSION)
    return {
        "binary_ready": binary is not None,
        "bundle_warmed": _tectonic_cache_dir().exists(),
        "managed": managed,
        "installed_version": current,
        "target_version": TECTONIC_VERSION,
        "update_available": update_available,
    }


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
    with urllib.request.urlopen(url, timeout=120) as resp:  # noqa: S310 # nosec B310 (URL fija de release oficial, SHA verificado)
        data = resp.read()
    if hashlib.sha256(data).hexdigest() != sha:
        return None
    archive.write_bytes(data)
    if fname.endswith(".tar.gz"):
        with tarfile.open(archive) as tf:
            tf.extractall(_bin_dir())  # noqa: S202 # nosec B202 (release pineada, SHA verificado)
    elif fname.endswith(".zip"):
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(_bin_dir())  # noqa: S202 # nosec B202 (release pineada, SHA verificado)
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


# Task 3: Async compile + cache
@dataclass
class CompileResult:
    status: str
    pdf: bytes | None = None
    errors: list[CompileError] = field(default_factory=list)
    log: str = ""


def document_hash(doc: DocumentNode, title: str) -> str:
    tex, _m, _f = build_document(doc, title)
    return hashlib.sha256(tex.encode("utf-8")).hexdigest()[:32]


def cached_pdf_path(page_id: str, doc_hash: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", page_id)
    return settings.data_dir / "pdf_cache" / safe / f"{doc_hash}.pdf"


def _write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


async def compile_page(
    page_id: str,
    doc: DocumentNode,
    title: str,
    *,
    figures_dir: Path,
    timeout: float = 120.0,
) -> CompileResult:
    doc_hash = document_hash(doc, title)
    cached = cached_pdf_path(page_id, doc_hash)
    if cached.exists():
        return CompileResult(status="ok", pdf=cached.read_bytes())

    binary = tectonic_path()
    if binary is None:
        return CompileResult(status="no_engine", log="Tectonic no disponible")

    tex, markers, figures = build_document(doc, title)

    with tempfile.TemporaryDirectory() as td:
        tdir = Path(td)
        (tdir / "main.tex").write_text(tex, encoding="utf-8")
        for fp in figures:
            src = Path(fp)
            if not src.is_absolute():
                src = figures_dir / fp
            if src.exists():
                shutil.copy2(src, tdir / figure_basename(fp))

        proc = await asyncio.create_subprocess_exec(
            str(binary), "main.tex", "--outdir", str(tdir),
            cwd=str(tdir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except TimeoutError:
            proc.kill()
            await proc.wait()
            return CompileResult(status="timeout", log="Timeout de compilación")

        log = out.decode("utf-8", "ignore") if out else ""
        try:
            (settings.data_dir / "logs").mkdir(parents=True, exist_ok=True)
            (settings.data_dir / "logs" / "last_compile.log").write_text(
                log, encoding="utf-8"
            )
        except OSError:
            pass

        pdf_file = tdir / "main.pdf"
        if proc.returncode == 0 and pdf_file.exists():
            data = pdf_file.read_bytes()
            _write_atomic(cached, data)
            return CompileResult(status="ok", pdf=data, log=log)
        return CompileResult(status="error", errors=parse_errors(log, markers), log=log)


_install_lock = asyncio.Lock()


async def install_engine(*, force: bool = False) -> dict[str, object]:
    """Descarga el motor pineado y precalienta los paquetes comunes (offline luego).

    `force=True` reinstala la versión pineada (para 'actualizar' un binario
    gestionado a la que trae esta versión de la app). Serializado con un lock:
    dos instalaciones concurrentes se corromperían el binario mutuamente.
    """
    async with _install_lock:
        return await _install_engine_locked(force=force)


async def _install_engine_locked(*, force: bool) -> dict[str, object]:
    if force:
        for name in ("tectonic", "tectonic.exe"):
            (_bin_dir() / name).unlink(missing_ok=True)

    binary = await asyncio.to_thread(tectonic_path, download=True)
    if binary is None:
        return {
            "installed": False,
            "warmed": False,
            "message": "No hay binario de Tectonic disponible para esta plataforma",
        }

    # Warm: compila un doc mínimo para cachear los paquetes del preámbulo.
    warm = DocumentNode(children=[TextNode(text="lablog warm-up $x^2$")])
    res = await compile_page(
        "__warm__", warm, "warm", figures_dir=settings.data_dir, timeout=300.0
    )
    return {
        "installed": True,
        "warmed": res.status == "ok",
        "version": TECTONIC_VERSION,
        "message": "Motor listo" if res.status == "ok" else f"Instalado; warm: {res.status}",
    }
