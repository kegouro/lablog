"""Proyección del estado de una página a partir de eventos."""

from __future__ import annotations

from typing import Any

from lablog.ast_nodes import CellNode, DocumentNode, MathNode, TextNode
from lablog.events import Event


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
                self.ast.children = [TextNode(text=latex)]

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
                self._update_cell_output(event.payload)

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

    def _update_cell_output(self, payload: dict[str, Any]) -> None:
        """Actualiza el output de una celda ejecutada."""
        cell_id = payload.get("cell_id")
        for child in self.ast.children:
            if isinstance(child, CellNode) and child.cell_id == cell_id:
                child.output = payload.get("output")
                child.figure_path = payload.get("figure_path")
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
        """Reubica una celda a un nuevo índice dentro de la lista de celdas."""
        cell_id = payload.get("cell_id")
        new_index = payload.get("new_index", 0)
        cells = [child for child in self.ast.children if isinstance(child, CellNode)]
        other = [child for child in self.ast.children if not isinstance(child, CellNode)]
        try:
            current = next(child for child in cells if child.cell_id == cell_id)
        except StopIteration:
            return
        cells.remove(current)
        new_index = max(0, min(new_index, len(cells)))
        cells.insert(new_index, current)
        self.ast.children = other + cells


def project(page_id: str, events: list[Event]) -> PageProjection:
    """Reconstruye la proyección de una página a partir de sus eventos."""
    projection = PageProjection(page_id)
    for event in events:
        projection.apply(event)
    return projection
