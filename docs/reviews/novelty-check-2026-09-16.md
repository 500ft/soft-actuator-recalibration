# Novelty check — pressure-only observability of a latent fatigue state under unit dispersion

Date: 2026-09-16. Scope: the question in [the program](../specs/observability-program/program.md). This check
runs *before* any new study, as the program requires. It complements, and does not replace, the
[annotated literature base](../A01_A04_Literature_Review.md) and the [2026-08-03 novelty audit](novelty-evidence-audit-2026-08-03.md).

## Question (one sentence)

Is the latent fatigue state of a soft pneumatic actuator identifiable from pressure-only P-V features
under realistic between-unit dispersion, and does a pressure-only state estimator transfer to units it
was not trained on?

## Method and gating

Retrieval: six web searches (2026-09-16) with synonym variants (identifiability/observability, hysteresis
loop area/fatigue, self-sensing/proprioception, transfer/unseen actuator, Fisher information/prognostics,
fatigue variability/Mullins) plus the repository's existing 60-entry literature base. Eligibility was graded
on aboutness only (0 off-topic, 1 tangential, 2 relevant, 3 core); citation counts and venue were not used
for eligibility. Evidence grade: A replicated/validated, B single controlled experiment or validated
simulation, C simulation or small-n, D position/preprint claim. Full-text access was possible for two
sources; the rest were graded from abstracts and the repository's earlier annotations, and are marked
"abstract only".

Survivorship caveat: web search ranks by its own relevance; two paywalled full texts (Torzini 2024,
Libby 2023) could not be fetched here, so their sample sizes are taken from the repository's earlier
reading, not re-verified today.

## Evidence table

| Source | Year | About. | Evid. | Key finding for this question |
|---|---|---|---|---|
| Mosadegh et al., *Adv. Funct. Mater.* (lit base §1) | 2014 | 2 | B | P-V hysteresis measured before/after >10⁶ cycles as a fatigue assessment; establishes P-V-tracks-fatigue as prior art. Not cross-unit, not identifiability. |
| Libby et al., ISMR / arXiv:2212.03420 | 2023 | 2 | B (abstract only) | FEM agreement drops from ~96 % to 80 % after repetitive high-angle bending; P-V hysteresis shifts with fatigue. Cross-actuator variability not reported in the abstract. |
| Endurance tests of a fabric-reinforced actuator, *Front. Mater.* 10.3389/fmats.2023.1112540 (full text) | 2023 | 2 | B | Ten Dragon Skin 30 actuators; burst pressure 37.1–41.15 kPa (<10 % spread); trajectory path-length variability mean 16.94 mm, SD 5.33 mm (~31 % CV); one of ten failed prematurely by leakage after "a few hundred cycles"; stress-softening shift over cycles. **Direct evidence that between-unit dispersion and a leak failure mode are real at n = 10.** |
| Torzini et al., *IJAMT* 134:2725 (lit base §1) | 2024 | 2 | B (not re-fetched) | Inflate/deflate-to-failure; micro-tears 0.2–0.4 mm precede rupture (~3439 cycles at 1 bar). Gradual-degradation regime. |
| Wong, Luo, Scharff, *Adv. Robot. Res.* (lit base §1) | 2026 | 1 | D | Durability benchmark protocol; cycles-to-failure as the lagging metric. |
| Lavazza et al., *Mech. Mater.* (lit base §1) | 2023 | 2 | B | Ecoflex 00-50: strain-rate and temperature dependence; Mullins stabilises after ~5 cycles. Grounds the temperature and rate axes of the dispersion model. |
| Liao et al., *IJMS* (lit base §1) | 2021 | 2 | B | Partly recoverable stress softening at rest: reversible vs irreversible must be separated in any state signal. |
| Kushawaha et al., arXiv:2503.16540 (lit base §5) | 2025 | 2 | C | Continual-learning drift compensation for a soft sensorised finger: always-on adaptation, per unit. No unseen-unit transfer, no latent-state identifiability. |
| Sugiyama et al., *Front. Robot. AI* (lit base §2) | 2025 | 2 | C | Non-unique mapping problem (a degraded reading mimics a different healthy state) handled with stochastic-LSTM fault detection. Closest analogue to the aliasing question; redundant added sensors, not pressure-only. |
| Passive/active acoustic sensing for SPAs, arXiv:2208.10299 (abstract/summary only) | 2022 | 2 | C | Models trained on one actuator transfer poorly to others; multi-actuator training helps slightly. Evidence that cross-unit transfer is a real failure mode for learned proprioception (acoustic, not pressure). |
| Han et al., *Adv. Intell. Syst.* 10.1002/aisy.202500444 (abstract only) | 2025 | 1 | C | Anchored morphological representations for latent proprioception across structures (vision-based). Transfer framing, different modality. |
| Boyacıoğlu & van Breugel, arXiv:2410.19975 | 2024 | 2 | B (theory) | Stochastic observability/constructability Gramians equal Fisher information matrices and bound estimator error via Cramér–Rao. Methodological anchor for Study B. |
| Fisher identifiability analysis of longitudinal vehicle dynamics, ASME *Letters Dyn. Sys. Control* (abstract only) | — | 1 | C | FIM-based practical identifiability of a dynamic model's parameters. Method precedent, other domain. |
| "On the observability of pressure in a pneumatic servo actuator" (ResearchGate, abstract only) | — | 1 | C | Pressure not locally observable from output motion in regions of state space. Opposite direction (pressure from motion), rigid pneumatics. |
| Joshi & Paik, *Soft Matter* (lit base §3) | 2023 | 2 | B | Bijective pressure–volume–force–displacement mapping with a pressure-oscillation trick to recover volume. Pressure-only sensing is established; fatigue state is not addressed. |
| L. Wang & Z. Wang, *Soft Robotics* (lit base §3) | 2020 | 2 | B | Canonical pressure-only mechanoreception. No degradation state. |
| Lindenroth et al., *IEEE/ASME TMECH* (lit base §4) | 2023 | 1 | B | Pressure+volume force sensing on coupled chambers; no fatigue, no identifiability. |
| Patent US 9,907,898 "monitoring the leak tightness of a plurality of pneumatically actuated actuators" | — | 1 | D | Pressure drop per unit time as a leak measure. Leak and stiffness are diagnosed by different observables in practice (decay vs pressure–flow), consistent with the aliasing hypothesis in Study B. |

Unverified: a search summary reported "failure at 531, 409 and 383 cycles across three samples" for a silicone
actuator; no fetched source contained those numbers, so they are not used.

## Claim ledger

```
Claim 1: P-V hysteresis (loop area, slope) changes with fatigue and has been used to assess it.
Support: Mosadegh 2014 (B), Libby 2023 (B, abstract), Frontiers 2023 (B)
Counter-evidence or gaps: none needed; this is prior art the program does not claim.
Confidence: high.

Claim 2: Pressure-only proprioception / self-sensing is established.
Support: Wang & Wang 2020 (B), Joshi & Paik 2023 (B), Zou 2024 and others in the lit base (B)
Gaps: all assume a healthy, per-unit-calibrated actuator.
Confidence: high.

Claim 3: Between-unit dispersion of nominally identical soft actuators is large enough to matter
(≈30 % CV in a kinematic path-length metric; <10 % in burst pressure; 1/10 early leak failure).
Support: Frontiers 2023 (B, n = 10). Torzini 2024 (B) for scatter in cycles-to-failure (not re-verified).
Gaps: no source reports dispersion of the P-V loop features themselves over life across units.
Confidence: moderate.

Claim 4: Learned proprioception models transfer poorly to units they were not trained on.
Support: acoustic-sensing arXiv:2208.10299 (C, abstract); Kushawaha 2025 (C) implicitly, by needing
per-unit continual adaptation.
Gaps: no pressure-only, fatigue-aware transfer study found.
Confidence: moderate (thin, two sources, different modalities).

Claim 5 (the open question): No retrieved work computes the identifiability (Fisher information /
Cramér–Rao) of a latent fatigue state from pressure-only P-V features under unit dispersion, nor
reports unseen-unit transfer of a pressure-only fatigue-state estimator.
Support: absence across 6 searches + the 60-entry lit base; nearest neighbours are Sugiyama 2025
(aliasing, added sensors) and Boyacıoğlu & van Breugel 2024 (method, no application).
Gaps: absence in one search engine is distinctiveness within retrieved evidence, not proof of
global novelty. A Scopus/IEEE Xplore pass with the same terms is the next check before submission.
Confidence: moderate.
```

## Verdict for the program

The open question stands as stated in the program: **identifiability of a latent state from pressure-only
features under dispersion, and unseen-unit transfer**, are not answered in the retrieved literature.
The foundations that the question rests on are grade B (single experiments), and the dispersion evidence is
one n = 10 study plus one fatigue-scatter study, so the dispersion model in Study A must carry its
magnitudes as *assumed with a cited order of magnitude*, not as measured for this actuator class.

Sources fetched in full today: [Frontiers 2023](https://www.frontiersin.org/journals/materials/articles/10.3389/fmats.2023.1112540/full),
[arXiv:2410.19975](https://arxiv.org/abs/2410.19975). Abstract-level: [arXiv:2212.03420](https://arxiv.org/abs/2212.03420),
[arXiv:2208.10299](https://arxiv.org/pdf/2208.10299), [Han 2025](https://advanced.onlinelibrary.wiley.com/doi/full/10.1002/aisy.202500444),
[ASME Letters](https://asmedigitalcollection.asme.org/lettersdynsys/article/2/2/021009/1127945/Fisher-Identifiability-Analysis-of-Longitudinal),
[US 9,907,898](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9907898), [Springer 10.1007/s00170-024-14216-0](https://link.springer.com/article/10.1007/s00170-024-14216-0) (paywalled).
