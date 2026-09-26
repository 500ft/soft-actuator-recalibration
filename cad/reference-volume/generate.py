"""Known-volume reference chamber for calibrating the volumetric drive.

Why this part exists. `docs/CAD_ITEMS.md` states the problem plainly: "Syringe displacement is not
automatically actual chamber volume." Every P-V loop this project would ever measure depends on knowing
the volume actually delivered, and nothing verifies that today. This is a rigid cavity of exactly the
volume the simulator assumes, against which the drive can be checked.

What it is NOT. It is not a specimen and not a mold. `docs/CAD_PLAN.md` forbids treating new mold
development as authorised, and no released specimen geometry exists in this repository to reuse, so none
is modelled here.

Provenance. Every dimension comes from `parameters.csv`, which classifies each one. Three are sourced
from the simulator's own declared constants; the rest are provisional or unresolved and are labelled so.
The cavity length is *solved*, never chosen: it is whatever makes the internal volume equal
``SLSParams.V0``, and the geometry check at the end of this script enforces that on the built solid.

Runs headless and writes STEP, STL and a JSON check report. No dialogs, no prompts.
"""

from __future__ import annotations

import csv
import json
import math
import os
import sys

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("CAD_OUT", os.path.join(HERE, "build"))


def load_params(path):
    out = {}
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            out[row["name"]] = row
    return out


def main():
    p = load_params(os.path.join(HERE, "parameters.csv"))
    V_target_m3 = float(p["target_cavity_volume"]["value"])
    V_target_mm3 = V_target_m3 * 1e9
    bore = float(p["bore_diameter"]["value"])
    wall = float(p["wall_thickness"]["value"])
    cap = float(p["end_cap_thickness"]["value"])

    # The one derived dimension: solve length so the cavity holds exactly the simulator's V0.
    r = bore / 2.0
    length = V_target_mm3 / (math.pi * r * r)

    outer_r = r + wall
    total_len = length + 2 * cap

    body = cq.Workplane("XY").circle(outer_r).extrude(total_len)
    cavity = cq.Workplane("XY").workplane(offset=cap).circle(r).extrude(length)
    part = body.cut(cavity)

    # A port so the cavity can actually be connected. Bored through the top cap into the cavity.
    port_r = 2.5 / 2.0          # PROVISIONAL: clearance for an M5 boss; see parameters.csv
    port = (cq.Workplane("XY").workplane(offset=total_len - cap)
            .circle(port_r).extrude(cap))
    part = part.cut(port)

    os.makedirs(OUT, exist_ok=True)
    step_path = os.path.join(OUT, "reference_volume.step")
    stl_path = os.path.join(OUT, "reference_volume.stl")
    cq.exporters.export(part, step_path)
    cq.exporters.export(part, stl_path)

    # --- geometry acceptance check -----------------------------------------------------------------
    # The part is only correct if the cavity it encloses is the volume the simulator assumes. Measure it
    # on the built solid rather than trusting the arithmetic: cavity = bounding solid minus the part.
    solid_v = part.val().Volume()
    envelope_v = math.pi * outer_r * outer_r * total_len
    measured_cavity = envelope_v - solid_v - (math.pi * port_r * port_r * cap)
    rel_err = abs(measured_cavity - V_target_mm3) / V_target_mm3

    # Hoop stress at the design pressure, thin-wall. Reported to show what actually governs the wall.
    P_mpa = float(p["design_pressure"]["value"]) / 1e6
    hoop = P_mpa * r / wall
    allowable = float(p["material_allowable_stress"]["value"])
    sf_required = float(p["safety_factor"]["value"])
    margin = (allowable / sf_required) / hoop if hoop > 0 else float("inf")

    report = {
        "part": "reference_volume",
        "purpose": "calibrate the volumetric drive against a known cavity volume",
        "derived": {"cavity_length_mm": round(length, 4), "outer_radius_mm": outer_r,
                    "total_length_mm": round(total_len, 4)},
        "acceptance": {
            "criterion": "enclosed cavity volume equals SLSParams.V0",
            "target_mm3": V_target_mm3,
            "measured_mm3": round(measured_cavity, 3),
            "relative_error": rel_err,
            "tolerance": 1e-3,
            "pass": bool(rel_err < 1e-3),
        },
        "hoop_stress_check": {
            "note": ("Reported to show the wall is NOT stress-governed. At this pressure the thickness is "
                     "set by what can be manufactured as a sealed part, which is an honest conclusion, "
                     "not a margin to spend."),
            "design_pressure_MPa": P_mpa,
            "hoop_stress_MPa": round(hoop, 5),
            "allowable_MPa_PROVISIONAL": allowable,
            "safety_factor_required": sf_required,
            "margin_vs_derated_allowable": round(margin, 1),
            "caveat": "material_allowable_stress is UNRESOLVED; this margin is indicative only.",
        },
        "unresolved_inputs": [r["name"] for r in load_params(
            os.path.join(HERE, "parameters.csv")).values() if r["status"] == "UNRESOLVED"],
        "exports": {"step": os.path.basename(step_path), "stl": os.path.basename(stl_path)},
    }
    with open(os.path.join(OUT, "geometry_check.json"), "w") as fh:
        json.dump(report, fh, indent=2)

    print(json.dumps(report, indent=2))
    if not report["acceptance"]["pass"]:
        print("GEOMETRY CHECK FAILED", file=sys.stderr)
        return 1
    print("\nGEOMETRY CHECK PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
