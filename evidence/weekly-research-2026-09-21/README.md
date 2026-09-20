# Week of 2026-09-21 — Day 1 (R0, R1) executed 2026-09-19

Branch `research/weekly-r0-r1-20260921`, **stacked on the open PR #22 head `1525a1b`** as the week plan
directs when #22 is unmerged (origin/main was `c8bbaf4`). This PR therefore contains PR #22's commits; it
must merge after #22, or be rebased if #22 changes.

Plan: [`docs/WEEKLY_RESEARCH_PLAN_2026-09-21.txt`](../../docs/WEEKLY_RESEARCH_PLAN_2026-09-21.txt).
Critique of that plan, with the evidence behind each point:
[`docs/reviews/weekly-plan-critique-2026-09-19.md`](../../docs/reviews/weekly-plan-critique-2026-09-19.md).

## R0 — baseline, provenance, immutability lock

Full console record: [`r0-baseline.txt`](r0-baseline.txt). Base `1525a1be28210cfeb30dc7b79cce3a79a65a1606`.
Python 3.11.8; numpy 2.1.1, scipy 1.15.2, matplotlib 3.10.1, reportlab 4.5.1, pypdf 6.12.2.

| locked artifact | SHA-256 at R0 | after R1 |
|---|---|---|
| `data/sim/studyC/studyC_results.json` | `aac3c48826bdd110…` | unchanged |
| `data/sim/studyC/studyC_fig_transfer.png` | `ebdcdb1bfd7066c2…` | unchanged |
| `docs/preprint_v1.pdf` | `6a6681fe1a77f7d9…` | unchanged |
| `docs/publication-readiness.json` | `6b58769bdb6b696d…` | unchanged |

Gates at R0 and after R1: `check_manuscript_numbers` 0, `check_publication_fallback` 0,
`--for-publication` **2 (publication BLOCKED, expected)**.

**Provenance finding.** The project venv resolves to the system `site-packages`, so it runs numpy 2.1.1 /
scipy 1.15.2, while the 2026-09-16 evidence recorded numpy 2.4.6 / scipy 1.17.1 for the same study. The
plan's R0 would not have caught this. R1 therefore makes exact reproduction a hard gate (below); it passed,
so the drift is verified harmless for these numbers rather than assumed to be.

## R1 — forensic failure map

`python -m scripts.analyze_studyC_failure` (33 s). Post-hoc and descriptive: no refit, no lambda change,
no split change, no new threshold, no unit dropped. The committed model is **reproduced** under an
identical contract solely to read its coefficients, and the script aborts unless every held-out u-RMSE
matches the committed value within 1e-9 — it did. It also aborts on a source-hash or verdict mismatch
(verified by corrupting a disposable copy: exit 1, `committed verdict is 'C-PASS', expected C-FAIL`).

Definitions were fixed before the numbers were read:
[`studyC-failure-analysis.md`](../../docs/specs/observability-program/studyC-failure-analysis.md).

### Per held-out unit

| unit | rupture | onset | post-onset probes | rupture deviation | u-RMSE | clock | coverage label |
|---|---|---|---|---|---|---|---|
| 7 | 1416 | 0.78 | 1 | 0.61 | **0.227** | 0.362 | sparse post onset |
| 12 | 2205 | 0.74 | 2 | 0.39 | **0.130** | 0.227 | sparse post onset |
| 17 | 2471 | 0.72 | 3 | 0.32 | **0.131** | 0.183 | adequate post onset |
| 22 | 3671 | 0.67 | 5 | 0.01 | **0.056** | 0.007 | adequate post onset |
| 23 | 3857 | 0.67 | 5 | 0.06 | **0.054** | 0.034 | adequate post onset |
| 28 | 3930 | 0.61 | 6 | 0.08 | **0.053** | 0.045 | adequate post onset |
| 26 | 4121 | 0.65 | 6 | 0.14 | **0.041** | 0.069 | adequate post onset |
| 0 | 4165 | 0.60 | 7 | 0.15 | **0.061** | 0.074 | adequate post onset |
| 24 | 4248 | 0.60 | 7 | 0.17 | **0.080** | 0.085 | adequate post onset |
| 29 | 4775 | 0.74 | 5 | 0.32 | **0.101** | 0.140 | adequate post onset |

By coverage label: sparse (n = 2) mean u-RMSE
0.179, 0 within target;
adequate (n = 8) mean 0.072,
6 within target. No unit had zero post-onset probes.

### The two candidate causes are collinear

corr(post-onset count, rupture deviation) = **-0.802**.
Error against each: coverage -0.857, rupture deviation
**+0.956**. Controlling for the other: coverage
-0.515, rupture deviation
**+0.872**.

Model-free confirmation — identical coverage, different rupture life:

| unit | rupture | post-onset probes | rupture deviation | u-RMSE |
|---|---|---|---|---|
| 22 | 3671 | 5 | 0.01 | 0.056 |
| 23 | 3857 | 5 | 0.06 | 0.054 |
| 29 | 4775 | 5 | 0.32 | 0.101 |

### Channel decomposition (no refit; each group held at its training mean, weights unchanged)

| condition | mean held-out u-RMSE |
|---|---|
| full model | 0.093 |
| pressure channels muted | 0.144 |
| clock channel muted | **0.213** |

Absolute standardised weight share: pressure_now 0.33,
pressure_lag 0.44, clock
0.23. Most weight sits on pressure, but accuracy depends more on
the clock: muting it costs 0.120 life versus
0.051 for pressure. The estimator is a clock
corrected by pressure. Units actively harmed by their clock channel: **[7]**
— unit 7 is the shortest-lived and worst unit, and improves from 0.227 to 0.191 with the clock muted.

### R1 decision gate

**Primarily clock-prior-limited; schedule coverage a secondary contributor that n = 10 cannot exclude.**
Both partials are non-trivial, so this is not a clean single-cause result. It does establish that a
schedule-only C2 would manipulate the weaker axis. Recommendation carried into R2: make the clock input
C2's primary axis (full / pressure-only / clock-only arms) with schedule secondary.

### Limitations

n = 10 held-out units; descriptive coefficients only, no p-values; reuses the committed Study C evaluation
rather than producing a new one; coverage and rupture deviation are collinear by construction; channel
muting bounds a channel's contribution *to this fitted model*, not the information content of the features.

## Scope held

Study C's **C-FAIL verdict is unchanged** and its preregistration untouched. No manuscript, PDF, readiness
record, frozen v1.3 artifact, Study A/B artifact or Phase D dataset was read-modified. No hardware, no
spending, no publication action. PV-08 unchanged.

## Not done (Day 1 scope)

R2 (C2 preregistration), R3, R4, R5 and M1 are Tuesday–Friday. R2 should be written against the critique's
recommendation, and per the plan R3 must not begin until R2 has a commit hash.

---

# Day 2 (R2) — executed 2026-09-20

Branch `research/weekly-r2-20260922`, from main `347a94b` (PRs #22 and #23 merged, so the Day 1 stack is
no longer a dependency).

## R2 — Study C2 design frozen before any C2 run

Preregistration: [`studyC2-preregistration.md`](../../docs/specs/observability-program/studyC2-preregistration.md).
Per the week plan, R3 may not start until this file has a commit hash, and R4 not until the owner reviews it.

The design departs from the plan's R2 sketch on three points, each traceable to a Day 1 measurement and
each recorded in the preregistration itself:

| # | plan's sketch | C2 as frozen | why |
|---|---|---|---|
| 1 | schedule is the only manipulated variable; 11 inputs frozen | **input arm is the primary axis** (`full`, `pressure_only`, `clock_only`); schedule secondary | R1: muting the clock costs 0.120 life vs 0.051 for pressure; a schedule-only grid cannot reach the plan's own *clock-dominated* label |
| 2 | "the three currently worst short-lived held-out units" | **rupture below the training median** | the plan's own guardrail forbids choosing from held-out outcomes; the pre-specifiable rule selects the same units 7, 12, 17 |
| 3 | oracle changes placement and probe count | **oracle matches the reference probe count per unit** | otherwise timing and count are confounded in the arm that exists to isolate timing |

### Design validated before freezing (generator parameters only; no estimator, no errors)

| schedule | probes/unit (held-out mean) | post-onset mean | cost vs reference |
|---|---|---|---|
| reference | 14.2 | 4.7 | 1.00x |
| dense | 27.6 | 9.2 | 1.94x |
| sparse | 7.4 | 2.4 | 0.52x |
| late_start | 13.3 | 4.4 | 0.94x |
| **onset_anchored_oracle** | **14.2** | **13.2** | **1.00x** |

The oracle fix works: identical probe cost, post-onset coverage nearly tripled. On unit 7, the worst unit,
it moves 1-of-6 post-onset probes to 5-of-6 at the same total count. Under `sparse`, unit 7 receives zero
post-onset probes, which makes that a useful negative condition rather than merely a cheap one.

### The contract is code, not prose

The parts that must not drift during R3 are pure functions in
[`pipeline/schedules.py`](../../pipeline/schedules.py), pinned by **46 acceptance tests**
(`tests/test_schedules.py`) committed *before* the runner exists: the reference schedule reproduces Study
C's cycles and seed namespace exactly; no schedule probes at or after rupture; every condition carries the
baseline exactly once and de-duplicates; schedule ordinals are stable under insertion so adding a schedule
cannot renumber existing seeds; the oracle matches reference probe count; normalised life is never an
input; the unchanged C rule still fails the committed (6, 7) counts; and every interpretation branch is
reachable and correctly ordered, with a feasible pass always outranking the oracle.

This is a small, deliberate reordering of the plan: the plan assigned the pure schedule and seed functions
to R3, but R2 owes "acceptance tests", and tests are only meaningful against a contract. Implementing the
contract in R2 and the runner in R3 keeps the design from drifting while the runner is written.

## Scope held

No C2 run was executed; `data/sim/studyC2/` does not exist yet. Study C's verdict, preregistration,
result JSON and figure are untouched, as are the v1.3 archive, the readiness record and PV-08.

## Next

R3 (runner) may begin: this preregistration now has a commit hash. R4 execution awaits owner review of the
preregistration, per the plan. M1 remains a Friday review-only checkpoint.
