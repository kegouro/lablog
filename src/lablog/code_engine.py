"""Motor de ejecución de celdas Jupyter para lablog."""

from __future__ import annotations

import contextlib
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar, Literal

from jupyter_client import KernelManager  # type: ignore[attr-defined]


class EngineStartError(RuntimeError):
    """El motor de ejecución no pudo iniciar o reiniciar el kernel."""


@dataclass
class ExecutionResult:
    status: Literal["ok", "error"]
    outputs: list[dict[str, Any]] = field(default_factory=list)
    figure_paths: list[str] = field(default_factory=list)
    text: str = ""


class CodeEngine:
    SUPPORTED_LANGUAGES: ClassVar[frozenset[str]] = frozenset({"python", "py"})

    def __init__(self, kernel_name: str = "python3") -> None:
        self.kernel_name = kernel_name
        self._manager: KernelManager | None = None
        self._client: Any = None
        self._lock = threading.Lock()

    def _do_start(self) -> None:
        """Inicia el kernel sin adquirir el lock (debe llamarse con lock)."""
        try:
            self._manager = KernelManager(kernel_name=self.kernel_name)
            self._manager.start_kernel()
            self._client = self._manager.client()
            self._client.start_channels()
            self._client.wait_for_ready(timeout=30)
            self._client.execute("import matplotlib; matplotlib.use('Agg')")
            self._drain_iopub()
        except Exception as exc:
            self._do_stop()
            raise EngineStartError(
                f"No se pudo iniciar el kernel '{self.kernel_name}'. "
                "Verifica que el entorno de ejecución esté instalado y disponible."
            ) from exc

    def _do_stop(self) -> None:
        """Detiene el kernel sin adquirir el lock (debe llamarse con lock)."""
        if self._client is not None:
            with contextlib.suppress(Exception):
                self._client.stop_channels()
            self._client = None
        if self._manager is not None:
            with contextlib.suppress(Exception):
                self._manager.shutdown_kernel(now=True)
            self._manager = None

    def start(self) -> None:
        with self._lock:
            self._do_start()

    def stop(self) -> None:
        with self._lock:
            self._do_stop()

    def is_ready(self) -> bool:
        return self._client is not None and self._client.is_alive()

    def _drain_iopub(self, timeout: float = 2.0) -> None:
        if not self._client:
            return
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                self._client.get_iopub_msg(timeout=0.1)
            except Exception:
                return

    def execute(
        self,
        code: str,
        figure_dir: Path | None = None,
        timeout: float = 30.0,
    ) -> ExecutionResult:
        with self._lock:
            if not self.is_ready():
                # Reinicio automático único si el kernel ha muerto.
                self._do_start()
            if not self.is_ready():
                raise EngineStartError("El kernel no está disponible tras intentar reiniciarlo.")

            if figure_dir:
                Path(figure_dir).mkdir(parents=True, exist_ok=True)

            msg_id = self._client.execute(code)
            outputs: list[dict[str, Any]] = []
            text_parts: list[str] = []
            error_parts: list[str] = []

            completed = self._collect_iopub(
                msg_id, timeout, outputs, text_parts, error_parts
            )

            if not completed:
                if self._manager is not None:
                    self._manager.interrupt_kernel()
                error_parts.append(
                    f"Ejecución interrumpida: superó el límite de {timeout:.0f}s."
                )

            status: Literal["ok", "error"] = "error" if error_parts else "ok"
            result_text = "".join(error_parts if error_parts else text_parts)

            figure_paths: list[str] = []
            if figure_dir and status == "ok":
                figure_paths = self._save_figures(figure_dir)

            return ExecutionResult(
                status=status,
                outputs=outputs,
                figure_paths=figure_paths,
                text=result_text,
            )

    def _collect_iopub(
        self,
        msg_id: str,
        timeout: float,
        outputs: list[dict[str, Any]],
        text_parts: list[str],
        error_parts: list[str],
    ) -> bool:
        """Recolecta salida hasta 'idle'. Devuelve True si terminó a tiempo."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                msg = self._client.get_iopub_msg(timeout=0.5)
            except Exception:
                continue

            if msg["parent_header"].get("msg_id") != msg_id:
                continue

            msg_type = msg["header"]["msg_type"]
            content = msg["content"]

            match msg_type:
                case "status":
                    if content["execution_state"] == "idle":
                        return True
                case "stream":
                    outputs.append(
                        {
                            "type": "stream",
                            "name": content["name"],
                            "text": content["text"],
                        }
                    )
                    text_parts.append(content["text"])
                case "execute_result":
                    data = content["data"]
                    outputs.append({"type": "execute_result", "data": data})
                    text_parts.append(data.get("text/plain", ""))
                case "display_data":
                    outputs.append({"type": "display_data", "data": content["data"]})
                case "error":
                    outputs.append(
                        {
                            "type": "error",
                            "ename": content["ename"],
                            "evalue": content["evalue"],
                        }
                    )
                    error_parts.append("\n".join(content["traceback"]))
        return False

    def _save_figures(self, figure_dir: Path) -> list[str]:
        save_code = f"""
import matplotlib.pyplot as plt
for i, num in enumerate(plt.get_fignums()):
    plt.figure(num).savefig({str(figure_dir)!r} + f"/fig_{{i}}.png", bbox_inches="tight")
plt.close("all")
"""
        msg_id = self._client.execute(save_code)
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            try:
                msg = self._client.get_iopub_msg(timeout=0.5)
            except Exception:
                continue
            if msg["parent_header"].get("msg_id") != msg_id:
                continue
            if (
                msg["header"]["msg_type"] == "status"
                and msg["content"].get("execution_state") == "idle"
            ):
                break
        return sorted(str(p) for p in Path(figure_dir).glob("fig_*.png"))
