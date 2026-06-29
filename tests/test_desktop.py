"""Smoke de los ayudantes de la app de escritorio (sin abrir ventana)."""

from __future__ import annotations

from lablog import desktop


def test_free_port_in_range() -> None:
    port = desktop._free_port()
    assert 1024 < port < 65536


def test_dist_ready_returns_bool() -> None:
    # No exige que exista el build; solo que el chequeo sea booleano y no lance.
    assert isinstance(desktop._dist_ready(), bool)


def test_wait_until_ready_times_out_fast() -> None:
    # Puerto cerrado: debe devolver False sin colgarse.
    assert desktop._wait_until_ready("http://127.0.0.1:9/api/v1/health", timeout=0.3) is False
