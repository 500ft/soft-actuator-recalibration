# Study B follow-up — correction to the 2026-09-23 resolution claim

**Date:** 2026-09-25
**Supersedes:** [`evidence/studyB-structural-2026-09-23/`](../studyB-structural-2026-09-23/README.md)
**Trigger:** owner critique, `docs/LITERATURE_CRITIQUE_AND_NEXT_STUDIES_2026-09-24.txt`, item 1 (P0)
**Historical record:** the original result is retained byte-for-byte at
`data/sim/studyB/studyB_structural_superseded_2026-09-23.json` with an additive annotation. Nothing in
the 2026-09-23 record was rewritten.

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

**The post-onset case converged at every one of its 25 points.** It is the case the "structurally aliased"
claim was about, and under the design Study B's write-up actually describes it is **identifiable**, not
practically aliased. The supported resolution is **±0.21 life**, the half-width of [0.75, 0.98] about the
minimum — roughly four times coarser than the withdrawn ±0.05. The point estimate also sits at 0.775
against a truth of 0.90, a downward bias of 0.12 life that the earlier record did not surface.

**The baseline observation is what buys identifiability.** At the same truth, B1 on the snapshot alone is
only *practical*: its upper bound never crosses the cut inside the physical domain, and its minimum sits at
0.65. At the pre-onset truth the contrast is starker still — B2 brackets the truth at [0.45, 0.5625], while
B1 puts its minimum at 0.95 when the truth is 0.50. This is the single most useful thing the repair
surfaced, and it was invisible while the code computed B1 and the write-up described B2.

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
under the corrected whitening. That subset is numerically singular, so its index sits at the float64 noise
floor and is only meaningful as "astronomically large". It must never be quoted as a number.

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

## Honest limits

- The ±0.21 resolution is one noise realisation at one operating point on one canonical unit. It is not a
  distribution, and no uncertainty is attached to it.
- `domain-limited` and `structural` can only be returned when the caller declares the physical domain.
  Declaring one is a claim — "the grid reached the edge of what is physically possible" — and here that
  claim is [0.02, 0.98], which is the profiler's own bound on u, not an independently justified range.
- `structural` remains a *candidate* label. Establishing a genuinely structural direction needs a noiseless
  symmetry analysis, which has not been run. Critique item 1 point 5 records that as outstanding.
- The chi-square(1) cut at 1.92 is an asymptotic approximation whose adequacy at this sample size has not
  been checked. Critique item 1 point 6 records that as outstanding too.
