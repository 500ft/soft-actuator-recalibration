# Engineering audit — provenance of consequential numbers

**Date:** 2026-09-25 · **Scope:** documentation and analysis only. No generator parameter, verdict rule,
acceptance threshold or committed study output was changed by this audit.

The question this audit asks of every consequential number: *can a technically literate reader see why
this value, and what would change if it were wrong?* It does not ask whether the values are correct.

A number is **consequential** if changing it could move a study verdict, a reported figure, or a pass/fail
outcome. The classification scheme and the full register are in
[`PARAMETER_PROVENANCE.md`](PARAMETER_PROVENANCE.md); this file records what the audit *found*.

---

## Headline

**The repository is unusually honest at the level of claims and unusually silent at the level of numbers.**

Its preregistration discipline is genuinely strong — four dated freeze statements, amendments recorded
rather than applied in place, both the original and amended Study A verdicts retained in the artifact, and
explicit guardrails forbidding a failing cell from being rerun with a new seed. Three numbers are flagged
*by the repository itself* as unsupported. That is better than most research code.

Underneath that, **the synthetic world the whole programme runs on is almost entirely unsourced.** Of the
consequential constants in `sim/` and `pipeline/`, the overwhelming majority have no sentence anywhere
saying where the number came from. The generator's fatigue law, its plant, its sensor noise model and its
entire probe design are chosen values presented without rationale.

This is not dishonesty. Four modules carry blanket disclaimers — `sim/fatigue.py:3-5` says the laws "are
deliberately transparent, deterministic assumptions … not calibrated fatigue predictions for a physical
actuator", and `sim/kinematics.py:8-9` calls its values "modelling choices for a synthetic study". Those
disclaimers are correct and they matter. But a file-level disclaimer tells a reader that *nothing* here is
calibrated; it does not tell them **why 0.70 and not 0.60**, or which of the forty unsourced numbers the
conclusions are actually sensitive to. That distinction is the gap.

The practical consequence is already on the record. The Study B resolution claim was withdrawn three times
in ten days — as "structurally aliased", then "±0.05 life", then "±0.21 life" — and each time the cause
was the same: **a number whose origin was a bound on the calculation rather than a property of the data.**
A rank test, then a grid edge, then a nuisance box. A provenance register is the standing defence against
a fourth.

---

## Findings

Priority reflects consequence if wrong, not effort to fix.

| # | Finding | Where | Priority | Corrective action |
|---|---|---|--:|---|
| 1 | **The same physical quantity is hard-coded in several places with no single source of truth.** Sensor sigmas (50 Pa, 10 Pa, 1e-9 m³) are re-declared in `pipeline/identifiability.py:56-57` instead of read from `SensorParams`. `3500.0` and `0.30` appear independently in three files. `80_000.0` appears in two. | `pipeline/identifiability.py:56-57`, `sim/fatigue.py:25`, `pipeline/dispersion.py:44,56`, `pipeline/validation.py:26,53-54`, `sim/plant.py:75` | **P0** | Give each a canonical definition and import it. Values must not change: verify by regenerating every committed output and diffing. Filed as `PV-PROV-01`. |
| 2 | **Three numbers are self-flagged as unsupported but are not linked from where they are used.** `RUPTURE_CV` 0.30 ("above every measured value found"), `PASS_COUNT` 8 ("no precedent in the literature"), the 1.92 chi-square cut ("a diagnostic scale and not a calibrated confidence interval"). A reader meeting them in code sees a bare number. | `pipeline/dispersion.py:50`, `pipeline/schedules.py:33`, `pipeline/identifiability.py` profile threshold | **P0** | Cross-reference each to its caveat at the point of definition. Done in this pass. |
| 3 | **The fatigue law's shape parameters have no stated origin.** Acceleration onset 0.70, Mullins amplitude 0.04 / τ 3.0 / permanent fraction 0.30, slow amplitude 0.04, accelerating amplitude 0.08, terminal leak 20.0, and the `z**2` leak growth exponent. These define what "life" *means* in every study. | `sim/fatigue.py:26-36`, `:118` | **P1** | Record each as a selected model value with its role and the sensitivity that has or has not been run. Two already have partial sourcing (`fatigue_exponent` 2.0, `rupture_cycles` 3500). |
| 4 | **The probe design is entirely unsourced, and it is a design the project would have to build.** Hold pressure 40 kPa, 2 s decay window, 0.3 s residual sample time, amplitude fraction 0.1, loop frequencies 1 Hz and 4 Hz, 24 replicates. | `pipeline/identifiability.py:21-22,31,36-37,46,66` | **P1** | Record as selected design values. Note that `literature/gaps.md` item 4 already questions the 2 Hz probe on rate-artefact grounds, which is the same concern one level down. |
| 5 | **The plant and sensor models are unsourced except at order of magnitude.** `SLSParams.k2`, `tau`, `V0`; `NetworkParams.R_l`, `C_m`; all ten `SensorParams` defaults; all three `PCCParams`. Gate 0 sources `k1`, `P_s`, `R_s`, `R_v` and `n_chambers` to "PneuNet-class … Dragon Skin grippers" at order of magnitude; the rest have nothing. | `sim/plant.py:54-56,78-79`, `sim/sensors.py:22-31`, `sim/kinematics.py:52-54` | **P1** | Record. Where a Gate-0 order-of-magnitude anchor exists, say so and say that it is an order of magnitude, not a calibration. |
| 6 | **Solver tolerances and numerical guards are unsourced.** Integrator rtol/atol and max_step in three modules, finite-difference `rel_step` 1e-3, rank tolerances 1e-9 / 1e-10, `INFEASIBLE_PENALTY` 1e15, optimiser `maxiter` 200 and restart factors 0.5 / 1.6. | `sim/plant.py:120,161-163`, `sim/network.py:71-121`, `pipeline/identifiability.py` various | **P2** | Lower consequence individually, but this class produced a real defect: a covariance was inverted at condition number 1.7e26 for weeks. Record the ones the results are sensitive to; a convergence study is the honest answer for the rest. |
| 7 | **The C2 schedule cadences have no stated magnitude rationale.** 250 / 125 / 500 cycles. They are frozen and preregistered, which fixes *when* they were chosen, not *why* those numbers. | `pipeline/schedules.py:37-39` | **P2** | Record as selected design values, preregistered, magnitude unsourced. |
| 8 | **No physical validation exists anywhere, and that should be stated once, centrally.** It is currently implied by scattered module disclaimers. | repository-wide | **P1** | Stated at the head of the provenance register. |

## What the audit did not find

Worth recording, because an audit that only lists faults misleads:

- **No fabricated measurement.** Every number labelled as measured traces to a cited publication, and the
  repository is consistent about never claiming its own hardware data.
- **No threshold relaxed to rescue a result.** Study C's bar is explicitly "not relaxed, reweighted or
  renegotiated for C2 under any outcome", and the dispersion audit states it leaves every committed verdict
  untouched.
- **No amendment applied in place.** Study A's withdrawn criterion iii is implemented as a flag that writes
  *both* verdicts, not as an edit to the original rule.
- **No silent revision of history.** The three withdrawn Study B figures are each recorded with what was
  wrong and why.

---

## Method and limits

Two read-only sweeps inventoried every module-level constant, dataclass default and in-function numeric
threshold in `sim/` and `pipeline/`, and every verdict rule, statistical threshold and design choice in
the observability-programme specifications and runners. Each was checked against the repository's own text
for a sentence naming the value's origin; a file-level disclaimer was not counted as an origin for a
specific number.

Limits of this audit:

- It reports **whether a number is justified in the repository**, not whether it is physically right. A
  sourced value can still be wrong for this actuator, and an unsourced value can be perfectly reasonable.
- It cannot recover original intent. Where a value's rationale was never written down, this audit records
  "no stated origin" rather than reconstructing a plausible one, which would be fabrication.
- Coverage is `sim/`, `pipeline/`, the observability-programme specs and the study runners. The older
  Phase A–D pipeline modules and the manuscript are inventoried only where the programme depends on them.
