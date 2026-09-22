# Study C2 — is the limitation the clock prior, the probe schedule, or the signal? (preregistration)

Frozen 2026-09-20 as task R2 of the [week plan](../../WEEKLY_RESEARCH_PLAN_2026-09-21.txt), **before any C2
run exists**. R3 may not begin until this file has a commit hash; R4 may not begin until the owner has
reviewed it or authorised execution.

This is a **follow-up that diagnoses** the Study C failure. It is not an amendment to Study C. Study C's
verdict stays **C-FAIL** and its [preregistration](studyC-transfer.md) is untouched. If a C2 arm meets the
unchanged rule, that is a conditional result *within this synthetic generator and this schedule set*, never
a transfer claim and never a retroactive revision of C.

## What changed from the week plan's R2 sketch, and why

The plan's C2 varied only the probe schedule while freezing the 11-input representation. [R1](../../../evidence/weekly-research-2026-09-21/README.md)
showed that would manipulate the weaker variable and could not reach the plan's own *clock-dominated*
label. Three changes, each traceable to a measurement:

1. **The input representation becomes the primary axis.** R1's channel decomposition: muting the clock
   costs 0.120 life, muting pressure costs 0.051; the estimator is a clock corrected by pressure, and the
   worst unit is actively *harmed* by its clock channel. Schedule becomes the secondary axis.
2. **The "materially reduce" subset is pre-specifiable.** The plan named "the three currently worst
   short-lived held-out units", which selects an evaluation subset from held-out outcomes and violates the
   plan's own guardrail. C2 uses **rupture life below the training median**, known from the generator
   before any error is computed. On this cohort it happens to select the same three units (7, 12, 17).
3. **The oracle matches probe count.** The plan's oracle changed placement *and* count, so a difference
   could not be attributed to timing. C2's oracle places exactly as many probes as the reference schedule
   for that unit. Verified: identical cost (1.00x), post-onset coverage 4.7 → 13.2 probes per unit.

## Question

Does the estimator fail on unseen units because it never observes them in the informative post-onset
regime, because it leans on a cycle-count prior calibrated to the training cohort, or because the pressure
features cannot carry normalised life at all?

## Hypotheses (any may fail; a failure is reported, not repaired)

- **H-C2-CLOCK** — the limitation is the clock prior. Pressure-only will not reach the rule, clock-only
  will be clearly worse than full, and full's residual failures will stay concentrated in below-median
  units under every schedule including the oracle. *This is R1's leading hypothesis.*
- **H-C2-SCHEDULE** — post-onset coverage is the limitation. A feasible schedule moves full to the rule.
- **H-C2-SIGNAL** — the features cannot carry life. Even the probe-count-matched oracle fails with full
  inputs, and failures are not confined to below-median units.
- **H-C2-PRESSURE-SUFFICIENT** — pressure-only reaches the rule on some feasible schedule. The strongest
  positive outcome available to this study, and the one that would justify a transfer claim being retested.

## Frozen design

Cohort and split are Study C's, unchanged: `sample_units(30, SEED)`, the seeded permutation from
`scripts/run_studyC.py`, 20 training and the **same 10 held-out identities**, split by identity, no
trace-level split, no new units, no new degradation family. Held-out outcomes may not be used to choose a
schedule, an arm, a lambda, or any other quantity.

### Primary axis — input arm (`pipeline.schedules.arm_columns`)

| arm | inputs | asks |
|---|---|---|
| `full` | all 11 (5 log-ratios, 5 lagged log-ratios, cycles/1000) | the committed Study C estimator |
| `pressure_only` | the 10 log-ratios; **no clock** | can pressure carry life with no cycle-count prior? |
| `clock_only` | cycles/1000 alone | does pressure add anything over a clock? |

Normalised life is never an input to any arm.

### Secondary axis — schedule (`pipeline.schedules.SCHEDULES`)

Every condition takes its young baseline at cycle 100, so the log-ratio normalisation is identical across
conditions; a follow-up landing on cycle 100 is de-duplicated, never doubled. Probes stop before rupture.

| schedule | definition | probes/unit (held-out mean) | post-onset (mean) | cost vs reference |
|---|---|---|---|---|
| `reference` | start 100, cadence 250 — **the committed Study C schedule** | 14.2 | 4.7 | 1.00x |
| `dense` | start 100, cadence 125 | 27.6 | 9.2 | 1.94x |
| `sparse` | start 100, cadence 500 | 7.4 | 2.4 | 0.52x |
| `late_start` | baseline 100, follow-up from 500, cadence 250 | 13.3 | 4.4 | 0.94x |
| `onset_anchored_oracle` | baseline 100 + the **same number of probes** as `reference`, spread from the unit's true onset to just before rupture | 14.2 | 13.2 | 1.00x |

The oracle uses generator truth and is a **mechanistic diagnostic upper bound, never a deployable policy**.
It is excluded from every practical recommendation, and a feasible pass always outranks it in the reading
below.

### Estimator contract (unchanged from Study C except the input columns)

Ridge regression; inputs standardised on training units and the **same** standardisation reused unchanged
on held-out units; lambda selected from {0.01, 0.1, 1.0} by leave-one-unit-out **on the 20 training units
only**, selected separately for each (arm, schedule) cell. No new estimator families, no feature
selection, no post-hoc threshold tuning.

### Seeds

`reference` reuses Study C's namespace `SeedSequence([SEED, 7, unit_index, probe_index])` so it reproduces
the committed run exactly; every other schedule uses `SeedSequence([SEED, 8, unit_index, schedule_ordinal,
probe_index])`. Schedule ordinals are stable under insertion, so adding a schedule later cannot renumber an
existing one's seeds.

### Metrics, per held-out unit, for every (arm, schedule) cell

u-RMSE; RMSE before and after onset (null when a segment is empty, never dropped); clock-only RMSE from
the training-median rupture life; delta versus clock; post-onset probe count and fraction; probe count and
cost ratio versus reference; `within_target` (u-RMSE ≤ 0.10); `beats_clock`. Cohort level: counts within
target and beating the clock, the unchanged rule, actuator-cluster bootstrap over whole units with 2000
seeded resamples, and the leave-one-held-out-unit-out range. Every row is reported, not only the best.

### The rule is unchanged

**C-PASS requires ≥ 8/10 held-out units within 0.10 life and ≥ 8/10 better than clock-only.** It is not
relaxed, reweighted or renegotiated for C2 under any outcome. Encoded as `passes_c_rule`, with a test
asserting the committed Study C counts (6, 7) still fail.

### "Materially reduce"

Mean u-RMSE on the pre-specified below-median subset falls by **≥ 0.05 life** versus the reference cell.
That subset is units 7, 12, 17 (rupture 1416, 2205, 2471 against a training median of 3625.6), whose
reference-cell mean is 0.1627, so the bar is ≤ 0.1127. Reported with its probe-count cost.

## Predeclared reading (`pipeline.schedules.interpretation_label`, fixed order of precedence)

| # | condition | label |
|---|---|---|
| 1 | `pressure_only` meets the rule on a feasible schedule | **signal-sufficient-without-clock** |
| 2 | `clock_only` is indistinguishable from `full` (its mean u-RMSE lies within full's leave-one-unit-out range) | **clock-dominated** |
| 3 | `full` meets the rule on a feasible schedule | **schedule-limited** |
| 4 | `full` meets the rule only under the oracle | **mixed-timing-feasibility** |
| 5 | the oracle still fails, and every failing unit is below the median rupture life | **clock-prior-limited** |
| 6 | otherwise | **signal-limited** |

A feasible pass always outranks the oracle, so the oracle can never become the recommendation. Each branch
has a test.

## Stopping rules and downgrade language

- Any cell that fails is reported with its numbers; no cell is rerun with a different seed to improve it.
- If a run is interrupted, record the interruption and restart from a clean output directory; never resume
  with a different seed.
- If the reference cell does not reproduce the committed Study C held-out rows, **stop** and repair
  provenance before interpreting anything.
- Nothing here may be described as transfer, prognosis, early warning, or a physical claim. Permitted
  wording is "within this synthetic generator and the tested schedules".

## Outputs

`data/sim/studyC2/studyC2_results.json` (with `preregistration_sha256`, base commit, generator hashes,
seeds, schedule definitions, train/test indices, every per-unit row, output hashes), written atomically;
`studyC2_fig_schedule_sensitivity.(png|pdf)`, declared in `docs/figure-manifest.json`. C2 never writes into
`data/sim/studyC/`; the Study C result and figure hashes must be identical before and after.

## Status of the contract

The parts of this design that must not drift are implemented as pure functions in
[`pipeline/schedules.py`](../../../pipeline/schedules.py) and pinned by 46 acceptance tests in
`tests/test_schedules.py`, committed with this document and before the runner exists. R3 consumes them and
does not redefine them.
