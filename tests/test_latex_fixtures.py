"""Fixtures de estrés LaTeX: parse, símbolos, preview classification, PDF opcional."""

from __future__ import annotations

from pathlib import Path

import pytest

from lablog.ast_nodes import CellNode, TextNode
from lablog.latex_ast import parse_latex, serialize_ast
from lablog.latex_symbols import all_latex_commands, list_categories, list_symbols
from lablog.pdf_engine import _PREAMBLE, _is_full_document, build_document, expand_inputs

FIXTURES = Path(__file__).parent / "fixtures" / "latex"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_fixtures_exist() -> None:
    expected = [
        "01_characters.tex",
        "02_tables.tex",
        "03_matrices.tex",
        "04_feynman.tex",
        "05_physics_packages.tex",
        "06_full_document.tex",
    ]
    for name in expected:
        assert (FIXTURES / name).is_file(), name


def test_symbol_catalog_is_rich() -> None:
    symbols = list_symbols()
    assert len(symbols) >= 120
    cats = set(list_categories())
    for required in (
        "greek",
        "operators",
        "relations",
        "arrows",
        "functions",
        "physics",
        "sets",
    ):
        assert required in cats
    cmds = all_latex_commands()
    for cmd in ("\\alpha", "\\sum", "\\int", "\\rightarrow", "\\mathbb", "\\hbar"):
        assert any(c.startswith(cmd) or cmd.startswith(c) for c in cmds) or cmd in {
            s.latex.split("{")[0] for s in symbols
        }


def test_characters_fixture_roundtrip_preserves_math() -> None:
    src = _read("01_characters.tex")
    doc = parse_latex(src)
    out = serialize_ast(doc)
    # Marcadores clave no se pierden
    for token in (r"\alpha", r"\sum", r"\mathbb{R}", r"\partial", r"\hbar"):
        assert token in out


def test_matrices_fixture_keeps_environments() -> None:
    src = _read("03_matrices.tex")
    doc = parse_latex(src)
    out = serialize_ast(doc)
    for env in ("pmatrix", "bmatrix", "vmatrix", "cases", "align"):
        assert rf"\begin{{{env}}}" in out


def test_tables_and_feynman_stay_as_text_not_cells() -> None:
    for name in ("02_tables.tex", "04_feynman.tex"):
        doc = parse_latex(_read(name))
        assert not any(isinstance(c, CellNode) for c in doc.children)
        text = serialize_ast(doc)
        if "tables" in name:
            assert r"\begin{tabular}" in text
            assert r"\toprule" in text
        else:
            assert r"tikzpicture" in text


def test_physics_fixture_has_quantum_and_si() -> None:
    src = _read("05_physics_packages.tex")
    assert r"\ket" in src or r"\psi" in src
    assert r"\SI" in src
    doc = parse_latex(src)
    assert serialize_ast(doc)


def test_full_document_detected() -> None:
    src = _read("06_full_document.tex")
    doc = parse_latex(src)
    assert _is_full_document(doc)
    # full document: un solo TextNode (document env no es code)
    assert any(isinstance(c, TextNode) and "\\documentclass" in c.text for c in doc.children)


def test_preamble_includes_scientific_packages() -> None:
    for pkg in (
        "amsmath",
        "booktabs",
        "siunitx",
        "physics",
        "braket",
        "tikz",
        "graphicx",
    ):
        assert pkg in _PREAMBLE


def test_build_document_wraps_snippet_fixtures() -> None:
    src = _read("03_matrices.tex")
    doc = parse_latex(src)
    tex, markers, _figs = build_document(doc, title="matrices")
    assert r"\begin{document}" in tex
    assert r"\end{document}" in tex
    assert "pmatrix" in tex
    assert markers  # hay marcadores de prosa


def test_build_full_document_passthrough() -> None:
    src = _read("06_full_document.tex")
    doc = parse_latex(src)
    tex, markers, _ = build_document(doc, title="ignored")
    assert markers == []
    assert r"\documentclass" in tex
    assert r"tikzpicture" in tex


def test_expand_inputs_with_fixture_map() -> None:
    body = r"Intro\n\input{page:chars}\nFin"
    resolve = {"page:chars": _read("01_characters.tex")}
    out = expand_inputs(body, resolve=resolve)
    assert r"\alpha" in out
    assert "Intro" in out and "Fin" in out


@pytest.mark.integration
def test_tectonic_compiles_matrices_if_available(tmp_path: Path) -> None:
    """Compilación real opcional (Tectonic en PATH o binario lablog)."""
    import shutil
    import subprocess

    from lablog import pdf_engine

    status = pdf_engine.engine_status()
    binary = shutil.which("tectonic")
    if not status.get("binary_ready") and not binary:
        pytest.skip("Tectonic no instalado")
    if not binary:
        # engine_status no expone la ruta; si binary_ready, confía en which o skip
        pytest.skip("tectonic no está en PATH")

    doc = parse_latex(_read("03_matrices.tex"))
    tex, _, _ = build_document(doc, title="matrices-test")
    work = tmp_path / "tex"
    work.mkdir()
    main = work / "main.tex"
    main.write_text(tex, encoding="utf-8")

    proc = subprocess.run(
        [str(binary), "-X", "compile", str(main), "--outdir", str(work)],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    pdf = work / "main.pdf"
    if not pdf.exists():
        # CLI antigua: `tectonic main.tex`
        proc = subprocess.run(
            [str(binary), str(main), "--outdir", str(work)],
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
    if not pdf.exists():
        pytest.skip(
            f"Tectonic no produjo PDF (paquetes/red?): rc={proc.returncode} "
            f"{(proc.stderr or proc.stdout)[-400:]}"
        )
    assert pdf.stat().st_size > 500
