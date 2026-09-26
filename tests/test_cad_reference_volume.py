"""The reference volume chamber must stay bound to the constant it exists to embody.

If SLSParams.V0 ever changes, the built part silently stops being a reference for anything. This test
fails in that case, which is the whole point of a code-CAD link.
"""
import csv
import json
import pathlib

import pytest

from sim.plant import NetworkParams, SLSParams

CAD = pathlib.Path(__file__).resolve().parents[1] / "cad" / "reference-volume"


def _params():
    with open(CAD / "parameters.csv", newline="") as fh:
        return {r["name"]: r for r in csv.DictReader(fh)}


def test_the_target_volume_is_the_simulators_own_V0():
    p = _params()
    assert float(p["target_cavity_volume"]["value"]) == SLSParams().V0, (
        "the reference chamber no longer matches SLSParams.V0, so it references nothing")
    assert float(p["design_pressure"]["value"]) == NetworkParams().P_s


def test_every_parameter_declares_its_provenance():
    allowed = {"sourced", "provisional", "derived", "imposed"}
    for name, r in _params().items():
        assert r["provenance"] in allowed, f"{name} has provenance {r['provenance']!r}"
        assert r["status"], f"{name} has no evidence status"
        if r["status"] == "UNRESOLVED":
            assert "TODO" in r["note"], f"{name} is unresolved but says nothing about how to resolve it"


def test_the_built_geometry_passed_its_acceptance_check():
    report = CAD / "build" / "geometry_check.json"
    if not report.exists():
        pytest.skip("part not built in this checkout; run cad/reference-volume/generate.py on the CAD host")
    r = json.loads(report.read_text())
    a = r["acceptance"]
    assert a["pass"] is True
    assert a["target_mm3"] == pytest.approx(SLSParams().V0 * 1e9), (
        "the recorded build targeted a different volume than the simulator declares today")
    assert a["relative_error"] < a["tolerance"]
