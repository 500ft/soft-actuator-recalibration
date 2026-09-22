# 06 — Soft pneumatic actuators, 2024–2026 update

An update pass over the [June 2026 base](../docs/A01_A04_Literature_Review.md), prioritising material that
would change a conclusion. Entries marked `[in base]` already appear there and are repeated only because
specimen-level numbers were recovered that the existing notes lack.

Grading and provenance rules in [README](README.md).

---

## Read this first: three findings that bear directly on the project's numbers

### 1. Real cross-actuator non-transfer, statistically tested — corroborates Study C

- **Lee, Zamora Yañez, Rogatinsky, Vo, Shingade & Ranzani 2025** — "Simplifying Data-Driven Modeling of the
  Volume-Flow-Pressure Relationship in Hydraulic Soft Robotic Actuators," arXiv:2506.23326.
  **[aboutness 3] [evidence B] [full-text, independently re-verified from the PDF]** Fits a 12-coefficient
  multivariate polynomial volume–pressure model per actuator, then applies a Chow test to every pair. Quoting
  the paper: "All pairwise tests between models from SBA1 through SBA4 produced significant differences, with
  p-values less than 10⁻⁷, thereby rejecting the hypothesis that any two models are identical," and "even the
  smallest F-statistic value (F = 1118.32) was greater than the critical value of 5.9 at a significance level
  of α = 0.0005."
  **Bearing:** real-hardware evidence that a pressure–volume model fitted on one actuator does not transfer to
  another. The nearest empirical anchor for [Study C's](../docs/specs/observability-program/studyC-transfer.md)
  C-FAIL.
  **Two caveats that must travel with this citation, both verified from the PDF:**
  1. The four actuators are *deliberately* different designs, not nominally identical units. Table V gives
     outer widths 14, 12, 11.3 and 48 mm, chamber diameters 2.4–23.5 mm, materials TPE and TPU, and maximum
     volumes 200, 450, 550 and 7000 mm³ — a 35× volume range. This bounds **cross-design** non-transfer. The
     project's claim concerns units from one mould, which is a strictly harder case to demonstrate.
  2. **The study is hydraulic, not pneumatic** — water is injected by syringe. Gas compressibility is a
     first-order term in a pneumatic pressure–volume loop and is absent here, so the mechanism generating the
     non-transfer may differ from the project's. Do not describe this as a pneumatic result.

### 2. Measured between-unit lifetime scatter is far below the simulation's assumption

- **Torzini, Puggelli, Volpe, Governi & Buonamici 2024** — "Characterization of fatigue behavior of 3D
  printed pneumatic fluidic elastomer actuators," *Int. J. Advanced Manufacturing Technology* 134:2725–2736.
  DOI 10.1007/s00170-024-14216-0. **[3] [A] [full-text]** `[in base]` Five specimens per group cycled to
  failure. 3D-printed TPU: 6456, 6018, 6350, 6638, 6589 cycles (mean 6410, SD 247, **CoV 3.9 %**). Cast
  Dragon Skin 30: 3233, 3480, 3769, 3434, 3279 (mean 3439, SD 211, **CoV 6.1 %**). Bending was logged every
  cycle through an embedded flex sensor, with "an average drift of 1.7° observed across all specimens".
  **Bearing:** the closest existing analogue to the project's premise — a per-cycle observable tracked over
  full life on nominally identical units. It also bounds controlled-fabrication scatter at CoV ≈ 4–6 %.

- **Du et al. 2025** — "Magnetic Tactile-Driven Soft Actuator for Intelligent Grasping and Firmness
  Evaluation," arXiv:2512.00907. **[3] [B] [full-text]** Three specimens cycled 0→35 kPa to rupture or
  delamination: failure at **531, 409 and 383 cycles** (CoV ≈ 17.5 %). The authors attribute the spread to
  "subtle microstructural differences such as foam porosity, magnet alignment, bonding uniformity, and wall
  thickness introduced during fabrication."
  **Bearing:** the counter-case to Torzini — hand-built composite actuators scatter roughly 3–4× more.
  *Housekeeping:* the [2026-09-16 novelty check](../docs/reviews/novelty-check-2026-09-16.md) recorded these
  three numbers as **unverified** because no fetched source contained them. They are now sourced. That open
  loop is closed.

  **Consequence for [Study A](../docs/specs/observability-program/studyA-preregistration.md).** Its
  dispersion model assumes rupture life with **CV 0.30**, cited as a repository fixture rather than a
  measurement. Every measured value located here is lower: 3.9 %, 6.1 %, and 17.5 % for a hand-built
  composite. A CV of 0.30 is therefore more dispersed than any published soft-actuator cohort found. Since
  [R1](../evidence/weekly-research-2026-09-21/README.md) showed transfer error tracks a unit's distance from
  the training median life, an overstated CV would *inflate* the very effect Study C reports. Logged in
  [gaps.md](gaps.md).

### 3. The project's probe may violate a stated methodological constraint

- **de la Morena, Ramos & Vázquez 2025** — "Hysteresis Modeling of Soft Pneumatic Actuators: An Experimental
  Review," *Actuators* 14(7):321. DOI 10.3390/act14070321. **[2] [D] [search-snippet]** `[in base]`
  Comparative review of hysteresis models, which uses quasi-static excitation because "higher-frequency
  excitations would introduce phase lag and distort hysteresis loop characterization."
  **Bearing:** the project's health probe runs at a fixed 2 Hz. If a probe at operating speed measures
  viscoelastic phase lag rather than the hysteretic state, the loop-area indicator may be partly a rate
  artefact. Study B's feature set already includes loop area at 1 Hz and 4 Hz, so the project has the means
  to test this. Logged in [gaps.md](gaps.md).

---

## (a) Fatigue and durability with specimen counts

Entries 1 and 2 above (Torzini 2024, Du 2025) belong here and are not repeated.

- **Bui et al. 2023** — "Endurance tests for a fabric-reinforced inflatable soft actuator," *Frontiers in
  Materials* 10:1112540. DOI 10.3389/fmats.2023.1112540. **[3] [A] [full-text]** `[in base]` Ten actuators;
  six cycled to 640 cycles and four to 1,280. Hysteresis loop widths and tip-path lengths increase up to
  roughly 160 cycles and then plateau. Burst pressure across specimens **37.1–41.15 kPa**, a range "less
  than 10 % of the burst pressure of the strongest soft actuator."
  **Bearing:** the only located study tracking a hysteresis feature over life on ten or more specimens — but
  the quantity is tip-trajectory hysteresis, not pressure–volume, and the tests stop well before failure.
- **Schreiber & Manns 2026** — "Investigation of the Long-Term Durability of Soft Pneumatic Actuators,"
  *Lecture Notes in Mechanical Engineering*. DOI 10.1007/978-3-032-16889-4_82. **[3] [B] [search-snippet]**
  Cyclic bending of 3D-printed TPU pneunets: "a consistent trajectory shift during initial cycles, which
  diminishes over time and can be effectively described using a logarithmic function" (R² > 0.95), and
  "beyond a threshold of 160 actuations, the trajectory exhibits no additional changes."
  **Bearing:** with Bui, two independent studies converge on a ~160-cycle log-saturating break-in. The
  project's generator applies a Mullins term that stabilises in a few cycles and then a monotone fatigue
  term; real drift is front-loaded and saturating. Specimen count not stated in the abstract.
- **Bowness & Doumit 2026** — "Soft pneumatic actuators for wearable systems," *Progress in Biomedical
  Engineering*. DOI 10.1088/2516-1091/ae6d5e. **[2] [D] [search-snippet]** Names manual winding as "a major
  source of unit-to-unit variation," with sensitivity to wrap alignment and pre-tension adding
  cycle-to-cycle asymmetry; reports photopolymer hinge degradation at ~100 cycles and that long-cycle data
  remain sparse. **Bearing:** a citable statement that unit-to-unit variation is a fabrication consequence,
  not noise — supports modelling it as a random effect, though it supplies no numbers.
- **Li et al. 2026** — "A Robotic Testing Platform for Pipelined Discovery of Resilient Soft Actuators,"
  arXiv:2602.20963. **[2] [B] [full-text]** Automated screening with three samples per condition; lifetime
  time-capped at three hours and reported in hours, no per-specimen standard deviations. Dielectric
  elastomer, not pneumatic. **Bearing:** the right methodology for generating multi-specimen life data at
  scale, but the paper does not publish spread.
- **Marl, Giesen & Heim 2025** — "Mullins effect of foamed liquid silicone elastomers," *Journal of Cellular
  Plastics*. DOI 10.1177/0021955X251317171. **[1] [B] [search-snippet]** Cyclic stress-softening of foamed
  liquid silicone. **Bearing:** material-level background for why the first tens of cycles dominate a
  pressure–volume loop change, supporting the treatment of break-in as a confounder distinct from fatigue.

## (b) Benchmarking and testing protocols

- **Wong, Luo & Scharff 2026** — "Durability of Soft Pneumatic Actuators: A Review and Benchmarking
  Protocol," *Advanced Robotics Research*. DOI 10.1002/adrr.202500172. **[3] [D] [search-snippet]** `[in base]`
  Cyclic durability "generally concentrated within 10³–10⁴ cycles"; extremes are a silicone actuator at
  **3.81 million cycles** and the best TPU at **123,000**. The proposed protocol requires reporting the
  cycle-counting metric, loading conditions, termination criteria, orientation, pressure profile and
  frequency. **Bearing:** those required fields are exactly the metadata a simulated cohort should declare,
  and the 10³–10⁴ modal range is the realistic horizon for any physical validation. Publisher blocked
  full-text retrieval; numbers come from indexed snippets.
- **Pană, Pătrașcu-Pană, Maican & Rădulescu 2026** — "Fault Detection, Sensing, and Intelligent Control in
  Soft Wearable Actuators: A Systematic Review," *Actuators* 15(8):431. DOI 10.3390/act15080431.
  **[2] [D] [search-snippet]** 106 included records; "the FDD subset was especially limited: nine records
  provided adjacent evidence and five were indirect," and the review names soft-actuator-specific fault
  benchmarks and multimodal health-state estimation as actionable priorities.
  **Bearing:** a defensible, countable statement that soft-actuator health-state estimation has essentially
  no empirical benchmark literature. Strengthens the novelty claim and answers a reviewer who asserts the
  problem is solved.
- **Thakker, Dela Cruz, Massoud & Libby 2026** — "Robust Silicone Pour Casting and Sensor Embedding
  Procedures for Soft Robotic Actuators," arXiv:2607.15422. **[2] [B] [search-snippet]** Fabrication protocol
  "validated across two operators and 24 successful fabrications"; no standard deviation or per-unit spread
  in the abstract. **Bearing:** the largest nominally identical batch located (n = 24) and the most likely
  existing source of real inter-unit dispersion data. Worth contacting the authors for the raw angle
  responses.
- **Lo Preti, Nazeer, Pinskier, Howard & Laschi 2026** — "Design-for-Benchmarking in Soft Robotics,"
  *Advanced Intelligent Systems*. DOI 10.1002/aisy.202600002. **[2] [D] [search-snippet]** Identifies
  component-versus-system performance gaps and calls consistent durability reporting the weakest current
  practice. **Bearing:** supports the project's scoping language that a component-level indicator validated
  in isolation does not license a system-level claim.
- **D'Andrea, Risitano & Santonocito 2025** — "Validation of Pneumatic Actuation for Fast Fatigue Testing of
  Additive-Manufactured Polymers," *Actuators* 14(12):598. DOI 10.3390/act14120598. **[1] [B] [search-snippet]**
  Pneumatic benchtop fatigue machine at ~9 % total harmonic distortion versus ~5 % for servo-hydraulic,
  without affecting results. **Bearing:** background for the cost-versus-fidelity trade-off if the pilot rig
  is ever built.

## (c) Self-sensing and pressure-only proprioception

- **Stella, Zhang, Della Santina, Hughes & Rus 2026** — "A Model-Based Decoupling Strategy for Proprioception
  and Contact Sensing in an Architected Soft Manipulator," arXiv:2607.15582. **[3] [B] [search-snippet]**
  Six pressure channels per segment against three kinematic degrees of freedom gives an overdetermined
  system; Huber regression flags outlier channels as contact. Relative bending error 0.11 ± 0.02; contact
  detection 97 % across 178 trials.
  **Bearing:** the strongest 2026 evidence that pressure alone carries both shape and contact information,
  and that **channel redundancy** is what makes the state separable. That is a design lever the project has
  not considered: Study B's aliasing might be broken by more observable channels rather than by more probes.
- **Manjunath, Wang, Li & Zhang 2026** — "Towards Effective Physical Reservoir Computing with a Pneumatic
  Soft Robot," arXiv:2609.02157. **[3] [B] [search-snippet]** Five-pouch sensing column, 36 matched trials;
  bending-angle estimation from 0.2 s of pressure history with a fixed ridge estimator. Two well-placed
  sensors recover most of the benefit and three essentially all of it; sealed pouches beat shared-manifold
  topologies, and higher baseline pressure *increases* error in shared-manifold configurations.
  **Bearing:** empirical support for the project's Study 4 negative result — pneumatic coupling through a
  shared manifold does degrade pressure-only estimation. Also uses a ridge readout on pressure history, the
  same estimator class as Study C.
- **Wang et al. 2025** — "Proprioceptive and Exteroceptive Information Perception in a Fabric Soft Robotic
  Arm via Physical Reservoir Computing," *Advanced Intelligent Systems*. DOI 10.1002/aisy.202400534;
  arXiv:2411.07309. **[3] [B] [search-snippet]** `[in base]` A weighted linear summation of embedded pressure
  readings predicts both bending posture and payload mass. **Bearing:** pose-from-pressure is not the hard
  part; fatigue-state-from-pressure is. Sets the baseline the project's framing must acknowledge.
- **Kushawaha, Pathan, Pagliarani, Cianchetti & Falotico 2025** — "Adaptive Drift Compensation for Soft
  Sensorized Finger Using Continual Learning," arXiv:2503.16540. **[3] [B] [search-snippet]** `[in base]`
  LSTM with memory buffer and regularisation across nine experiments with full setup resets.
  **Bearing:** the closest prior art to the recalibration question, but it compensates *sensor* drift on one
  specimen rather than *actuator fatigue* state across specimens. That distinction is the project's
  contribution and should be stated explicitly rather than left implicit.
- **Shen, Miyazaki & Kawashima 2025** — "Control Pneumatic Soft Bending Actuator with Online Learning
  Pneumatic Physical Reservoir Computing," *IEEE RoboSoft 2025*. arXiv:2503.15819. **[2] [B] [search-snippet]**
  `[in base]` Zero-shot online learning reducing bending-control RMSE by over 37 % on average versus a linear
  model. **Bearing:** the online-learning alternative to discrete recalibration. A reviewer will ask why
  intermittent recalibration is preferable to continuous adaptation, and this is the paper they will cite.

## (d) Health monitoring and fault detection

- **Deshpande, Cheng & Hester 2026** — "Real-time Puncture Detection and Recovery for Pneumatic Soft
  Actuators," arXiv:2609.08804. **[3] [B] [search-snippet]** Detects punctures in a multi-chamber bending
  actuator from a single six-axis inertial measurement unit, identifying which chamber is punctured;
  autoencoder plus fully connected networks reach **96.85 % accuracy**.
  **Bearing:** the strongest 2026 soft-actuator fault detection, but it detects a *discrete* fault from an
  IMU, not a *continuous* fatigue state from pressure. It does not pre-empt the project's claim.
- **Duan, Lv, Wang, Li, Yi, He & Lv 2025** — "Diagnosing Faults of Pneumatic Soft Actuators Based on
  Multimodal Spatiotemporal Features and Ensemble Learning," *Machines* 13(8):749. DOI 10.3390/machines13080749.
  **[3] [B] [search-snippet]** Sliding-window Kalman filtering and ensemble trees over multi-source signals;
  fault modes are root-bonding leakage and rupture-induced leakage.
  **Bearing:** confirms the realistic fault taxonomy is leak-and-rupture, both discrete and late. The project
  must argue why a *gradual* indicator adds value over detecting the leak that ends the actuator's life.
- **Avtges, Ketchum, Young, Kim, Truby & Murphey 2026** — "Damage Adaptation in Seconds for Architected
  Materials," arXiv:2606.17394. **[2] [B] [search-snippet]** Proprioceptive recovery from cuts, burns and
  actuator repairs in under one minute on a six-degree-of-freedom soft wrist, without simulation.
  **Bearing:** the recalibration-cost baseline. If adaptation costs under a minute, the project's
  calibration-event budget of two events versus five needs a cost model that survives the comparison.
- **Kashef Tabrizian, Terryn & Vanderborght 2025** — "Toward Autonomous Self-Healing in Soft Robotics,"
  *Advanced Intelligent Systems*. DOI 10.1002/aisy.202400790. **[1] [D] [search-snippet]** Classifies
  self-healing damage detection as conductive, capacitive, optical or pneumatic. **Bearing:** places
  pneumatic damage detection in a recognised taxonomy.

## (e) Hysteresis and pressure–volume as a condition indicator

Lee et al. 2025 and de la Morena et al. 2025 are covered above.

- **Hu, Jin, Chu & Yi 2026** — "Transfer Learning-Based Piezoelectric Actuators Feedforward Control with
  GRU-CNN," *Applied Sciences* 16(3):1305. DOI 10.3390/app16031305. **[2] [B] [search-snippet]** A
  hysteresis-compensating model trained on one piezoelectric actuator and transferred to a **cross-batch**
  unit and a **cross-type** unit, with explicit analysis of how target data volume and source–target
  similarity affect the transfer strategy.
  **Bearing:** not a soft actuator, but the only located paper that separates *cross-batch* (nominally
  identical) from *cross-type* transfer of a hysteresis model. That is precisely the experimental design the
  project needs, and the framing is worth adopting while noting the domain gap.

---

## What empirical evidence is still missing

- **Nobody tracks pressure–volume loop features over a full fatigue life on multiple specimens.** The closest
  is Bui et al. (n = 10), which tracks tip-trajectory hysteresis and stops before failure. The only located
  P–V-over-cycling measurement is in a patent, before-and-after only.
  *Needed:* P–V loops at ten or more points across life on eight or more specimens cycled to failure.
- **Inter-unit lifetime scatter is measured at n = 3 to 5, and the two estimates disagree by more than 4×**
  (3.9 %, 6.1 %, 17.5 %). No study fits a life distribution to soft-actuator cycles-to-failure.
  *Needed:* fifteen or more nominally identical specimens from one batch and one fabricator, cycled to
  failure, with a fitted distribution. At n = 3–5 one cannot distinguish 4 % from 18 %.
- **No dataset separates break-in from fatigue.** Two studies converge on a ~160-cycle log-saturating
  transient in kinematic output; nobody has shown whether the P–V indicator is confounded by it.
  *Needed:* quasi-static P–V probes at cycles 0, 10, 50, 160, 500, then decade-spaced to failure.
- **Cross-actuator non-transfer is demonstrated only across deliberately different designs.** Lee et al.
  reject model equality at p < 10⁻⁷, but across a 4× range of chamber diameter. The project's claim concerns
  nominally identical units. *Needed:* the Chow-test design of Lee et al. applied within a single batch.
- **No published pressure-only fatigue-state estimate exists to benchmark against.** Every located
  2024–2026 soft-robot health method detects discrete faults at or after end of life. The project is not
  scooped, but it has no comparator, so a reviewer will ask for a physical proof of concept rather than
  accept a simulation-only result.
