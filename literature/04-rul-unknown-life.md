# 04 — Estimating state when a unit's total life is unknown

Serves the [R1 failure map](../evidence/weekly-research-2026-09-21/README.md), which found the Study C
estimator is *a clock corrected by pressure* — muting the cycle-count input cost 0.120 life against 0.051
for the pressure features — and that failures concentrate on units whose life is atypical relative to the
training median.

Grading and provenance rules in [README](README.md). Every entry here is `[search-snippet]` unless marked
otherwise; identifiers were resolved against metadata services.

---

## Read this first

### The principled version of what the project built by accident

- **Zhou & Howey 2023** — "Bayesian hierarchical modelling for battery lifetime early prediction,"
  *IFAC-PapersOnLine* 56(2). DOI 10.1016/j.ifacol.2023.10.708. **[3] [B] [search-snippet; authorship
  verified against Crossref]** Hierarchical Bayesian model combining *individual-unit* features from the
  first ~100 cycles, about 5–10 % of life, with *population-level* features; end-of-life prediction at
  RMSE 3.2 days and 8.6 % mean absolute percentage error under five-fold cross-validation, roughly 12–13 %
  better than the non-hierarchical baseline.
  *Provenance note:* two independent search passes returned different author attributions for this DOI. The
  record above is from Crossref and supersedes the other. Flagged because it is the kind of error this
  folder's grading scheme exists to catch.
  **Bearing:** this is the statistical architecture the project's "clock plus sensor correction" estimator is
  an unprincipled version of. A ridge regression with a cycle-count column is a flat model imitating a
  hierarchy; this paper does it properly and reports the gain.

- **Gebraeel, Lawley, Li & Ryan 2005** — "Residual-life distributions from component degradation signals: a
  Bayesian approach," *IIE Transactions* 37(6). DOI 10.1080/07408170590929018. **[3] [B] [search-snippet]**
  Bayesian updating of the stochastic parameters of a degradation model from real-time condition data,
  yielding a closed-form residual-life distribution; validated on accelerated bearing tests.
  **Bearing:** the canonical template for replacing a population life prior with a unit-specific posterior —
  exactly the move the project's estimator does not make.
- **Gebraeel 2006** — "Sensory-Updated Residual Life Distributions for Components With Exponential
  Degradation Patterns," *IEEE Trans. Automation Science and Engineering* 3(4). DOI 10.1109/TASE.2006.876609.
  **[3] [B] [search-snippet]** Explicitly "combines population-specific degradation characteristics with
  component-specific sensory data," benchmarked against non-sensory policies.
  **Bearing:** the clearest statement of the population-versus-individual trade-off the project diagnosed.
- **Yu, Shao, Xu & Wang 2022** — "An adaptive and generalized Wiener process model with a recursive filtering
  algorithm for remaining useful life estimation," *Reliability Engineering & System Safety* 217.
  DOI 10.1016/j.ress.2021.108099. **[3] [B] [search-snippet]** Recursive Bayesian filter on the drift plus
  online expectation-maximisation, designed so that **no population data from identical units is required**.
  **Bearing:** the strongest candidate architecture for an estimator that works when the training-median life
  cannot be trusted — the direct answer to R1's finding.

### A caution about how much a state-triggered policy can ever buy

- **Andersen & Nielsen 2024** — "A comparative study of time-based maintenance and condition-based
  maintenance for multi-component systems," *Reliability Engineering & System Safety* 251.
  DOI 10.1016/j.ress.2024.110759. **[3] [C] [search-snippet]** Optimises both policies as Markov decision
  processes over gamma-process degradation. The **largest** relative cost improvement of condition-based over
  time-based maintenance is **45 %**, in the single-component case, and the improvement *grows with
  heterogeneity in component mean time to failure*.
  **Bearing:** two payoffs. It puts a published ceiling on what state-triggering can buy, and it confirms the
  advantage rises precisely with per-unit life dispersion — the regime where the project's estimator fails.
- **Pedersen & Vatn 2022** — "Optimizing a condition-based maintenance policy by taking the preferences of a
  risk-averse decision maker into account," *Reliability Engineering & System Safety* 228.
  DOI 10.1016/j.ress.2022.108775. **[3] [C] [search-snippet]** Remaining-life-driven resource acquisition
  lowers renewal cost but *raises the probability of long-downtime cycles*, so optimising long-run cost rate
  "may lead to decisions that are not in line with the preferences of a risk-averse decision maker."
  **Bearing:** the cleanest published case for preferring a conservative fixed schedule — and the reason is
  variance, not mean. Directly relevant to how the project frames its two-versus-five calibration-event claim.

---

## (a) Bayesian and adaptive personalisation of a population prior

Gebraeel 2005/2006, Yu et al. 2022 and Kuzhiyil et al. 2023 are covered above.

- **Zhou, Serban & Gebraeel 2011** — "Degradation modeling applied to residual lifetime prediction using
  functional data analysis," *Annals of Applied Statistics* 5(2B). DOI 10.1214/10-AOAS448.
  **[3] [B] [search-snippet]** Nonparametric functional-data degradation model with an *empirical Bayes*
  update using training signals as the prior, designed for sparse or short observation windows.
  **Bearing:** relevant if pressure features are short and sparse — it avoids committing to a parametric
  degradation law, which the project's generator currently imposes.
- **Wen, Wu, Das & Tseng 2018** — "Degradation modeling and RUL prediction using Wiener process subject to
  multiple change points and unit heterogeneity," *RESS* 176. DOI 10.1016/j.ress.2018.04.005.
  **[3] [C] [search-snippet]** Fully Bayesian multiple-change-point Wiener model where *all* parameters are
  random, with an exact recursive online update per unit.
  **Bearing:** handles units differing both in rate *and* in where their degradation phases break — the
  likeliest structure behind the project's worst units, given Study B's onset-dependent aliasing.
- **Xu 2022** — "Online Bayesian prediction of remaining useful life for gamma degradation process under
  conjugate priors," arXiv:2212.02688. **[3] [D] [search-snippet]** Derives a conjugate prior for the
  homogeneous gamma process and extends it to the heterogeneous case. **Bearing:** the cheapest possible
  implementation of per-unit personalisation if the damage variable is monotone.
- **Zheng, Dong, Wang et al. 2024** — "Adaptive Wiener process–based remaining useful life prediction method
  considering multi-source variability," *Heliyon* 10(16). DOI 10.1016/j.heliyon.2024.e35925.
  **[2] [C] [search-snippet]** Particle-filter estimation with expectation-maximisation updating, aimed at
  uneven measurement intervals. **Bearing:** relevant to C2's irregular schedules, which would otherwise be
  absorbed silently into the cycle-count term.
- **Elwany & Gebraeel 2008** — "Sensor-driven prognostic models for equipment replacement and spare parts
  inventory," *IIE Transactions* 40(7). DOI 10.1080/07408170701730818. **[2] [C] [search-snippet]** Argues
  population failure-time distributions "do not distinguish between the different degradation
  characteristics of individual components." **Bearing:** the decision-side argument for why personalising
  the prior is worth its modelling cost.
- **Lin, Chai, Fan et al. 2023** — "Remaining useful life prediction using nonlinear multi-phase Wiener
  process and variational Bayesian approach," *RESS* 240. DOI 10.1016/j.ress.2023.109800.
  **[2] [C] [search-snippet]** Variational Bayes treating all parameters as random. Abstract not retrievable;
  detail provisional.

## (b) Stochastic degradation and first-passage remaining life

- **Zhang, Si, Hu & Lei 2018** — "Degradation data analysis and remaining useful life estimation: a review on
  Wiener-process-based methods," *European Journal of Operational Research* 271(3).
  DOI 10.1016/j.ejor.2018.02.033. **[3] [A] [search-snippet]** Focused review of first-passage-time
  formulations including random-effects drift and adaptive variants. **Bearing:** the most efficient entry
  point to this literature.
- **Wang Z., Chen Y., Cai Z. et al. 2020** — "Methods for predicting the remaining useful life of equipment
  in consideration of the random failure threshold," *J. Systems Engineering & Electronics* 31(1).
  DOI 10.23919/JSEE.2020.000018. **[3] [C] [search-snippet]** Nonlinear Wiener model with unit-to-unit
  variability and measurement error, deriving the remaining-life density under three *random failure
  threshold* constraint types.
  **Bearing:** the paper that most directly formalises "the end-of-life level itself differs per unit," not
  just the rate. Relevant because the project has no agreed end-of-life criterion for a soft actuator.
- **Sun, Li, Wang et al. 2020** — "An improved inverse Gaussian process with random effects and measurement
  errors for RUL prediction of hydraulic piston pump," *Measurement* 173. DOI 10.1016/j.measurement.2020.108604.
  **[3] [C] [search-snippet]** Inverse-Gaussian process with unit-level random effects and state-dependent
  measurement error, on two pump case studies. **Bearing:** the closest hardware analogue to a fluid-power
  actuator — monotone wear, noisy pressure-derived observations, unit heterogeneity.
- **Si, Wang, Hu, Chen & Zhou 2013** — "A Wiener-process-based degradation model with a recursive filter
  algorithm," *Mechanical Systems and Signal Processing* 35(1–2). DOI 10.1016/j.ymssp.2012.08.016.
  **[3] [C] [search-snippet]** Kalman-type recursive filter on a hidden drift state with first-hitting-time
  remaining life; the workhorse the adaptive-drift papers extend.
- **Wang H., Liao H., Ma X. & Bao R. 2021** — "Remaining useful life prediction and optimal maintenance time
  determination for a single unit using isotonic regression and gamma process model," *RESS* 210.
  DOI 10.1016/j.ress.2021.107504. **[3] [C] [search-snippet]** Single-unit prediction without a fitted
  population, enforcing monotonicity by isotonic regression. **Bearing:** the "single unit" framing is
  exactly the project's failure regime.
- **Tang, Yu, Wang et al. 2014** — "Remaining useful life prediction of lithium-ion batteries based on the
  Wiener process with measurement error," *Energies* 7(2). DOI 10.3390/en7020520. **[2] [C] [search-snippet]**
  Exact closed-form remaining-life distribution under measurement noise. **Bearing:** a pressure-derived
  health signal is noisy enough that ignoring measurement error biases the first-passage time.
- **Si, Wang, Hu & Zhou 2011** — "Remaining useful life estimation — a review," *EJOR* 213(1).
  DOI 10.1016/j.ejor.2010.11.018. **[2] [A] [search-snippet]** Standard taxonomy. Also listed in
  [02](02-unit-variability-population.md).
- **Lu & Meeker 1993** — DOI 10.1080/00401706.1993.10485038. **[2] [B] [search-snippet]** The ancestor of
  every "each unit has its own life" formulation. Primary entry in [02](02-unit-variability-population.md).

## (c) Health indices without a known end-of-life

- **de Pater & Mitici 2022** — "Developing health indicators and RUL prognostics for systems with few failure
  instances and varying operating conditions using a LSTM autoencoder," *Engineering Applications of
  Artificial Intelligence* 117. DOI 10.1016/j.engappai.2022.105582. **[3] [C] [search-snippet]** Trains on
  *unlabelled* data where true remaining life is unknown because units were preventively replaced before
  failure; reports a 97 % monotonicity improvement and 19 % error reduction against supervised baselines.
  **Bearing:** the best-matched paper to "we never observe true end-of-life for most units," which is the
  situation any physical soft-actuator pilot will be in.
- **Bajarunas, Baptista, Goebel & Chao 2024** — "Health index estimation through integration of general
  knowledge with unsupervised learning," *RESS* 251. DOI 10.1016/j.ress.2024.110352. **[3] [C] [search-snippet]**
  Unsupervised model baking *general* degradation priors such as monotonicity into architecture and loss;
  on turbofans and lithium-ion cells it matches a supervised model trained with health-index labels.
  **Bearing:** shows an unlabelled health index can reach supervised parity, which removes the justification
  for using cycle count as a pseudo-label — precisely what the project's clock column does.
- **Liu K., Gebraeel & Shi 2013** — "A data-level fusion model for developing composite health indices,"
  *IEEE T-ASE* 10(3). DOI 10.1109/TASE.2013.2250282. **[3] [C] [search-snippet]** Fuses multiple degradation
  signals into one composite health index. **Bearing:** the reference method for building one scalar index
  from several pressure-derived features instead of leaning on cycle count.
- **Liu K., Chehade & Song 2015** — "Optimize the signal quality of the composite health index via data
  fusion," *IEEE T-ASE*. DOI 10.1109/TASE.2015.2446752. **[3] [C] [search-snippet]** Defines a
  degradation-specific signal-to-noise metric and constructs the fused index by maximising it.
  **Bearing:** a defensible objective for weighting pressure features when no end-of-life labels exist.
- **Saxena, Goebel, Simon & Eklund 2008** — "Damage propagation modeling for aircraft engine run-to-failure
  simulation," *ICPHM*. DOI 10.1109/PHM.2008.4711414. **[1] [C] [search-snippet]** Generates the standard
  turbofan benchmark, in which remaining-life targets must be assigned by convention.
  **Bearing:** background worth reading to see that the field's standard benchmark quietly bakes in a
  *chosen* labelling convention — the same arbitrary normalising choice the project makes with cycle count.

## (d) Condition-based versus scheduled maintenance

Andersen & Nielsen 2024 and Pedersen & Vatn 2022 are covered above.

- **de Jonge, Teunter & Tinga 2017** — "The influence of practical factors on the benefits of condition-based
  maintenance over time-based maintenance," *RESS* 158. DOI 10.1016/j.ress.2016.10.002.
  **[3] [C] [search-snippet]** Finds the relative benefit "strongly depends on the behavior of the
  deterioration process, the severity of failures, the required setup time, **the accuracy of the condition
  measurements**, and **the amount of randomness in the deterioration level at which failure occurs**."
  **Bearing:** the headline citation for this section. It names measurement accuracy and failure-level
  randomness as the two factors that erode a state-triggered policy's advantage toward parity with a clock —
  both of which the project has in abundance.
- **Fauriat & Zio 2020** — "Optimization of an aperiodic sequential inspection and condition-based
  maintenance policy driven by value of information," *RESS* 204. DOI 10.1016/j.ress.2020.107133.
  **[3] [C] [search-snippet]** Uses value of information to schedule the next inspection aperiodically when
  state is known only through imperfect monitoring. **Bearing:** the decision-theoretic version of R1's
  muting experiment — formal machinery for asking whether a pressure measurement is worth more than the clock
  at a given moment. Links this theme to [05](05-measurement-scheduling.md).
- **Chen, Ye & Xiang 2015** — "Condition-based maintenance using the inverse Gaussian degradation model,"
  *EJOR* 243(1). DOI 10.1016/j.ejor.2014.11.029. **[2] [C] [search-snippet]** Threshold policy on an
  inverse-Gaussian process with random effects, thresholds optimised jointly. **Bearing:** shows how to turn
  a personalised posterior into an actual replacement rule rather than stopping at a number.
- **"Advanced optimization and comparative assessment of time- and condition-based maintenance strategies"
  2026** — *Results in Materials* 30. DOI 10.1016/j.rinma.2026.100911. **[3] [C] [search-snippet]**
  Head-to-head Monte Carlo comparison of block replacement (pure clock), periodic inspection, and
  quantile-based inspection under a combined cost-rate and cost-variability objective; the state-triggered
  policy wins on both, block replacement is worst.
  **Bearing:** an explicit three-way baseline design — clock only, fixed-interval inspection, state-triggered
  — which is the comparison structure the project's Study 3 already uses and could cite for precedent.
- **Alaswad & Xiang 2017** — "A review on condition-based maintenance optimization models," *RESS* 157.
  DOI 10.1016/j.ress.2016.08.009. **[2] [A] [search-snippet]** Survey by degradation process and inspection
  scheme. **Bearing:** policy-structure vocabulary — control-limit, two-threshold, periodic versus aperiodic.
- **de Jonge & Scarf 2020** — "A review on maintenance optimization," *EJOR* 285(3).
  DOI 10.1016/j.ejor.2019.09.047. **[2] [A] [search-snippet]** Reviews 200+ papers from 2001–2018.
  **Bearing:** the authoritative map of where a degradation-triggered policy sits against age- and
  block-replacement baselines.
- **Srinivasan & Parlikad 2013** — "Value of condition monitoring in infrastructure maintenance," *Computers
  & Industrial Engineering* 66(2). DOI 10.1016/j.cie.2013.05.022. **[2] [C] [search-snippet]** Frames
  monitoring as an investment whose value must be quantified against the decision it improves. Abstract not
  retrievable. **Bearing:** one of few papers asking whether monitoring pays at all rather than assuming it.
- **Quatrini, Costantino, Di Gravio & Patriarca 2020** — "Condition-Based Maintenance: an extensive
  literature review," *Machines* 8(2):31. DOI 10.3390/machines8020031. **[1] [A] [search-snippet]**
  Bibliometric analysis over 4000+ contributions. Background only.

---

## What this literature does not settle

- **Nobody estimates a life-normalising constant from a non-monotone, non-cumulative signal.** Every
  first-passage formulation assumes a state that accumulates toward a threshold. Chamber pressure is a
  *performance* observable, not a damage accumulator, and it can recover through viscoelastic relaxation,
  temperature and re-seating. The health-index papers fuse many sensors, which the project does not have.
- **The population-prior literature personalises a *rate*, not a *total life scale*.** Gebraeel-style
  updating personalises drift; R1 says the project's estimator mis-scales per-unit total life. Only Severson
  and the hierarchical battery work attack the total-life constant directly, and both use rich early-cycle
  features validated against fully observed end-of-life. Without run-to-failure units neither transfers as is.
- **No published benchmark says how much a clock covariate *should* contribute.** R1's muting experiment has
  no counterpart: the field reports error against a baseline model, not feature-ablation of the age term. So
  there is no external standard for "a healthy estimator loses at most X % when age is removed." Establishing
  one is a contribution the project is positioned to make.
- **Every condition-versus-schedule comparison assumes a correctly specified degradation model.** None models
  the realistic failure the project actually has — an estimator that is *partly a clock*. Whether a
  state-triggered policy driven by a biased estimator still beats a fixed schedule is, on this evidence, an
  open question and arguably the sharpest one the project's data could answer.
- **There is no agreed end-of-life criterion for a soft actuator.** Failure-threshold randomness is
  acknowledged and even parameterised, but always from data requiring observed failures. Leak, stiffness
  drift and stroke loss are all candidates and the literature picks none, so any result will be conditional
  on a definition the project must choose and defend.
