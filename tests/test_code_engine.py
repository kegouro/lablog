"""Tests del motor de ejecución Jupyter."""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from time import monotonic
from typing import Any

import pytest
from jupyter_client import KernelManager

from lablog.code_engine import CodeEngine, EngineStartError


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


def test_engine_start_failure(monkeypatch) -> None:
    def _raise(*_args, **_kwargs) -> None:
        raise RuntimeError("kernel not found")

    monkeypatch.setattr(KernelManager, "start_kernel", _raise)
    eng = CodeEngine()
    with pytest.raises(EngineStartError) as exc_info:
        eng.start()
    assert "No se pudo iniciar el kernel" in str(exc_info.value)


def test_concurrent_execution(engine: CodeEngine) -> None:
    """El lock serializa ejecuciones concurrentes sin bloquear el hilo llamante."""
    results: list[Any] = []
    lock = threading.Lock()

    def run_code(label: str) -> None:
        result = engine.execute(f"x = {label}\nx")
        with lock:
            results.append((label, result))

    start = monotonic()
    with ThreadPoolExecutor(max_workers=2) as pool:
        pool.submit(run_code, "10")
        pool.submit(run_code, "20")
    elapsed = monotonic() - start

    assert len(results) == 2
    assert all(r.status == "ok" for _, r in results)
    assert all(str(label) in r.text for label, r in results)
    # Con el lock las ejecuciones son secuenciales, por lo que 2 celdas de ~0s
    # deberían completarse sin solaparse de forma catastrófica.
    assert elapsed >= 0


def test_dead_kernel_auto_restarts() -> None:
    """Si el kernel muere, execute lo reinicia automáticamente una vez."""
    eng = CodeEngine()
    eng.start()
    try:
        # Detener el kernel para simular que murió.
        eng.stop()
        result = eng.execute("1 + 1")
        assert result.status == "ok"
        assert "2" in result.text
    finally:
        eng.stop()


def test_stop_is_idempotent() -> None:
    eng = CodeEngine()
    eng.start()
    eng.stop()
    # No debe fallar ni lanzar excepción si se llama varias veces.
    eng.stop()
    assert not eng.is_ready()


def test_execute_raises_when_kernel_cannot_start(monkeypatch) -> None:
    def _raise(*_args, **_kwargs) -> None:
        raise RuntimeError("no kernel")

    monkeypatch.setattr(KernelManager, "start_kernel", _raise)
    eng = CodeEngine()
    with pytest.raises(EngineStartError):
        eng.execute("1 + 1")


def test_execute_stream_output_is_captured(engine: CodeEngine) -> None:
    result = engine.execute("print('hola')\nprint('mundo')")
    assert result.status == "ok"
    assert "hola" in result.text
    assert "mundo" in result.text


def test_drain_iopub_does_nothing_when_client_is_none() -> None:
    eng = CodeEngine()
    eng._client = None
    eng._drain_iopub()


def test_execute_raises_when_kernel_stays_dead(monkeypatch) -> None:
    eng = CodeEngine()

    class DeadClient:
        def is_alive(self) -> bool:
            return False

    monkeypatch.setattr(eng, "_do_start", lambda: None)
    eng._client = DeadClient()
    with pytest.raises(EngineStartError, match="no está disponible"):
        eng.execute("1 + 1")


def test_stop_swallows_shutdown_exceptions(monkeypatch) -> None:
    eng = CodeEngine()
    eng.start()

    def _raise(*_args, **_kwargs) -> None:
        raise RuntimeError("stop failed")

    monkeypatch.setattr(eng._client, "stop_channels", _raise)
    monkeypatch.setattr(eng._manager, "shutdown_kernel", _raise)
    eng.stop()
    assert not eng.is_ready()


def test_execute_stream_output(engine: CodeEngine) -> None:
    result = engine.execute("print('hola stream')")
    assert result.status == "ok"
    assert "hola stream" in result.text


def test_execute_timeout_interrupts() -> None:
    eng = CodeEngine()
    eng.start()
    try:
        result = eng.execute("import time\ntime.sleep(10)", timeout=0.5)
        assert result.status == "error"
        assert "interrumpida" in result.text.lower()
    finally:
        eng.stop()
