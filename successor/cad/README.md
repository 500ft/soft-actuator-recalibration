# McKibben successor concepts

The original eighteen register entries and the added double-clevis coupler have parametric CadQuery models. All
nineteen exports pass STEP round-trip checks and independent volume checks. The geometry re-drive report records
the exercised dimensions, positions and clearance constraints. This remains CONCEPT / HOLD; no pressure rating or
fabrication release is claimed.

## Load path and interfaces

The lower, ported fitting connects to the fixed frame end. The closed fitting connects through a double-clevis
coupler to the S2M, then through the adjustment fork and fine-thread rod to the upper plate. Four pins keep this
chain on one axis. `SAR-0110` was added because the supplied register had no part connecting the muscle's upper
knuckle eye to the cell's lower knuckle eye. Its interfaces use the existing pin and bearing sizes.

[geometry.json](geometry.json) holds each input and its evidence. [build_concepts.py](build_concepts.py) builds the
solids; [oracle.py](oracle.py) provides independent algebra and quadrature without importing CadQuery. The rod-end,
cell, fitting, braid and rail models are reference envelopes. Rail stiffness uses the published section area,
rather than the solid bounding-envelope area. No mass or inertia of a purchased item is inferred from that envelope.

The free latex and braid are shown in the muscle assembly. Their deformed seal zones are omitted until the actual
materials and crimp procedure are selected. Standalone stock envelopes carry the derived cut length. The ferrules
show their uncrimped condition. The fitting's fluid passage ends before the blind mechanical thread; the result
records their minimum remaining web.

The S2M cable has a separate conservative routing keep-out, checked against the rails and excluded from physical
part volume. Its bend exceeds the vendor minimum. Actual cable diameter, slack loop, strain relief and cable force
still require inspection. The pressure hose must be clamped to the fixed frame so its force bypasses the load cell.

## Reference chamber and pressure hold

The chamber's main cavity length is solved from the selected volume and bore area. Cap-port volume is reported
separately. The end flanges and blind cap-bolt pattern are a new machined concept; they do not reuse the closed
study's printed chamber. Standard seal grooves remain omitted at P3. The symbolic pneumatic routing diagram shows
the functional order and tube-length allowances; the CAD tube runs are not a connected pressure assembly.

O12 confirms bladder and braid. O13 confirms pressure, cell and mechanical interfaces. O14b supplies the Mac sensor
audit; the pressure-sensor part and tee port stay omitted. O15 confirms the chamber volume. The committed P1–P7
qualification plan is required before pressure-part detail, and owner approval is still required before physical
work. Decision 0004 authorizes none of that work.

The [draft P1-P7 plan](../docs/pressure_qualification_plan.md) records the prescribed tests and the inputs still
missing. Its pull-out requirement exceeds the proposed cell rating and operating-frame load case; use a separately
qualified load train or obtain a reviewed redesign. The plan remains on HOLD and supplies no test authorization.

## Executed checks and limitations

The output `04_ANALYSIS/successor-concepts/result.json` holds the force and stiffness screen, the named clearances,
the cavity and port volumes, and the input hash. The original and current HBK displacement values are retained as
separate cases: the current [HBK B03594 datasheet](https://www.hbm.com/fileadmin/mediapool/hbmdoc/technical/B03594.pdf)
changed the 1 kN rated displacement from the older sheet used by the handoff. O13 must identify the applicable cell.

The stiffness screen includes the two rails, simple plate-strip bending, the adjustment rod and the load cell.
Clevis, joint, thread and support compliance remain outside that estimate. SAR-SIM-02 and a dial-gauge load test
are the checks on the frame. SAR-SIM-01, pull-out and hydrostatic qualification apply to the fittings. SAR-SIM-03,
hydrostatic proof, leak testing and gravimetric volume measurement apply to the chamber. No physical tests were run.

STEP round-trip metrics include volume, bounds, centroid and principal volume moments. These quantities describe the
concept solids. The re-drive checks compare every modeled shape with its independent volume expression after
changing each geometric input. They also detect position changes through centroid and inertia changes. Native
SOLIDWORKS is optional for this track under handoff 04; the CadQuery source remains the editable model.

## Regeneration

```powershell
python successor/cad/build_concepts.py --output <Desktop-repo-folder>
python successor/cad/redrive_concepts.py --output <analysis-folder>/redrive_result.json
python successor/cad/render_review.py --output <analysis-folder>
python -m unittest discover -s successor/tests -v
```

Code is MIT licensed. CAD, drawings and documents are CC BY 4.0 under decision 0004. The closed study and its tests
remain unchanged.
