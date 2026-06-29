"""lablog como aplicación de escritorio nativa, portable y offline.

Arranca el motor FastAPI (que ya sirve la UI compilada de ``ui/dist``) en un
hilo en segundo plano sobre ``127.0.0.1`` y abre una ventana nativa del sistema
operativo con :mod:`webview` (pywebview). No usa el navegador ni la red: todo el
JavaScript, CSS, fuentes y KaTeX vienen empaquetados en el bundle.

Uso::

    lablog app            # tras `npm run build` en ui/
    python -m lablog.desktop

Requiere el extra ``desktop`` (``uv sync --extra desktop``) y que exista la UI
compilada en ``ui/dist``.
"""

from __future__ import annotations

import socket
import threading
import urllib.error
import urllib.request
from time import monotonic, sleep

from lablog.config import ui_dist_dir


def _dist_ready() -> bool:
    return (ui_dist_dir() / "index.html").exists()


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_until_ready(url: str, timeout: float = 20.0) -> bool:
    deadline = monotonic() + timeout
    while monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            sleep(0.05)
    return False


def _start_server(port: int) -> threading.Thread:
    import uvicorn

    from lablog.api import app

    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    # Los manejadores de señales de uvicorn solo funcionan en el hilo principal.
    server.install_signal_handlers = lambda: None  # type: ignore[attr-defined]
    thread = threading.Thread(target=server.run, daemon=True, name="lablog-engine")
    thread.start()
    return thread


def run(width: int = 1280, height: int = 820) -> None:
    """Lanza lablog como ventana de escritorio. Bloquea hasta cerrarla."""
    if not _dist_ready():
        raise SystemExit(
            "No se encontró la UI compilada en 'ui/dist'.\n"
            "Compílala primero:\n\n    cd ui && npm install && npm run build\n"
        )

    try:
        import webview  # noqa: PLC0415  (import perezoso: extra 'desktop')
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Falta pywebview. Instálalo con:\n\n    uv sync --extra desktop\n"
        ) from exc

    port = _free_port()
    _start_server(port)

    url = f"http://127.0.0.1:{port}/"
    if not _wait_until_ready(f"{url}api/v1/health"):
        raise SystemExit("El motor no respondió a tiempo.")

    webview.create_window(
        "lablog",
        url=url,
        width=width,
        height=height,
        min_size=(900, 600),
    )
    # El hilo del motor es daemon: muere al cerrarse la ventana.
    webview.start()


if __name__ == "__main__":
    run()
