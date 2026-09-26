# Reference volume chamber — design notes

A rigid cavity of exactly the volume the simulator assumes, for calibrating the volumetric drive.

**Built 2026-09-26** on the CAD host with CadQuery 2.8.0, headless, no dialogs.
Artifacts: `build/reference_volume.step`, `.stl`, `geometry_check.json`. Parameters and their provenance:
[`parameters.csv`](parameters.csv). Generator: [`generate.py`](generate.py).

## Why this part, and why not a specimen

`docs/CAD_ITEMS.md` states the problem this solves: **"Syringe displacement is not automatically actual
chamber volume."** Every pressure–volume loop this project would measure depends on knowing the volume
actually delivered, and nothing verifies that. A rigid cavity of known volume is the instrument that
closes it.

It is deliberately **not** a specimen or a mold. `docs/CAD_PLAN.md` requires a one-specimen pilot to reuse
*existing released* geometry and says to "stop and rescope" if reuse is unavailable. No specimen or mold
geometry exists anywhere in this repository, so none was designed. That constraint is respected, not
worked around.

---

## Decision: cavity length

**Question.** How long must the bore be for the chamber to hold the volume the simulator assumes?

**Known inputs**
- Target cavity volume `V0` = 5.0 × 10⁻⁶ m³ = 5000 mm³ — *sourced*, `SLSParams.V0` in `sim/plant.py`
- Bore diameter `D` = 16.0 mm — **provisional**, chosen for machinability; any value is admissible
  provided the derived length holds the volume

**Model.** A right circular cylinder, so `V = π r² L`, therefore `L = V / (π r²)`.

**Substitution.** `L = 5000 mm³ / (π × (8.0 mm)²) = 5000 / 201.06 mm² = 24.868 mm`

**Dimensional check.** mm³ / mm² = mm. ✓

**Result.** Cavity length **24.868 mm**, giving a part of Ø22.0 mm × 32.868 mm overall.

**Decision.** The length is *solved*, never chosen. If the bore diameter changes the length follows, and
the volume stays at `V0`. That is what makes the part a reference rather than an approximation.

**Validation.** The generator measures the enclosed cavity on the built solid — envelope minus part
volume minus the port bore — and asserts it against `V0`. Measured 5000.0 mm³, relative error
1.8 × 10⁻¹⁶. **Status: geometry verified in CAD. Not yet manufactured or measured.**

---

## Decision: wall thickness

**Question.** How thick must the wall be to contain the design pressure?

**Known inputs**
- Design pressure `P` = 80 kPa gauge = 0.080 MPa — *sourced*, `NetworkParams.P_s` in `sim/plant.py`.
  The probe itself operates at 40 kPa (`P_HOLD_PA`), so the supply pressure is the worst credible case.
- Internal radius `r` = 8.0 mm — from the bore above

**Assumptions**
- Thin-wall hoop stress applies. Valid while `r/t ≳ 10`; here `r/t = 2.7`, so the thin-wall form is
  *conservative* — it overestimates hoop stress for a thick wall. Acceptable given the margin below.
- Material allowable `σ_allow` = 30 MPa — **UNRESOLVED**. A placeholder order of magnitude for PLA. A real
  allowable must come from the print material datasheet *and* be derated for layer adhesion and print
  orientation, which for a pressure-containing printed part is the governing weakness.
- Safety factor SF = 4 — *imposed*, justified by property scatter in printed parts compounded with an
  allowable that is itself unverified.

**Model.** Thin-wall hoop stress `σ = P r / t`.

**Substitution.** `σ = 0.080 MPa × 8.0 mm / 3.0 mm = 0.213 MPa`

**Dimensional check.** MPa × mm / mm = MPa. ✓

**Result.** Hoop stress **0.213 MPa** against a derated allowable of 30/4 = 7.5 MPa. **Margin ≈ 35×.**

**Sensitivity.** Even if the true allowable were ten times worse than the placeholder — 3 MPa, which would
be a very poor print — the margin is still 3.5×. The conclusion is insensitive to the unresolved input.

**Decision.** Wall thickness **3.0 mm**, and the governing constraint is **manufacturing, not stress**. At
80 kPa this part is nowhere near structurally limited; 3 mm is the practical minimum for a sealed printed
pressure part. That is the honest finding, and the 35× margin is not spare capacity to spend elsewhere —
it is a statement that strength was never the binding constraint.

**Validation.** None performed. A leak-and-hold test at design pressure is the test that matters, and it
is a leak test, not a strength test. **Status: predicted only.**

---

## What is unresolved

| input | why it matters | how to resolve |
|---|---|---|
| `port_thread` | The part cannot connect to anything without matching the drive's fitting | Measure the fitting on the existing volumetric drive. M5×0.8 is a common pneumatic boss but **nothing in this repository specifies it** |
| `material_allowable_stress` | Sets the real margin | Material datasheet, derated for layer adhesion and print orientation |
| end-cap thickness | Carries bending, not hoop stress; currently by inspection | Check as a flat circular plate if the part is ever used above the design pressure |

## What this part does not establish

- It does not validate the simulator. It makes one number in the simulator physically checkable.
- It is not evidence about any actuator. It is a calibration artifact.
- The geometry check confirms the **model** encloses `V0`. A manufactured part's true volume must be
  measured — by gravimetric fill, which is the intended use — and will differ by the print tolerance.
