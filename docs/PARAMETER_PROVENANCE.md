# Parameter provenance and evidence status

Every consequential number in this repository, what kind of number it is, and what the repository can
actually show about where it came from.

A number is **consequential** if changing it could change a study verdict, a reported figure, a pass/fail
outcome, or a claim in [`docs/results.md`](results.md). Incidental numbers — plot sizes, array shapes,
loop bookkeeping — are deliberately out of scope. Keeping this register small is what keeps it read.

This document does not duplicate the analyses. Each row points at the place where the number is used and
argued. It also does not restate [`literature/claim-ledger.md`](../literature/claim-ledger.md), which maps
*claims* to *literature*; this register maps *numbers* to *evidence*.

---

## How to read a row

Two independent axes. Confusing them is the failure this register exists to prevent.

### Provenance — what kind of number it is

| class | meaning |
|---|---|
| **imposed criterion** | A bar the project committed to in advance. Not discovered; chosen, and defensible only by argument. |
| **measured input** | A value someone physically measured. In this repository that means measured *by a cited publication*, never by this project. |
| **sourced assumption** | A value taken from an external source, with the source named and its applicability stated. |
| **derived result** | Computed from other declared numbers. Inherits every weakness of its inputs. |
| **selected model value** | A generator or design parameter this project chose to define its synthetic world. |
| **simulation result** | An output of running this repository's code. |
| **provisional estimate** | A placeholder standing in for evidence that does not exist yet. Must say what would replace it. |

### Evidence status — how well supported it is

| status | meaning |
|---|---|
| **hardware-validated** | Checked against physical measurement of the system being modelled. |
| **literature-anchored** | Matches a value measured elsewhere, on a stated material, geometry and protocol. |
| **internally consistent** | Reproduces this repository's own committed outputs. Says nothing about reality. |
| **unverified** | Chosen, and not checked against anything. |
| **known-unrepresentative** | Deliberately not a best estimate — a stress case or a convenience value. |

> **Nothing in this repository is hardware-validated.** No physical actuator has been built, cycled or
> measured for this project. Every simulation result is a statement about the generator, and the generator
> is a set of selected model values. `hardware-validated` appears in the table above only so that its
> absence everywhere below is visible rather than implied.

### The rule this register enforces

**A simulation result is not a measurement.** A calculated value, a fitted value, a value recovered from
synthetic data, and an assumed coefficient are all *predictions about a model*. None of them is evidence
about a physical soft actuator. Wherever this repository states a number, the sentence must survive the
question "measured on what, by whom?" — and if the honest answer is "nothing, it came out of the
generator", the sentence must say so.

---

## The register

`origin` quotes or paraphrases the repository's own justification. **"none stated"** means the audit found
no sentence anywhere naming where the number came from — it is not a judgement that the value is wrong.

### Acceptance criteria and verdict rules

These decide what counts as success. Every one is an **imposed criterion**: chosen, and defensible only by
argument.

| value | where | origin | status |
|---|---|---|---|
| `PASS_RMSE` 0.10 life | `pipeline/schedules.py:28` | "two Study A grid steps" (`studyB-identifiability.md:41`) | unverified — derived from a grid this project also chose |
| `PASS_COUNT` 8 of 10 | `pipeline/schedules.py:33` | **"no precedent in the literature — it is a defensible preregistered choice, not a field standard"** (`literature/gaps.md:59`) | unverified, and self-flagged |
| `MATERIAL_REDUCTION_LIFE` 0.05 | `pipeline/schedules.py:34` | "Descriptive rule fixed before the run" (`schedules.py:112`) — freezes *when*, not *why* | unverified |
| Study A criterion i, ratio ≥ 2 | `studyA-preregistration.md:72` | none stated | unverified |
| Study A degeneracy cut 1e-6 | `studyA-preregistration.md:71` | none stated | unverified |
| Study B σ_u ≤ 0.10 | `studyB-identifiability.md:39` | "two Study A grid steps" | unverified |
| chi-square(1) cut 1.92 | `pipeline/identifiability.py` profile threshold | 95% asymptotic likelihood-ratio cut, Raue et al. 2009 | **sourced but uncalibrated here** — see below |

> The 1.92 cut is the clearest example of why the two axes are separate. Its *provenance* is excellent: a
> standard statistic with a named source. Its *status* is not: the cut is asymptotic, and this problem has
> a nonlinear feature map, bounded nuisance parameters, infeasible regions, an estimated and strongly
> correlated covariance, and near-zero information across the plateau. Until `PV-CRIT-09` runs a coverage
> check it is **a diagnostic scale, not a calibrated confidence interval**. A good citation does not make a
> number appropriate to the problem it is being used on.

### Dispersion magnitudes

Every row has a table entry at `studyA-preregistration.md:30-43`, but most of those entries read "assumed"
or "magnitude assumed" rather than naming a measurement.

| value | where | origin | status |
|---|---|---|---|
| `RUPTURE_CV` 0.30 | `pipeline/dispersion.py:50` | cites Torzini 2024 "as its order of magnitude", but the preregistration itself records that **Torzini measures 0.039 and 0.061, and the highest located measurement is 0.175** (`studyA-preregistration.md:102-105`) | **known-unrepresentative** — an assumed stress case, explicitly not a best estimate |
| CV 0.05 / 0.15 sweep points | `scripts/run_dispersion_audit.py` | Torzini 2024, Du 2025 — small cohorts of specific materials and protocols | literature-anchored, and not a measurement of this project's apparatus |
| `EA_OVER_R` 40e3 / 8.314 | `pipeline/dispersion.py:24` | labelled "assumed" in the code | unverified |
| temperature range 15–35 °C | `pipeline/dispersion.py:69` | none stated | unverified |
| `SEED` 20260916 | `pipeline/dispersion.py:21` | none stated (a date) | not consequential to conclusions, but fixes every cohort |

### The fatigue law — what "life" means in every study

All **selected model values**. `sim/fatigue.py:3-5` states the file-level position: these are "deliberately
transparent, deterministic assumptions … not calibrated fatigue predictions for a physical actuator."

| value | where | origin | status |
|---|---|---|---|
| `rupture_cycles` 3500 | `sim/fatigue.py:25` | "repo fixture" | unverified |
| `fatigue_exponent` 2.0 | `sim/fatigue.py:36` | "magnitude assumed", Mars & Fatemi | unverified |
| `acceleration_onset_fraction` 0.70 | `sim/fatigue.py:26` | none stated | unverified |
| `mullins_amplitude` 0.04 | `sim/fatigue.py:27` | none stated | unverified |
| `mullins_cycles_tau` 3.0 | `sim/fatigue.py:28` | none stated | unverified |
| `mullins_permanent_fraction` 0.30 | `sim/fatigue.py:29` | the *split concept* is cited to Liao 2021; the **value** is not | unverified |
| `slow_fatigue_amplitude` 0.04 | `sim/fatigue.py:31` | none stated | unverified |
| `accelerating_fatigue_amplitude` 0.08 | `sim/fatigue.py:32` | none stated | unverified |
| `terminal_leak_multiplier` 20.0 | `sim/fatigue.py:35` | none stated | unverified |
| leak growth exponent `z**2` | `sim/fatigue.py:118` | none stated | unverified |
| `recovery_tau_s` 86400 | `sim/fatigue.py:30` | "order-of-magnitude protocol choice" | unverified |

> `acceleration_onset_fraction` deserves singling out. It sets the regime boundary that Study B's entire
> finding is *about*, and it is one of the two parameters aliased with the life coordinate. It has no
> stated origin. Every "pre-onset" and "post-onset" statement in this repository is conditional on a number
> nobody wrote a reason for.

### Plant, network, sensors, kinematics

| group | where | origin | status |
|---|---|---|---|
| `SLSParams.k1`, `NetworkParams.P_s`, `R_s`, `R_v`, `n_chambers` | `sim/plant.py` | Gate 0: "PneuNet-class … Dragon Skin grippers", **order of magnitude only** | unverified as calibration; an order-of-magnitude anchor is not a fit |
| `SLSParams.k2` 2.0e10, `tau` 0.10 s, `V0` 5.0e-6 m³ | `sim/plant.py:54-56` | none stated | unverified |
| `NetworkParams.R_l` 8.0e9, `C_m` 5.0e-12 | `sim/plant.py:78-79` | none stated | unverified |
| all ten `SensorParams` defaults | `sim/sensors.py:22-31` | none stated | unverified |
| `PCCParams` `length_m`, `kappa_gain`, `plane_azimuth_rad` | `sim/kinematics.py:52-54` | none stated; file says "modelling choices for a synthetic study" | unverified |

### The probe — a design this project would have to build

All **selected design values**, none with a stated origin.

| value | where | note |
|---|---|---|
| `P_HOLD_PA` 40 kPa | `pipeline/identifiability.py:21` | hold pressure for the decay probe |
| decay window 2.0 s, 2001 points | `pipeline/identifiability.py:22` | **also the reason `decay_half_life_s` is undefined at low leak** — the decay never halves inside the window on 54 of 192 bound-box corners |
| residual sample time 0.3 s | `pipeline/identifiability.py:46` | |
| `amp_frac` 0.1 | `pipeline/identifiability.py:31` | loop amplitude as a fraction of `V0` |
| loop frequencies 1 Hz, 4 Hz | `pipeline/identifiability.py:36-37` | `literature/gaps.md` item 4 questions rate artefacts at 2 Hz; the same concern applies here |
| `n_rep` 24 | `pipeline/identifiability.py:66` | replicates behind every noise covariance |
| C2 cadences 250 / 125 / 500 cycles | `pipeline/schedules.py:37-39` | preregistered, magnitudes unsourced |

### Numerical settings

**P2, but not harmless.** A covariance was inverted at condition number 1.7 × 10²⁶ for weeks before anyone
looked; the NaN it produced was mistaken for a flat likelihood. Integrator tolerances in `sim/plant.py` and
`sim/network.py`, finite-difference `rel_step` 1e-3, rank tolerances 1e-9 and 1e-10, `INFEASIBLE_PENALTY`
1e15, optimiser `maxiter` 200 and restart factors 0.5 / 1.6 all have no stated origin. None has a
convergence study. Tracked as `PV-PROV-04`.

---

## Traceability index

Where to find the reasoning behind each major decision. Links, not duplicated mathematics.

| decision | argued in | evidence | canonical inputs | status |
|---|---|---|---|---|
| Can the cohort pose a cross-unit question? | [Study A preregistration](specs/observability-program/studyA-preregistration.md) | [`evidence/observability-2026-09-16/`](../evidence/observability-2026-09-16/README.md) | dispersion table, prereg:30-43 | A-FAIL original, A-PASS amended; **both retained** |
| Is the life coordinate identifiable? | [Study B preregistration](specs/observability-program/studyB-identifiability.md) | [`evidence/studyB-structural-correction-2026-09-25/`](../evidence/studyB-structural-correction-2026-09-25/README.md) | `PARAMS`, `FEATURES`, nuisance box | B-PASS; post-onset precision **withdrawn**, identifiability itself **open** |
| Does the estimator transfer to unseen units? | [Study C preregistration](specs/observability-program/studyC-transfer.md) | [`evidence/next-five-2026-09-16/`](../evidence/next-five-2026-09-16/README.md) | `PASS_RMSE`, `PASS_COUNT` | C-FAIL |
| Why does it fail? | [Study C failure analysis](specs/observability-program/studyC-failure-analysis.md) | [`evidence/weekly-research-2026-09-21/`](../evidence/weekly-research-2026-09-21/README.md) | channel-muting definitions | "a clock corrected by pressure" |
| Is the assumed dispersion defensible? | [`literature/gaps.md`](../literature/gaps.md) item 1 | [`evidence/dispersion-audit-2026-09-23/`](../evidence/dispersion-audit-2026-09-23/README.md) | `RUPTURE_CV` | C-FAIL survives 0.05/0.15/0.30 for **opposite** reasons |
| Does probe placement change what is estimable? | [Study C2 preregistration](specs/observability-program/studyC2-preregistration.md) | none — **not executed** | `SCHEDULES`, `ARMS` | frozen, awaiting `PV-CRIT-03` |

## What would move a row from unverified to supported

Nothing in this register becomes `hardware-validated` without physical measurement, and this project has
none. Short of that:

- A **selected model value** becomes defensible when a sensitivity run shows which conclusions depend on
  it and over what range they survive. That is an argument, not a measurement, and it should be labelled
  as one.
- An **imposed criterion** becomes defensible when the consequence of the bar is stated: what passes, what
  fails, and what a reader should conclude from each. `PASS_COUNT` 8 has this; the Study A ratio of 2 does
  not.
- A **sourced assumption** becomes defensible when the source's material, geometry and protocol are stated
  alongside the number, so a reader can judge transfer. The dispersion rows mostly lack this.

Outstanding work: `PV-PROV-01` to `PV-PROV-04` in [`SPRINT_TASKS.csv`](SPRINT_TASKS.csv).
