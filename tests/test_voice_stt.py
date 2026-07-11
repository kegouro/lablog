"""Tests del registro STT modular (sin depender de faster-whisper)."""

from __future__ import annotations

import pytest

from lablog.voice.engines import (
    EngineInfo,
    TranscriptResult,
    get_engine,
    list_engines,
    register_engine,
    transcribe_audio,
    unregister_engine,
)
from lablog.voice.engines.registry import _ENGINES


class _FakeEngine:
    def __init__(self, eid: str = "fake", *, available: bool = True) -> None:
        self._id = eid
        self._available = available

    @property
    def id(self) -> str:
        return self._id

    @property
    def label(self) -> str:
        return f"Fake {self._id}"

    @property
    def kind(self) -> str:
        return "local"

    @property
    def description(self) -> str:
        return "motor de prueba"

    def available(self) -> bool:
        return self._available

    def info(self) -> EngineInfo:
        return EngineInfo(
            id=self.id,
            label=self.label,
            kind=self.kind,
            available=self.available(),
            description=self.description,
        )

    def transcribe(
        self,
        audio: bytes,
        *,
        filename: str = "audio.wav",
        language: str | None = None,
    ) -> TranscriptResult:
        return TranscriptResult(
            text=f"heard:{audio.decode('utf-8', errors='ignore')}",
            engine=self.id,
            language=language or "es",
        )


@pytest.fixture(autouse=True)
def _clean_registry() -> None:
    # No tocar whisper builtin: solo quitar fakes al final.
    yield
    for eid in list(_ENGINES):
        if eid.startswith("fake"):
            unregister_engine(eid)


def test_list_engines_includes_browser_and_whisper() -> None:
    ids = {e.id for e in list_engines()}
    assert "browser" in ids
    assert "whisper" in ids
    browser = next(e for e in list_engines() if e.id == "browser")
    assert browser.kind == "client"
    assert browser.available is True


def test_register_custom_engine() -> None:
    register_engine(_FakeEngine("fake-a"), replace=True)
    eng = get_engine("fake-a")
    assert eng.available()
    result = eng.transcribe(b"hola")
    assert result.text == "heard:hola"
    assert result.engine == "fake-a"


def test_transcribe_audio_uses_registered_engine() -> None:
    register_engine(_FakeEngine("fake-b"), replace=True)
    result = transcribe_audio(b"lab", engine_id="fake-b")
    assert "lab" in result.text


def test_browser_engine_not_on_server() -> None:
    with pytest.raises(RuntimeError, match="cliente"):
        get_engine("browser")


def test_whisper_unavailable_without_extra() -> None:
    whisper = get_engine("whisper")
    # En CI sin [voice] suele ser False; si está instalado, True.
    info = whisper.info()
    assert info.id == "whisper"
    assert info.kind == "local"
    if not info.available:
        assert info.requires_extra == "voice"
