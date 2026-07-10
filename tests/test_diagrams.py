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
    parse_lablog_preset_id,
    replace_or_append_diagram,
)
from lablog.diagrams.expand import parse_lablog_params

client = TestClient(app)


def test_catalog_has_core_presets() -> None:
    ids = {p.preset_id for p in list_presets()}
    assert "rc_series_charge" in ids
    assert "voltage_divider" in ids
    assert "mass_spring_damper" in ids
    assert "qed_moller" in ids
    assert "rlc_series_step" in ids
    assert "second_order_step" in ids
    assert "wheatstone" in ids
    assert "pi_controller" in ids


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
    assert body["diagram_presets"] >= 8
    assert "version" in body


def test_wheatstone_balance_and_highlight_lines() -> None:
    preset = get_preset("wheatstone")
    assert preset is not None
    out = expand_preset(preset, {"R1": 1000, "R2": 1000, "R3": 1000, "R4": 1000, "Vex": 5})
    assert "circuitikz" in out["latex"]
    # lablog-param lines deben tener highlight.line resuelto
    by_id = {p["id"]: p for p in out["param_specs"]}
    assert by_id["R1"]["highlight"]["line"] is not None
    assert by_id["R1"]["highlight"]["line"] >= 1
    sim = expand_simulation(preset, out["params"])
    assert "equilibrio" in sim["source"] or "Vg" in sim["source"]

    pi = get_preset("pi_controller")
    assert pi is not None
    pi_out = expand_preset(pi, {"Kp": 2, "Ki": 1, "K": 1, "tau": 0.5})
    assert "tikzpicture" in pi_out["latex"]
    assert pi_out["has_simulation"] is True


def test_rlc_and_second_order_expand() -> None:
    rlc = get_preset("rlc_series_step")
    assert rlc is not None
    out = expand_preset(rlc, {"R": 50, "L": 1e-3, "C": 1e-6, "V0": 12})
    assert "circuitikz" in out["latex"]
    assert "lablog-diagram: preset=rlc_series_step" in out["latex"]
    assert out["params"]["R"] == 50
    sim = expand_simulation(rlc, out["params"])
    assert "zeta" in sim["source"] or "ζ" in sim["source"] or "wn" in sim["source"]

    so = get_preset("second_order_step")
    assert so is not None
    so_out = expand_preset(so, {"wn": 3, "zeta": 0.2, "K": 2})
    assert "tikzpicture" in so_out["latex"]
    assert so_out["params"]["zeta"] == 0.2
    so_sim = expand_simulation(so, so_out["params"])
    assert "LABLOG_PARAMS" in so_sim["source"]


def test_parse_preset_id_and_replace_preserves_tail() -> None:
    preset = get_preset("rc_series_charge")
    assert preset is not None
    block = expand_preset(preset)["latex"]
    doc = f"% intro\n\n{block}\n\nTexto del lab que no debe borrarse.\n"
    assert parse_lablog_preset_id(doc) == "rc_series_charge"

    new_block = expand_preset(preset, {"R": 470})["latex"]
    updated = replace_or_append_diagram(doc, new_block)
    assert "Texto del lab que no debe borrarse" in updated
    assert "% intro" in updated
    assert "lablog-param: R=470" in updated or "R=470" in updated
    # append path
    plain = "Solo texto."
    appended = replace_or_append_diagram(plain, new_block)
    assert appended.startswith("Solo texto.")
    assert "lablog-diagram" in appended


def test_api_apply_diagram() -> None:
    r = client.post("/api/v1/diagrams/presets/rc_series_charge/expand", json={})
    assert r.status_code == 200
    latex = r.json()["latex"]
    doc = f"Prefacio.\n\n{latex}\n\nEpilogo.\n"

    r = client.post(
        "/api/v1/diagrams/apply",
        json={"latex": doc, "params": {"R": 2200, "C": 2e-6}},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["preset_id"] == "rc_series_charge"
    assert "document_latex" in body
    assert "Prefacio" in body["document_latex"]
    assert "Epilogo" in body["document_latex"]
    assert body["params"]["R"] == 2200
    assert "lablog-param: R=2200" in body["document_latex"]

    r = client.post("/api/v1/diagrams/apply", json={"latex": "sin diagrama"})
    assert r.status_code == 422
