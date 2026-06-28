"""Nodos del AST de un documento LaTeX de lablog."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


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
