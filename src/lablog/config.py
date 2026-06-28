"""Configuración central de lablog.

Los valores se pueden sobreescribir con variables de entorno (ver `.env.example`).
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Configuración mutable solo en inicialización."""

    def __init__(self) -> None:
        self.data_dir = Path(
            os.getenv("LABLOG_DATA_DIR", Path.home() / ".lablog")
        ).expanduser().resolve()
        self.host = os.getenv("LABLOG_HOST", "127.0.0.1")
        self.port = int(os.getenv("LABLOG_PORT", "8000"))

        _cors = os.getenv(
            "LABLOG_CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        )
        self.cors_origins = [origin.strip() for origin in _cors.split(",") if origin.strip()]
        self.cors_credentials = os.getenv("LABLOG_CORS_CREDENTIALS", "true").lower() in {
            "1",
            "true",
            "yes",
        }
        self.site_dir = Path(
            os.getenv("LABLOG_SITE_DIR", self.data_dir / "site")
        ).expanduser().resolve()

    @property
    def event_dir(self) -> Path:
        return self.data_dir / "events"

    @property
    def vault_dir(self) -> Path:
        return self.data_dir / "vault"

    @property
    def figures_dir(self) -> Path:
        return self.data_dir / "figures"


settings = Settings()
