"""Contrato de motores STT (speech-to-text).

Diseño:
- Protocolo pequeño y estable: cualquier motor gratis/local/futuro se enchufa aquí.
- El backend nunca importa proveedores de pago; solo engines locales.
- ``available()`` es barato (no carga modelos).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class TranscriptResult:
    """Resultado normalizado de un motor STT."""

    text: str
    engine: str
    language: str | None = None
    duration_s: float | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class EngineInfo:
    """Metadatos públicos de un motor (para GET /voice/engines)."""

    id: str
    label: str
    kind: str  # "local" | "client"
    available: bool
    description: str = ""
    requires_extra: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@runtime_checkable
class SttEngine(Protocol):
    """Motor de transcripción.

    Implementaciones deben ser thread-safe en ``transcribe`` o proteger el
    modelo con un lock (Whisper lo hace).
    """

    @property
    def id(self) -> str: ...

    @property
    def label(self) -> str: ...

    @property
    def kind(self) -> str: ...

    @property
    def description(self) -> str: ...

    def available(self) -> bool:
        """True si el motor puede usarse sin instalar nada más ahora."""
        ...

    def info(self) -> EngineInfo:
        """Snapshot para la API."""
        ...

    def transcribe(
        self,
        audio: bytes,
        *,
        filename: str = "audio.wav",
        language: str | None = None,
    ) -> TranscriptResult:
        """Transcribe bytes de audio a texto plano.

        ``filename`` solo sirve de pista de formato (extensión).
        """
        ...
