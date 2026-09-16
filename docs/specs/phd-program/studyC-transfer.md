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
