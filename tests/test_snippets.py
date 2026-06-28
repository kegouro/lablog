"""Tests del catálogo de snippets parametrizados."""

from __future__ import annotations

from lablog.snippets import Parameter, Snippet, find_snippet, render_snippet


def test_render_snippet() -> None:
    snippet = Snippet(
        id="line_plot",
        name="Line plot",
        category="matplotlib",
        description="Test line plot",
        template="plt.plot([{x0}, {x1}], [{y0}, {y1}])",
        parameters=[
            Parameter(name="x0", default=0, min=-10, max=10, step=1, description="X inicial"),
            Parameter(name="x1", default=1, min=-10, max=10, step=1, description="X final"),
            Parameter(name="y0", default=0, min=-10, max=10, step=1, description="Y inicial"),
            Parameter(name="y1", default=1, min=-10, max=10, step=1, description="Y final"),
        ],
    )
    code = render_snippet(snippet, {"x0": 0, "x1": 2, "y0": 0, "y1": 4})
    assert code == "plt.plot([0, 2], [0, 4])"


def test_find_snippet() -> None:
    snippet = find_snippet("line_plot")
    assert snippet is not None
    assert snippet.category == "matplotlib"


def test_find_snippet_missing() -> None:
    assert find_snippet("no_existe") is None


def test_catalog_has_parameters() -> None:
    for snippet in Snippet.catalog():
        assert snippet.parameters
        for param in snippet.parameters:
            assert param.description
