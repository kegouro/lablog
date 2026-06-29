# Real PDF Compilation (Tectonic) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compile the current lablog page to a real PDF with Tectonic (XeTeX), with code cells (source + output + figure), source-line error mapping, and an "approximate preview → compile" affordance.

**Architecture:** A new pure module builds a XeLaTeX document from the page projection and parses Tectonic's error log back to source cells. An async endpoint runs Tectonic in a temp dir with a hard timeout and a content-hash PDF cache. The React preview gains a compile button, a PDF viewer panel, and an error panel.

**Tech Stack:** Python 3.11+, FastAPI (async subprocess), Tectonic binary; React 19 + TypeScript.

## Global Constraints

- Python line length 100; Ruff selects `E,F,I,N,W,UP,B,C4,SIM`; Mypy strict.
- No `--shell-escape` ever (security).
- Tectonic version pinned; per-platform SHA256 hardcoded in code (not read from the release).
- Preamble package order is exact; `hyperref` MUST be last.
- Code/output use `fancyvrb` `Verbatim` (NOT `listings`); no `inputenc`.
- AI commits end with: `Co-Authored-By: Kimi Code <noreply@example.com>`.
- Validation gate for every backend task: `ruff check src tests && mypy -p lablog && pytest -q`.

---

### Task 1: Document builder + error parser (pure, TDD)

**Files:**
- Create: `src/lablog/pdf_engine.py`
- Test: `tests/test_pdf_engine.py`

**Interfaces:**
- Produces:
  - `@dataclass SourceMarker(tex_line:int, kind:str, ref:str)`
  - `@dataclass CompileError(message:str, source_line:int|None, ref:str|None, kind:str|None)`
  - `build_document(doc:DocumentNode, title:str) -> tuple[str, list[SourceMarker], list[str]]` (returns `tex`, `markers`, `figure_paths` where `figure_paths` are the raw `CellNode.figure_path` values referenced, in order)
  - `parse_errors(log:str, markers:list[SourceMarker]) -> list[CompileError]`
  - `figure_basename(figure_path:str) -> str`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_pdf_engine.py
from __future__ import annotations

from lablog.ast_nodes import CellNode, DocumentNode, MathNode, TextNode
from lablog.pdf_engine import (
    SourceMarker,
    build_document,
    figure_basename,
    parse_errors,
)


def _doc() -> DocumentNode:
    return DocumentNode(
        children=[
            TextNode(text="Intro $x^2$\n\\section{S}\n"),
            CellNode(cell_id="c1", language="python", source="print('é')", output="é\n",
                     figure_path="c1/fig_0.png"),
        ]
    )


def test_build_document_preamble_order_hyperref_last() -> None:
    tex, _markers, _figs = build_document(_doc(), "T")
    assert "\\usepackage{fancyvrb}" in tex
    assert "\\usepackage{inputenc}" not in tex
    # hyperref after every other \usepackage
    assert tex.index("hyperref") > tex.rindex("\\usepackage{graphicx}")


def test_build_document_cell_uses_verbatim_and_includegraphics() -> None:
    tex, _markers, figs = build_document(_doc(), "T")
    assert "\\begin{Verbatim}[breaklines=true,breakanywhere=true]" in tex
    assert "print('é')" in tex          # code
    assert "\\includegraphics" in tex
    assert "fig_0.png" in tex           # figure by basename
    assert figs == ["c1/fig_0.png"]


def test_build_document_escapes_title() -> None:
    tex, _m, _f = build_document(DocumentNode(children=[]), "100% #1")
    assert "\\%" in tex and "\\#" in tex


def test_build_document_emits_source_markers() -> None:
    tex, markers, _f = build_document(_doc(), "T")
    assert "% lablog-src: kind=cell ref=c1" in tex
    assert any(m.kind == "cell" and m.ref == "c1" for m in markers)


def test_parse_errors_maps_to_nearest_marker() -> None:
    markers = [SourceMarker(5, "text", "prose"), SourceMarker(20, "cell", "c1")]
    log = "main.tex:23: Undefined control sequence \\foo"
    errors = parse_errors(log, markers)
    assert errors and errors[0].ref == "c1" and errors[0].kind == "cell"
    assert errors[0].source_line == 23


def test_parse_errors_handles_no_preceding_marker() -> None:
    errors = parse_errors("main.tex:2: oops", [SourceMarker(10, "cell", "c1")])
    assert errors and errors[0].ref is None


def test_figure_basename() -> None:
    assert figure_basename("c1/fig_0.png") == "fig_0.png"
    assert figure_basename("/abs/path/p/fig_1.png") == "fig_1.png"
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest tests/test_pdf_engine.py -q`
Expected: FAIL (module/symbols not defined).

- [ ] **Step 3: Implement `pdf_engine.py` (pure parts)**

```python
"""Construye y compila documentos LaTeX reales con Tectonic (XeTeX)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from lablog.ast_nodes import CellNode, DocumentNode, MathNode, Node, TextNode
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
```

- [ ] **Step 4: Run to verify pass**

Run: `pytest tests/test_pdf_engine.py -q`
Expected: PASS (7 tests).

- [ ] **Step 5: Lint/type/commit**

Run: `ruff check src/lablog/pdf_engine.py tests/test_pdf_engine.py && mypy -p lablog`
```bash
git add src/lablog/pdf_engine.py tests/test_pdf_engine.py
git commit -m "feat(pdf): document builder and error parser for Tectonic

Co-Authored-By: Kimi Code <noreply@example.com>"
```

---

### Task 2: Tectonic binary acquisition

**Files:**
- Modify: `src/lablog/pdf_engine.py`
- Test: `tests/test_pdf_engine.py` (append)

**Interfaces:**
- Produces:
  - `TECTONIC_VERSION: str`, `TECTONIC_SHA256: dict[tuple[str,str], str]`
  - `engine_status() -> dict[str, bool]` → `{"binary_ready", "bundle_warmed"}`
  - `tectonic_path() -> Path | None` (PATH → cache → download; None if unavailable)
  - `_platform_key() -> tuple[str, str]` (e.g. `("Darwin","arm64")`)

- [ ] **Step 1: Write failing tests**

```python
# append to tests/test_pdf_engine.py
import shutil

from lablog import pdf_engine


def test_platform_key_shape() -> None:
    sysname, arch = pdf_engine._platform_key()
    assert isinstance(sysname, str) and isinstance(arch, str)


def test_engine_status_keys() -> None:
    st = pdf_engine.engine_status()
    assert set(st) == {"binary_ready", "bundle_warmed"}
    assert all(isinstance(v, bool) for v in st.values())


def test_tectonic_path_uses_PATH_when_present(monkeypatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda _name: "/usr/bin/tectonic")
    assert str(pdf_engine.tectonic_path()) == "/usr/bin/tectonic"
```

- [ ] **Step 2: Run → FAIL.** `pytest tests/test_pdf_engine.py -q`

- [ ] **Step 3: Implement acquisition**

Append to `pdf_engine.py` (add imports `import os, platform, shutil, hashlib, tarfile, urllib.request` and `from lablog.config import settings`):

```python
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
    with urllib.request.urlopen(url, timeout=120) as resp:  # noqa: S310 (https pin)
        data = resp.read()
    if hashlib.sha256(data).hexdigest() != sha:
        return None
    archive.write_bytes(data)
    if fname.endswith(".tar.gz"):
        with tarfile.open(archive) as tf:
            tf.extractall(_bin_dir())  # noqa: S202 (release confiable, sha verificado)
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
```

- [ ] **Step 4: Run → PASS.** `pytest tests/test_pdf_engine.py -q`

- [ ] **Step 5: Lint/type/commit**

```bash
ruff check src/lablog/pdf_engine.py tests/test_pdf_engine.py && mypy -p lablog
git add src/lablog/pdf_engine.py tests/test_pdf_engine.py
git commit -m "feat(pdf): pinned Tectonic acquisition with hardcoded sha256

Co-Authored-By: Kimi Code <noreply@example.com>"
```

> NOTE for the executor: the four SHA256 values are empty. Fill them by fetching
> the release asset list for `tectonic@0.15.0` and computing/reading SHA256 per
> asset. If the release tag differs, adjust `TECTONIC_VERSION` and `_ASSET`
> accordingly. Leaving them empty is acceptable for merge ONLY if download is
> guarded (it returns None → 503), but flag it in the PR.

---

### Task 3: Async compile + cache

**Files:**
- Modify: `src/lablog/pdf_engine.py`
- Test: `tests/test_pdf_engine.py` (append; cache test only — real compile under marker)

**Interfaces:**
- Produces:
  - `@dataclass CompileResult(status:str, pdf:bytes|None, errors:list[CompileError], log:str)` — `status ∈ {"ok","error","timeout","no_engine"}`
  - `document_hash(doc:DocumentNode, title:str) -> str`
  - `cached_pdf_path(page_id:str, doc_hash:str) -> Path`
  - `async compile_page(page_id:str, doc:DocumentNode, title:str, *, figures_dir:Path, timeout:float) -> CompileResult`

- [ ] **Step 1: Write failing test (cache + hash, no Tectonic)**

```python
# append to tests/test_pdf_engine.py
def test_document_hash_stable_and_sensitive() -> None:
    a = DocumentNode(children=[TextNode(text="x")])
    b = DocumentNode(children=[TextNode(text="y")])
    assert pdf_engine.document_hash(a, "T") == pdf_engine.document_hash(a, "T")
    assert pdf_engine.document_hash(a, "T") != pdf_engine.document_hash(b, "T")


def test_cached_pdf_path_under_data_dir(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(pdf_engine.settings, "data_dir", tmp_path)
    p = pdf_engine.cached_pdf_path("page1", "deadbeef")
    assert p.name == "deadbeef.pdf" and "page1" in str(p)
```

- [ ] **Step 2: Run → FAIL.**

- [ ] **Step 3: Implement async compile + cache**

Add imports: `import asyncio`, `from dataclasses import field`, `import shutil` (already). Append:

```python
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
    import tempfile

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
        except (TimeoutError, asyncio.TimeoutError):
            proc.kill()
            await proc.wait()
            return CompileResult(status="timeout", log="Timeout de compilación")

        log = out.decode("utf-8", "ignore") if out else ""
        try:
            (settings.data_dir / "logs").mkdir(parents=True, exist_ok=True)
            (settings.data_dir / "logs" / "last_compile.log").write_text(log, encoding="utf-8")
        except OSError:
            pass

        pdf_file = tdir / "main.pdf"
        if proc.returncode == 0 and pdf_file.exists():
            data = pdf_file.read_bytes()
            _write_atomic(cached, data)
            return CompileResult(status="ok", pdf=data, log=log)
        return CompileResult(status="error", errors=parse_errors(log, markers), log=log)
```

- [ ] **Step 4: Run → PASS** (cache/hash tests). Add the real-compile test guarded:

```python
import os
import pytest

@pytest.mark.skipif(
    os.getenv("LABLOG_RUN_TECTONIC_TESTS") != "1",
    reason="set LABLOG_RUN_TECTONIC_TESTS=1 to exercise real Tectonic",
)
def test_real_compile_minimal(tmp_path) -> None:
    import asyncio as _a
    doc = DocumentNode(children=[TextNode(text="Hola $x^2$")])
    res = _a.run(pdf_engine.compile_page("p", doc, "T", figures_dir=tmp_path))
    assert res.status == "ok" and res.pdf and res.pdf[:4] == b"%PDF"
```

Run: `pytest tests/test_pdf_engine.py -q` (real test skips).

- [ ] **Step 5: Lint/type/commit**

```bash
ruff check src/lablog/pdf_engine.py tests/test_pdf_engine.py && mypy -p lablog
git add src/lablog/pdf_engine.py tests/test_pdf_engine.py
git commit -m "feat(pdf): async Tectonic compile with timeout and content cache

Co-Authored-By: Kimi Code <noreply@example.com>"
```

---

### Task 4: Endpoints

**Files:**
- Modify: `src/lablog/api.py`
- Test: `tests/test_api.py` (append)

**Interfaces:**
- Consumes: `pdf_engine.compile_page`, `pdf_engine.engine_status`.
- Produces routes: `GET /api/v1/pages/{id}/export/pdf` (async), `GET /api/v1/pdf/engine-status`. A per-page `asyncio.Lock` registry.

- [ ] **Step 1: Write failing tests**

```python
# append to tests/test_api.py  (uses existing TestClient `client` pattern)
def test_engine_status_shape(client) -> None:
    r = client.get("/api/v1/pdf/engine-status")
    assert r.status_code == 200
    assert set(r.json()) == {"binary_ready", "bundle_warmed"}


def test_pdf_export_503_without_engine(client, monkeypatch) -> None:
    from lablog import pdf_engine
    monkeypatch.setattr(pdf_engine, "tectonic_path", lambda **_: None)
    # create a page first
    pid = client.post("/api/v1/pages", json={"title": "X"}).json()["page_id"]
    r = client.get(f"/api/v1/pages/{pid}/export/pdf")
    assert r.status_code == 503
```

> If `tests/test_api.py` does not expose a `client` fixture, mirror the existing
> TestClient setup used by the other tests in that file (do not invent a new one).

- [ ] **Step 2: Run → FAIL.** `pytest tests/test_api.py -q`

- [ ] **Step 3: Implement routes**

In `api.py`: add `import asyncio` and `from lablog import pdf_engine`. Add a lock registry near module globals:

```python
_pdf_locks: dict[str, asyncio.Lock] = {}


def _pdf_lock(page_id: str) -> asyncio.Lock:
    lock = _pdf_locks.get(page_id)
    if lock is None:
        lock = asyncio.Lock()
        _pdf_locks[page_id] = lock
    return lock
```

Add the status route (near `/health`):

```python
@router.get("/pdf/engine-status")
def pdf_engine_status() -> dict[str, bool]:
    return pdf_engine.engine_status()
```

Add the dedicated PDF route **before** the generic `export_page` route (route order matters):

```python
@router.get("/pages/{page_id}/export/pdf")
async def export_page_pdf(page_id: str) -> Response:
    events = _events(page_id)
    proj = project(page_id, events)
    title = proj.title or "lablog_export"
    figures_dir = settings.figures_dir / page_id
    async with _pdf_lock(page_id):
        result = await pdf_engine.compile_page(page_id, proj.ast, title, figures_dir=figures_dir)
    if result.status == "ok" and result.pdf is not None:
        filename = f"{title.replace(' ', '_')}.pdf"
        return Response(
            content=result.pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename={filename}"},
        )
    if result.status == "no_engine":
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Tectonic no disponible")
    if result.status == "timeout":
        raise HTTPException(status.HTTP_504_GATEWAY_TIMEOUT, "Compilación excedió el tiempo límite")
    raise HTTPException(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={"errors": [asdict(e) for e in result.errors], "log": result.log[-4000:]},
    )
```

Remove the `pdf` branch from the generic `export_page` (the `if format == "pdf": return _pandoc_export(...)` lines).

- [ ] **Step 4: Run → PASS.** `pytest tests/test_api.py -q`

- [ ] **Step 5: Lint/type/commit**

```bash
ruff check src tests && mypy -p lablog && pytest -q
git add src/lablog/api.py tests/test_api.py
git commit -m "feat(pdf): async export/pdf endpoint and engine-status

Co-Authored-By: Kimi Code <noreply@example.com>"
```

---

### Task 5: Frontend API layer

**Files:**
- Modify: `ui/src/lib/api.ts`

**Interfaces:**
- Produces: `compilePdf(pageId:string): Promise<Blob>` (throws `PdfCompileError` with `errors`/`status` on 4xx/5xx), `pdfEngineStatus(): Promise<{binary_ready:boolean;bundle_warmed:boolean}>`, and an exported `PdfCompileError` class / type.

- [ ] **Step 1: Implement** (no FE test runner configured; verify via `tsc`)

```ts
// ui/src/lib/api.ts — append
export interface PdfError { message: string; source_line: number | null; ref: string | null; kind: string | null }

export class PdfCompileError extends Error {
  status: number
  errors: PdfError[]
  constructor(status: number, message: string, errors: PdfError[] = []) {
    super(message)
    this.status = status
    this.errors = errors
  }
}

export async function pdfEngineStatus(): Promise<{ binary_ready: boolean; bundle_warmed: boolean }> {
  return fetchJson('/pdf/engine-status')
}

export async function compilePdf(pageId: string): Promise<Blob> {
  const res = await fetch(`${API_BASE}/pages/${pageId}/export/pdf`)
  if (res.ok) return res.blob()
  let detail: { errors?: PdfError[] } = {}
  try {
    const body = await res.json()
    detail = body.detail ?? body
  } catch {
    // sin cuerpo JSON
  }
  const msg =
    res.status === 422 ? 'Errores de compilación LaTeX'
    : res.status === 504 ? 'La compilación superó el tiempo límite'
    : res.status === 503 ? 'Motor PDF (Tectonic) no disponible'
    : `Error ${res.status}`
  throw new PdfCompileError(res.status, msg, detail.errors ?? [])
}
```

- [ ] **Step 2: Verify** `cd ui && npx tsc --noEmit` → clean.

- [ ] **Step 3: Commit**

```bash
git add ui/src/lib/api.ts
git commit -m "feat(pdf): client compilePdf and engine status

Co-Authored-By: Kimi Code <noreply@example.com>"
```

---

### Task 6: Preview affordance + PDF viewer + error panel + ExportMenu

**Files:**
- Modify: `ui/src/components/preview/latex-preview.tsx`
- Modify: `ui/src/components/shell/export-menu.tsx`

**Interfaces:**
- Consumes: `compilePdf`, `pdfEngineStatus`, `PdfCompileError`.

- [ ] **Step 1: Implement preview affordance + viewer**

In `latex-preview.tsx`, add local state and a header row with a **"Vista aproximada"** badge and a **"Compilar PDF"** button. On click:
1. `const st = await pdfEngineStatus()`; if `!st.binary_ready` show a `toast.info('Primera vez: preparando el motor (~1 min)')`.
2. Set `compiling=true` (disable button).
3. `try { const blob = await compilePdf(activePageId); setPdfUrl(URL.createObjectURL(blob)); setErrors([]) }`
   `catch (e) { if (e instanceof PdfCompileError) setErrors(e.errors); toast.error(e.message) }`
   `finally { setCompiling(false) }`.
4. Render: when `pdfUrl` set, an overlay/panel with `<iframe src={pdfUrl} className="h-full w-full" title="PDF" />` + a Descargar `<a download>` + close (revoke URL on close). When `errors.length`, an error panel listing `Celda {ref} · línea {source_line}: {message}` (use `Documento` when `kind!=='cell'`).

Exact button + state scaffold:

```tsx
// imports
import { useState } from 'react'   // (merge with existing imports)
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { FileText, Loader2 } from 'lucide-react'
import { compilePdf, pdfEngineStatus, PdfCompileError, type PdfError } from '@/lib/api'

// inside LatexPreview():
const [compiling, setCompiling] = useState(false)
const [pdfUrl, setPdfUrl] = useState<string | null>(null)
const [errors, setErrors] = useState<PdfError[]>([])

const handleCompile = async () => {
  if (!activePageId || compiling) return
  setErrors([])
  try {
    const st = await pdfEngineStatus()
    if (!st.binary_ready) toast.info('Primera vez: preparando el motor (~1 min)')
  } catch { /* sigue */ }
  setCompiling(true)
  try {
    const blob = await compilePdf(activePageId)
    if (pdfUrl) URL.revokeObjectURL(pdfUrl)
    setPdfUrl(URL.createObjectURL(blob))
  } catch (e) {
    if (e instanceof PdfCompileError) setErrors(e.errors)
    toast.error(e instanceof Error ? e.message : 'Error al compilar')
  } finally {
    setCompiling(false)
  }
}
```

Header (replace the existing "Vista previa" header row):

```tsx
<div className="flex items-center justify-between px-1">
  <div className="flex items-center gap-2">
    <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
      Vista previa
    </span>
    <span className="rounded bg-muted px-1.5 py-0.5 text-[9px] uppercase tracking-wider text-muted-foreground">
      Aproximada
    </span>
  </div>
  <Button variant="outline" size="sm" className="h-7 gap-1.5 text-xs" disabled={!activePageId || compiling} onClick={handleCompile}>
    {compiling ? <Loader2 className="size-3.5 animate-spin" /> : <FileText className="size-3.5" />}
    Compilar PDF
  </Button>
</div>
```

Error panel (render above or below the preview body when `errors.length > 0`):

```tsx
{errors.length > 0 && (
  <div className="rounded-lg border border-destructive/40 bg-destructive/5 p-2 text-xs">
    <p className="mb-1 font-semibold text-destructive">Errores de compilación</p>
    <ul className="space-y-0.5">
      {errors.map((e, i) => (
        <li key={i} className="font-mono">
          {e.kind === 'cell' ? `Celda ${e.ref}` : 'Documento'}
          {e.source_line != null ? ` · línea ${e.source_line}` : ''}: {e.message}
        </li>
      ))}
    </ul>
  </div>
)}
```

PDF viewer overlay (inside the preview container; revoke on close):

```tsx
{pdfUrl && (
  <div className="absolute inset-0 z-30 flex flex-col bg-card">
    <div className="flex items-center justify-between border-b px-2 py-1">
      <span className="text-xs font-medium">PDF compilado</span>
      <div className="flex gap-1">
        <a className="text-xs underline" href={pdfUrl} download="lablog.pdf">Descargar</a>
        <button className="text-xs" onClick={() => { URL.revokeObjectURL(pdfUrl); setPdfUrl(null) }}>Cerrar</button>
      </div>
    </div>
    <iframe src={pdfUrl} title="PDF" className="min-h-0 flex-1" />
  </div>
)}
```

(Ensure the preview container is `relative` so the overlay positions correctly.)

- [ ] **Step 2: ExportMenu PDF item** — in `export-menu.tsx`, route the `pdf` format through `compilePdf` (download the blob; on `PdfCompileError` show `toast.error`). Keep other formats via `exportPage`.

- [ ] **Step 3: Verify** `cd ui && npx tsc --noEmit && npm run build` → clean.

- [ ] **Step 4: Commit**

```bash
git add ui/src/components/preview/latex-preview.tsx ui/src/components/shell/export-menu.tsx
git commit -m "feat(pdf): compile button, PDF viewer, error panel

Co-Authored-By: Kimi Code <noreply@example.com>"
```

---

### Task 7: Docs + final validation

**Files:**
- Modify: `README.md`

- [ ] **Step 1:** Add a "Real PDF compilation" subsection under the desktop/export area: Tectonic, offline after first compile, `\begin{python}` cells become code+output+figure, error panel maps to cells, threat model line (no `--shell-escape`).

- [ ] **Step 2: Full validation**

```bash
ruff check src tests && mypy -p lablog && pytest -q
cd ui && npx tsc --noEmit && npm run build && npm run lint
```
Expected: all green (real-compile test skipped without `LABLOG_RUN_TECTONIC_TESTS=1`).

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: document real PDF compilation with Tectonic

Co-Authored-By: Kimi Code <noreply@example.com>"
```

---

## Self-review notes

- **Spec coverage:** acquisition (T2), build_document/markers (T1), async compile + timeout + tempdir + log (T3), cache (T3), endpoints + lock + status (T4), FE api (T5), affordance + viewer + error panel + ExportMenu (T6), threat model + README (T7). All spec sections mapped.
- **Type consistency:** `compile_page` / `CompileResult` / `CompileError` / `SourceMarker` names match across tasks; `engine_status` keys match FE expectations.
- **Known placeholder (intentional, flagged):** `TECTONIC_SHA256` values are empty and called out as an executor task; guarded so empty → 503 rather than a silent wrong binary.
