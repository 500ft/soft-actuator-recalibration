# 01 — Identifiability and observability

Serves [Study B](../docs/specs/observability-program/studyB-identifiability.md), which computes a
Cramér–Rao bound on a latent normalised-life coordinate from pressure-only features and reports it
identifiable before the acceleration onset and aliased with onset fraction and leak after it.

**Outcome:** the objection recorded below was acted on. Brun's subset index and a profile likelihood were run
on 2026-09-23; the aliasing group is confirmed and is a *triple*, but the limit is **practical at this noise
level**, not structural, and the wording was corrected repo-wide.
[Evidence](../evidence/studyB-structural-2026-09-23/README.md).

Grading and provenance rules are in [README](README.md). `[full-text]` means the abstract or paper page was
fetched; `[search-snippet]` means a search summary plus a verified metadata record.

---

## Read this first: the strongest objection to Study B's method

- **Wieland, Hauber, Rosenblatt, Tönsing & Timmer 2021** — "On structural and practical identifiability,"
  *Current Opinion in Systems Biology* 17:60–69. DOI 10.1016/j.coisb.2021.03.005; arXiv:2102.05100.
  **[aboutness 3] [evidence D] [full-text]** Argues explicitly that "the classical approach based on the
  Fisher information matrix has severe shortcomings" for practical identifiability: FIM-based intervals are
  local, can be unreliable for finite samples under nonlinearity, and are *insensitive to practical
  non-identifiability*. Recommends profile likelihood instead.
  **Bearing:** a published objection to Study B's core inference, now answered rather than omitted. Study B
  computed a local linearised bound; this paper says that object cannot certify practical identifiability. The
  profile likelihood it recommends was run on 2026-09-23 and downgraded the claim from structural to practical.

- **Chis, Villaverde, Banga & Balsa-Canto 2016** — "On the relationship between sloppiness and
  identifiability," *Mathematical Biosciences* 282:147–161. DOI 10.1016/j.mbs.2016.10.009.
  **[3] [B] [search-snippet]** Concludes sloppiness is *not* equivalent to lack of structural or practical
  identifiability — sloppy models can be identifiable — and that identifiability criteria beat sloppiness
  measures for experimental design.
  **Bearing:** guarded against the overreach of reading an ill-conditioned information matrix as proof of
  non-identifiability. The test was run on 2026-09-23 and this caution proved correct: the wording was
  downgraded from structural to practical.

---

## (a) Foundations: Fisher information, Cramér–Rao, observability

- **Kay 1993** — "Fundamentals of Statistical Signal Processing, Vol. I: Estimation Theory," *Prentice Hall*.
  ISBN 0-13-345711-7. **[3] [A] [search-snippet]** Standard derivation of the FIM, the Cramér–Rao bound, its
  regularity conditions, and the fact that a singular FIM means a parameter or combination is not locally
  identifiable. **Bearing:** licenses the bound as a statement about *any* unbiased estimator, not only the
  ridge estimator Study C happens to use.
- **Van Trees 1968** — "Detection, Estimation, and Modulation Theory, Part I," *Wiley*. ISBN 0-471-89955-0.
  **[2] [A] [search-snippet]** Introduces the Bayesian/posterior Cramér–Rao bound for estimating random
  parameters and states. **Bearing:** normalised life is a latent state with a prior, not a fixed unknown
  constant, so the classical and Bayesian bounds answer different questions about Study B's σ_u. Worth
  stating which one is being reported.
- **Hermann & Krener 1977** — "Nonlinear controllability and observability," *IEEE Trans. Automatic Control*
  22(5):728–740. DOI 10.1109/TAC.1977.1101601. **[2] [A] [search-snippet]** Defines local weak observability
  and the observability rank condition via Lie derivatives — the noise-free structural counterpart of a
  full-rank FIM. **Bearing:** supplies the vocabulary for claiming the aliasing is structural rather than a
  noise artefact, and the standard that claim would have to meet.
- **Lall, Marsden & Glavaški 2002** — "A subspace approach to balanced truncation for model reduction of
  nonlinear control systems," *Int. J. Robust and Nonlinear Control* 12(6):519–535. DOI 10.1002/rnc.657.
  **[2] [B] [search-snippet]** Origin of *empirical* observability Gramians estimated from simulated
  perturbation responses rather than analytic solutions. **Bearing:** fits a simulator with no closed-form
  output map, which is exactly Study B's situation.
- **Powel & Morgansen 2015** — "Empirical observability Gramian rank condition for weak observability of
  nonlinear systems with control," *54th IEEE CDC*. DOI 10.1109/CDC.2015.7403218. **[3] [B] [search-snippet]**
  Conditions under which the rank of an empirical observability Gramian certifies local weak observability.
  **Bearing:** would convert Study B's finite-difference sensitivity matrix from a heuristic into a
  rank-based observability test, including its dependence on the excitation applied.
- **Krener & Ide 2009** — "Measures of unobservability," *48th IEEE CDC*. DOI 10.1109/CDC.2009.5400067.
  **[3] [B] [search-snippet]** Scalar measures grading *how badly* a state is unobservable rather than a
  binary verdict. **Bearing:** matches Study B's map, where identifiability degrades continuously across
  life rather than flipping at a point.

## (b) Structural versus practical identifiability

- **Raue et al. 2009** — "Structural and practical identifiability analysis of partially observed dynamical
  models by exploiting the profile likelihood," *Bioinformatics* 25(15):1923–1929.
  DOI 10.1093/bioinformatics/btp358. **[3] [B] [search-snippet]** The canonical profile-likelihood method: a
  flat profile in all directions indicates structural non-identifiability; one that flattens on a single side
  indicates practical non-identifiability from data quantity or quality. **Bearing:** the one diagnostic that
  separates "aliased by model structure" from "aliased at this noise level," which a FIM-only analysis cannot.
- **Miao, Xia, Perelson & Wu 2011** — "On identifiability of nonlinear ODE models and applications in viral
  dynamics," *SIAM Review* 53(1):3–39. DOI 10.1137/090757009. **[3] [A] [search-snippet]** Connects structural
  identifiability methods to practical/sensitivity-based ones including FIM and correlation criteria for
  partially observed systems. **Bearing:** cleanest single citation for FIM conditioning as an identifiability
  criterion, with its caveats stated in the same place.
- **Raue et al. 2014** — "Comparison of approaches for parameter identifiability analysis of biological
  systems," *Bioinformatics* 30(10):1440–1448. DOI 10.1093/bioinformatics/btu006. **[3] [B] [search-snippet]**
  Benchmarks profile likelihood, bootstrap, Bayesian sampling and FIM approaches on shared models, reporting
  where the linearised approach misleads. **Bearing:** indicates what a reviewer will expect as a cross-check
  on a bound-only identifiability map.
- **Villaverde 2019** — "Observability and structural identifiability of nonlinear biological systems,"
  *Complexity* 2019:8497093. DOI 10.1155/2019/8497093; arXiv:1812.04525. **[3] [B] [full-text]** Shows
  structural identifiability is a special case of observability once parameters are treated as constant
  states. **Bearing:** formal justification for treating the life coordinate and its two nuisance parameters
  as one joint observability problem, which is what "aliasing" means.
- **Díaz-Seoane, Rey Barreiro & Villaverde 2023** — "STRIKE-GOLDD 4.0," *Bioinformatics* 39(1):btac748.
  DOI 10.1093/bioinformatics/btac748. **[2] [B] [search-snippet]** Software for observability–identifiability
  rank tests on nonlinear ODE models, reporting which specific states or parameters are unidentifiable.
  **Bearing:** usable if a reduced analytic form of the degradation and leak model can be written down; it
  would settle structurally whether onset fraction and leak alias with life, independent of noise.
- **Simpson & Maclaren 2023** — "Profile-Wise Analysis," *PLOS Computational Biology* 19(9):e1011515.
  DOI 10.1371/journal.pcbi.1011515. **[2] [C] [search-snippet]** Propagates per-parameter profile likelihoods
  into prediction intervals, so non-identifiable parameters can still yield identifiable *predictions*.
  **Bearing:** the project's downstream claim is a recalibration decision, not a parameter value, so
  predictions may survive an aliased coordinate. Directly relevant to how Study B's result should be framed.

## (c) Diagnosing aliasing, collinearity and sloppiness

- **Brun, Reichert & Künsch 2001** — "Practical identifiability analysis of large environmental simulation
  models," *Water Resources Research* 37(4):1015–1030. DOI 10.1029/2000WR900350. **[3] [B] [search-snippet]**
  Defines a per-parameter importance measure and a *collinearity index* quantifying near-linear dependence
  within a parameter subset, with values above roughly 10–20 flagged as poorly identifiable.
  **Bearing:** the most directly usable tool for Study B's open question, because it scores *subsets* and so
  would name the {life, onset, leak} triple explicitly rather than reporting pairwise angles.
- **Gutenkunst et al. 2007** — "Universally sloppy parameter sensitivities in systems biology models,"
  *PLoS Computational Biology* 3(10):e189. DOI 10.1371/journal.pcbi.0030189. **[3] [B] [search-snippet]**
  Across 17 models, information-matrix eigenvalue spectra span many decades with eigenvectors aligned to
  parameter *combinations*; collective predictions stay tight while individual parameters stay loose.
  **Bearing:** the standard reference for reading Study B's result as an eigen-spectrum problem, and for the
  caution that a loose coordinate does not by itself invalidate the model's predictions.
- **Meshkat, Eisenberg & DiStefano 2009** — "An algorithm for finding globally identifiable parameter
  combinations of nonlinear ODE models using Gröbner bases," *Mathematical Biosciences* 222(2):61–72.
  DOI 10.1016/j.mbs.2009.08.010. **[3] [B] [search-snippet]** Computes the *identifiable combinations* when
  individual parameters are not identifiable, giving an explicit reparameterisation. **Bearing:** the
  constructive answer to aliasing — report the identifiable combination of life, onset and leak rather than
  the coordinate alone.
- **Massonis & Villaverde 2020** — "Finding and breaking Lie symmetries," *Symmetry* 12(3):469.
  DOI 10.3390/sym12030469. **[3] [B] [search-snippet]** Each Lie symmetry leaving the output invariant is a
  direction of structural non-identifiability, and the paper shows how to break one by fixing a parameter or
  adding an input or output. **Bearing:** a symmetry linking life scale to onset fraction would explain
  *why* the aliasing begins precisely at acceleration onset.
- **Tönsing, Timmer & Kreutz 2014** — "Cause and cure of sloppiness in ordinary differential equation
  models," *Physical Review E* 90(2):023303. DOI 10.1103/PhysRevE.90.023303; arXiv:1406.1734.
  **[3] [B] [search-snippet]** Traces the broad eigenvalue spectrum to model topology *and experimental
  design*, and constructs non-sloppy designs. **Bearing:** argues sloppiness is partly a property of the
  probing schedule, which reframes post-onset aliasing as potentially design-curable — the same hypothesis
  Study C2's schedule axis tests.
- **Transtrum & Qiu 2014** — "Model reduction by manifold boundaries," *Physical Review Letters*
  113(9):098701. DOI 10.1103/PhysRevLett.113.098701. **[2] [B] [search-snippet]** Uses model-manifold
  geodesics to find the least-constrained directions and take limits along them. **Bearing:** a principled
  alternative to fixing nuisance parameters by hand.

## (d) Identifiability in degradation and prognostics

- **Acuña, Orchard & Saona 2018** — "Conditional predictive Bayesian Cramér–Rao lower bounds for prognostic
  algorithms design," *Applied Soft Computing* 72:647–660. DOI 10.1016/j.asoc.2018.01.033.
  **[3] [B] [full-text]** Bayesian CRLBs on predicted-state mean squared error conditional on measurement
  data, used as a design and admissibility criterion, demonstrated on lithium-ion end-of-discharge.
  **Bearing:** the closest published analogue to Study B — a Cramér–Rao bound on a latent degradation state
  used as a design criterion rather than an accuracy claim. Precedent for the whole approach.
- **Lin & Khoo 2024** — "Identifiability study of lithium-ion battery capacity fade using degradation mode
  sensitivity...," *Journal of Power Sources* 599:234446. DOI 10.1016/j.jpowsour.2024.234446;
  arXiv:2309.17331. **[3] [B] [full-text]** Derives analytic sensitivity gradients of an observable with
  respect to degradation-mode parameters and identifies four regimes in which different modes limit apparent
  capacity — identifiability that *changes with degradation state*.
  **Bearing:** the nearest domain analogue of Study B's central finding. An observable-only degradation
  problem where mechanisms become mutually confounded in specific regimes, with sensitivity gradients used
  to locate the informative windows. The strongest precedent that regime-dependent identifiability is real
  and reportable.
- **Kamariotis, Sardi, Papaioannou, Chatzi & Straub 2023** — "On off-line and on-line Bayesian filtering for
  uncertainty quantification of structural deterioration," *Data-Centric Engineering* 4:e17.
  DOI 10.1017/dce.2023.13; arXiv:2205.03478. **[2] [C] [full-text]** Compares MCMC and particle filtering for
  jointly inferring deterioration states and uncertain parameters on a nonlinear fatigue-crack model.
  **Bearing:** the standard machinery for joint latent-state-plus-parameter inference from sparse noisy
  observations, and the practical symptoms that appear when those quantities are weakly separable.
- **Chatzis, Chatzi & Smyth 2014** — "On the observability and identifiability of nonlinear structural and
  mechanical systems," *Structural Control and Health Monitoring* 22(3):574–593. DOI 10.1002/stc.1690.
  **[3] [B] [search-snippet]** Applies nonlinear observability and identifiability rank analysis to joint
  state-and-parameter estimation in mechanical systems including hysteretic and degrading elements.
  **Bearing:** the mechanical-engineering precedent for this exact class of claim, and a venue-appropriate
  citation for a soft-robotics fatigue-state paper.

## (e) Experimental design to restore identifiability

- **Franceschini & Macchietto 2008** — "Model-based design of experiments for parameter precision: state of
  the art," *Chemical Engineering Science* 63(19):4846–4872. DOI 10.1016/j.ces.2007.11.034.
  **[3] [A] [search-snippet]** Reviews information-based design criteria for nonlinear dynamic models, the
  dynamic-optimisation formulation over inputs *and sampling times*, and the local-design limitation.
  **Bearing:** the reference for proposing an information-based probe schedule to break the post-onset
  aliasing — a more principled C2 successor than a fixed cadence grid.
- **Raue, Kreutz, Maiwald, Klingmüller & Timmer 2011** — "Addressing parameter identifiability by model-based
  experimentation," *IET Systems Biology* 5(2):120–130. DOI 10.1049/iet-syb.2010.0061.
  **[3] [B] [search-snippet]** Uses profile likelihoods to decide *which* new measurement would remove a
  specific non-identifiability, rather than optimising a scalar criterion blindly.
  **Bearing:** directly answers "what to do about it" — the profile shape says whether a second observable
  channel or a different excitation is needed to separate life from onset and leak.
- **White et al. 2016** — "The limitations of model-based experimental design and parameter estimation in
  sloppy systems," *PLOS Computational Biology* 12(12):e1005227. DOI 10.1371/journal.pcbi.1005227;
  arXiv:1602.05135. **[3] [C] [search-snippet]** In sloppy systems, information-optimal designs give
  diminishing returns: experiments needed to constrain individual parameters grow steeply while predictions
  are already well constrained. **Bearing:** the honest counterweight — chasing identifiability of the latent
  coordinate may cost more experiments than the recalibration decision justifies.
- **Pronzato & Pázman 2013** — "Design of Experiments in Nonlinear Models," *Springer*.
  ISBN 978-1-4614-6362-7. **[2] [A] [search-snippet]** Textbook treatment of information-based optimality
  criteria, the asymptotic-normality assumptions behind them, and small-sample corrections where the bound is
  optimistic. **Bearing:** the place to check whether Study B's regularity conditions actually hold near the
  acceleration onset, where the sensitivity structure changes.

---

## What this literature does not give the project

- **No soft-robotics identifiability precedent.** A dedicated search returned only parameter-fitting work for
  soft pneumatic actuators, no structural or practical identifiability analysis of a latent state from
  pressure-only features. That supports the novelty claim and simultaneously means there is no template to copy.
- **No treatment of a self-referential normalised-life coordinate.** Every entry identifies physical
  parameters or states with fixed units. A coordinate whose normalisation is defined *by the degradation
  model itself* invites aliasing with any parameter that rescales the clock, which is exactly what the onset
  fraction does. That time-reparameterisation class of non-identifiability is not analysed in the retrieved work.
- **No convention for regime-resolved reporting.** Only Lin & Khoo report identifiability varying by
  degradation regime. There is no established presentation for "identifiable before onset, aliased after," so
  the project must define and defend it.
- **The structural tools assume a closed-form model.** Lie symmetries, Gröbner-basis combinations and
  STRIKE-GOLDD all need explicit equations and an output map. The project computes numerical features from a
  simulator, so only the sensitivity-matrix tools transfer — and those are the ones Wieland et al. and Chis
  et al. warn cannot certify a *structural* claim.
- **Nothing validates a simulation-derived bound against real between-unit dispersion.** The bound is a
  statement about estimators under the assumed generator, not about actuators.
