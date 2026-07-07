"""Nodos del AST de un documento LaTeX de lablog."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


@dataclass
class TextNode:
    text: str
    type: Literal["text"] = "text"


@dataclass
class MathNode:
    latex: str
    mode: Literal["inline", "display"] = "inline"
    type: Literal["math"] = "math"


@dataclass
class CellNode:
    cell_id: str
    language: str
    source: str
    output: str | None = None
    figure_path: str | None = None
    type: Literal["cell"] = "cell"
    status: Literal["idle", "running", "ok", "error"] = "idle"


@dataclass
class SectionNode:
    title: str
    children: list[Node] = field(default_factory=list)
    type: Literal["section"] = "section"


@dataclass
class DocumentNode:
    title: str = ""
    children: list[Node] = field(default_factory=list)
    type: Literal["document"] = "document"


Node = TextNode | MathNode | CellNode | SectionNode | DocumentNode


def node_to_json(node: Node) -> dict[str, Any]:
    """Serializa un nodo AST a dict JSON-safe de forma determinista."""
    return asdict(node)
