# Literature

Working literature base for the cross-unit observability programme. Compiled 2026-09-22.

This folder **complements and does not replace** [`docs/A01_A04_Literature_Review.md`](../docs/A01_A04_Literature_Review.md),
the 59-entry annotated base compiled 2026-06-18. That base was organised around the project's original
framing — P-V hysteresis as a fatigue indicator, pressure-only proprioception, shared-manifold coupling.
The research question has since changed, so this folder covers what the June base does not.

## Why a second base was needed

The June base predates every result in the [observability programme](../docs/specs/observability-program/program.md):

| finding | date | what it created a literature need for |
|---|---|---|
| Study A: dispersion breaks the indicator's unit-invariance in value but not in trigger timing | 2026-09-16 | between-unit variability and population/hierarchical degradation models |
| Study B: the latent life coordinate is identifiable before the acceleration onset and structurally aliased with onset and leak after it | 2026-09-16 | identifiability and observability theory — Fisher information, practical identifiability, parameter aliasing |
| Study C: one estimator transferred to 10 unseen units reached only 6/10 within target, **C-FAIL** | 2026-09-16 | cross-unit transfer, domain generalisation, unit-level holdout protocols |
| R1 failure map: the estimator is *a clock corrected by pressure*; muting the clock costs 0.120 life, muting pressure 0.051; failures concentrate on units whose life is atypical | 2026-09-19 | remaining-useful-life estimation when a unit's total life is unknown, and population-prior personalisation |
| C2 design: a probe-schedule axis with a probe-count-matched oracle | 2026-09-20 | optimal inspection scheduling and degradation-test measurement planning |

The June base contains essentially nothing on the first four rows.

## Method, and its limits

Six parallel searches, one per gap theme, each instructed to report only sources actually retrieved and to
mark whether it read the full text or only a search snippet. Grading follows the repository's
[research-analysis doctrine](../docs/reviews/novelty-check-2026-09-16.md): **aboutness decides eligibility,
importance never does**. Citation counts and venue prestige were not used to judge topical relevance.

- **Aboutness** — 3 directly answers the question, 2 same domain, 1 background, 0 dropped.
- **Evidence** — A replicated/validated or standard result, B single well-controlled study or rigorous
  derivation, C simulation only or small-n, D position paper or preprint claim.
- **Provenance** — `[full-text]` where the paper or abstract page was fetched, `[search-snippet]` where only
  a search result summary was seen. A snippet-only entry is *unverified*, not merely less important.

Honest limits of this pass, stated up front:

1. **Search-engine survivorship.** These are web and domain-restricted searches, not Scopus or Web of
   Science queries. What the index ranked low is invisible here. The
   [novelty check](../docs/reviews/novelty-check-2026-09-16.md) already flags a Scopus pass as a
   precondition for any submission, and that is still outstanding.
2. **Snippet-only entries are provisional.** Where an entry is marked `[search-snippet]`, the finding line
   reflects a summary, not a reading. Do not cite those without opening them.
3. **Absence is not proof.** Nothing here establishes global novelty. It establishes distinctiveness within
   what was retrieved.
4. **No entry here changes a study verdict.** Study A's A-FAIL, Study B's B-PASS and Study C's C-FAIL stand
   on their own evidence.

## Contents

| file | theme | serves |
|---|---|---|
| [`01-identifiability-observability.md`](01-identifiability-observability.md) | Fisher information, CRLB, structural vs practical identifiability, parameter aliasing | Study B |
| [`02-unit-variability-population.md`](02-unit-variability-population.md) | random-effects degradation, lifetime scatter, population vs individual prognostics | Study A, Study C |
| [`03-transfer-unseen-units.md`](03-transfer-unseen-units.md) | cross-unit transfer, domain generalisation, calibration transfer, unit-level holdout | Study C |
| [`04-rul-unknown-life.md`](04-rul-unknown-life.md) | Bayesian personalisation of a population prior, condition-based vs scheduled policies | R1's clock-prior finding |
| [`05-measurement-scheduling.md`](05-measurement-scheduling.md) | optimal inspection intervals, degradation-test measurement planning | Study C2's schedule axis |
| [`06-soft-actuator-recent.md`](06-soft-actuator-recent.md) | 2024–2026 soft actuator durability, self-sensing, multi-specimen data | the project's empirical foundation |
| [`claim-ledger.md`](claim-ledger.md) | every project claim mapped to supporting and counter evidence | the whole programme |
| [`gaps.md`](gaps.md) | what the literature does **not** answer, and what only an experiment can settle | next-step decisions |

## How to use this when writing

Claim language is governed by the [RoboSoft v2 claim spine](../docs/specs/robosoft-v2/claim-spine.md), not by
this folder. A citation here supports a *method* or a *prior finding*; it never upgrades a simulation-only
result into an experimental one. Before citing an entry marked `[search-snippet]`, open the paper.
