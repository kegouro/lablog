from lablog.completions import suggest
from lablog.pdf_engine import expand_inputs
from lablog.templates import get_template, list_templates


def test_list_templates_includes_physics():
    ids = {t.id for t in list_templates()}
    assert "lab-report-physics" in ids
    assert "em-notes" in ids
    assert get_template("missing") is None
    assert get_template("em-notes") is not None


def test_suggest_filters_commands():
    items = suggest("sec")
    labels = [i.label for i in items]
    assert any("section" in lab for lab in labels)


def test_suggest_environments():
    items = suggest("align")
    assert any(i.kind == "environment" and "align" in i.label for i in items)


def test_expand_inputs_page_key():
    child = "Child content $x$"
    parent = "Intro\n\\input{page:abc}\nOutro"
    out = expand_inputs(parent, resolve={"page:abc": child, "abc": child})
    assert "Child content" in out
    assert "\\input" not in out


def test_expand_inputs_detects_cycle():
    a = "A \\input{page:b}"
    b = "B \\input{page:a}"
    out = expand_inputs(a, resolve={"page:a": a, "page:b": b, "a": a, "b": b})
    assert "cyclic" in out
