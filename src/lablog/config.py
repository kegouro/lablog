"""Configuración central de lablog.

Los valores se pueden sobreescribir con variables de entorno (ver `.env.example`).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def ui_dist_dir() -> Path:
    """Ruta a la UI compilada (``ui/dist``), también dentro de un binario.

    En un bundle de PyInstaller los datos viven bajo ``sys._MEIPASS``; en
    desarrollo, en la raíz del repositorio.
    """
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / "ui" / "dist"
    return Path(__file__).resolve().parents[2] / "ui" / "dist"


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
