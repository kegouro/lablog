"""Presets de diagramas: expand, clamp, API."""

from __future__ import annotations

from fastapi.testclient import TestClient

from lablog.api import app
from lablog.diagrams import (
    clamp_params,
    colorize_named_component,
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
    assert "half_wave_rectifier" in ids
    assert "thin_lens" in ids
    assert "rc_lowpass" in ids
    assert "noninverting_opamp" in ids


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
    assert body["diagram_presets"] >= 12
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


def test_list_presets_sorted_by_category() -> None:
    ordered = list_presets()
    assert len(ordered) >= 12
    # circuitos antes que particulas en el orden canónico
    idx = {p.preset_id: i for i, p in enumerate(ordered)}
    assert idx["rc_series_charge"] < idx["qed_moller"]
    assert ordered[idx["rc_lowpass"]].category == "circuitos"


def test_half_wave_and_thin_lens() -> None:
    hwr = get_preset("half_wave_rectifier")
    assert hwr is not None
    out = expand_preset(hwr, {"Vpeak": 12, "f": 60, "Rload": 2200, "C": 47e-6})
    assert "circuitikz" in out["latex"]
    assert "D*" in out["latex"] or "D" in out["latex"]
    sim = expand_simulation(hwr, out["params"])
    assert "ripple" in sim["source"] or "vo" in sim["source"]

    lens = get_preset("thin_lens")
    assert lens is not None
    # do = 0.3, f = 0.1 → di = 0.15, m = -0.5
    lout = expand_preset(lens, {"f": 0.1, "do": 0.3})
    assert "tikzpicture" in lout["latex"]
    assert abs(lout["params"]["di"] - 0.15) < 1e-9
    assert abs(lout["params"]["m"] - (-0.5)) < 1e-9
    assert "0.15" in lout["latex"] or "di" in lout["latex"]
    lsim = expand_simulation(lens, {"f": 0.1, "do": 0.3})
    assert "di=" in lsim["source"] or "1.0 / f" in lsim["source"]


def test_tikz_color_highlight_and_pyspice_source() -> None:
    raw = r"\draw (0,0) to[R, R=$1k$, name=R1] (1,0);"
    colored = colorize_named_component(raw, "R1", "orange")
    assert "color=orange,name=R1" in colored.replace(" ", "")

    # color= de un componente anterior no bloquea al siguiente en la misma línea
    multi = r"\draw (0,0) to[R, color=red, name=R2] (1,0) to[R, name=R1] (2,0);"
    multi_c = colorize_named_component(multi, "R1", "orange")
    assert "color=orange,name=R1" in multi_c.replace(" ", "")
    assert "color=red,name=R2" in multi_c.replace(" ", "") or "color=red, name=R2" in multi_c

    preset = get_preset("rc_series_charge")
    assert preset is not None
    out = expand_preset(preset, highlight_param="R")
    assert "color=orange" in out["latex"] or "color=orange" in out["latex"].replace(" ", "")
    assert "lablog-highlight: R" in out["latex"]
    assert out.get("supports_pyspice") is True

    sim = expand_simulation(preset, prefer_pyspice=True)
    assert sim["backend"] == "pyspice"
    assert "PySpice" in sim["source"] or "numpy_fallback" in sim["source"]

    rlc = get_preset("rlc_series_step")
    assert rlc is not None
    rlc_sim = expand_simulation(rlc, prefer_pyspice=True)
    assert rlc_sim["backend"] == "pyspice"
    assert "RLC" in rlc_sim["source"] or "rlc" in rlc_sim["source"].lower()
    assert "numpy_fallback" in rlc_sim["source"]

    hwr = get_preset("half_wave_rectifier")
    assert hwr is not None
    hwr_sim = expand_simulation(hwr, prefer_pyspice=True)
    assert hwr_sim["backend"] == "pyspice"
    assert "half" in hwr_sim["source"].lower() or "rectifier" in hwr_sim["source"].lower()

    r = client.post(
        "/api/v1/diagrams/presets/rc_series_charge/expand",
        json={"highlight_param": "C"},
    )
    assert r.status_code == 200
    assert "lablog-highlight: C" in r.json()["latex"]


def test_rc_lowpass_and_opamp() -> None:
    lp = get_preset("rc_lowpass")
    assert lp is not None
    out = expand_preset(lp, {"R": 2200, "C": 100e-9})
    assert "circuitikz" in out["latex"]
    sim = expand_simulation(lp, out["params"])
    assert "fc" in sim["source"] and "logspace" in sim["source"]

    oa = get_preset("noninverting_opamp")
    assert oa is not None
    oout = expand_preset(oa, {"Rf": 20_000, "Rg": 1000})
    assert "op amp" in oout["latex"]
    osim = expand_simulation(oa, oout["params"])
    assert "Ganancia" in osim["source"] or "G =" in osim["source"]


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
