"""Modelos de presets de diagramas (fuente de verdad de parámetros)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class HighlightSpec(BaseModel):
    """Dónde resaltar el parámetro en editor / esquema / celda."""

    tikz: str | None = None
    latex: str | None = None
    line: int | None = None
    color: Literal["amber", "sky", "rose", "emerald", "violet"] = "amber"


class ParamSpec(BaseModel):
    id: str
    label: str
    description: str
    value: float
    unit: str = ""
    min: float | None = None
    max: float | None = None
    step: float | None = None
    scale: Literal["linear", "log"] = "linear"
    precision: int = 4
    highlight: HighlightSpec = Field(default_factory=HighlightSpec)
    derived: bool = False

    @model_validator(mode="after")
    def _range_ok(self) -> ParamSpec:
        if self.min is not None and self.max is not None and self.min >= self.max:
            msg = f"param {self.id}: min must be < max"
            raise ValueError(msg)
        if self.scale == "log" and self.min is not None and self.min <= 0:
            msg = f"param {self.id}: log scale requires min > 0"
            raise ValueError(msg)
        return self


class DiagramPreset(BaseModel):
    preset_id: str
    version: int = 1
    kind: Literal[
        "circuitikz",
        "feynman_tikz",
        "block_diagram",
        "mechanics",
        "optics",
        "generic_tikz",
    ]
    title: str
    summary: str
    category: str = "general"
    tags: list[str] = Field(default_factory=list)
    params: list[ParamSpec]
    tikz_template: str
    sim_backend: Literal["none", "numpy_ode", "scipy_signal"] = "none"
    sim_template: str | None = None

    @field_validator("params")
    @classmethod
    def _unique_ids(cls, params: list[ParamSpec]) -> list[ParamSpec]:
        ids = [p.id for p in params]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate param ids")
        if len(params) > 12:
            raise ValueError("too many params (max 12)")
        return params

    def defaults(self) -> dict[str, float]:
        return {p.id: p.value for p in self.params}

    def param_map(self) -> dict[str, ParamSpec]:
        return {p.id: p for p in self.params}

    def summary_dict(self) -> dict[str, Any]:
        return {
            "preset_id": self.preset_id,
            "version": self.version,
            "kind": self.kind,
            "title": self.title,
            "summary": self.summary,
            "category": self.category,
            "tags": self.tags,
            "param_ids": [p.id for p in self.params],
            "has_simulation": bool(self.sim_template and self.sim_backend != "none"),
        }
