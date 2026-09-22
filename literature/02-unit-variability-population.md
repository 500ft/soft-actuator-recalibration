# 02 — Unit-to-unit variability and population models

Serves [Study A](../docs/specs/observability-program/studyA-preregistration.md) (a 30-unit cohort with
dispersed degradation-law parameters and Weibull rupture life) and [Study C](../docs/specs/observability-program/studyC-transfer.md)
(20 training / 10 held-out units split by identity, where transfer error tracked distance from the training
median life).

Grading and provenance rules in [README](README.md).

---

## Read this first: two findings that challenge the project's own setup

- **Bae, Kuo & Kvam 2007** — "Degradation models and implied lifetime distributions," *Reliability
  Engineering & System Safety* 92(5):601–608. DOI 10.1016/j.ress.2006.02.002. **[2] [B] [search-snippet]**
  Maps degradation-path families and their random-parameter distributions onto the lifetime distributions
  they *induce*.
  **Bearing — a checkable concern.** Study A specifies two randomisations independently: rupture life is
  drawn Weibull (mean 3500, CV 0.30) *and* the degradation-law parameters are separately dispersed. This
  literature says a degradation model plus a random-parameter distribution already *implies* a lifetime
  distribution. If the implied and imposed distributions disagree, the generator carries an internal
  inconsistency, and the Study C transfer result may be measuring part of it. This is testable inside the
  repository and is logged in [gaps.md](gaps.md) as an open item.

- **Du, Huang, Fan & Wei 2026** — "Fatigue Life Mapping of Rubber Isolators...," *Polymers* 18(14):1732.
  DOI 10.3390/polym18141732. **[3] [B] [full-text]** Six rubber cylinders per condition across five
  displacement levels (30 tests). Weibull shape fits come out at m = 1.28, 2.95, 3.75 and 7.76 as conditions
  change — scatter is severe and *load-dependent*, not a material constant.
  **Bearing:** Study A's fixed CV = 0.30 corresponds to roughly m ≈ 3.7, one point on a range spanning
  1.3 to 7.8. Conclusions about "how far a unit sits from the median" may not survive a change of duty cycle.

---

## (a) Random-effects and hierarchical degradation models

- **Lu & Meeker 1993** — "Using Degradation Measures to Estimate a Time-to-Failure Distribution,"
  *Technometrics* 35(2):161–174. DOI 10.1080/00401706.1993.10485038. **[3] [A] [search-snippet]** Origin of
  the general-path model: each unit's path has fixed population effects plus unit-specific random effects,
  with the induced time-to-failure distribution obtained by Monte Carlo. **Bearing:** the exact structural
  move the project needs — dispersed per-unit parameters are random effects, not noise around a shared clock.
- **Lawless & Crowder 2004** — "Covariates and Random Effects in a Gamma Process Model...," *Lifetime Data
  Analysis* 10(3):213–227. DOI 10.1023/b:lida.0000036389.14073.dd. **[3] [A] [search-snippet]** Random
  gamma-distributed scale parameter on a gamma degradation process, with the implied lifetime distribution.
  **Bearing:** canonical citation for a unit-specific degradation rate drawn from a population distribution
  in a monotone-damage process.
- **Wang 2010** — "Wiener processes with random effects for degradation data," *Journal of Multivariate
  Analysis* 101(2):340–351. DOI 10.1016/j.jmva.2008.12.007. **[3] [B] [search-snippet]** Per-unit random
  drift and diffusion, EM estimation, consistency results. **Bearing:** supports estimating a *population
  distribution* of per-unit rates from a modest cohort rather than one pooled rate.
- **Zhang, Si, Hu & Kong 2015** — "Degradation modeling–based remaining useful life estimation: a review on
  approaches for systems with heterogeneity," *Proc. IMechE Part O* 229(4). DOI 10.1177/1748006x15579322.
  **[3] [A] [search-snippet]** Survey organised around heterogeneity: random-effects, covariate and mixture
  approaches for units that do not share a degradation clock. **Bearing:** best single entry point for a
  related-work section justifying the modelling choice.
- **Leadbetter, Gonzalez Caceres & Phatak 2024** — "Bayesian Hierarchical Modelling of Noisy Gamma
  Processes...," arXiv:2406.11216. **[3] [D] [full-text]** Shows process volatility and measurement noise are
  *not identifiable* from sparse single-unit data, and that pooling across units is one of only three fixes.
  **Bearing:** a direct caution — with short noisy traces, per-unit rate estimates can be confounded with
  observation noise unless a hierarchy carries the load. Connects this theme to [01](01-identifiability-observability.md).
- **Zaidan, Harrison, Mills & Fleming 2015** — "Bayesian Hierarchical Models for aerospace gas turbine engine
  prognostics," *Expert Systems with Applications* 42(1):539–553. DOI 10.1016/j.eswa.2014.08.007.
  **[3] [B] [search-snippet]** Fleet-wide hierarchical model sharing information across engines, reported to
  beat the non-hierarchical baseline. **Bearing:** the closest published analogue to "train on 20 units,
  predict a 21st."
- **Lewis-Beck, Tian & Meeker 2021** — "Prediction of Future Failures for Heterogeneous Reliability Field
  Data," arXiv:2011.03140. **[2] [D] [full-text]** Hierarchical joint model across subpopulations; borrowing
  strength gives calibrated intervals even with few observed failures. **Bearing:** precedent for the
  few-per-group regime a 20-unit training split sits in.
- **Karmakar & Pradhan 2025** — "Residual Lifetime Prediction for Heterogeneous Degradation Data by Bayesian
  Semi-Parametric Method," arXiv:2504.15794; DOI 10.1002/qre.70182. **[3] [D] [search-snippet]** Replaces the
  Gaussian random-effects assumption with a Dirichlet-process mixture so the population can be multimodal.
  **Bearing:** addresses the risk that a CV = 0.30 cohort is not well described by one parametric
  random-effects family.
- **Si, Wang, Hu & Zhou 2011** — "Remaining useful life estimation — a review on the statistical data driven
  approaches," *European Journal of Operational Research* 213(1):1–14. DOI 10.1016/j.ejor.2010.11.018.
  **[2] [A] [search-snippet]** Standard taxonomy, including where population priors and unit-level updating
  enter. **Bearing:** background framing only.
- **Meeker, Escobar & Pascual 2022** — *Statistical Methods for Reliability Data*, 2nd ed., Wiley.
  ISBN 9781118115459. **[2] [A] [search-snippet]** Textbook treatment of degradation models with random
  effects, censoring and Bayesian estimation. **Bearing:** definitional grounding.

## (b) Stochastic degradation processes with unit-specific parameters

- **Si, Wang, Hu & Zhou 2014** — "Estimating Remaining Useful Life With Three-Source Variability in
  Degradation Modeling," *IEEE Trans. Reliability* 63(1):167–190. DOI 10.1109/tr.2014.2299151.
  **[3] [B] [search-snippet]** Decomposes RUL uncertainty into temporal, unit-to-unit and measurement
  variability, estimating all three jointly.
  **Bearing:** the vocabulary the project should adopt. Study C's transfer error is dominated by the
  *unit-to-unit* term, and this is the standard citation for separating it from the other two.
- **Wang & Xu 2010** — "An Inverse Gaussian Process Model for Degradation Data," *Technometrics*
  52(2):188–197. DOI 10.1198/tech.2009.08197. **[3] [B] [search-snippet]** IG process for monotone
  degradation with a gamma random effect for subject-to-subject heterogeneity. **Bearing:** a ready
  alternative if the damage variable is monotone and a Gaussian random effect is unwanted.
- **Ye & Chen 2014** — "The Inverse Gaussian Process as a Degradation Model," *Technometrics* 56(3):302–311.
  DOI 10.1080/00401706.2013.830074. **[3] [B] [search-snippet]** Gives the IG process a physical reading as a
  limiting compound Poisson process. **Bearing:** useful if unit-level dispersion should carry a mechanism
  story rather than be a fitted nuisance.
- **Wang, Wang, Hong & Jiang 2021** — "Degradation data analysis based on gamma process with random effects,"
  *European Journal of Operational Research* 292(3). DOI 10.1016/j.ejor.2020.11.036. **[3] [B] [search-snippet]**
  Modern implementation of the Lawless–Crowder idea with the induced failure-time distribution.
- **Zhang, Hu, Si & Zhang 2017** — "Stochastic degradation process modeling and RUL estimation with flexible
  random-effects," *Journal of the Franklin Institute* 354(6). DOI 10.1016/j.jfranklin.2016.06.039.
  **[3] [C] [search-snippet]** Lets the random-effects distribution match available information rather than
  being fixed by convenience. **Bearing:** relevant to whether a Weibull-lifetime cohort is well served by a
  Gaussian random effect on degradation-law parameters.
- **Peng & Tseng 2009** — "Mis-Specification Analysis of Linear Degradation Models," *IEEE Trans.
  Reliability* 58(3):444–455. DOI 10.1109/tr.2009.2026784. **[2] [B] [search-snippet]** Quantifies
  mean-life bias when the assumed path or random-effect structure is wrong, finding the effect mild at large
  n. **Bearing:** the implication at n = 20–30 is the opposite, and it supplies a defensible framework for a
  misspecification sensitivity study.
- **Chen, Li & Xie 2023** — "Reliability modeling and statistical analysis of accelerated degradation process
  with memory effects and unit-to-unit variability," arXiv:2310.18567. **[2] [C] [full-text]**
  Fractional-Brownian-motion degradation with unit-to-unit variability in the acceleration model.
  **Bearing:** a reminder that a shared clock fails in two independent ways, memory and unit dispersion, and
  only the second is in the project's simulation.

## (c) Lifetime scatter and small-sample estimation, including elastomers

- **Gope 1999** — "Determination of sample size for estimation of fatigue life by using Weibull or log-normal
  distribution," *International Journal of Fatigue* 21(8):745–752. DOI 10.1016/s0142-1123(99)00048-1.
  **[3] [B] [search-snippet]** Tabulates error factors for n = 3–25 at stated probability and confidence
  levels. **Bearing:** the most directly usable answer to "how many specimens," and it places n = 30 near the
  *top* of the tabulated range rather than comfortably beyond it.
- **Gehling, Schieppati, Balasooriya & Kerschbaumer 2023** — "Fatigue Behavior of Elastomeric Components,"
  *Polymer Reviews* 63(3). DOI 10.1080/15583724.2023.2166955. **[3] [A] [search-snippet]** States the
  mechanism behind elastomer life scatter: randomly distributed compound inhomogeneities act as inherent
  flaws from which cracks nucleate, so nucleation life shows large scatter needing many specimens for a
  proper statistical description.
  **Bearing:** the best physical justification in this folder for why *unit identity*, not cycle count, is
  the right unit of analysis in a soft-actuator cohort.
- **Zhang, Xie & Tang 2006** — "Bias correction for the least squares estimator of Weibull shape parameter,"
  *Reliability Engineering & System Safety* 91(8):930–939. DOI 10.1016/j.ress.2005.09.010.
  **[3] [B] [search-snippet]** Quantifies and corrects small-sample bias in the Weibull shape estimate — the
  parameter that *is* the scatter. **Bearing:** the correction a reviewer will ask for if an empirical CV or
  shape is reported from 20 training units.
- **Makalic & Schmidt 2023** — "Maximum likelihood estimation of the Weibull distribution with reduced bias,"
  *Statistics and Computing* 33. DOI 10.1007/s11222-023-10236-0. **[2] [B] [search-snippet]** The scale
  estimate is near-unbiased at small n while the shape is strongly biased. **Bearing:** confirms the
  dispersion parameter, not mean life, is the fragile quantity in a 20–30 unit cohort.
- **Mars & Fatemi 2004** — "Factors that Affect the Fatigue Life of Rubber: A Literature Survey," *Rubber
  Chemistry and Technology* 77(3):391–412. DOI 10.5254/1.3547831. **[2] [A] [search-snippet]** Catalogue of
  what moves rubber fatigue life. **Bearing:** establishes between-specimen dispersion as expected and
  physically grounded, not an artefact. Complements the 2002 survey already in the June base.
- **Tee, Loo & Andriyana 2018** — "Recent advances on fatigue of rubber...," *International Journal of
  Fatigue* 110:115–129. DOI 10.1016/j.ijfatigue.2018.01.007. **[2] [A] [search-snippet]** Post-2004 update on
  crack nucleation and growth. **Bearing:** current-state citation for elastomer fatigue methodology.
- **ISO 12107:2012** — *Metallic materials — Fatigue testing — Statistical planning and analysis of data*.
  https://www.iso.org/standard/50242.html **[2] [A] [search-snippet]** Normative specimen-allocation rules
  for estimating fatigue-life distributions with a practical number of specimens. **Bearing:** a standards
  anchor for defending a cohort size, though written for metals.
- **Meeker et al. 2022** — "Modern Statistical Models and Methods for Estimating Fatigue-Life and
  Fatigue-Strength Distributions," arXiv:2212.04550. **[2] [D] [full-text]** Argues the history of fatigue
  testing is matched by a history of mishandled censoring and wrong regression variables. **Bearing:**
  relevant if any simulated unit is censored before rupture, where small-sample scatter estimates usually
  go wrong.
- **Cui 2008** — "Determination of sample size for Weibull distribution in structural reliability tests,"
  *Chinese Journal of Mechanical Engineering* 44(1):51. DOI 10.3901/jme.2008.01.051. **[2] [C] [search-snippet]**
  Second, independent sample-size relation, shape assumed known. Full text not retrieved; treat details as
  unverified.

## (d) Population versus individual prognostics, and unit-level evaluation

- **Yan & Wiston 2026** — "Mission-Phase Feature Learning for eVTOL Li-Ion Battery Prognostics: A
  Leakage-Safe Cell-Held-Out Benchmark," *Batteries* 12(9):322. DOI 10.3390/batteries12090322.
  **[3] [C] [search-snippet]** Random-Forest state-of-health error rises from 0.037 to 0.620 percentage
  points when the split moves from row-random to leave-one-cell-out — roughly a 17-fold inflation from
  sample-level leakage.
  **Bearing:** the strongest citable precedent that held-out-*unit* evaluation is the correct protocol and
  that held-out-*sample* evaluation silently flatters a model. Direct support for Study C's split design.
- **Gebraeel, Lawley, Li & Ryan 2005** — "Residual-life distributions from component degradation signals: a
  Bayesian approach," *IIE Transactions* 37(6):543–557. DOI 10.1080/07408170590929018. **[3] [B] [search-snippet]**
  Population prior over degradation coefficients updated in real time to a closed-form residual-life
  distribution for the individual unit; validated on accelerated bearing fatigue.
  **Bearing:** the canonical population-prior-plus-individual-update architecture — the principled response
  to a held-out unit sitting far from the training median. See also [04](04-rul-unknown-life.md).
- **Coble & Hines 2013** — "Identifying Suitable Degradation Parameters for Individual-Based Prognostics,"
  IGI Global, 135–150. DOI 10.4018/978-1-4666-2095-7.ch007. **[3] [D] [search-snippet]** Defines the
  population-based versus individual-based split and proposes *trendability, monotonicity, prognosability* as
  selection metrics; the population prognoser is reported to have the largest errors.
  **Bearing:** supplies the exact terminology for the project's finding — and note the repository already
  implements those three metrics in `pipeline/hi_metrics.py`, so the connection is concrete.
- **Kim, Song & Liu 2022** — "Individualized Degradation Modeling and Prognostics in a Heterogeneous Group via
  Incorporating Intrinsic Covariate Information," *IEEE Trans. Automation Science and Engineering* 19(1).
  DOI 10.1109/tase.2021.3070532. **[3] [B] [search-snippet]** Conditions the unit-level model on intrinsic
  covariates rather than assuming exchangeability. **Bearing:** if held-out error tracks distance from the
  training median, an observable unit-level covariate is exactly the fix.
- **Guo, Huang, Wu & Wang 2025** — "A transfer learning approach for remaining useful life prediction subject
  to hard failure considering within and between population variations," *Reliability Engineering & System
  Safety* 262:111145. DOI 10.1016/j.ress.2025.111145. **[3] [C] [search-snippet]** Separates within- from
  between-population variation and transfers under a hard-failure threshold. **Bearing:** closest framing to
  the project's result, though its transfer target is a new population rather than a new unit.
- **Jeong, Kim, Kim & Choi 2020** — "Reliability analysis of a tendon-driven actuation for soft robots,"
  *International Journal of Robotics Research* 39(4). DOI 10.1177/0278364920907151. **[2] [B] [search-snippet]**
  Reliability treatment of a soft-robot actuation mechanism. **Bearing:** in-domain precedent that this
  framing is publishable in robotics venues, not only reliability ones.

---

## What this literature does not settle

- **No sample-size guidance is transfer-aware.** Gope, Cui and ISO 12107 answer how many specimens estimate a
  lifetime *distribution* to a stated precision. None answers how many training units are needed before
  held-out-unit error stops depending on where that unit sits in the population — which is what Study C's
  20/10 split actually measures.
- **The error-versus-distance-from-median relationship appears unreported.** The population-versus-individual
  literature asserts population prognosers do worse on average, and the leakage literature reports aggregate
  inflation. No retrieved paper regresses held-out-unit error on the unit's rank within the training life
  distribution, which is precisely [R1's](../evidence/weekly-research-2026-09-21/README.md) finding.
- **Random-effects distribution shape is assumed, not tested, at this cohort size.** Gaussian, gamma,
  flexible and nonparametric options all exist, but nothing establishes at what n they can be
  *discriminated*. At 20 training units they almost certainly cannot.
- **The two randomisations may be inconsistent** — see Bae, Kuo & Kvam above. Logged in [gaps.md](gaps.md).
- **Elastomer scatter is load-dependent and the simulation treats it as fixed** — see Du et al. above.
- **No validated bridge from simulated to real cohorts.** Published real soft-actuator datasets run n = 3 to
  n = 10 specimens, so a 30-unit simulated cohort is larger than essentially any real one and the literature
  offers no check on whether the unit-level effect sizes are realistic.
