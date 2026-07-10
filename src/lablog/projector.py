"""Proyección del estado de una página a partir de eventos."""

from __future__ import annotations

from typing import Any, Literal

from lablog.ast_nodes import CellNode, DocumentNode, MathNode, TextNode
from lablog.events import Event
from lablog.latex_ast import parse_latex


class PageProjection:
    """Estado actual de una página proyectado desde eventos."""

    def __init__(self, page_id: str) -> None:
        self.page_id = page_id
        self.title: str = ""
        self.project_id: str | None = None
        self.deleted: bool = False
        self.ast = DocumentNode()
        self.vault_files: list[dict[str, Any]] = []

    def apply(self, event: Event) -> None:
        """Aplica un evento al estado."""
        match event.type:
            case "page_created":
                self.title = event.payload.get("title", "")
                self.project_id = event.payload.get("project_id")
                self.ast.title = self.title

            case "page_metadata_updated":
                if "title" in event.payload:
                    self.title = event.payload["title"]
                    self.ast.title = self.title
                if "project_id" in event.payload:
                    self.project_id = event.payload["project_id"]

            case "page_deleted":
                self.deleted = True

            case "text_inserted":
                pos = event.payload.get("position", 0)
                text = event.payload.get("text", "")
                self._insert_text(pos, text)

            case "text_deleted":
                pos = event.payload.get("position", 0)
                length = event.payload.get("length", 0)
                self._delete_text(pos, length)

            case "document_replaced":
                latex = event.payload.get("latex", "")
                self.ast = parse_latex(latex)

            case "math_inserted":
                latex = event.payload.get("latex", "")
                mode = event.payload.get("mode", "inline")
                self.ast.children.append(MathNode(latex=latex, mode=mode))

            case "cell_inserted":
                self.ast.children.append(
                    CellNode(
                        cell_id=event.payload.get("cell_id", ""),
                        language=event.payload.get("language", ""),
                        source=event.payload.get("source", ""),
                    )
                )

            case "cell_updated":
                self._update_cell_source(event.payload)

            case "cell_executed":
                self._update_cell_output(event.payload, status="ok")

            case "execution_failed":
                tb = event.payload.get("traceback") or []
                ename = event.payload.get("ename", "")
                evalue = event.payload.get("evalue", "")
                output = "\n".join(tb) if tb else f"{ename}: {evalue}".strip(": ")
                self._update_cell_output(
                    {
                        "cell_id": event.payload["cell_id"],
                        "output": output,
                        "figure_path": None,
                    },
                    status="error",
                )

            case "cell_deleted":
                self._delete_cell(event.payload)

            case "cell_moved":
                self._move_cell(event.payload)

            case "vault_file_added":
                self.vault_files.append(event.payload)

    def _insert_text(self, position: int, text: str) -> None:
        """Inserta texto plano en el documento."""
        if not self.ast.children or not isinstance(self.ast.children[-1], TextNode):
            self.ast.children.append(TextNode(text=""))

        last = self.ast.children[-1]
        assert isinstance(last, TextNode)
        current = last.text
        pos = len(current) if position < 0 else max(0, min(position, len(current)))
        last.text = current[:pos] + text + current[pos:]

    def _delete_text(self, position: int, length: int) -> None:
        """Elimina texto plano del documento."""
        if not self.ast.children or not isinstance(self.ast.children[-1], TextNode):
            return

        last = self.ast.children[-1]
        assert isinstance(last, TextNode)
        current = last.text
        pos = max(0, min(position, len(current)))
        end = min(pos + length, len(current))
        last.text = current[:pos] + current[end:]

    def _update_cell_output(
        self,
        payload: dict[str, Any],
        status: Literal["idle", "running", "ok", "error"] = "ok",
    ) -> None:
        """Actualiza el output y estado de una celda ejecutada."""
        cell_id = payload.get("cell_id")
        for child in self.ast.children:
            if isinstance(child, CellNode) and child.cell_id == cell_id:
                child.output = payload.get("output")
                child.figure_path = payload.get("figure_path")
                child.status = status
                break

    def _update_cell_source(self, payload: dict[str, Any]) -> None:
        """Actualiza el código fuente o lenguaje de una celda."""
        cell_id = payload.get("cell_id")
        for child in self.ast.children:
            if isinstance(child, CellNode) and child.cell_id == cell_id:
                if payload.get("language") is not None:
                    child.language = payload["language"]
                if payload.get("source") is not None:
                    child.source = payload["source"]
                break

    def _delete_cell(self, payload: dict[str, Any]) -> None:
        """Elimina una celda del AST."""
        cell_id = payload.get("cell_id")
        self.ast.children = [
            child for child in self.ast.children
            if not (isinstance(child, CellNode) and child.cell_id == cell_id)
        ]

    def _move_cell(self, payload: dict[str, Any]) -> None:
        """Reordena una celda entre las demás celdas, sin alterar el resto.

        Mantiene los nodos de texto en su posición: solo se reordenan las celdas
        ocupando los mismos "slots" que ya ocupaban en el documento.
        """
        cell_id = payload.get("cell_id")
        new_index = payload.get("new_index", 0)
        children = self.ast.children
        slots: list[int] = []
        cells: list[CellNode] = []
        for i, c in enumerate(children):
            if isinstance(c, CellNode):
                slots.append(i)
                cells.append(c)
        try:
            current = next(j for j, c in enumerate(cells) if c.cell_id == cell_id)
        except StopIteration:
            return
        new_index = max(0, min(new_index, len(cells) - 1))
        moved = cells.pop(current)
        cells.insert(new_index, moved)
        for slot, cell in zip(slots, cells, strict=True):
            children[slot] = cell


def project(page_id: str, events: list[Event]) -> PageProjection:
    """Reconstruye la proyección de una página a partir de sus eventos."""
    projection = PageProjection(page_id)
    for event in events:
        projection.apply(event)
    return projection
