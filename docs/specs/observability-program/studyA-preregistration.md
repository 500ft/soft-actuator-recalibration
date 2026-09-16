# Study A — break the invariance (preregistration)

Committed before the run; the evidence file records the commit that froze this text. Any change after the
run is an amendment with a dated rationale.

## Hypothesis and what can fail

H_A: with physically motivated between-unit dispersion of the degradation law and plant, the normalised
P-V loop-area indicator varies between units by more than its within-unit measurement noise, so that the
cross-unit question can be posed. **This study can fail.** If it fails, Studies C–E are not meaningful on
this generator and the program reports that.

Prediction recorded before running: dispersion of the *degradation law* (Mullins, fatigue amplitudes,
onset, exponent) breaks the invariance; dispersion of the *plant level* (k1, k2, τ, wall thickness,
temperature) does **not**, because young-normalisation cancels a constant scale and τ does not evolve
with life in this generator. The one-axis ablation tests this prediction.

## Generator change (minimal)

`FatigueParams.fatigue_exponent` (default 2.0) replaces the hard-coded square in the accelerating term:
`fatigue_accelerating = accelerating_fatigue_amplitude · z**fatigue_exponent`. With the default the
committed outputs must regenerate byte-identical (checked in the evidence). No other law changes.

## Dispersion model (`sim/dispersion.py`)

Each unit *i* draws independent parameters from a seeded generator (`seed = 20260916`, one
`SeedSequence` child per unit). Magnitudes are **assumed with a cited order of magnitude**, not measured
for this actuator class; see the novelty check for the sources.

| Axis | Parameter(s) | Distribution | Rationale (assumed unless cited) |
|---|---|---|---|
| Rupture life | `rupture_cycles` | Weibull, mean 3500, CV 0.30 | repo fixture (validation cohort); order of Torzini 2024 / Frontiers 2023 scatter |
| Mullins | `mullins_amplitude` | lognormal, CV 0.25 | stress-softening magnitude varies with filler/cure (Liao 2021, Lavazza 2023) |
| | `mullins_permanent_fraction` | truncated normal 0.30 ± 0.08 in [0.05, 0.70] | recoverable vs permanent split (Liao 2021) |
| | `mullins_cycles_tau` | lognormal, CV 0.30 | stabilisation within ~5 cycles (Lavazza 2023), scatter assumed |
| Fatigue law | `slow_fatigue_amplitude`, `accelerating_fatigue_amplitude` | lognormal, CV 0.25 each | assumed |
| | `acceleration_onset_fraction` | truncated normal 0.70 ± 0.08 in [0.45, 0.90] | micro-tear onset scatter (Torzini 2024), magnitude assumed |
| | `fatigue_exponent` | truncated normal 2.0 ± 0.35 in [1.2, 3.0] | crack-growth power-law exponent spread (Mars & Fatemi 2002), magnitude assumed |
| Leak | `terminal_leak_multiplier` | lognormal, CV 0.35 | 1 of 10 units failed early by leak (Frontiers 2023) |
| Viscoelastic time constant | `tau` | lognormal, CV 0.25 | assumed |
| Base stiffness scatter | `k1`, `k2` | lognormal, CV 0.10 each | property database scatter (Marechal 2021), magnitude assumed |
| Wall thickness | `k1`, `k2` ×= t/t₀ | normal 1.00 ± 0.08 in [0.75, 1.25] | cast-wall tolerance assumed; thin-wall stiffness ∝ thickness |
| Temperature | `k1`, `k2` ×= T/T₀; `tau` ×= exp[(Eₐ/R)(1/T − 1/T₀)] | T uniform 15–35 °C, T₀ = 25 °C, Eₐ = 40 kJ/mol | entropic modulus ∝ T; Arrhenius shift, Eₐ assumed; per-unit constant ambient (bench-to-bench), not in-test drift |

## Probe and indicator

Volumetric probe at a **fixed** 2 Hz (the operator does not know each unit's loss peak), amplitude
0.1·V₀, 8 periods, last period kept (`sim.plant.pv_loop`). Loop area *A* by the shoelace formula.
Indicator: h_i(u) = A_i(u) / A_i(u₁) with u₁ = 0.05 (post-Mullins baseline). Two versions:

- ideal: analytic loop, no noise (the Study 3 construction);
- measured: pressure noise 50 Pa + 10 Pa LSB and volume noise 1e-9 m³ (`SensorParams` defaults) applied
  to the probe loop, R = 5 repeats per stage with distinct seeds; the indicator uses the same noisy
  baseline draw convention (baseline repeat-mean).

Life grid u ∈ {0.05, 0.10, …, 0.95} (19 stages). Cohort N = 30 units.

## Metrics (per stage u)

- SD_between(u): SD over units of the per-unit repeat-mean measured indicator.
- SD_within(u): RMS over units of the per-unit repeat SD.
- ratio(u) = SD_between / SD_within; ICC(1)(u) = (MS_B − MS_W) / (MS_B + (R − 1)·MS_W).
- Trigger life per unit at τ = 0.05 on the repeat-mean measured indicator (`first_crossing`), its SD and
  range across units. Grid step 0.05.
- Ideal-indicator SD_between(u) (invariance check independent of noise).
- Ablation: one dispersion axis at a time (others canonical), SD_between of the ideal indicator at u = 0.5
  and 0.9.

## Verdict rules (fixed now)

- **A-DEGENERATE**: ideal SD_between(0.9) < 1e-6 → invariance persists; stop.
- **A-PASS**: median over u ≥ 0.30 of ratio(u) ≥ 2 **and** median ICC(1) over u ≥ 0.30 ≥ 0.5 **and**
  SD of trigger life across units ≥ 0.10 (two grid steps).
- **A-FAIL**: anything else. Reported as such; no downstream study proceeds on this generator.

## Outputs

`data/sim/studyA/studyA_results.json`, `studyA_fig_indicator_spread.png/.pdf`, `studyA_fig_ablation.png/.pdf`
via `python -m scripts.run_studyA` (seeded, deterministic). Tests in `tests/test_dispersion.py` and
`tests/test_studyA.py` cover: default `fatigue_exponent` reproduces the canonical law exactly; sampled units
are reproducible and within the stated supports; metric functions on a hand-built case; verdict logic.
