"""Presets de diagramas parametrizados (Circuitikz, TikZ, …) y generación de sim."""

from lablog.diagrams.catalog import get_preset, list_presets
from lablog.diagrams.expand import clamp_params, expand_preset, expand_simulation
from lablog.diagrams.models import DiagramPreset, ParamSpec

__all__ = [
    "DiagramPreset",
    "ParamSpec",
    "clamp_params",
    "expand_preset",
    "expand_simulation",
    "get_preset",
    "list_presets",
]
