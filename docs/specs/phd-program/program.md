# PhD-scope research program — pressure-only observability of soft-actuator fatigue state

Proposed 2026-09-16. Status: **preregistered plan; Studies A and B executed on the same branch after this
file was committed (the evidence records the commit).** Task status lives only in
[SPRINT_TASKS.csv](../../SPRINT_TASKS.csv) (rows PV-PHD-*). This program does not modify the frozen v1.3
release, the v1.4 candidate, PV-08, or the [RoboSoft v2 claim spine](../robosoft-v2/claim-spine.md).

## Audited state, verified against the tree on 2026-09-16

| Claim in the program brief | Verified? | Evidence |
|---|---|---|
| Studies 1–4 reproduce to floating-point noise | Yes, with a caveat | 50/50 regenerated outputs identical between pre- and post-refactor code ([PV-R04](../../../evidence/ponytail-2026-09-14/README.md)); current-code regeneration still differs from the *committed* artifacts (documented drift, [START_HERE](../../START_HERE.md)). |
| A RoboSoft 2027 manuscript exists, not submitted | Yes | `docs/preprint_v1_4_candidate.md`; [SUBMISSION.md](../../SUBMISSION.md) decision HOLD; deadline **2026-10-15** per [v2 scope](../robosoft-v2/scope.md). |
| Submission task PV-11 is open | **No such row** | The ledger has no PV-11; submission is gated by PV-08 (author review) and the v2 must-haves. This program adds no submission row; it is the owner's decision. |
| Normalised health indicator is invariant to every actuator parameter | Yes, exactly | `indicator_invariance_check` in `study3_cluster_ci_results.json`: max deviation 2.6e-14 across held-out units and 3.5e-13 across a wide (k1, k2, τ, rupture) sweep; per-actuator r 0.9570–0.9574. Mechanism: `degraded_sls` scales k2 by `loss_multiplier(u)`, which depends only on the canonical `FatigueParams` shared by every unit; normalising by the young value cancels k2. |

## Question

Is the fatigue state of a soft pneumatic actuator observable from pressure–volume dynamics alone under
realistic between-unit dispersion, and does a pressure-only estimator transfer to unseen units?

## Known vs open

[Novelty check 2026-09-16](../../reviews/novelty-check-2026-09-16.md): P-V hysteresis tracking fatigue and
pressure-only self-sensing are prior art (grade B). Between-unit dispersion is real at n = 10 (Frontiers
2023). Open in the retrieved literature: identifiability of a *latent* fatigue state from pressure-only
features under unit dispersion, and unseen-unit transfer of such an estimator. Distinctiveness within
retrieved evidence, not proven global novelty; a Scopus/IEEE Xplore pass is required before submission.

## Studies

| Study | Type | Gate it answers | Kill criterion | Spec |
|---|---|---|---|---|
| A — break the invariance | simulation, now | Can the cohort pose the cross-unit question at all? | between-unit spread of the normalised indicator not above within-unit noise, or trigger lives not distinct → cohort degenerate; **nothing downstream is meaningful** | [studyA-preregistration.md](studyA-preregistration.md) |
| B — identifiability | theory + simulation, now | Where in the operating envelope is the latent state identifiable from pressure-only features; which mechanisms alias? | latent state unidentifiable from pressure across most of the envelope even with a per-unit young baseline → pressure-only thesis dead; report | [studyB-identifiability.md](studyB-identifiability.md) |
| C — unseen-unit transfer | simulation, after A passes | Does one estimator trained on some units predict others, against fixed-schedule, per-unit-calibration and full-state-oracle baselines; what is the adversarial worst unit? | transfer error not better than the fixed schedule on held-out units → no transfer claim | [studyC-transfer.md](studyC-transfer.md) |
| D — pilot | hardware, owner-gated | Does the preregistered prediction from C hold on one real unit against a competing sensor? | see section D | this file |
| E — decisive | hardware, funded | ≥6 units, two materials/geometries, unseen-unit holdout | see section E | this file |

Order: A → B (B can run on the A cohort regardless of A's verdict, because its map is per unit) → C only
if A passes → D only after C and the CAD/rig entry decisions → E only with funding.

### Study D — pilot (owner-gated, order of cost: hundreds of dollars)

One actuator from an existing released mold or a purchased PneuNet, one pressure sensor, one syringe pump
or regulator with a stroke encoder (volume proxy per [Gate 1](../../Gate1_Volume_Estimation_Literature.md)),
cycled to failure; competing sensor: a camera on a printed target or a strain gauge. Before the run, the
Study C estimator's prediction of the unit's state trajectory is committed with its hash. Entry decision and
fixtures: [CAD_PLAN.md](../../CAD_PLAN.md) PV-CAD-02. Costs are assumed order-of-magnitude, not quoted.
Pass: the predicted-vs-measured state trajectory error lies inside the Study C held-out interval. Fail: report.

### Study E — decisive (funded)

≥6 actuators across two materials or geometries, fatigue-to-failure, unseen-unit holdout, competitor sensor.
Funding buys actuators, the cycling rig and the reference sensing. Claim language follows the
[claim-language gates](../robosoft-v2/claim-spine.md#claim-language-gates): "experimentally supported"
only here, with uncertainty and device-level replication.

## Do not

- Grow the synthetic cohort of Studies 1–4 or reuse it for any cross-unit claim.
- Add estimator variants; Study C uses one estimator and named baselines.
- Claim transfer, prognosis or a physical health diagnostic from the current invariant simulation.
- Touch `docs/preprint_v1.pdf`, the readiness record, or PV-08.

RoboSoft: the v1.4 candidate is submitted, if the owner decides so after PV-08, **scoped to simulation with
the invariance stated as a caveat**. Studies A–C are not RoboSoft content unless they are complete,
reviewed and fit the six-page core before 2026-10-15.

## Ledger mapping

| Row | Study | Owner | Status rule |
|---|---|---|---|
| PV-PHD-00 | novelty check | Agent | done when the claim ledger exists |
| PV-PHD-A | Study A | Agent | done when the preregistered verdict (PASS/FAIL/DEGENERATE) is recorded with evidence |
| PV-PHD-B | Study B | Agent | done when the identifiability map and kill-criterion verdict are recorded |
| PV-PHD-C | Study C | Agent | blocked until PV-PHD-A = PASS |
| PV-PHD-D | Study D | Owner | blocked on PV-PHD-C and the CAD/rig entry decision |
| PV-PHD-E | Study E | Owner | blocked on funding and PV-PHD-D |
