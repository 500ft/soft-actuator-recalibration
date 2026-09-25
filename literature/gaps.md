# Gaps: what the literature does not answer

Two kinds of item. **Actionable now** means the project can settle it in its own simulator or repository
this week. **Needs an experiment** means no amount of analysis will close it.

Nothing here changes a study verdict. These are follow-ups, and none is authorised work — they are
candidates for the owner to schedule.

---

## Actionable now, inside the repository

*Items 1 and 3 are resolved; the rest stand.*

### 1. ~~The dispersion magnitude and the two randomisations~~ — RESOLVED 2026-09-23

[Study A](../docs/specs/observability-program/studyA-preregistration.md) draws rupture life Weibull with
**CV 0.30**, citing "repo fixture (validation cohort); order of Torzini 2024 / Frontiers 2023 scatter."
Two problems, both checkable:

- **The cited order is wrong.** Torzini 2024 measures CoV **3.9 %** (TPU) and **6.1 %** (cast silicone) at
  n = 5 per group. Du 2025 measures **17.5 %** at n = 3. CV 0.30 is 5–8× the cited source and above every
  measured value located. Since [R1](../evidence/weekly-research-2026-09-21/README.md) found transfer error
  tracks a unit's distance from the training median, an overstated CV would **inflate the very effect
  Study C reports**.
- **Two randomisations are specified independently.** Rupture life is drawn Weibull *and* the
  degradation-law parameters are separately dispersed. Bae, Kuo & Kvam 2007 establish that a degradation
  model plus a random-parameter distribution already *implies* a lifetime distribution. If the implied and
  imposed distributions disagree, the generator is internally inconsistent.

**RESOLVED 2026-09-23** ([evidence](../evidence/dispersion-audit-2026-09-23/README.md)), with two
corrections to this item as filed.

*Correction 1 — the inconsistency framing was wrong.* Rupture life is definitional here, an input to
`fatigue_state`, with every multiplier expressed in normalised life. There is no absolute failure threshold
to invert, so there is no "implied" distribution to disagree with the imposed one. Bae/Kuo/Kvam concerns
threshold-crossing models and this is not one. The well-posed version is the reverse: because rupture is
imposed, the *state at rupture* may vary — and it does. Across 200 units the leak multiplier at rupture
spans 8.75–45.80 (CV 0.32), an implicit random failure threshold the preregistration never declares.

*Correction 2 — the prediction was wrong.* This item predicted an overstated CV was inflating the
distance-from-median effect. It is not: the correlation is +0.948, +0.965 and +0.956 at CV 0.05, 0.15 and
0.30. The effect is scale-invariant.

*The real finding.* C-FAIL survives every dispersion level **for opposite reasons**. At a literature-anchored
CV 0.05 the estimator is accurate (10/10 within target) but a bare cycle counter is *better* (2/10 beat it).
At Study A's CV 0.30 it beats the clock (7/10) but is no longer accurate (6/10). The two criteria move in
opposite directions and neither point clears 8 on both. The unified per-unit rule at every CV: the pressure
features earn their place only on units where the clock prior is wrong. Study A's CV 0.30 still needs
justifying, since it is above every measured value and decides which criterion Study C fails. Equally, no
tested CV may be called the realistic one: the published figures are specific designs, not a measurement of
this project's apparatus, so 0.30 stays an assumed stress case and 0.05/0.15 a literature-anchored floor.

### 2. At ten held-out units, the pass/fail distinction may be inside sampling noise

Little et al. 2017 warn that entity-wise cross-validation carries high variance when entities are few. The
[C-FAIL](../docs/specs/observability-program/studyC-transfer.md) verdict is 6 of 10 against a bar of 8. No
source gives a power analysis mapping cohort size to expected pass-rate variance, and the 8-of-10 threshold
itself has **no precedent** in the literature — it is a defensible preregistered choice, not a field standard.

*Check:* resample the 20/10 split many times in the simulator and report the distribution of the pass count
under the same estimator. If 8 of 10 falls comfortably inside that distribution, the verdict stands but must
be reported with its variance. Cost: hours, and it strengthens the result either way.

### 3. ~~"Structurally aliased" needs a structural test~~ — RESOLVED 2026-09-23

[Study B](../docs/specs/observability-program/studyB-identifiability.md) reports the life coordinate as
structurally aliased after onset, on the evidence of a rank-deficient information matrix and small whitened
angles. Wieland et al. 2021 argue the Fisher approach is "insensitive to practical non-identifiability," and
Chis et al. 2016 show sloppiness is not equivalent to non-identifiability. The current evidence does not
license the word *structurally*.

**RESOLVED 2026-09-23, CORRECTED 2026-09-25.** Both diagnostics were run
([evidence](../evidence/studyB-structural-2026-09-23/README.md)). Brun's subset index confirms the aliasing
group and shows it is a *triple* — {u, onset, leak} at 6.3 × 10⁵ against 57 for {u, onset} and 8.3 for
{u, leak} — a joint dependency no pairwise measure reveals. A side finding: pre-onset the onset fraction, leak and exponent are exactly inert, so they
are irrelevant there rather than confounded.

The profile-likelihood half of that run was **wrong and has been redone**
([correction](../evidence/studyB-structural-correction-2026-09-25/README.md)). It described a stacked
baseline-plus-snapshot likelihood but computed the snapshot alone, and its grid ended at u = 0.90, which is
the post-onset truth, so the upper bound was unreachable and the reported "±0.05 life" was a grid edge.
Repairing it also exposed a covariance inverted at condition number 1.7 × 10²⁶, an optimiser searching
across eleven orders of magnitude, and a feature that is undefined on much of the parameter box.

Corrected: under the stacked design the post-onset coordinate is **identifiable**, not practically aliased,
resolvable to about **±0.21 life** with the point estimate biased low by 0.12. The snapshot alone is only
practical, and at the pre-onset truth it puts its minimum at 0.95 when the truth is 0.50 — so the young
baseline is what buys identifiability. The collinearity result above is unchanged to six figures.

### 4. The probe may be measuring a rate artefact rather than a hysteretic state

de la Morena et al. 2025 state that condition characterisation should use quasi-static excitation because
"higher-frequency excitations would introduce phase lag and distort hysteresis loop characterization."
Study A probes at a fixed 2 Hz.

*Check:* Study B's feature set already contains loop area at 1 Hz and 4 Hz. Compare how much of the
indicator's life-dependence is rate-invariant. If the two frequencies disagree systematically, part of the
indicator is viscoelastic phase lag rather than fatigue state. Cost: hours, using existing code.

### 5. The generator's degradation shape disagrees with measured actuator behaviour

Two independent studies — Bui 2023 and Schreiber & Manns 2026 — report a **log-saturating break-in
transient over roughly 160 cycles**, after which kinematic drift plateaus. The project's generator applies a
Mullins term stabilising within a few cycles and then a monotone accelerating fatigue term. Nobody has shown
whether a P–V indicator is confounded by that transient.

*Check:* compare the generator's early-life indicator trajectory against a log-saturating shape and record
whether the difference matters over the probed range. Cost: hours. Informs whether the generator needs a
break-in phase before any hardware comparison.

---

## Needs an experiment

### 6. No one has tracked pressure–volume features over a full fatigue life on multiple specimens

The closest is Bui 2023, which tracks *tip-trajectory* hysteresis on ten actuators and stops at 640–1,280
cycles without reaching failure. The only located P–V-over-cycling measurement is a patent, before-and-after
only.
*Needed:* quasi-static P–V loops at ten or more points across life on eight or more specimens cycled to
failure. This is the project's [Study D/E](../docs/specs/observability-program/program.md) and it is what a
reviewer will demand.

### 7. Cross-unit non-transfer is demonstrated, but not yet for pressure–volume on identical units

Wall 2023 shows 97 % within-unit collapsing to 35 % across nominally identical soft pneumatic actuators, but
for *acoustic* sensing and *classification*. Lee 2025 rejects V–P model equality at p < 10⁻⁷, but across
deliberately different designs and in *hydraulic* actuators.
*Needed:* the Chow-test design of Lee et al. applied within a single batch, on pneumatic units.
Thakker et al. 2026 report 24 fabrications across two operators and is the most likely existing source of
the underlying data — worth contacting the authors.

### 8. No pre-deployment abstain test exists

Guenard et al. 2007 argue transfer counts as successful only if leverage and residual diagnostics survive,
not on error alone — but they flag samples after the fact. Nothing in the retrieved literature predicts,
from an *unlabelled* new unit, whether transfer will fail on it. Yet that is exactly the decision a fielded
recalibration trigger must make.
*This is the most defensible next contribution available to this repository.* A concrete version: report
per-unit leverage or novelty relative to the training cohort alongside the 6-of-10 result, and test whether
it separates the four failures. Partly actionable now; a real claim needs hardware.

### 9. No agreed end-of-life criterion for a soft actuator

Leak, stiffness drift and stroke loss are all candidates, and the literature picks none. Random failure
thresholds are formalised but always parameterised from observed failures. Any remaining-life result will be
conditional on a definition the project must choose and defend.

### 10. No benchmark for how much a clock covariate should contribute

R1's muting experiment has no published counterpart. The field reports error against a baseline model, not
feature-ablation of the age term, so there is no external standard for "a healthy estimator loses at most
X % when age is removed." Establishing one is a contribution rather than a gap to be filled by citation.

### 11. Policy performance under a mis-specified estimator is unquantified

Every condition-versus-schedule comparison found assumes a correctly specified condition signal. None models
a state-triggered policy whose state is *partly a clock* — which is what R1 showed this project has. Whether
such a policy still beats a fixed schedule is open, and on the evidence assembled here it is the sharpest
question the project's own data could answer.

---

## Outstanding from the previous pass

The [novelty check](../docs/reviews/novelty-check-2026-09-16.md) requires a **Scopus or Web of Science pass**
before any submission. An IEEE Xplore pass was completed on 2026-09-16. Scopus needs an institutional login
and remains the owner's to run.
