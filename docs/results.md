# Results

This document summarizes unchanged simulation results with a corrected methods
interpretation. Read the [correction](corrections/v1.3-methods-2026-09-05.md)
and [unreviewed manuscript candidate](preprint_v1_4_candidate.md). Archived v1.3
is preserved, not cleared for a new deposit. All results remain synthetic.

## Study 1: health-indicator validation

The study compares candidate health indicators against known synthetic fatigue
state, recovery behavior, onset changes, measurement noise, and held-out
actuator-life trajectories. Its figures are stored under `data/sim/study1/`.

## Study 2: pressure-only proprioception drift

The Phase D cohort shows increasing pose-estimation error when a young
calibration is held fixed as the simulated actuator ages. The study compares
static and dynamic correctors under shared and isolated supply topologies.

## Study 3: recalibration policy

| Result | Committed output |
| --- | --- |
| Dataset | 2,000 synthetic traces split by actuator identity |
| P-V association | Pooled `r = 0.885`; actuator-cluster bootstrap `[0.853, 0.950]`, leave-one-actuator-out `[0.576, 0.973]`; point-level `[0.835, 0.958]` (superseded) |
| P-V policy | 2 recalibrations per actuator versus 5 for always-on (identical on every held-out actuator, so the 60% saving has no sampling interval) |
| Cycle-count baseline | Misses the train-derived macro-averaged stage-RMSE budget at its train-selected period |
| Deployed threshold lead | No positive temporal lead at `tau = 0.05` |

Actuator-cluster resampling and leave-one-actuator-out sensitivity are already
reported in the committed outputs; point-level inference is superseded.

Study 3's health signal is a separate analytic SLS probe with zero rest input,
not the noisy Phase D volume channel. Noise, quantization and variable-rest
robustness of that signal have not been demonstrated. Shared latent fatigue
drives both endpoints, so correlation is structurally favored.

The policy endpoint averages stage-level pose RMSE over five sampled life stages
and then actuators. A pass is not a maximum-error or continuous accuracy guarantee.
The 60% event-count saving includes initial calibration; sensing overhead and
recalibration downtime were not measured.

![P-V loop-area growth and pose degradation](../data/sim/phaseD/study3_fig3_leading_indicator.png)

![Recalibration policy trade-off](../data/sim/phaseD/study3_fig4_recal_tradeoff.png)

## Study 4: shared-manifold sensitivity

Shared-manifold cross-talk is second-order within the tested network envelope
and increases as the simulated supply becomes softer. The result is conditional
on the lumped pneumatic-network parameters and is not a measurement of a
physical gripper.

![Shared-manifold sensitivity](../data/sim/phaseD/study4_fig_crosstalk_sensitivity.png)

## Result sources

- Study JSON and figures: `data/sim/`
- Frozen claim ledger: [`result_spine.md`](result_spine.md)
- Figure-generation lineage: [`data-and-figures.md`](data-and-figures.md)
- Manuscript-number checks: `scripts/check_manuscript_numbers.py`

## Observability program — Studies A and B (2026-09-16, synthetic, preregistered)

[Program](specs/observability-program/program.md) · [evidence](../evidence/observability-2026-09-16/README.md).
Question: is the fatigue state observable from pressure alone across dispersed units?

- **Study A** (30 units with assumed dispersion of the degradation law and plant): the normalised loop-area
  indicator's between-unit spread is 5–17× its measurement noise from mid-life (ICC 0.98), so the value is no
  longer unit-invariant; only degradation-law dispersion produces this, plant-level dispersion cancels under
  young-normalisation. The trigger life at τ = 0.05 still spreads by only 0.044 life, so the preregistered
  verdict is **A-FAIL** on its timing criterion and Study C stays blocked.
- **Study B** (Cramér–Rao bounds on the latent life coordinate from five pressure-only features): with a young
  baseline the coordinate is identifiable before the acceleration onset (σ_u ≈ 0.02–0.03 life, scaling with
  noise/amplitude) and structurally unidentifiable after it (aliased with the unit's onset fraction and leak).
  Verdict **B-PASS** by its rule; the regime boundary is the result.

Boundary: one synthetic generator, assumed dispersion magnitudes, local bounds; no physical claim.
