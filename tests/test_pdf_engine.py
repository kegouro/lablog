from __future__ import annotations

import shutil

from lablog import pdf_engine
from lablog.ast_nodes import CellNode, DocumentNode, TextNode
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


# Task 2: Tectonic binary acquisition
def test_platform_key_shape() -> None:
    sysname, arch = pdf_engine._platform_key()
    assert isinstance(sysname, str) and isinstance(arch, str)


def test_engine_status_keys() -> None:
    st = pdf_engine.engine_status()
    assert set(st) == {"binary_ready", "bundle_warmed"}
    assert all(isinstance(v, bool) for v in st.values())


def test_tectonic_path_uses_path_when_present(monkeypatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda _name: "/usr/bin/tectonic")
    assert str(pdf_engine.tectonic_path()) == "/usr/bin/tectonic"
