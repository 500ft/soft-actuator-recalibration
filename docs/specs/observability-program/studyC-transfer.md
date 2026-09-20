# Study C — unseen-unit transfer with a falsifiable cohort (preregistration draft; blocked on A-PASS)

Not executable until Study A records A-PASS. Fixed now so that A's result cannot shape C's design.

- Cohort: Study A's generator, N = 30 units, split by **unit identity** 20 train / 10 test (seeded, fixed
  before any fitting); no trace-level split.
- Estimator: **one** — ridge regression from the young-baseline-normalised Study B feature vector to u,
  hyperparameter chosen on the 20 training units by leave-one-unit-out. No variants.
- Baselines: fixed-schedule (predict u from cycle count with the training-median rupture life);
  per-unit calibration (ridge fitted on the unit's own first three stages, an upper bound on what
  self-calibration can buy); full-state oracle (true u).
- Metrics on the 10 held-out units: u-RMSE per unit; actuator-cluster bootstrap and leave-one-unit-out
  intervals (existing tooling); trigger-life error at τ chosen on training units.
- Adversarial worst case: Latin-hypercube search of 200 units over the dispersion supports; report the
  unit with the largest u-RMSE and its parameter vector.
- **C-PASS**: held-out u-RMSE ≤ 0.10 life for ≥ 8 of 10 units and better than the fixed schedule on
  ≥ 8 of 10. **C-FAIL** otherwise: no transfer claim.

## Amendment 2026-09-16 (recorded before any Study C run)

Study B showed the latent life coordinate is structurally unidentifiable from one probe plus a young baseline
after the acceleration onset (aliased with the unit's onset fraction and leak), and Study A's amendment
(criteria i, ii) unblocked this study. The design is therefore fixed as follows before running; the original
draft above is retained.

- **Probe schedule in cycles, not life fraction.** Probes every 250 cycles from cycle 100 (post-Mullins
  baseline) until the unit's rupture. A probe index is therefore a clock reading, which the clock baseline is
  allowed to use; the life fraction is never given to any estimator.
- **Estimator input (one estimator, ridge):** log-ratio of the five Study B features to the unit's own young
  baseline (5), the same log-ratio at the previous probe (5, first probe repeated), and the cycle count / 1000
  (clock). Inputs standardised on the training units. Ridge λ ∈ {0.01, 0.1, 1} chosen by leave-one-unit-out
  on the 20 training units; fitted on all their probes; applied unchanged to the 10 held-out units.
- **Baselines:** clock-only (u = cycles / median training rupture life, clipped to 1); per-unit calibration
  (same ridge fitted on the unit's own first three probes with true labels — an upper bound that needs a pose
  sensor, reported as such); full-state oracle (true u, error 0 by definition).
- **Metrics on held-out units:** u-RMSE per unit over its probes, split pre-/post-onset (Study B's regime
  boundary); actuator-cluster bootstrap (2000 seeded resamples of whole units) and leave-one-unit-out range.
- **Adversarial worst case:** 200 further units drawn from the dispersion model (seed 20260918), the fitted
  estimator applied; report the worst unit's RMSE and parameters. (Replaces the Latin-hypercube wording: the
  dispersion supports are distributions, so seeded sampling from the model is the search.)
- **Verdict (unchanged):** C-PASS if held-out u-RMSE ≤ 0.10 for ≥ 8 of 10 units **and** below clock-only on
  ≥ 8 of 10; C-FAIL otherwise. Pre-onset-only performance is reported but does not change the verdict.
