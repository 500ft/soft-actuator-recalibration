> **SUPERSEDED 2026-09-25.** The resolution claim below — "practically aliased ... resolvable to about
> ±0.05 life" — is **withdrawn**. The run behind it described a stacked baseline-plus-snapshot likelihood
> but computed the snapshot alone, ended its grid at the post-onset truth so no upper bound could exist,
> and ignored a non-converged point. Corrected result: under the stacked design the post-onset coordinate
> is **identifiable**, resolvable to about **±0.21 life**, with the minimum biased low by 0.12. The
> collinearity finding in this record is unaffected and still stands.
> See [`evidence/studyB-structural-correction-2026-09-25/`](../studyB-structural-correction-2026-09-25/README.md).
> This record is left otherwise unedited on purpose.

# Study B follow-up — is the post-onset aliasing structural? — 2026-09-23

Task: [`literature/gaps.md`](../../literature/gaps.md) item 3. Branch `research/studyB-structural-test-20260923`
from main `e8a79f4`. Generator `scripts/run_studyB_structural.py` (7 min), tools added to
`pipeline/identifiability.py`, 12 tests in `tests/test_structural_identifiability.py`.

**Study B's B-PASS verdict and its reported bounds are unchanged.** This decides only which word the
finding supports.

## Why this was run

Study B reported the latent life coordinate as **"structurally aliased"** with the acceleration-onset
fraction and the leak multiplier after onset, on the evidence of a rank-deficient Fisher information matrix
and small whitened angles. The literature review surfaced two objections to that inference:

- Wieland et al. 2021 — a Fisher-based analysis "is insensitive to practical non-identifiability."
- Chis et al. 2016 — sloppiness is not equivalent to non-identifiability, so an ill-conditioned information
  matrix does not license the word *structural*.

The two prescribed diagnostics were run: Brun et al. 2001's collinearity index over parameter *subsets*, and
a profile likelihood over u with every nuisance parameter re-optimised at each point.

## Result 1 — the aliasing group is real, and it is a *triple*, not a pair

Brun's index on the B2 stacked design, post-onset points only (4 points across the canonical unit and three
dispersed units; values above ~10 flag a poorly identifiable subset):

| subset | median γ | reading |
|---|--:|---|
| u + τ (orthogonal control) | **1.05** | independent, as expected |
| u + leak | **8.27** | *below* the poor flag |
| u + onset fraction | **56.96** | poorly identifiable |
| **u + onset + leak** | **6.27 × 10⁵** | jointly near-dependent |

The triple is four orders of magnitude above either pair. **No pairwise measure reveals this**, which is
exactly why a subset index was required and why Study B's pairwise angles under-stated the problem. This
*confirms* Study B's naming of {life, onset, leak} as the aliasing group, on stronger evidence than it had.

### A trap that had to be handled

Before onset, the onset fraction, leak multiplier and fatigue exponent have **exactly zero** sensitivity —
verified directly: their whitened sensitivity magnitudes are `0`, while u's is 59.2. Their collinearity is
therefore *undefined*, not infinite-because-aliased. Those parameters are **inert** pre-onset, not confounded.
The runner records an `inert_parameters` field per point and excludes inert subsets from the aggregate, so
an infinity is never read as aliasing. This sharpens the story: pre-onset the nuisance parameters do not
exist as a confound at all; post-onset they activate *and* immediately entangle with u.

## Result 2 — the aliasing is practical, not structural

Profile likelihood on the canonical unit, all six nuisance parameters re-optimised at each of 17 u values,
with the 95 % χ²(1) cut at Δ(−log L) = 1.92:

| true u | verdict | minimum at | u values within the cut |
|---|---|--:|---|
| 0.50 (pre-onset) | **identifiable** | 0.50 | 0.50 only — 1 of 17 points |
| 0.90 (post-onset) | **practical** | 0.80 | 0.80–0.90 — 3 of 17 points |

Reading these against Raue et al. 2009's criterion:

- At u = 0.50 the profile rises steeply on **both** sides and recovers the truth exactly. Identifiable.
- At u = 0.90 the profile is flat at ≈ 4 × 10⁶ for every u ≤ 0.70, falls off a cliff between 0.75 and 0.80,
  and is flat at the floor across 0.80–0.90. It rises on **one side only**.

A profile flat in *both* directions would be structural non-identifiability. This one is not. The data
still separate post-onset from pre-onset decisively — it is the *resolution within* the post-onset region
that collapses, to roughly ±0.05 life, and the minimum sits at 0.80 when the truth is 0.90, a bias of one
resolution width.

**Verdict: practical, not structural.**

## Consequence — wording corrected

| was | now |
|---|---|
| "structurally aliased with onset fraction and leak" | "**practically aliased at this noise level**: resolvable to about ±0.05 life within the post-onset region, but not finer" |

Updated in `docs/results.md`, `docs/specs/observability-program/studyB-identifiability.md`,
`evidence/observability-2026-09-16/README.md` and `literature/claim-ledger.md`. The finding itself — a
regime boundary at the acceleration onset — stands; only its strength is corrected. Being practical rather
than structural is the *more useful* result, because a practical limit can be moved by better probes or
lower noise, which is what a C2 successor could test.

## Checks

`pytest -q` (count in the PR) including 12 new tool tests · numbers 0 · arXiv 0 · fallback 0 /
`--for-publication` **2 (BLOCKED)** · presentation 0 / 4 · `git diff --check` clean. Study A, Study C and the
committed Study B bounds are untouched; the new outputs are additional files under `data/sim/studyB/`.
