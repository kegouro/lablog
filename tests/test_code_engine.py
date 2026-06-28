"""Tests del motor de ejecución Jupyter."""

from __future__ import annotations

import pytest

from lablog.code_engine import CodeEngine


@pytest.fixture(scope="session")
def engine() -> CodeEngine:
    eng = CodeEngine()
    eng.start()
    yield eng
    eng.stop()


def test_execute_simple_code(engine: CodeEngine) -> None:
    result = engine.execute("1 + 1")
    assert result.status == "ok"
    assert "2" in result.text


def test_execute_matplotlib_figure(engine: CodeEngine, tmp_path) -> None:
    code = """
import matplotlib.pyplot as plt
plt.figure()
plt.plot([1, 2, 3], [1, 4, 9])
plt.title('Test')
"""
    result = engine.execute(code, figure_dir=tmp_path)
    assert result.status == "ok"
    assert len(result.figure_paths) == 1


def test_execute_error(engine: CodeEngine) -> None:
    result = engine.execute("1 / 0")
    assert result.status == "error"
    assert "ZeroDivisionError" in result.text
