# Dispersion audit — literature/gaps.md item 1 — 2026-09-23

Branch `research/dispersion-audit-20260923` from main `e8a79f4`. Generator
`scripts/run_dispersion_audit.py` (~12 min, `--replot` redraws from the saved result).
**No committed study output changes.** Study A, B and C verdicts and artifacts are untouched.

---

## Correction 1 — the item was partly mis-filed, by me

The gaps item asked to "compute the implied rupture-life distribution from the dispersed degradation-law
parameters and compare against the imposed Weibull," citing Bae, Kuo & Kvam 2007. **That framing does not
apply to this generator.** `fatigue_state` takes `rupture_cycles` as an *input* and expresses every
multiplier in normalised life u = cycles/rupture, so there is no absolute failure threshold to invert.
Bae/Kuo/Kvam concerns threshold-crossing models; this is not one. Rupture is definitional, not derived, so
there is no second distribution to disagree with the first.

The well-posed version of the concern is the reverse: *because* rupture is imposed, the degradation state
reached at rupture is free to vary between units.

## Finding A — the generator does contain an implicit random failure threshold

State at u = 1 across 200 units:

| quantity at rupture | mean | CV | range |
|---|--:|--:|---|
| compliance multiplier | 1.160 | 0.022 | 1.106 – 1.259 |
| loss multiplier | 1.160 | 0.022 | 1.106 – 1.259 |
| fatigue total | 0.121 | 0.193 | 0.071 – 0.226 |
| **leak multiplier** | **20.69** | **0.322** | **8.75 – 45.80** |

Units do not rupture in the same condition. Compliance and loss vary mildly (CV 0.022), but the leak
multiplier at rupture spans a **factor of five**. That is an implicit random failure threshold in the sense
of Wang, Chen & Cai 2020, and it is a modelling choice the preregistration never states. It should be
declared rather than discovered, because a reader would reasonably assume a shared end-of-life condition.

## Correction 2 — my prediction about the transfer effect was wrong

The gaps item predicted that an overstated CV was "inflating the very effect Study C reports," so that a
lower CV would weaken it. **It does not.** The correlation between held-out error and a unit's distance
from the training median is +0.948, +0.965 and +0.956 at CV 0.05, 0.15 and 0.30 — essentially unchanged.
The effect is scale-invariant, not an artefact of the assumed dispersion.

## Finding B — C-FAIL survives every dispersion level, but for opposite reasons

Study C's evaluation re-run on cohorts drawn at three rupture-life CVs. Published cohorts for reference:
Torzini 2024 gives 0.039 and 0.061, Du 2025 gives 0.175. Study A assumes 0.30.

**None of the three is "the realistic" CV.** The published values come from small cohorts of particular
materials, geometries and loading protocols, and none of them measures the apparatus this project will
build; they anchor a lower end rather than establishing a universal lifetime CV. 0.30 remains an *assumed
stress case*. What the sweep supports is the direction of travel across it, not a verdict at any one CV.

| rupture CV | within 0.10 life | beats the clock | estimator mean | clock mean | verdict |
|--:|--:|--:|--:|--:|---|
| **0.05** (Torzini-like) | **10 / 10** | **2 / 10** | 0.027 | **0.021** | C-FAIL |
| **0.15** (Du-like) | 9 / 10 | 4 / 10 | 0.067 | 0.064 | C-FAIL |
| **0.30** (Study A) | 6 / 10 | **7 / 10** | 0.093 | 0.123 | C-FAIL |

The two pass criteria move in **opposite directions** as dispersion changes, and across the tested range
neither point clears 8 on both. At the low, literature-anchored CVs the estimator is accurate — every unit
inside the target — but a bare cycle counter is *more* accurate, so it fails the beat-the-clock criterion.
At the assumed dispersion it beats the clock, because the clock has become bad, but it is no longer accurate
enough. On three points the curves cross at roughly CV 0.27 at about 6.5 of 10, so no tested dispersion
satisfies both. Extrapolation beyond these three points is not warranted.

### The unified rule behind all three

Per-unit, at every CV, the same rule holds: **the pressure features earn their place only on units where
the clock prior is wrong for that unit.**

- At CV 0.05 the held-out lives span 3079–3690 cycles. Only the two most atypical units beat the clock; for
  the eight near-median units the clock alone is better.
- At CV 0.30 the lives span 1416–4775. Every unit with a deviation above 0.14 beats the clock; every unit
  below 0.08 loses to it.

This is a single scale-invariant explanation for the whole Study C result, and it is sharper than "failures
concentrate on short-lived units." It also confirms [R1's](../weekly-research-2026-09-21/README.md) clock-prior
reading from a second direction: the estimator is a clock correction, so it can only add value where the
clock is wrong.

Note the estimator *contains* the clock as an input, so in principle it could match clock-only performance by
zeroing the pressure weights. That it does not, at CV 0.05, means the regularised fit is still spending
variance on pressure features that do not generalise — the ridge penalty is not discounting them enough.

## What this means for the programme

- Study A's CV 0.30 should be justified or changed. It is above every measured value found, and the choice
  materially changes which criterion Study C fails.
- The implicit random failure threshold should be stated in the preregistration.
- The C rule's two criteria are not jointly satisfiable across the dispersion range by this estimator. That
  is a property of the evaluation design as much as of the estimator, and a C2 successor should say which
  criterion it is optimising.

## Checks

`pytest -q` (count in the PR) · numbers 0 · arXiv 0 · fallback 0 / `--for-publication` **2 (BLOCKED)** ·
presentation 0 / 4 · `git diff --check` clean. `pipeline/dispersion.py` gained a `rupture_cv` parameter whose
default is unchanged; verified the default reproduces the committed Study A cohort exactly.
