# Study C failure map — analysis definitions (R1)

Written 2026-09-19 as task R1 of the [week plan](../../WEEKLY_RESEARCH_PLAN_2026-09-21.txt). This is a
**post-hoc descriptive analysis of the committed Study C result**, not a new evaluation. Study C's verdict
remains **C-FAIL** and is not revisited here. Generator: `scripts/analyze_studyC_failure.py`.

## Question

Which property of a held-out unit predicts its transfer error?

- **Schedule coverage** — how many of its probes fell after its own acceleration onset, the regime
  [Study B](studyB-identifiability.md) showed to be informative. A fixable observation-design property.
- **Clock-prior mismatch** — how far its rupture life sits from the training-median rupture life that the
  estimator's `cycles / 1000` input is implicitly calibrated to. A property of the estimator's inputs.

These are **collinear by construction**: a short-lived unit necessarily receives fewer probes on a
fixed-cycle schedule. The analysis must therefore report both, their collinearity, and the partial
associations, instead of reporting whichever one is examined first.

## What this analysis may not do

No refitting, no change of lambda, no change to the held-out split, no new threshold, no unit dropped from
an aggregate. The committed model is **reproduced** under the identical contract (same units, same seeded
records, same training indices, same lambda, same standardisation) solely to read its coefficients; the
script aborts unless every reproduced held-out u-RMSE equals the committed value within 1e-9, and aborts if
the source JSON hash or the committed verdict is not what it expects.

## Definitions, fixed before the numbers were read

| Term | Definition |
|---|---|
| post-onset probe | probe cycle ≥ `acceleration_onset_fraction × rupture_cycles` |
| `no_post_onset` | 0 post-onset probes |
| `sparse_post_onset` | 1–2 post-onset probes |
| `adequate_post_onset` | ≥ 3 post-onset probes |
| rupture deviation | `abs(rupture_cycles − median(training rupture_cycles)) / median` |
| within target | u-RMSE ≤ 0.10 life (Study C's unchanged rule) |
| beats clock | u-RMSE < clock-only u-RMSE |

Raw counts are stored alongside every label so a later reader can regroup without rerunning anything.

## Channel decomposition

Every estimator input is standardised, so a group's contribution can be muted by holding it at its training
mean — the model's own no-information value for that group — with **weights unchanged**. Reported per group
(`pressure_now` 5 inputs, `pressure_lag` 5 inputs, `clock` 1 input): summed absolute standardised weight,
and held-out u-RMSE with that group muted. A unit whose error *falls* when the clock is muted is flagged:
the clock channel actively harms it.

This bounds each channel's contribution **to this fitted model**. It is not a measure of the information
content of the features themselves, which is Study B's question.

## Outputs

`data/sim/studyC/studyC_failure_analysis.json` (schema_version, `source_sha256`, `post_hoc_descriptive:
true`, definitions, per-unit rows, aggregates, associations, coverage-matched comparisons, channel
decomposition, limitations) and `studyC_fig_failure_map.(png|pdf)`, captioned "diagnostic failure map; not a
new held-out evaluation". Declared in `docs/figure-manifest.json`.

## Decision gate

The week plan offered three readings. R1 adds a fourth, because the plan's Study C2 design varies only the
probe schedule and therefore cannot test it:

| Reading | Evidence pattern | Implication for C2 |
|---|---|---|
| schedule-limited | error concentrated in low-coverage units, and survives controlling for rupture deviation | the plan's schedule grid is the right next experiment |
| signal-limited | error stays high in adequately covered units regardless of rupture deviation | schedule sweeping is wasted; go to features or interventions |
| **clock-prior-limited** | error tracks rupture deviation after controlling for coverage, and muting the clock channel helps the worst units | **a schedule grid alone cannot test this**; C2 needs a clock-input arm |
| mixed | no single axis dominates | carry both forward, declare a probe budget |

Statistical limits: n = 10 held-out units, descriptive coefficients only, no p-values, and at n = 10 two
collinear predictors cannot be cleanly separated even by a partial coefficient. The coverage-matched
comparison (units with identical post-onset probe counts but different rupture deviation) is reported
because it does not depend on a linear model.
