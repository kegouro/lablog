"""Tests de tabla de símbolos LaTeX y favoritos."""

from __future__ import annotations

from pathlib import Path

from lablog.latex_symbols import FavoritesStore, find_symbol, list_symbols


def test_list_symbols() -> None:
    symbols = list_symbols()
    assert len(symbols) > 0
    assert symbols[0].latex.startswith("\\")


def test_find_symbol() -> None:
    sym = find_symbol("alpha")
    assert sym is not None
    assert sym.latex == "\\alpha"


def test_find_symbol_missing() -> None:
    assert find_symbol("no_existe") is None


def test_favorites_roundtrip(tmp_path: Path) -> None:
    store = FavoritesStore(tmp_path / "favs.json")
    assert store.list_favorites() == []

    store.add("alpha")
    store.add("beta")
    assert store.list_favorites() == ["alpha", "beta"]

    store.remove("alpha")
    assert store.list_favorites() == ["beta"]

    store2 = FavoritesStore(tmp_path / "favs.json")
    assert store2.list_favorites() == ["beta"]
