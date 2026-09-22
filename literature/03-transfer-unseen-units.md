# 03 — Transfer to unseen units

Serves [Study C](../docs/specs/observability-program/studyC-transfer.md), which trained one ridge estimator
on 20 simulated units and reached 6 of 10 held-out units within target against a preregistered bar of 8,
recording **C-FAIL**.

Grading and provenance rules in [README](README.md).

---

## Read this first

### The closest precedent found anywhere — real soft pneumatic actuators, nominally identical

- **Wall, Zöller & Brock 2023** — "Passive and active acoustic sensing for soft pneumatic actuators,"
  *International Journal of Robotics Research* 42(8). DOI 10.1177/02783649231168954; arXiv:2208.10299.
  **[aboutness 3] [evidence B] [full-text]** Reports **97 % classification within a single soft pneumatic
  actuator but only 35 % on an unseen, nominally identical actuator** against a 25 % chance baseline, rising
  to just **47 %** when training pools multiple actuators. The authors attribute this to per-specimen
  silicone fabrication signatures and recommend per-actuator calibration.
  **Bearing:** the closest published analogue to Study C's failure mode — near-perfect within-unit, collapse
  across nominally identical units, on real soft pneumatic hardware. Stronger corroboration than the
  cross-design hydraulic result in [06](06-soft-actuator-recent.md), because these units *were* meant to be
  the same. It also shows pooling more training units helps only marginally, which tempers any expectation
  that enlarging the cohort would rescue Study C.

### A caution that lands directly on the C-FAIL verdict

- **Little, Varoquaux, Saeb, Lonini, Jayaraman, Mohr & Kording 2017** — "Using and understanding
  cross-validation strategies," *GigaScience* 6(5):gix020. DOI 10.1093/gigascience/gix020.
  **[2] [D] [search-snippet]** The counterpoint to entity-wise validation: it is correct when the target use
  case is an unseen entity, but it carries **higher variance when entities are few**.
  **Bearing:** with 10 held-out units, the difference between 6 and 8 passes may sit inside sampling
  variance. The C-FAIL verdict is preregistered and stands, but it should be reported with this caveat, and
  the project can settle the question in its own simulator by resampling the split. Logged in
  [gaps.md](gaps.md).

- **Gulrajani & Lopez-Paz 2021** — "In Search of Lost Domain Generalization," *ICLR*; arXiv:2007.01434.
  **[3] [A] [search-snippet]** On a common testbed of 7 datasets and 9 algorithms, carefully tuned empirical
  risk minimisation matches or beats every published domain-generalisation algorithm, and none beats it by
  more than a point; a method without a stated model-selection rule is incomplete.
  **Bearing:** deflationary and reassuring. The plain ridge estimator is not obviously the wrong model class,
  and the gap is more likely in the data and protocol than in algorithmic sophistication. It also supports
  the C2 decision to hold the estimator fixed and vary inputs and schedule instead.

---

## (a) Cross-unit and cross-machine transfer for remaining life

- **Al-Dahidi, Di Maio, Baraldi & Zio 2016** — "Remaining useful life estimation in heterogeneous fleets
  working under variable operating conditions," *Reliability Engineering & System Safety* 156.
  DOI 10.1016/j.ress.2016.07.019. **[3] [B] [search-snippet]** Formalises the fleet case where units differ
  in history, material and manufacturing, and estimates life by first identifying homogeneous *sub-fleets*
  rather than fitting one fleet-wide model. **Bearing:** the standard precedent that one estimator over a
  heterogeneous cohort is the wrong object, and that stratification — for instance by lifetime regime — is
  the accepted fix.
- **Zhu, Peng & Wang 2022** — "Bayesian transfer learning with active querying for intelligent cross-machine
  fault prognosis under limited data," *Mechanical Systems and Signal Processing* 183:109628.
  DOI 10.1016/j.ymssp.2022.109628. **[3] [B] [search-snippet]** Cross-*machine* prognosis using Bayesian
  transfer plus active querying to choose which target observations to label. **Bearing:** the "buy a few
  labels on the new unit" strategy — the cheapest known remedy for Study C's four failing units, and one
  that a physical pilot could actually afford.
- **Mao, Zhang & Feng 2023** — "Tensor representation-based transferability analytics and selective transfer
  learning of prognostic knowledge," *RESS* 242:109695. DOI 10.1016/j.ress.2023.109695.
  **[3] [B] [search-snippet]** Introduces an explicit *transferability analytic* and selects which sources to
  transfer from rather than using all. **Bearing:** implies the 20 training units should not carry equal
  weight for an atypical-lifetime target.
- **Nejjar, Geissmann, Zhao, Taal & Fink 2023** — "Domain Adaptation via Alignment of Operation Profile for
  Remaining Useful Lifetime Prediction," arXiv:2302.01704. **[3] [C] [full-text]** Shows existing adaptation
  methods fail because they align marginal distributions without distinguishing operation phases, producing
  misalignment when phases are under- or over-represented. **Bearing:** the structural analogue of Study C —
  short-lived units are under-represented in the training cohort, and the composition of the trajectory, not
  just its distribution, is what breaks.
- **Fan, Nowaczyk & Rögnvaldsson 2020** — "Transfer learning for remaining useful life prediction based on
  consensus self-organizing models," *RESS* 203:107098. DOI 10.1016/j.ress.2020.107098.
  **[2] [B] [search-snippet]** Learns a consensus model across a population rather than a single
  source-to-target map. **Bearing:** the "pool the cohort, then transfer" design Study C assumes implicitly
  without the consensus machinery.
- **Wang, Ragab, Hou, Chen, Wu & Li 2025** — "Deep Domain Adaptation for Turbofan Engine RUL Prediction,"
  arXiv:2510.03604. **[2] [D] [search-snippet]** Survey separating methodology from *evaluation*.
  **Bearing:** current map of which methods have been evaluated under which protocol.

## (b) Domain generalisation, where no target data exists

- **Ding, Jia, Cao et al. 2023** — "Domain generalization via adversarial out-domain augmentation for
  remaining useful life prediction of bearings under unseen conditions," *Knowledge-Based Systems* 261:110199.
  DOI 10.1016/j.knosys.2022.110199. **[3] [B] [search-snippet]** Generates adversarial pseudo-domains
  maximising divergence from training domains, for zero target data. **Bearing:** the canonical
  generalisation answer to Study C's setting, where the remedy is synthetic domain expansion rather than
  more real units.
- **Ding, Li & Qi 2022** — "Multi-source domain generalization for degradation monitoring of journal
  bearings under unseen conditions," *RESS* 230:108966. DOI 10.1016/j.ress.2022.108966.
  **[3] [B] [search-snippet]** Treats each source as a separate domain and learns a representation holding on
  an unseen one. **Bearing:** the natural reframing of the project's cohort — each *unit* is a domain.
- **Hosseinli & Gryllias 2026** — "Physics-Informed Domain Generalization for Bearing Prognostics Under
  Unseen Operating Conditions," *PHM Society European Conference* 9(1). DOI 10.36001/phme.2026.v9i1.4972.
  **[3] [C] [full-text]** Constrains learned degradation to physically consistent crack-growth dynamics and
  disentangles domain-invariant degradation features from domain-specific ones.
  **Bearing:** the physics-constrained version of what the project's ridge estimator does unconstrained. The
  physical prior is what stops a model drifting on atypical units — a concrete C2 successor.
- **Shang, Xu & Shang 2025** — "CITDG: a causality and information-theory inspired domain generalization
  method," *Mechanical Systems and Signal Processing*. DOI 10.1016/j.ymssp.2025.113527.
  **[2] [C] [search-snippet]** Separates features causal for degradation from spurious domain-correlated
  ones. **Bearing:** the diagnostic frame for Study C's failure — a pressure feature co-varying with
  *lifetime* in the training cohort rather than with *fatigue state* will invert on an atypically short-lived
  unit.
- **Fink, Wang, Svensén, Dersin, Lee & Ducoffe 2020** — "Potential, challenges and future directions for deep
  learning in prognostics and health management," *Engineering Applications of Artificial Intelligence*
  92:103678. DOI 10.1016/j.engappai.2020.103678. **[2] [D] [search-snippet]** Names transferability across
  units and the scarcity of run-to-failure data as structural blockers. **Bearing:** licenses reporting a
  cross-unit failure as a field-level finding rather than a project defect.

## (c) Evaluation protocols and unit-level holdout

- **Saeb, Lonini, Jayaraman, Mohr & Kording 2017** — "The need to approximate the use-case in clinical machine
  learning," *GigaScience* 6(5):gix019. DOI 10.1093/gigascience/gix019. **[3] [B] [search-snippet]** Shows
  record-wise cross-validation lets a model exploit entity identity as a confound and report accuracy that
  collapses under leave-subject-out validation.
  **Bearing:** the canonical statement of *why* unit-level holdout is the only meaningful protocol here.
  Read alongside its counterpoint by Little et al., above.
- **Saxena, Sankararaman & Goebel 2014** — "Performance Evaluation for Fleet-based and Unit-based Prognostic
  Methods," *PHM Society European Conference* 2(1). DOI 10.36001/phme.2014.v2i1.1511.
  **[3] [D] [search-snippet]** Distinguishes fleet-based from unit-based evaluation and argues the
  appropriate metrics differ. **Bearing:** the most on-point precedent for the protocol question — a
  fleet-trained model must be scored per unit, which is what the 8-of-10 gate does.
- **Ragab, Eldele, Tan, Foo, Chen, Wu, Kwoh & Li 2023** — "ADATIME: A Benchmarking Suite for Domain
  Adaptation on Time Series Data," *ACM TKDD* 17(8). DOI 10.1145/3587937. **[3] [A] [search-snippet]** Finds
  time-series adaptation papers mutually incomparable because of inconsistent splits, and that many use
  *labelled target data for model selection*, violating the unsupervised premise.
  **Bearing:** the strongest argument that Study C's preregistered, target-label-free unit holdout is the
  honest protocol, and that many reported cross-domain gains are protocol artefacts.
- **Ramasso & Saxena 2014** — "Performance Benchmarking and Analysis of Prognostic Methods for CMAPSS
  Datasets," *International Journal of Prognostics and Health Management* 5(2). DOI 10.36001/ijphm.2014.v5i2.2236.
  **[2] [A] [search-snippet]** Re-benchmarking shows published scores are not comparable because protocols
  differ. **Bearing:** a stated pass criterion is meaningful only alongside its split definition, which is
  why a preregistered 8-of-10 is worth more than a pooled error figure.
- **Arias Chao, Kulkarni, Goebel & Fink 2021** — "Aircraft Engine Run-to-Failure Dataset under Real Flight
  Conditions," *Data* 6(1):5. DOI 10.3390/data6010005. **[2] [B] [search-snippet]** Releases a 128-engine
  simulated dataset with unit identity preserved so held-out-*unit* evaluation is possible.
  **Bearing:** the reference design for a simulated multi-unit cohort with unit-level splits, and the closest
  published analogue to the project's 20/10 design.

## (d) Calibration transfer and instrument standardisation

This chemometrics literature solved a structurally similar problem decades ago and is the most
under-exploited resource in this folder.

- **Kunz, Ottaway, Kalivas & Andries 2010** — "Impact of standardization sample design on Tikhonov
  regularization variants for spectroscopic calibration maintenance and transfer," *Journal of Chemometrics*
  24(3–4):218–229. DOI 10.1002/cem.1302. **[3] [B] [full-text]** A Tikhonov formulation handles both
  maintenance and transfer by augmenting the primary calibration set with a few weighted samples from the
  secondary condition; the *composition* of that augmenting set, not merely its size, governs success.
  **Bearing:** the closest formal match to the project's estimator, because ridge *is* Tikhonov. Its
  conclusion is directly actionable: an atypical-lifetime target needs an atypical-lifetime unit represented
  in the training set.
- **Wang, Veltkamp & Kowalski 1991** — "Multivariate instrument standardization," *Analytical Chemistry*
  63(23). DOI 10.1021/ac00023a016. **[3] [B] [search-snippet]** The founding paper, introducing direct and
  piecewise direct standardisation from a small set of samples measured on *both* instruments.
  **Bearing:** the canonical alternative design — measure a handful of paired standardisation units and learn
  a correction instead of hoping one fit generalises.
- **Feudale, Woody, Tan, Myles, Brown & Ferré 2002** — "Transfer of multivariate calibration models: a
  review," *Chemometrics and Intelligent Laboratory Systems* 64(2):181–192. DOI 10.1016/S0169-7439(02)00085-0.
  **[3] [A] [search-snippet]** Builds the taxonomy on the claim that a model becomes *invalid* when
  prediction samples carry variation the calibration set never saw. **Bearing:** supplies precise vocabulary
  — the 10 test units are "secondary conditions," and the taxonomy narrows which correction family applies
  when no paired measurements exist.
- **Bouveresse, Hartmann, Massart, Last & Prebble 1996** — "Standardization of Near-Infrared Spectrometric
  Instruments," *Analytical Chemistry* 68(6). DOI 10.1021/ac9510595. **[3] [B] [search-snippet]** Compares
  univariate slope and bias correction of *predictions* against full multivariate correction of the
  *signals*, and says when the cheap fix suffices. **Bearing:** the cheapest candidate remedy — per-unit
  slope and intercept correction of the predicted state, with a stated boundary for when it is not enough.
- **Andrew & Fearn 2004** — "Transfer by orthogonal projection," *Chemometrics and Intelligent Laboratory
  Systems* 72(1):51–56. DOI 10.1016/j.chemolab.2004.02.004. **[3] [B] [search-snippet]** Estimates the
  subspace where between-instrument differences live and projects it out *before* calibration.
  **Bearing:** the model-side analogue of what the project needs — fit orthogonal to the directions along
  which the training units differ from one another.
- **Nikzad-Langerodi, Zellinger, Lughofer & Saminger-Platz 2018** — "Domain-Invariant Partial-Least-Squares
  Regression," *Analytical Chemistry* 90(11):6693–6701. DOI 10.1021/acs.analchem.8b00498.
  **[3] [B] [search-snippet]** Adds a domain regulariser aligning source and target latent distributions,
  enabling *label-free* adaptation. **Bearing:** the standard-free escape hatch — align using the unlabelled
  pressure features of a held-out actuator without observing its true state.
- **Guenard, Wehlburg, Pell & Haaland 2007** — "Importance of Prediction Outlier Diagnostics in Determining a
  Successful Inter-Vendor Multivariate Calibration Model Transfer," *Applied Spectroscopy* 61(7):747–754.
  DOI 10.1366/000370207781393280. **[3] [B] [search-snippet]** Argues prediction error alone is an inadequate
  success criterion; transfer counts as successful only if leverage and residual diagnostics survive.
  **Bearing:** possibly the most actionable entry in this folder. Study C's failures concentrated on atypical
  units, which is exactly the regime this paper says must be caught by an abstain-or-flag diagnostic rather
  than a pass/fail count. See [gaps.md](gaps.md).
- **Workman 2018** — "A Review of Calibration Transfer Practices and Instrument Differences in Spectroscopy,"
  *Applied Spectroscopy* 72(3):340–365. DOI 10.1177/0003702817736064. **[3] [A] [full-text]** After roughly
  25 years of method development, identical results from two instruments under one calibration "still eludes
  technologists," with residual failure attributed to device reproducibility and reference-value quality
  rather than the algorithm.
  **Bearing:** the field's own negative result, and the honest prior for the 8-of-10 bar — universal
  cross-unit agreement may not be attainable at all.
- **Mishra, Nikzad-Langerodi, Marini et al. 2021** — "Are standard sample measurements still needed to
  transfer multivariate calibration models between near-infrared spectrometers? The answer is not always,"
  *TrAC Trends in Analytical Chemistry* 143:116331. DOI 10.1016/j.trac.2021.116331. **[3] [A] [full-text]**
  Critical review of standard-free transfer concluding such methods are promising but not a universal
  substitute. **Bearing:** the hedged answer for a project with no paired standards across its units.
- **Kim, Kwon, Jeon & Park 2020** — "Adaptive Calibration of Soft Sensors Using Optimal Transportation
  Transfer Learning for Mass Production and Long-Term Usage," *Advanced Intelligent Systems* 2(6).
  DOI 10.1002/aisy.201900178. **[3] [B] [search-snippet]** States soft sensors "suffer from high
  manufacturing tolerances and signal drift," and applies optimal-transport adaptation so a master
  calibration can be re-fitted to another mass-produced unit and re-adjusted as it drifts.
  **Bearing:** calibration transfer applied to soft devices specifically, demonstrating that cross-unit
  transfer needs an explicit adaptation step a plain ridge fit does not have.

## (e) Transfer failures and negative results

Wall et al. 2023 is the headline entry and is covered above.

- **Zhao, Zhang, Wang et al. 2021** — "Applications of Unsupervised Deep Transfer Learning to Intelligent
  Fault Diagnosis: A Survey and Comparative Study," *IEEE Trans. Instrumentation and Measurement* 70.
  DOI 10.1109/TIM.2021.3116309. **[3] [A] [full-text]** Re-implements the main methods under a common
  codebase and finds transferability, backbone choice and negative transfer "rarely studied," with published
  gains not surviving uniform re-evaluation. **Bearing:** the field's own comparative study says cross-domain
  gains are fragile under honest protocol, which contextualises a 6-of-10 result without excusing it.
- **Hendriks, Dumond & Knox 2022** — "Towards better benchmarking using the CWRU bearing fault dataset,"
  *Mechanical Systems and Signal Processing* 169:108732. DOI 10.1016/j.ymssp.2021.108732.
  **[3] [B] [search-snippet]** Identifies a flaw in the standard use of a benchmark dataset, so reported
  cross-domain results partly measure a protocol artefact. **Bearing:** a model negative-result paper — the
  publishable contribution can be "the evaluation was wrong."
- **Wang, Dai, Póczos & Carbonell 2019** — "Characterizing and Avoiding Negative Transfer," *CVPR*;
  arXiv:1811.09751. **[2] [B] [search-snippet]** Formal definition of negative transfer and when a less
  related source actively *hurts* the target. **Bearing:** the definition needed to state formally whether
  the failing units suffered negative transfer from lifetime mismatch, plus the filtering remedy.
- **Michau & Fink 2021** — "Unsupervised transfer learning for anomaly detection," *Knowledge-Based Systems*
  216:106816. DOI 10.1016/j.knosys.2021.106816. **[2] [B] [search-snippet]** Transfers between units that
  have each seen only *complementary* subsets of the operating envelope. **Bearing:** the setting where no
  training unit individually resembles the target, which is what an atypical lifetime amounts to.
- **Tiboni, Protopapa, Tommasi & Averta 2023** — "Domain Randomization for Robust, Affordable and Effective
  Closed-Loop Control of Soft Robots," *IROS*; arXiv:2303.04136. **[2] [C] [full-text]** Randomises uncertain
  dynamics parameters during training to gain robustness to unknown per-unit dynamics, with adaptive
  parameter inference. **Bearing:** a concrete fix — randomise the latent material and geometry parameters
  that set lifetime, rather than assuming one map covers them.
- **Gao, Michelis, Spielberg & Katzschmann 2024** — "Sim-to-Real of Soft Robots With Learned Residual
  Physics," *IEEE Robotics and Automation Letters* 9(10). DOI 10.1109/LRA.2024.3446287.
  **[2] [B] [full-text]** Learns a neural residual force field from sparse real data, cutting error by about
  60 % versus classical system identification. **Bearing:** the residual left after nominal parameter
  identification is large and must be learned from *that hardware* — and notably the residual is never tested
  on a second physical copy, so even this result is single-specimen.
- **Thuruthel, Shih, Laschi & Tolley 2019** — "Soft robot perception using embedded soft sensors and
  recurrent neural networks," *Science Robotics* 4(26). DOI 10.1126/scirobotics.aav1488.
  **[2] [B] [search-snippet]** Notes both the sensors and the encasing system are nonlinear and time-variant.
  **Bearing:** drift and time-variance are intrinsic to elastomeric devices, so a fixed-cohort estimator is
  fitting a moving target even within one unit.

---

## What this literature does not settle

- **There is no established pass criterion for unit-level holdout.** The protocol literature establishes that
  fleet-trained models must be scored per unit, but no source found states a conventional threshold. The
  8-of-10 bar is a defensible preregistered choice, not a field standard, and the literature cannot say
  whether 6 of 10 is "close" or "failed."
- **At 10 test units the variance warning applies** — see Little et al. above. No source gives a power
  analysis mapping cohort size to expected pass-rate variance. This *is* testable in the project's own
  simulator by resampling the split, and doing so would strengthen or properly qualify the C-FAIL verdict.
- **The chemometrics remedies assume a shared physical sample the project does not have.** Direct and
  piecewise standardisation correct an instrument response applied to the *same specimen* measured twice.
  Distinct actuators with different true lifetimes have no common sample, so part of the gap may be
  irreducible physical heterogeneity rather than a correctable transfer map.
- **Nobody has shown fabrication heterogeneity is observable from pressure alone.** Cross-unit failure is
  consistently attributed to fabrication variance, and a remedy exists *when a few labelled target samples
  are available*. No source demonstrates zero-shot transfer to an uncalibrated soft actuator from a
  pressure-only channel — which is exactly what Study C asks. That is an identifiability question
  [01](01-identifiability-observability.md) already touches, and it is open.
- **No pre-deployment abstain test exists.** Guenard et al. comes closest but flags samples after the fact.
  Nothing predicts, from an *unlabelled* new unit, whether transfer will fail on it — yet that is exactly the
  decision a fielded recalibration trigger must make. Logged in [gaps.md](gaps.md) as the most defensible
  next contribution.
- **Held-out-physical-unit evaluation is essentially absent from soft robotics.** Wall et al. is the only
  located paper reporting a genuine train-on-A, test-on-B number. Running a unit-level holdout at all — even
  one that fails — is above the field's current evaluation norm and is worth stating plainly.
