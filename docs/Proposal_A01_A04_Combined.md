# Research Proposal

## P-V Hysteresis as a Fatigue Leading Indicator and Its Coupling to Pressure-Only Proprioception in Shared-Manifold Soft Grippers

**Author:** [Name] · NYU Tandon, Dept. of Mechanical & Aerospace Engineering
**Target venue:** IEEE Robotics and Automation Letters (RA-L) — primary; *Soft Robotics* — alternate
**Est. effort:** one semester (≈15 weeks), solo · **Hardware:** ≈ $320
**Companion docs:** `Draft1_A01_A04_Combined.pdf` (Draft 1, not committed to the repository), [`A01_A04_Literature_Review.md`](A01_A04_Literature_Review.md)

---

## 1. Problem and motivation

Soft pneumatic grippers face two monitoring problems in deployment: **(i) fatigue** — silicone actuators fail by cyclic fatigue, and current practice detects failure only *after* rupture; and **(ii) proprioception** — recovering gripper pose without added sensors, using the pressure signals already in the control loop. Both are studied in isolation. This project argues that in the most practical multi-finger topology — chambers sharing a pneumatic manifold to cut valve count — the two problems are **physically coupled** through inter-chamber pressure cross-talk, and that a single pressure stream can monitor both.

## 2. Research questions and hypotheses

- **RQ1 (leading indicator).** Can cycle-resolved features of the in-loop pressure–volume (P-V) hysteresis loop predict fatigue failure onset with *positive lead time*, after reversible Mullins softening is separated out?
- **RQ2 (cross-talk).** By how much does shared-manifold inter-chamber cross-talk degrade pressure-only pose/contact reconstruction, and can an explicit coupling model recover it?
- **RQ3 (coupling — the spine).** Does fatigue-induced change in chamber compliance shift the cross-talk coupling, so that the same P-V feature that signals fatigue also predicts proprioception degradation — making joint monitoring from one pressure stream worthwhile?

**Central hypothesis (falsifiable, mechanistic):** As an actuator fatigues, its chamber compliance *C* rises; on a shared manifold, the inter-chamber pressure-redistribution gain is a monotone function of *C*; therefore the measured cross-talk coupling coefficients will drift **monotonically with the same P-V loop-shape feature (loop area / compliance slope) that signals fatigue**, with correlation *r* detectable before proprioception RMSE exceeds a task threshold.

## 3. Novelty positioning (honest, post-literature-sweep)

A 6-cluster literature sweep (45 verified papers, see companion review) sharpened the claims. **What already exists, and must be cited as the boundary:**

- P-V hysteresis is *already* used as a **before/after** fatigue diagnostic (Mosadegh et al. 2014, >10⁶ cycles; Libby et al. 2023 shows the loop shifts with fatigue). → **We do NOT claim first use of P-V for fatigue.**
- Pressure-only multi-chamber proprioception exists (L. Wang 2020, 2023; J. Wang 2025; Joshi & Paik 2023; Zou et al. 2024) — but assumes *independent / clean* per-chamber supply.
- Hysteresis-loop-area-as-damage-proxy has strong cross-domain precedent (metals: Haghshenas et al. 2021; flight control: Guo et al. 2021; SHM/AE: Galanopoulos et al. 2023; early-warning theory: Scheffer et al. 2009). → This *supports* the leading-indicator framing rather than undermining it.

**What survives as contribution (to our knowledge — absence in a thorough search, not proof of absence):**

1. The first **operational, cycle-resolved P-V loop-shape *leading indicator*** with a fitted degradation model and quantified positive lead time, explicitly separating irreversible fatigue drift from reversible Mullins recovery — distinct from before/after diagnostics and cycles-to-failure benchmarking.
2. The first characterization of **shared-manifold inter-chamber cross-talk as a degradation mechanism for pressure-only proprioception** (nearest prior art: Lindenroth et al. 2021, which senses on coupled parallel chambers but never frames cross-talk as a sensing confound).
3. The **coupling** itself — fatigue → compliance → cross-talk drift → corrupted proprioception — and a **fatigue-triggered recalibration policy** (contrast: Kushawaha 2025 adapts *always*; Sugiyama 2025 masks anomalous sensors). No verified paper assembles this chain.

## 4. The coupling mechanism, prediction, and fallback (de-risks the whole paper)

The draft asserted the coupling in §6; this proposal makes it a **predicted, falsifiable mechanism stated up front**:

> fatigue ↑ → chamber compliance *C* ↑ → manifold pressure-redistribution gain *G(C)* ↑ → cross-talk matrix coefficients drift → pressure-only pose estimate (calibrated on fresh actuators) degrades.

> **Gate 0 update (2026-06-19, PASS — see [`Gate0_Coupling_Simulation.md`](Gate0_Coupling_Simulation.md)).**
> A lumped-RC simulation now confirms this mechanism *in software, before any hardware*:
> inter-chamber cross-talk rises monotonically with chamber compliance in 100 % of 400
> randomized parameter sets. Critically, the coupling is **dynamic** — the steady-state
> (DC) cross-talk gain is compliance-independent, so the fatigue signal lives in the
> pressure *transients* and is observable only near the actuation band (~1–5 Hz). This
> sharpens the prediction: the cross-talk drift is visible to history-dependent (ARX/ESN)
> correctors and invisible to a static ridge map — making the §5.3 corrector comparison a
> *mechanistically predicted* result, not just an empirical sweep.

- **Confirming result:** cross-talk coefficients track the P-V compliance feature with *r* ≥ 0.5 (*p* < 0.05) over early-to-mid fatigue; a P-V-triggered recalibration restores pose RMSE toward the fresh baseline. → Full coupled paper.
- **Negative result (still publishable):** if the cross-talk corrector re-estimates online faster than fatigue drifts, the coupling is *benign*. That is itself a useful finding and the paper still delivers (1) the leading-indicator study and (2) the first shared-manifold cross-talk characterization for pressure-only sensing.

Either way there is a result floor — the reason this is the right primary bet.

## 5. Methodology

### 5.1 Hardware
- **Gripper:** three-chamber Dragon Skin 20A silicone gripper, chambers on a **shared brass manifold**, one solenoid valve per chamber, regulated supply. PneuNet-class geometry (Mosadegh 2014).
- **Sensing:** one Honeywell HSC pressure sensor (±0.5% FS) tee-fitted per chamber; volume estimated from regulated flow (or a pressure-oscillation observer, Joshi & Paik 2023). 100 Hz via Teensy 4.1.
- **Ground truth (fixed from draft):** **fingertip SE(3) via a small rigid marker cluster on the least-deforming distal boss**, OptiTrack/Vicon at 120 Hz, hardware-synced to <1 ms. Curvature/PCC (Webster & Jones 2010) reported only as a *modeled output validated against* the rigid-cluster pose — never as measured truth (avoids marker-shear-on-silicone + curvature-error-accumulation, per Monet 2020, Cell Reports 2024).

### 5.2 Study 1 — P-V fatigue leading indicator (RQ1)
- **N = 10** actuators cycled to failure. **Fix (loading regime):** cycle under **representative grasp loading** (against a compliant contact), not free inflation — or run a free-inflation arm in parallel and *report whether the indicator transfers*. State explicitly which.
- **Mullins control:** establish each actuator's healthy baseline **after** stress-softening stabilizes (~first 5–10 cycles, Lavazza 2023); use **within-actuator baselining** (each actuator is its own control) to suppress casting build-variance, instead of a cross-actuator 2σ threshold.
- **Failure-mode classification:** label each end-of-life as sudden rupture / slow leak / delamination; report which mode P-V predicts. **Risk to name:** if sudden-rupture dominates with no precursor, the leading-indicator value is bounded — report honestly.
- **Features:** loop area (hysteresis energy), peak pressure, pressure@80%-volume slope, inflation/deflation asymmetry, PCA PC1 of loop shape.
- **Model & metric:** fit a logistic/double-logistic degradation model per feature (HI criteria: monotonicity, trendability, prognosability — Lei 2018); report **per-actuator lead-time distribution with CIs** (not a single number; acknowledge N=10 power), and early-warning **AUC**.

### 5.3 Study 2 — Shared-manifold cross-talk characterization & correction (RQ2)
- **Cross-talk measurement (fixed from draft):** measure the 3×3 coupling matrix in the **operating condition** (all valves live, perturb one chamber across pressure levels) — **not** with neighbors sealed (sealed neighbors are isometric and give the wrong coupling). Report the matrix as pressure-dependent.
- **Correctors compared on pose reconstruction (N≈2000 labeled traces):**
  1. **Ridge regression** — uncorrected baseline.
  2. **ARX** — explicitly subtracts the modeled cross-talk component (the *interpretable, scientifically primary* corrector; lumped-RC grounding from Joshi & Paik 2021).
  3. **ESN** (~100 nodes, hyperparameters reported) — black-box dynamic comparator (Youssef 2022). Note: this is a *computational* reservoir, not physical RC.
- **Metrics:** pose RMSE (mm + deg), contact F1, inference latency.

### 5.4 Study 3 — Coupled failure + recalibration (RQ3)
- Track the cross-talk matrix and pose RMSE as actuators age; test the §4 prediction (cross-talk drift vs. P-V feature correlation).
- Evaluate a **P-V-triggered recalibration** policy (recalibrate when the health monitor crosses threshold) vs. fixed calibration and vs. always-on continual learning (Kushawaha 2025 as the baseline-to-beat on efficiency).

## 6. Go/No-Go decision gates — and the fallback

**Gate 0 (simulation, \$0) — DONE, PASS.** Before any hardware, the coupling spine was
pre-tested in a lumped-RC model (`Gate0_Coupling_Simulation.md`): cross-talk is monotone
in compliance across 400 randomized configs, and the coupling is dynamic (probe at
~1–5 Hz). The full gate ladder (0 → 0b failure-mode scout → 1 volume-estimator bench →
2 equipment audit → Week-3 hardware) is in [`Experimental_Protocol.md`](Experimental_Protocol.md).

**Week-3 hardware gate.** Before the full N=10 campaign, run the **cheap coupling check**: on 2–3 actuators, fatigue partially and test whether the cross-talk matrix shifts with the P-V compliance feature.
- **Coupling real (r ≥ 0.5):** commit to the full coupled study.
- **Coupling weak:** pivot freed effort to **G02 (kirigami force-stroke fatigue maps)** — it reuses the *same cycling rig and force/displacement instrumentation*, has a guaranteed result floor, and is a clean parallel mechanics paper. (The combined paper still stands on Studies 1+2 as a reduced contribution.)

## 7. Metrics summary
| Study | Primary metric | Secondary |
|---|---|---|
| 1 Fatigue LI | lead-time (cycles, distribution + CI), AUC | HI monotonicity/trendability, false-alarm rate |
| 2 Cross-talk | pose RMSE (mm/deg), contact F1 | coupling-matrix magnitude, inference latency |
| 3 Coupling | cross-talk-vs-P-V correlation r | recalibration RMSE recovery, triggers vs. continual-learning cost |

## 8. Timeline (15 weeks)
1–2 fabricate gripper + cycling rig + mocap sync · 3 **decision gate** · 4–7 Study 1 fatigue campaign · 6–9 Study 2 cross-talk (overlaps) · 10–12 Study 3 coupling + recalibration · 13–14 analysis + figures · 15 write-up.

## 9. Risks and mitigations
- **Coupling weak →** §6 gate + G02 fallback (already a publishable reduced paper).
- **Sudden-rupture dominates (no precursor) →** report as a scoped negative for those modes; the indicator may only serve gradual-degradation failure modes — state the operating envelope.
- **N=10 underpowered for AUC →** within-actuator baselining + report CIs honestly; frame as a first characterization, not a deployment-grade prognostic.
- **Mullins/recovery masquerades as fatigue →** post-stabilization baseline + rest-recovery control (Liao 2021).
- **Pose ground-truth ambiguity →** rigid-cluster tip SE(3) primary; curvature only as validated model output.
- **Citation pitfalls →** keep pressure-only vs. added-sensor strictly separated (Draft 1 error); US Patent 10,639,801 and Mosadegh et al. 2014 already establish before/after P-V hysteresis fatigue assessment, so claim only cycle-resolved prognostic lead time and fatigue-triggered recalibration.

## 10. Expected contributions
1. An operational, cycle-resolved **P-V loop-shape leading indicator** for soft-actuator fatigue with quantified lead time and Mullins separation.
2. The first **shared-manifold cross-talk characterization** as a pressure-only-proprioception degradation mechanism, with an interpretable ARX corrector.
3. A demonstrated (or refuted) **fatigue↔proprioception coupling** and a **P-V-triggered recalibration** policy — joint health-and-pose monitoring from one pressure stream.

## 11. Why this fits the author
Combines silicone fabrication + pneumatic instrumentation (ME-advantaged), system identification + ML (ridge/ARX/ESN), and a falsifiable systems hypothesis — and the recalibration-trigger idea (RQ3) is the same "stop trusting the model when it goes stale" instinct as the author's prior control-theory work.
