# Study B follow-up — correction to the 2026-09-23 resolution claim

**Date:** 2026-09-25
**Supersedes:** [`evidence/studyB-structural-2026-09-23/`](../studyB-structural-2026-09-23/README.md)
**Trigger:** owner critique, `docs/LITERATURE_CRITIQUE_AND_NEXT_STUDIES_2026-09-24.txt`, item 1 (P0)
**Historical record:** the superseded result is retained at
`data/sim/studyB/studyB_structural_superseded_2026-09-23.json`. Every original field and value is
unchanged, but **byte identity is not expected**: a `SUPERSEDED` key was prepended and the file was
re-serialised, so it will not hash to the original. To recover the exact original bytes:

```
git show 34376d9:data/sim/studyB/studyB_structural.json
```

| | commit |
|---|---|
| source of the superseded artifact | `34376d9` (main, via PR #35) |
| this correction | the head of `fix/studyB-resolution-correction-20260925` (PR #36) |

The 2026-09-23 evidence record carries a superseded banner and is otherwise unedited.

---

## What was claimed, and why it was wrong

The 2026-09-23 follow-up concluded that the post-onset life coordinate is *practically aliased, resolvable
to about ±0.05 life*. The owner's critique found three defects, and all three are confirmed:

1. **The likelihood did not match its own description.** The stored method string read "B2 stacked design
   (snapshot + young baseline)", but `neg_log_likelihood` computed the aged snapshot alone. The baseline
   observation never entered the calculation.
2. **The grid ended at the answer.** `U_GRID` ran 0.10–0.90 while the post-onset truth *is* 0.90. No upper
   crossing could exist, so the upper confidence bound was unreachable by construction and the ±0.05
   figure was read off a grid edge.
3. **A solver failure was scored as a shape.** One point at u = 0.70 did not converge, and the classifier
   ignored it. A stalled optimiser and a flat likelihood look identical in the output.

Rechecking those three exposed three further defects in the same code path, none of which had been noticed:

4. **The covariance was inverted at cond ≈ 1.7 × 10²⁶.** The feature vector mixes loop areas near 10⁻²
   with a secant stiffness near 10¹¹, so the standard deviations span thirteen orders of magnitude. Almost
   all of that is *scale*: factoring Σ = D R D leaves a correlation matrix with condition number under 5.
   Whitening now divides by the standard deviations first and applies the correlation Cholesky second, so
   Σ⁻¹ is never formed.
5. **The nuisance optimiser was searching across eleven orders of magnitude.** The fitted stiffnesses sit
   near 10¹⁰ while tau is near 10⁻¹, and L-BFGS-B on raw variables stalled. Strictly positive parameters
   are now fitted in log space, and each grid point is warm-started from its neighbour.
6. **Part of the parameter box has no defined feature vector.** `operational_half_life` returns nan
   whenever the decay never halves inside the 2 s window, which happens across much of the box at low
   leak — 54 of 192 bound-box corners. Those points are now treated as infeasible, given a finite search
   penalty, and counted, instead of silently propagating nan into the profile.

Defects 4–6 are why the first corrected attempt returned `unresolved` at every point: the optimiser was
failing, not the model.

## The corrected result

Both designs are now computed and stored. B2 stacks the young baseline at u = 0.05 with the aged snapshot
under shared nuisance parameters (ten features); B1 is the snapshot alone (five). The grid spans the full
physical domain [0.02, 0.98], and each threshold crossing is refined by two bisection passes.

| design | true u | verdict | minimum | 95% interval | non-converged |
|---|--:|---|--:|---|---|
| **B2** | 0.90 | **identifiable** | 0.775 | **[0.75, 0.98]** | none |
| B1 | 0.90 | practical | 0.65 | [0.5625, open] | none |
| **B2** | 0.50 | unresolved (see below) | 0.475 | [0.45, 0.5625] | 1 of 25 |
| B1 | 0.50 | unresolved (see below) | 0.95 | open to open | 1 of 21 |

**The post-onset case converged at every one of its 25 points**, and it is the case the "structurally
aliased" claim was about. Under the design Study B's write-up actually describes, the profile crosses the
threshold on both sides of its minimum, which is what this implementation's `identifiable` label means —
no more than that.

**It does not mean the state is precisely located, and no resolution figure is claimed.** The defensible
statement is:

> Under this B2 synthetic observation model and one noise realisation, the data support a broad,
> asymmetric region around approximately [0.75, 0.98], with a likelihood plateau across most of it and
> both terminations sitting on nuisance-parameter bounds. Widening those bounds to a still-physical range
> removes the upper termination entirely. **Precision is not established, and whether the post-onset
> coordinate is identifiable at all remains open.**

Three facts force that narrowing, and all three are in the stored profile:

1. **The upper region is a plateau, not a rise.** Δ(−log L) is ~0 at u = 0.775, 0.80, 0.85, 0.90, 0.95,
   0.965 and 0.9725. The total negative-log-likelihood variation across that whole span is
   **5.8 × 10⁻¹⁰**, against a threshold of 1.92 — nine orders of magnitude smaller. The profile does not
   distinguish any life value in the upper half of the domain from any other.
2. **Both terminations coincide with nuisance bounds, and the upper one is purely an artefact of them.**
   At u = 0.98 the onset fraction *and* the fatigue exponent are pinned to the box; at u = 0.75 the same two
   are pinned. Re-profiling with a widened but still physical box removes the upper crossing **entirely**
   (Δ falls from 36.5 to 5.7 × 10⁻¹⁰; see [Bound sensitivity](#bound-sensitivity--the-upper-crossing-is-entirely-an-artefact-of-the-box)).
   So the interval does not close where the data run out, it closes where the optimiser runs out of freedom
   to compensate — **and the `identifiable` verdict is itself bound-dependent.**
3. **An earlier withdrawn claim had the same shape.** "±0.05 life" was a grid edge dressed as a bound.
   Quoting "±0.21 life" off a plateau that terminates on the parameter box would be the same mistake in a
   new place, so it is withdrawn too.

Following Raue et al. 2009 (<https://doi.org/10.1093/bioinformatics/btp358>) and Wieland et al. 2021
(<https://arxiv.org/abs/2102.05100>): a threshold crossing establishes a tested profile behaviour. It does
not by itself establish a stable, precise, or structurally unique estimate.

### The point estimate error is one realisation, not a bias

The minimum sits at 0.775 against a truth of 0.90. That is **an observed downward error of 0.125 in this
one realisation**, and the record says only that. *Bias* is an expectation over a declared sampling
distribution, and none has been drawn: this is a single sensor seed on a single canonical unit. Calling it
bias would claim a repeated-draw result from one draw. Establishing bias needs preregistered seeds, a
defined estimator — including how it breaks ties across a flat minimum, which matters a great deal here —
and a mean error with uncertainty. That is filed as prospective work, not done.

**The modelled young-baseline observation improves localisation under this design.** At the same truth,
B1 on the snapshot alone is only *practical*: its upper bound never crosses the cut inside the physical
domain, and its minimum sits at 0.65. At the pre-onset truth the contrast is starker — B2 brackets the truth
at [0.45, 0.5625] while B1 puts its minimum at 0.95 when the truth is 0.50. This is the most useful thing
the repair surfaced, and it was invisible while the code computed B1 and the write-up described B2.

It is deliberately *not* stated as "the baseline buys identifiability". The baseline here is simulated at
u = 0.05 **and the profiler treats that coordinate as known**, which is a strong calibration oracle. The
result demonstrates the value of that specified reference observation inside this design; it says nothing
about whether a fielded actuator can obtain such a baseline. Four cases would need separating before any
deployment claim, and this run tests only the first:

| baseline | tested here |
|---|---|
| observed on the same unit at a *known* cycle count | yes, and assumed exact |
| *assumed* to have normalised life 0.05 | no |
| acquired after unknown prior use | no |
| acquired under different rest, temperature or loading history than the aged observation | no |

### On the two `unresolved` verdicts

The convergence gate is strict by design: any failed point makes the whole profile unresolved, because a
stalled optimiser and a flat likelihood are indistinguishable from the output alone. Both u = 0.50 profiles
have exactly one failure. Whether that failure is load-bearing differs, and the record should say so:

- **B2 at u = 0.50** — the failure is at u = 0.85, with Δ(−log L) = 113, far above the cut and 0.29 away
  from the nearest interval edge. Dropping it gives `identifiable` with the *identical* interval
  [0.45, 0.5625]. The verdict is unresolved by the rule; the interval is robust.
- **B1 at u = 0.50** — the failure is at u = 0.40 with Δ(−log L) = 0.02, inside the flat region that
  decides the classification, so it *is* load-bearing. It hardly matters: this design puts its minimum at
  0.95 when the truth is 0.50, so it locates nothing either way.

The gate was not relaxed after seeing these numbers. The strict verdict stands as the headline and the
diagnostic sits beside it.

## What did *not* change

The collinearity finding is unaffected. Under the corrected whitening the post-onset canonical indices are
γ = 60.8 for {u, onset} and 5.83 for {u, leak} against 1.25 × 10⁶ for the {u, onset, leak} triple —
identical to six significant figures to the merged numbers. The aliasing group, and the point that it is a
*joint* dependency no pairwise angle reveals, both stand.

One caveat the merged record should have carried: the `all_seven` index moved from 6.5 × 10⁷ to 8.3 × 10⁷
under a numerically *better* whitening. A quantity that moves by 28% when the arithmetic improves is
reporting rounding, not structure. That subset is numerically singular — λ_min is at the float64 rank
tolerance — so **no magnitude for it appears in the artifact at all**. `collinearity_report` now returns
`None` with a status of `numerically_singular`, and the two numbers above are quoted here only to show why
the magnitude was withdrawn. The same applies to every pre-onset row, which reports
`undefined_inert_parameter`: a subset containing a parameter with zero sensitivity cannot be confounded
with anything, so its index is undefined rather than infinite.

Study B's own B-PASS verdict, its Cramér–Rao map and its bounds are untouched.

## Verification

- `python -m scripts.run_studyB_structural` — regenerated from the committed code.
- `python -m pytest -q` — 318 passed.
- Five new tests pin the acceptance criteria from the critique: a dimension check proving B2 consumes all
  ten observations and B1 five; a baseline perturbation that must change the B2 likelihood; a failed
  optimisation producing `unresolved`; an open bound that can never be printed as a half-width; and a flat
  profile on a narrow grid that is `domain-limited`, not `structural`.
- Two further tests pin the whitening: it reproduces the quadratic form on a well-conditioned covariance,
  and it stays finite on one with cond > 10²⁰ whose correlation matrix is benign.

## Bound sensitivity — the upper crossing is entirely an artefact of the box

Because both terminations sit on nuisance bounds, the run re-profiles the upper region with a widened but
still physically admissible box: onset fraction 0.30–0.98 instead of the dispersion support 0.45–0.90, and
fatigue exponent 1.0–5.0 instead of 1.2–3.0. The result is decisive.

| u | Δ(−log L), default box | Δ(−log L), widened box | parameters pinned (default → widened) |
|--:|--:|--:|:--|
| 0.9000 | 5.1e-10 | 2.9e-10 | 0 → 0 |
| 0.9500 | 5.8e-10 | 5.1e-10 | 0 → 0 |
| 0.9650 | 3.4e-10 | 2.2e-10 | 0 → 0 |
| 0.9725 | 1.7e-10 | 3.6e-10 | 1 → 0 |
| **0.9800** | **36.54** | **5.7e-10** | **2 → 1** |

The entire upper "rise" — the thing that closed the interval and produced the `identifiable` verdict —
**disappears when the box is widened**. Δ falls from 36.5 to 5.7 × 10⁻¹⁰, which is plateau level. Crossings
go from `[0.98]` to `[]`.

Three consequences, and they are the main result of this closeout:

1. **No resolution figure is supportable.** The upper bound of [0.75, 0.98] is where the optimiser ran out
   of nuisance freedom, not where the likelihood rose. The artifact now refuses to emit a
   `resolution_life_fraction` when a termination is bound-pinned or when the crossing moves.
2. **The `identifiable` verdict is itself bound-dependent**, and the artifact records that as
   `verdict_is_bound_dependent`. Under the widened box the post-onset profile does not close on its upper
   side at all. Whether the post-onset coordinate is identifiable at all is therefore **an open question**,
   not a finding.
3. **The plateau runs to the edge of the physical domain.** Under the widened box the likelihood is flat
   from u = 0.775 all the way to u = 0.98. That is closer to the original "aliased" intuition than to the
   interim "identifiable" reading — though it still does not license the word *structurally*, which needs
   the noiseless symmetry analysis that has not been run.

The honest summary of this whole episode: three successive readings of the same post-onset region gave
"structurally aliased", then "practically aliased, ±0.05", then "identifiable, ±0.21". **All three were
artefacts of how the calculation was bounded** — by a rank test, by a grid edge, and by a nuisance box.
What the data actually support is a flat likelihood across the upper half of the domain and no precision
claim at all.

## What is explicitly unresolved

These are open, and none of them is answered by this run:

- **Whether the chi-square(1) cut at 1.92 is calibrated here.** It is an asymptotic likelihood-ratio
  approximation, and this problem has a nonlinear feature map, bounded nuisance parameters, infeasible
  regions, an estimated and strongly correlated covariance, and near-zero information across the plateau.
  Until a parametric coverage simulation checks it against known u values, the threshold is a **diagnostic
  scale, not a calibrated confidence interval**. If coverage turns out poor, the threshold must not be
  tuned to make it nominal — report an empirical rule or say the scale is diagnostic.
- **Whether the interval terminations survive a justified change of nuisance bounds.** The check above is
  one widening, not a sensitivity study.
- **Coverage, interval width, minimum error and unresolved-fraction across repeated seeds.** Everything
  here is one realisation.
- **Whether any of it holds on a unit other than the canonical one.** A canonical-unit profile cannot
  support a cross-unit observability statement, and Study C already showed transfer is where this project
  fails.
- **Whether a genuinely structural direction exists.** `structural` remains a *candidate* label; a
  noiseless symmetry analysis has not been run.

Filed as `PV-CRIT-09` (coverage and bound-sensitivity study) and `PV-CRIT-10` (repeated-seed and
cross-unit profiling). Items 1.5 and 1.6 of the 2026-09-24 critique remain open within them.

## Honest limits

- No resolution or precision claim is made anywhere in this record. The interval is a **bound on ignorance
  over the tested domain**, not a measurement error bar.
- `domain-limited` and `structural` can only be returned when the caller declares the physical domain.
  Declaring one is a claim — "the grid reached the edge of what is physically possible" — and here that
  claim is [0.02, 0.98], the profiler's own bound on u, not an independently justified physical range.
- `identifiable` in this implementation means only that the profile crosses the chosen threshold on both
  sides of its minimum. It does not imply a unique interior minimum, a symmetric interval, or stability
  under a change of nuisance bounds. It must not be promoted to "well resolved".
- The evaluation is entirely synthetic. Nothing here is evidence about hardware.
