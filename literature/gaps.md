# Gaps: what the literature does not answer

Two kinds of item. **Actionable now** means the project can settle it in its own simulator or repository
this week. **Needs an experiment** means no amount of analysis will close it.

Nothing here changes a study verdict. These are follow-ups, and none is authorised work — they are
candidates for the owner to schedule.

---

## Actionable now, inside the repository

### 1. The dispersion magnitude is higher than any measured value, and the two randomisations may be inconsistent

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

*Check:* sample the generator, compute the implied rupture-life distribution from the dispersed
degradation-law parameters alone, and compare against the imposed Weibull. Then re-run Study C at CV 0.05
and 0.15 to see whether the C-FAIL verdict and the distance-from-median effect survive realistic dispersion.
Cost: hours. This is the highest-value item in this folder.

### 2. At ten held-out units, the pass/fail distinction may be inside sampling noise

Little et al. 2017 warn that entity-wise cross-validation carries high variance when entities are few. The
[C-FAIL](../docs/specs/observability-program/studyC-transfer.md) verdict is 6 of 10 against a bar of 8. No
source gives a power analysis mapping cohort size to expected pass-rate variance, and the 8-of-10 threshold
itself has **no precedent** in the literature — it is a defensible preregistered choice, not a field standard.

*Check:* resample the 20/10 split many times in the simulator and report the distribution of the pass count
under the same estimator. If 8 of 10 falls comfortably inside that distribution, the verdict stands but must
be reported with its variance. Cost: hours, and it strengthens the result either way.

### 3. "Structurally aliased" needs a structural test

[Study B](../docs/specs/observability-program/studyB-identifiability.md) reports the life coordinate as
structurally aliased after onset, on the evidence of a rank-deficient information matrix and small whitened
angles. Wieland et al. 2021 argue the Fisher approach is "insensitive to practical non-identifiability," and
Chis et al. 2016 show sloppiness is not equivalent to non-identifiability. The current evidence does not
license the word *structurally*.

*Check:* compute Brun's collinearity index over the {life, onset, leak} subset — it scores subsets rather
than pairs, so it names the aliasing group directly — and add a profile-likelihood pass on the reduced
model. Either upgrade the wording or downgrade it to "practically aliased at this noise level." Cost: a day.

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
