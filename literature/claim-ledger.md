# Claim ledger

Every claim the project currently makes, mapped to supporting and counter evidence from this folder.
Following the repository's [research-analysis doctrine](../docs/reviews/novelty-check-2026-09-16.md): if a
claim has no entry here, it should not appear in a write-up.

Confidence is about the *literature's* support for the claim, not about the project's internal evidence,
which is recorded in the [study verdicts](../docs/results.md).

---

```
Claim 1: P-V hysteresis changes with fatigue and has been used to assess it.
Support: Mosadegh 2014 (B), Libby 2023 (B), Bui 2023 (A, n=10), Torzini 2024 (A, n=5 per group)
Counter: none
Confidence: HIGH. Prior art; the project does not claim it.
```

```
Claim 2: Pressure-only proprioception is established.
Support: Wang & Wang 2020 (B), Joshi & Paik 2023 (B), Wang 2025 (B, linear readout suffices for pose),
         Stella 2026 (B, 6 pressure channels vs 3 DoF, bending error 0.11 ± 0.02)
Counter: none for pose. All assume a healthy, per-unit-calibrated actuator.
Confidence: HIGH. Also prior art. Note Wang 2025 shows a *linear* readout suffices for pose, so
         pose-from-pressure is not the hard part; fatigue-state-from-pressure is.
```

```
Claim 3: Between-unit dispersion of nominally identical soft actuators is large enough to matter.
Support: Torzini 2024 (A) CoV 3.9% TPU / 6.1% silicone, n=5 per group;
         Du 2025 (B) 531/409/383 cycles, CoV 17.5%, n=3;
         Bui 2023 (A) burst pressure 37.1-41.15 kPa across n=10;
         Gehling 2023 (A) mechanism: randomly distributed flaws drive nucleation-life scatter;
         Bowness & Doumit 2026 (D) manual winding named as a major source of unit-to-unit variation
Counter: the measured magnitudes are all well BELOW the project's assumed CV 0.30.
Confidence: HIGH that dispersion exists and is physically grounded.
            LOW that the project's assumed magnitude is right. See gaps.md item 1.
```

```
Claim 4: Learned models transfer poorly to units they were not trained on.
Support: Wall 2023 (B) 97% within-unit -> 35% on an unseen NOMINALLY IDENTICAL soft pneumatic actuator
           (25% chance baseline), only 47% when pooling multiple actuators -- the closest precedent found;
         Lee 2025 (B) Chow tests reject V-P model equality, smallest F = 1118.32 vs critical 5.9, p < 1e-7;
         Saeb 2017 (B) record-wise CV inflates accuracy that collapses under entity-wise CV;
         Yan & Wiston 2026 (C) ~17x error inflation moving from row-random to leave-one-cell-out;
         Kim 2020 (B) soft sensors "suffer from high manufacturing tolerances and signal drift"
Counter: Lee 2025 is HYDRAULIC and tests deliberately different designs spanning a 35x volume range,
         so it bounds cross-design, not cross-unit, non-transfer.
Confidence: HIGH, and materially stronger than at the 2026-09-16 novelty check, which rated this
            moderate on two thin sources. Wall 2023 is direct, in-domain and on nominally identical units.
```

```
Claim 5 (the open question): No published work computes the identifiability of a latent fatigue state
from pressure-only features under unit dispersion, nor reports unseen-unit transfer of such an estimator.
Support: absence across 6 web searches (2026-09-16), an IEEE Xplore pass, and 6 further theme searches
         (2026-09-22); nearest neighbours remain Lin & Khoo 2024 (B, regime-dependent identifiability in
         batteries), Acuna 2018 (B, Bayesian CRLB for prognostics), Wall 2023 (B, cross-unit failure but
         classification, not state estimation);
         Pana 2026 (D) systematic review: of 106 records the fault-detection subset was 9 adjacent and
         5 indirect, with no direct soft-actuator health-state benchmark
Counter: none found.
Confidence: MODERATE-HIGH, up from moderate. Still distinctiveness within retrieved evidence, not proven
            global novelty. The Scopus pass remains outstanding.
```

```
Claim 6 (Study B): The latent life coordinate is identifiable before the acceleration onset, and after
it remains identifiable from a baseline-plus-snapshot probe but only coarsely (corrected 2026-09-25).
Support (method): Kay 1993 (A), Hermann & Krener 1977 (A), Powel & Morgansen 2015 (B) for empirical
         Gramian rank tests, Acuna 2018 (B) for a Bayesian CRLB used as a prognostic design criterion
Support (precedent for regime-dependent identifiability): Lin & Khoo 2024 (B) -- batteries, four regimes
         where different degradation modes limit the observable
Counter -- and this is the important one: Wieland 2021 (D) argues the FIM approach has "severe
         shortcomings" for practical identifiability and is "insensitive to practical non-identifiability",
         recommending profile likelihood; Chis 2016 (B) shows sloppiness is NOT equivalent to
         non-identifiability, so an ill-conditioned FIM does not license the word "structurally"
Confidence: MODERATE for the regime boundary as an observation about this generator.
            RESOLVED 2026-09-23, CORRECTED 2026-09-25. Brun's subset index confirms the {u, onset, leak}
            triple aliases jointly (1.25e6 vs 60.8 and 5.83 for the pairs) and that result is unchanged.
            The profile likelihood was recomputed after the 2026-09-24 critique found it used the snapshot
            alone while claiming a stacked design, and stopped its grid at the post-onset truth. Under the
            stacked design the post-onset coordinate is IDENTIFIABLE, resolvable to about +/-0.21 life with
            the minimum biased low by 0.12; the snapshot alone is only practical. Do not quote the
            all_seven index as a number: that subset is numerically singular.
            See evidence/studyB-structural-correction-2026-09-25/.
```

```
Claim 7 (R1): The Study C estimator is a clock corrected by pressure, and fails where the clock is wrong.
Support (architecture it approximates): Zhou & Howey 2023 (B) hierarchical Bayes combining individual and
         population features beats the non-hierarchical baseline by 12-13%;
         Gebraeel 2005/2006 (B) population prior + unit-specific Bayesian update;
         Elwany & Gebraeel 2008 (C) population distributions "do not distinguish between the different
         degradation characteristics of individual components"
Support (why it matters): de Jonge 2017 (C) names measurement accuracy and failure-level randomness as the
         factors eroding a condition-based policy's advantage; Andersen & Nielsen 2024 (C) the advantage
         GROWS with dispersion in per-unit mean life
Counter: no published work reports a clock-ablation of a prognostic estimator, so there is no external
         benchmark for how much a healthy estimator should lose when age is removed.
Confidence: HIGH for the finding itself (it is a direct measurement on the committed model).
            The literature supplies the fix (hierarchical/Bayesian personalisation) but no comparator.
```

```
Claim 8 (Study C protocol): Unit-level holdout is the correct evaluation protocol.
Support: Saeb 2017 (B) canonical statement that entity-wise CV is required when the use case is a new
         entity; Saxena 2014 (D) fleet-trained models must be scored per unit; ADATIME / Ragab 2023 (A)
         many time-series adaptation papers use labelled target data for model selection, violating the
         premise; Arias Chao 2021 (B) reference design preserving unit identity
Counter: Little 2017 (D) entity-wise CV carries HIGHER VARIANCE when entities are few.
Confidence: HIGH that the protocol is right. The 8-of-10 threshold itself has NO precedent in the
            literature and at n=10 the 6-vs-8 distinction may sit inside sampling variance.
            See gaps.md item 2.
```

```
Claim 9 (Study C2 hypothesis): Probe placement, at fixed probe count, changes what can be estimated.
Support: Tung & Chen 2025 (B) "designs with periodic inspection times are the least efficient";
         Munford & Shahani 1972 (A) near-optimal NON-periodic sequences at matched inspection count;
         Guestrin 2005 (B) same number of observations, better placed, with a submodularity guarantee;
         Tonsing 2014 (B) sloppiness is partly a property of the experimental design, hence curable by it
Counter: Severson 2019 (B) 124 cells, cycle lives 150-2300, predicted to 9.1% error from the first 100
         cycles -- a window over which median capacity had INCREASED 0.2%. A pre-onset window carried the
         signal in another system, so "probes fell pre-onset" cannot alone explain transfer failure.
         Jawaid & Smith 2015 (B) greedy scheduling guarantees hold for log-det surrogates and FAIL for
         estimation-error trace, which is what C2 measures.
Confidence: MODERATE. The design-matters claim is well supported; the specific causal story
            ("timing caused Study C's failure") is not, and Severson is a live counterexample.
```

```
Claim 10: A state-triggered recalibration policy beats a cycle-count clock.
Support: Andersen & Nielsen 2024 (C) largest observed advantage 45%, growing with life dispersion;
         Cheikh 2026 (C) quantile-based inspection beats block replacement on mean AND variability;
         Chen 2015 (C), Fauriat & Zio 2020 (C) for the policy machinery
Counter: de Jonge 2017 (C) the advantage shrinks with noisy measurements and random failure levels;
         Pedersen & Vatn 2022 (B) a remaining-life-driven policy can RAISE the probability of
         long-downtime cycles, so a fixed schedule can be preferable once variance enters the objective;
         Avtges 2026 (B) if damage adaptation costs under a minute, the calibration-event budget needs a
         cost model that survives that comparison
Confidence: LOW-MODERATE, and conditional. Every comparison found assumes a CORRECTLY SPECIFIED condition
            signal. None models this project's actual situation -- a state-triggered policy whose state is
            partly a clock. That regime is unquantified. See gaps.md item 5.
```

---

## Claims the project should NOT make on this evidence

- That the pressure–volume indicator is validated on hardware. No study tracks P–V features over a full
  fatigue life on multiple specimens; the closest tracks tip-trajectory hysteresis and stops before failure.
- That transfer failure is *caused* by observation timing. Severson 2019 is an unrebutted counterexample.
- That the life coordinate is *structurally* non-identifiable. Tested and the answer is no. Say
  "identifiable after onset from a baseline-plus-snapshot probe, but only to about ±0.21 life, with the
  point estimate biased low". **The earlier "±0.05 life" is withdrawn** — it was read off a grid edge.
- That a single aged snapshot can locate life. It cannot: without the young baseline the post-onset profile
  never closes on its upper side, and pre-onset it puts its minimum at the wrong end of the domain.
- That the assumed CV of 0.30 is realistic for soft actuators. Every measured value found is lower.
- That a state-triggered policy beats a clock in general. The literature says it depends on measurement
  accuracy and life dispersion, and can reverse under a variance-aware objective.
