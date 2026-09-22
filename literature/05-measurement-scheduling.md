# 05 — When to measure: inspection scheduling and measurement design

Serves [Study C2](../docs/specs/observability-program/studyC2-preregistration.md), whose secondary axis
varies the probe schedule (cadences of 125, 250 and 500 cycles, a late start, and a probe-count-matched
oracle concentrated after the unit's acceleration onset).

Grading and provenance rules in [README](README.md). Every entry in this file is `[search-snippet]`: the
identifiers were resolved against metadata services, but the papers were not read in full. Two load-bearing
claims were independently re-verified and are marked as such.

---

## Read this first: one result that supports the C2 hypothesis, one that undercuts it

- **Tung & Chen 2025** — "Optimal Designs for Gamma Degradation Tests," arXiv:2508.09569.
  **[aboutness 3] [evidence B] [abstract independently verified]** Analytically optimises the number of test
  units, the number of inspections and the inspection *times* for gamma degradation tests. Quoting the
  abstract verbatim: **"Interestingly, we show that designs with periodic inspection times are the least
  efficient."**
  **Bearing:** the strongest theoretical support for C2's hypothesis. At a fixed probe count, *where* probes
  sit changes estimation efficiency, and a uniform cadence — which is exactly what Study C used — is the
  worst case.

- **Severson et al. 2019** — "Data-driven prediction of battery cycle life before capacity degradation,"
  *Nature Energy* 4:383–391. DOI 10.1038/s41560-019-0356-8.
  **[3] [B] [numbers independently verified]** 124 lithium iron phosphate cells with cycle lives spanning
  **150 to 2,300 cycles**. Models using only the first 100 cycles — a window over which median capacity had
  *increased* by 0.2 %, i.e. before any degradation was visible — predicted cycle life to **9.1 % test
  error**, and the first 5 cycles classified cells into short- and long-life groups at **4.9 % error**.
  **Bearing:** an unrebutted counterexample to the project's framing. A pre-onset observation window carried
  the lifetime signal in a different degradation system. "The probes fell before acceleration" therefore
  cannot by itself establish that observation timing caused Study C's transfer failure — the signal might be
  present pre-onset and simply not captured by the five chosen features.

---

## (a) Optimal inspection intervals and scheduling

- **Barlow, Hunter & Proschan 1963** — "Optimum Checking Procedures," *J. SIAM* 11(4). DOI 10.1137/0111080.
  **[2] [A] [search-snippet]** The founding formulation: choose checking times to minimise expected cost of
  undetected failure plus inspection cost, yielding a *non-uniform* optimal sequence. **Bearing:** the
  canonical statement that equal spacing is a convenience, not an optimum.
- **Munford & Shahani 1972** — "A Nearly Optimal Inspection Policy," *J. Operational Research Society* 23(3).
  DOI 10.1057/jors.1972.56. **[2] [A] [search-snippet]** Closed-form near-optimal non-periodic sequence
  performing essentially as well as the exact optimum for Weibull and gamma lifetimes. **Bearing:** compares
  schedules *at matched inspection count*, which is precisely the contrast C2's oracle implements.
- **Castro & Landesa 2019** — "A dependent complex degrading system with non-periodic inspection times,"
  *Computers & Industrial Engineering* 133. DOI 10.1016/j.cie.2019.04.053. **[2] [B] [search-snippet]**
  Dynamic policy setting the next inspection time from health information revealed at the current one.
  **Bearing:** the formal template for a "concentrate probes after onset" schedule, though onset there is an
  arrival process rather than a fatigue knee.
- **Wang, Zhao & He 2026** — "Maintenance planning for nonlinearly degrading systems," *Reliability
  Engineering & System Safety*. DOI 10.1016/j.ress.2026.112637. **[2] [C] [search-snippet]** Non-periodic
  intervals for nonlinear degradation, densifying as the degradation rate rises. **Bearing:** the closest
  analogue to the onset-concentrated oracle, framed as a maintenance-cost rather than estimation problem.

## (b) Degradation-test planning and measurement allocation

- **Balakrishnan & Qin 2019** — "Nonparametric optimal designs for degradation tests," *Journal of Applied
  Statistics* 47(2). DOI 10.1080/02664763.2019.1648392. **[3] [C] [search-snippet]** Optimises sample size,
  *measurement frequency* and total operation time under a budget, minimising bootstrap mean squared error of
  a first-passage percentile, without committing to a parametric degradation family. **Bearing:** the most
  usable framing when a Wiener or gamma path cannot be assumed, and "measurement frequency" is literally the
  125/250/500 knob.
- **Shat & Schwabe 2021** — "Experimental Designs for Accelerated Degradation Tests Based on Linear Mixed
  Effects Models," arXiv:2102.09446. **[3] [B] [search-snippet]** Optimal designs minimising asymptotic
  variance of the median-failure-time estimator, treating measurement time points as design variables.
  **Bearing:** the machinery for asking whether a given cadence is efficient — but it assumes a *linear* path
  and so cannot represent post-onset acceleration.
- **Tseng & Lee 2016** — "Optimum Allocation Rule for Accelerated Degradation Tests," *Technometrics* 58(2).
  DOI 10.1080/00401706.2015.1033109. **[2] [B] [search-snippet]** Analytic optimum allocation across stress
  levels for the exponential-dispersion family. **Bearing:** the transferable result is that optima are often
  *corner* solutions — effort concentrates rather than spreads — the same structural claim the oracle makes
  in the time dimension.
- **Tung, Lee & Tseng 2022** — "Analytical approach for designing accelerated degradation tests under an
  exponential dispersion model," *J. Statistical Planning and Inference* 218. DOI 10.1016/j.jspi.2021.10.002.
  **[3] [B] [search-snippet]** Reports that the number of measurement times and the allocation of test units
  are **non-identifiable decision variables**.
  **Bearing:** a direct warning for C2. Probe count and unit count can trade off against each other, so a
  probe-count-matched comparison isolates timing only if unit count and total duration are also pinned. C2
  does hold the cohort fixed, which satisfies this — worth stating explicitly in the write-up.
- **Lee, Tseng & Hong 2020** — "Global planning of accelerated degradation tests," *Naval Research Logistics*
  67(6). DOI 10.1002/nav.21923. **[3] [B] [search-snippet]** Semi-analytical determination of sample size and
  configuration under an explicit cost constraint. **Bearing:** formalises the measurement-budget trade-off —
  total probes are a cost, and a plan must say what each buys.
- **Park & Yum 1997** — "Optimal Design of Accelerated Degradation Tests," *Engineering Optimization* 28(3).
  DOI 10.1080/03052159708941132. **[2] [B] [search-snippet]** Early joint optimisation of stress levels, unit
  allocation and measurement times. **Bearing:** the historical anchor for treating measurement timing as a
  first-class design variable.

## (c) Information-based selection of measurement times

- **Chaloner & Verdinelli 1995** — "Bayesian Experimental Design: A Review," *Statistical Science* 10(3).
  DOI 10.1214/ss/1177009939. **[2] [A] [search-snippet]** Ties design criteria to expected-utility
  maximisation and makes explicit that a design is optimal only relative to a stated utility and prior.
  **Bearing:** an essential caveat — the oracle schedule is optimal for *some* estimand, and this forces the
  project to name which one before claiming timing causes transfer failure.
- **Rodríguez-Narciso & Christen 2015** — "Optimal sequential Bayesian analysis for degradation tests,"
  *Lifetime Data Analysis* 22(3). DOI 10.1007/s10985-015-9339-7. **[3] [B] [search-snippet]** Sequentially
  selects the *next* observation time to maximise precision on a time-to-failure quantile against test cost.
  **Bearing:** the closest published analogue to an *adaptive* oracle — it picks probe times online from
  accumulated data rather than from oracle knowledge of onset, which is the deployable version C2's oracle
  is not.
- **Li, Hu, Sun & Kang 2017** — "A Bayesian Optimal Design for Sequential Accelerated Degradation Testing,"
  *Entropy* 19(7):325. DOI 10.3390/e19070325. **[2] [C] [search-snippet]** Sequential design where early data
  forms the prior for later stages, motivated as a fix for over- and under-testing caused by bad prior
  guesses. **Bearing:** shows the prior-misspecification failure mode — a schedule optimised under wrong
  nominal parameters can be worse than a naive one.
- **Liu & Tang 2010** — "A Bayesian optimal design for accelerated degradation tests," *Quality and
  Reliability Engineering International* 26(8). DOI 10.1002/qre.1151. **[2] [B] [search-snippet]** Minimises
  expected pre-posterior variance of the quantity of interest. **Bearing:** the right criterion for scoring
  C2's five schedules *before* running them rather than only after.

## (d) Sensor scheduling and value of information

- **Jawaid & Smith 2015** — "Submodularity and greedy algorithms in sensor scheduling for linear dynamical
  systems," *Automatica* 61. DOI 10.1016/j.automatica.2015.08.022. **[2] [B] [search-snippet]** Greedy sensor
  scheduling has near-optimality guarantees only for submodular surrogates such as log-determinant of the
  information matrix; the *trace* of estimation error — the quantity actually of interest — is not
  submodular, so the guarantee does not transfer.
  **Bearing:** an important negative result. A greedily constructed schedule is provably good only under a
  specific information criterion, not under prediction error, which is what C2 measures.
- **Guestrin, Krause & Singh 2005** — "Near-optimal sensor placements in Gaussian processes," *ICML*.
  DOI 10.1145/1102351.1102385. **[2] [B] [search-snippet]** Mutual-information placement of a *fixed number*
  of observations is submodular, giving a greedy guarantee, and beats entropy-based placement which pushes
  observations to the boundary. **Bearing:** the canonical formalisation of "same number of probes, better
  placed," and it predicts that a naive information criterion would push probes toward the ends of the cycle
  range rather than around onset.
- **Andriotis, Papakonstantinou & Chatzi 2021** — "Value of structural health information in partially
  observable stochastic environments," *Structural Safety* 93:102072; arXiv:1912.12534.
  **[2] [B] [search-snippet]** Formalises value of information inside partially observable Markov decision
  processes for deteriorating systems, showing such a policy inherently schedules observation actions by
  their value, and that added monitoring improves long-run cost only under globally optimal policies.
  **Bearing:** supplies the decision-theoretic vocabulary for what a probe is *worth*, the missing half of a
  probe-count-matched comparison.

## (e) Observation-window effects on prognostic accuracy

Severson et al. 2019 belongs here and is covered above.

- **Chen, Li, Zhou & Xia 2021** — "Two-phase degradation data analysis with change-point detection based on
  Gaussian process degradation model," *Reliability Engineering & System Safety* 216:107916.
  DOI 10.1016/j.ress.2021.107916. **[2] [C] [search-snippet]** Two-phase change-point degradation model
  estimating parameters and the unit-specific change point jointly.
  **Bearing:** this is the model class the project's acceleration-onset framing assumes, and it shows the
  change point is *a parameter with its own estimation variance*. An oracle schedule defined by the true
  onset is therefore a stronger assumption than a schedule that must locate onset from data — worth saying
  plainly when the oracle result is reported.
- **Jeon, Jin & Kim 2026** — "Effects of Window and Batch Size on Autoencoder-LSTM Models for Remaining Useful
  Life Prediction," *Machines* 14(2):135. DOI 10.3390/machines14020135. **[2] [C] [search-snippet]**
  Systematic window-length sweep reporting an optimal plateau and increasing lag error as windows grow too
  long. **Bearing:** methodological precedent for sweeping a timing parameter with everything else fixed,
  though it varies window *length* on a dense signal rather than probe *placement* on a sparse one.

---

## What this literature does not settle

- **No probe-placement theory for a change-point path.** Every analytic design result here assumes a smooth
  monotone path in a known family. None derives optimal measurement times for a two-phase path with an
  unknown onset, which is exactly the structure the oracle exploits. The change-point literature models that
  structure but does not do design for it.
- **Oracle schedules are not a studied object.** Sequential designs place the next probe from data observed
  so far; value-of-information work places it by expected future value. Nothing here analyses a schedule
  built with hindsight knowledge of the true onset, so there is no published expectation for how large the
  oracle-versus-cadence gap should be, nor whether that gap is an upper bound or an artefact.
- **The criterion these optima optimise is never prediction transfer.** Every result targets asymptotic
  variance of a parameter, a lifetime quantile, or maintenance cost. Jawaid & Smith show guarantees hold for
  log-determinant surrogates and fail for estimation-error trace. Nothing establishes that a schedule optimal
  for parameter estimation also maximises cross-unit transfer accuracy, which is the failure being diagnosed.
- **Severson et al. remains unrebutted.** A pre-onset window sufficed elsewhere, so C2 must carry its own
  separation between "timing was wrong" and "these features carry no usable pre-onset information." No
  precedent here supplies that test.
