from __future__ import annotations

import os
import shutil

import pytest

from lablog import pdf_engine
from lablog.ast_nodes import CellNode, DocumentNode, TextNode
from lablog.latex_ast import parse_latex, serialize_ast
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
    assert "\\usepackage{fvextra}" in tex
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


# Task 2: Tectonic binary acquisition
def test_platform_key_shape() -> None:
    sysname, arch = pdf_engine._platform_key()
    assert isinstance(sysname, str) and isinstance(arch, str)


def test_engine_status_keys() -> None:
    st = pdf_engine.engine_status()
    assert {"binary_ready", "bundle_warmed", "managed", "update_available"} <= set(st)
    assert isinstance(st["binary_ready"], bool)
    assert isinstance(st["bundle_warmed"], bool)
    assert st["target_version"] == pdf_engine.TECTONIC_VERSION


def test_tectonic_path_uses_path_when_present(monkeypatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda _name: "/usr/bin/tectonic")
    assert str(pdf_engine.tectonic_path()) == "/usr/bin/tectonic"


# Task 3: Async compile + cache
def test_document_hash_stable_and_sensitive() -> None:
    a = DocumentNode(children=[TextNode(text="x")])
    b = DocumentNode(children=[TextNode(text="y")])
    assert pdf_engine.document_hash(a, "T") == pdf_engine.document_hash(a, "T")
    assert pdf_engine.document_hash(a, "T") != pdf_engine.document_hash(b, "T")


def test_cached_pdf_path_under_data_dir(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(pdf_engine.settings, "data_dir", tmp_path)
    p = pdf_engine.cached_pdf_path("page1", "deadbeef")
    assert p.name == "deadbeef.pdf" and "page1" in str(p)


@pytest.mark.skipif(
    os.getenv("LABLOG_RUN_TECTONIC_TESTS") != "1",
    reason="set LABLOG_RUN_TECTONIC_TESTS=1 to exercise real Tectonic",
)
def test_real_compile_minimal(tmp_path) -> None:
    import asyncio as _a
    doc = DocumentNode(children=[TextNode(text="Hola $x^2$")])
    res = _a.run(pdf_engine.compile_page("p", doc, "T", figures_dir=tmp_path))
    assert res.status == "ok" and res.pdf and res.pdf[:4] == b"%PDF"


# Task 1: Backend — modo raw
def test_full_document_compiles_raw() -> None:
    src = (
        "\\documentclass{article}\n\\begin{document}\nHola $x$\n\\end{document}"
    )
    doc = parse_latex(src)
    tex, markers, figs = pdf_engine.build_document(doc, "T")
    assert tex == serialize_ast(doc)  # passthrough exacto
    assert "fvextra" not in tex  # sin doble preámbulo
    assert markers == [] and figs == []


def test_documentclass_inside_cell_not_raw() -> None:
    src = "\\begin{python}\nprint('documentclass test \\\\documentclass')\n\\end{python}"
    doc = parse_latex(src)
    tex, _markers, _figs = pdf_engine.build_document(doc, "T")
    assert "fvextra" in tex  # sigue en modo bitácora con nuestro preámbulo


def test_parse_errors_without_markers_is_raw() -> None:
    errors = pdf_engine.parse_errors("main.tex:7: Undefined control sequence", [])
    assert errors[0].source_line == 7
    assert errors[0].ref is None and errors[0].kind == "raw"
