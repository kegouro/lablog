"""Presets de diagramas: expand, clamp, API."""

from __future__ import annotations

from fastapi.testclient import TestClient

from lablog.api import app
from lablog.diagrams import (
    clamp_params,
    expand_preset,
    expand_simulation,
    get_preset,
    list_presets,
)
from lablog.diagrams.expand import parse_lablog_params

client = TestClient(app)


def test_catalog_has_core_presets() -> None:
    ids = {p.preset_id for p in list_presets()}
    assert "rc_series_charge" in ids
    assert "voltage_divider" in ids
    assert "mass_spring_damper" in ids
    assert "qed_moller" in ids


def test_expand_rc_defaults() -> None:
    preset = get_preset("rc_series_charge")
    assert preset is not None
    out = expand_preset(preset)
    assert "circuitikz" in out["latex"]
    assert "lablog-diagram: preset=rc_series_charge" in out["latex"]
    assert out["params"]["R"] == 1000
    assert out["has_simulation"] is True
    parsed = parse_lablog_params(out["latex"])
    assert parsed["R"] == 1000
    assert parsed["C"] == 1e-6


def test_clamp_params_range() -> None:
    preset = get_preset("rc_series_charge")
    assert preset is not None
    out = clamp_params(preset, {"R": 1e12, "C": -1, "V0": 50})
    assert out["R"] == 1e6
    assert out["C"] == 1e-12  # min after invalid
    assert out["V0"] == 50


def test_simulation_source_contains_params_block() -> None:
    preset = get_preset("rc_series_charge")
    assert preset is not None
    sim = expand_simulation(preset, {"R": 2200, "C": 2e-6, "V0": 12})
    assert "LABLOG_PARAMS_START" in sim["source"]
    assert "R = 2200" in sim["source"] or "R = 2.2e" in sim["source"]
    assert "matplotlib" in sim["source"]


def test_feynman_has_no_simulation() -> None:
    preset = get_preset("qed_moller")
    assert preset is not None
    out = expand_preset(preset, {"spread": 2.0})
    assert "tikzpicture" in out["latex"]
    assert out["has_simulation"] is False


def test_api_list_and_expand() -> None:
    r = client.get("/api/v1/diagrams/presets")
    assert r.status_code == 200
    data = r.json()
    assert any(p["preset_id"] == "rc_series_charge" for p in data)

    r = client.post("/api/v1/diagrams/presets/rc_series_charge/expand", json={})
    assert r.status_code == 200
    body = r.json()
    assert "latex" in body and "circuitikz" in body["latex"]

    r = client.post(
        "/api/v1/diagrams/presets/rc_series_charge/simulate-source",
        json={"params": {"R": 500}},
    )
    assert r.status_code == 200
    assert "LABLOG_PARAMS" in r.json()["source"]


def test_api_unknown_preset() -> None:
    assert client.get("/api/v1/diagrams/presets/nope").status_code == 404


def test_health_reports_presets() -> None:
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["diagram_presets"] >= 4
    assert "version" in body
