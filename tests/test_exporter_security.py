"""Seguridad del export HTML estático."""

from __future__ import annotations

from lablog.exporter import _inline, _safe_href


def test_safe_href_blocks_javascript() -> None:
    out = _safe_href("javascript:alert(1)", "click")
    assert "javascript" not in out.lower() or "href" not in out
    assert "click" in out


def test_safe_href_allows_https() -> None:
    out = _safe_href("https://example.com/a", "doc")
    assert 'href="https://example.com/a"' in out
    assert "doc" in out


def test_inline_escapes_href_attribute_quotes() -> None:
    # quote=True debe escapar " en la URL si llegara a permitirse.
    evil = r'\href{https://x.com/" onclick="alert(1)}{x}'
    out = _inline(evil)
    assert "onclick" not in out or "&quot;" in out
