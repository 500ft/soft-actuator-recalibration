# Critique of the week plan of 2026-09-21, with R1 evidence

Written 2026-09-19, before executing R0/R1, and completed after them. Subject:
[`docs/WEEKLY_RESEARCH_PLAN_2026-09-21.txt`](../WEEKLY_RESEARCH_PLAN_2026-09-21.txt). The plan is sound in
structure: provenance first, a preregistration before any run, verdict language that cannot be revised after
seeing results, and an explicit stop rule. The findings below are defects in its *experimental logic*, not
its discipline. Each one is stated with the evidence that supports it.

## 1. R1's two candidate causes are collinear, and the plan never says so

The plan frames R1 as testing whether failures concentrate in units with poor post-onset coverage, and its
decision gate reads a "yes" as *schedule limitation*. But on a fixed-cycle schedule a short-lived unit
**necessarily** receives fewer probes, so coverage is entangled with rupture life, and rupture life is also
what makes the estimator's `cycles / 1000` clock input wrong. Measured across the ten held-out units:

| relationship | Pearson (n = 10, descriptive) |
|---|---|
| post-onset probe count vs rupture deviation from the training median | **−0.802** (the confound) |
| error vs post-onset probe count | −0.857 |
| error vs rupture deviation | **+0.956** |
| error vs post-onset count, controlling for rupture deviation | −0.515 |
| error vs rupture deviation, controlling for post-onset count | **+0.872** |

The cleanest evidence needs no model at all. Three units have **identical** post-onset coverage:

| unit | rupture cycles | post-onset probes | rupture deviation | u-RMSE |
|---|---|---|---|---|
| 22 | 3671 | 5 | 0.01 | 0.056 |
| 23 | 3857 | 5 | 0.06 | 0.054 |
| 29 | 4775 | 5 | **0.32** | **0.101** |

Coverage held constant, the error nearly doubles as rupture life becomes atypical. Had R1 been run as
written, it would have reported "errors concentrated in low-coverage units" and sent Wednesday and Thursday
into a schedule sweep. The plan's own stated purpose is to "prevent another week of tuning the wrong
variable"; as written, R1 was the mechanism by which that would have happened.

**Fix applied:** R1 now reports both axes, their collinearity, partial coefficients, and the
coverage-matched comparison, and its decision gate gains a fourth reading, *clock-prior-limited*.

## 2. C2 lists "clock-dominated" as an outcome but contains no arm that can produce it

R2's interpretation rules include a *null/clock-dominated* verdict. Yet the C2 estimator contract freezes
"exactly the current 11-input representation", and the only manipulated variable is the probe schedule. A
design that never varies the clock input cannot conclude anything about the clock's role. The label is
unreachable by construction.

**Fix applied (evidence, not just argument):** R1 adds a channel decomposition that needs no refit. Each
input group is held at its training mean — the model's own no-information value — with weights unchanged:

| condition | mean held-out u-RMSE |
|---|---|
| full model | 0.093 |
| pressure channels muted | 0.144 |
| **clock channel muted** | **0.213** |

Absolute standardised weight sits mostly on pressure (0.33 current + 0.44 lag vs 0.23 clock), but accuracy
depends more on the clock: removing it costs 0.120 life, removing pressure costs 0.051. The estimator is a
**clock corrected by pressure**. And exactly one unit is *harmed* by its clock channel — unit 7, the
shortest-lived and worst-performing unit, improves from 0.227 to 0.191 when the clock is muted.

**Recommendation for R2:** make the clock input the primary axis of C2, not a frozen constant. Minimum
arms: full 11-input (reference), pressure-only (clock muted), clock-only. Schedule becomes the secondary
axis. Without this, C2 spends its compute on the variable R1 indicates is *not* dominant.

## 3. The "materially reduce" rule selects its evaluation subset from held-out outcomes

R2 proposes measuring improvement on "the three currently worst short-lived held-out units". Those units are
identified *by their held-out errors*, which the plan's own guardrail forbids: "Never choose a schedule,
feature, lambda, or model using held-out outcomes." It is a descriptive rule rather than a tuning knob, so
the harm is limited, but it still hard-codes a post-hoc selection into a preregistration.

**Fix:** define the subset by a property knowable without seeing any outcome — for instance units whose
rupture life is below the training median, or above a stated deviation threshold. Both are available from
the generator before evaluation.

## 4. The oracle arm confounds observation timing with probe count

The diagnostic oracle places probes "at the unit's true onset and at two fixed post-onset cycle offsets".
That changes both *when* probes occur and *how many* there are, so a difference cannot be attributed to
timing. The arm exists precisely to isolate timing.

**Fix:** hold the probe count equal to the reference schedule's count for that unit and move only the
placement, or report both arms (matched-count and matched-placement) and interpret only their difference.

## 5. Adding figures without declaring them breaks a tested gate

`tests/test_figure_manifest.py` asserts in both directions: every declared output must be tracked and
present, and **every committed figure under `data/` must have a manifest entry**. The plan lists four new
figures across R1 and R3 and never mentions `docs/figure-manifest.json`. Following it literally produces a
red suite at the end of Wednesday.

**Fix applied:** the R1 figure is declared. R3 must do the same for the C2 figures.

## 6. R0 records the environment but never checks that the result still reproduces

R0's acceptance conditions cover hashes and gate states, but nothing verifies that the committed Study C
numbers can still be *produced* by the current code and environment. This was not hypothetical: the
project venv resolves to the system `site-packages`, so it now runs numpy 2.1.1 / scipy 1.15.2, whereas the
2026-09-16 evidence recorded numpy 2.4.6 / scipy 1.17.1 for the same study.

**Fix applied:** R1 reproduces the committed model under an identical contract and aborts unless every
held-out u-RMSE matches within 1e-9. It passed, so the drift is confirmed harmless for these numbers — but
that is now a verified fact rather than an assumption. Recommend adding the reproduction check to R0.

## 7. Smaller points

- **Spec file extension.** The plan asks for `.txt` for `studyC-failure-analysis` and
  `studyC2-schedule-preregistration`; every existing file in `docs/specs/observability-program/` is `.md`
  and is cross-linked as such. Used `.md` for consistency.
- **Threshold sensitivity.** C-PASS needs 8/10 on two counts; the result was 6/10 and 7/10, and the
  cluster bootstrap on mean error, [0.064, 0.131], straddles the 0.10 target. Two units decide the verdict.
  The plan is right to forbid moving the threshold; it should also state that a near-miss and a pass are
  not strongly distinguishable at n = 10, so C2 should not be read as a precise measurement.
- **R1 writes into `data/sim/studyC/`.** R3 is forbidden from writing there, for good reason. R1's outputs
  are new files and leave the locked hashes untouched (verified), but a `studyC_failure/` namespace would
  have been cleaner.

## Verdict for the week's Day 1 decision gate

**Primarily clock-prior-limited, with schedule coverage a secondary contributor that n = 10 cannot rule
out.** Both partial coefficients are non-trivial (+0.872 for rupture deviation, −0.515 for coverage), so
this is not a clean single-cause result and must not be reported as one. What it does establish is that a
schedule-only C2 would test the weaker of the two axes.

The sharper question for C2 is not "do more probes help?" but "can the pressure features carry normalised
life *without* a cycle-count prior calibrated to the training cohort?" Study B already showed the latent
coordinate is aliased with onset and leak after onset; R1 adds that the deployed estimator leans on the
clock for most of its accuracy and fails where that clock is wrong. Those two findings point at the same
next experiment, and it is not a cadence sweep.
