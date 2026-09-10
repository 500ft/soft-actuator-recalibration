# Author review packet — 2026-09-09

Status: prepared, not author-approved. Review [v1.4 correction candidate](preprint_v1_4_candidate.md), not the historical PDF. The [readiness record](publication-readiness.json) remains blocked. No new experiment, v2 result, PDF or DOI has been produced.

## Recommended decisions, with reasons

1. **Keep actuator-cluster uncertainty in the abstract.** The candidate already reports r=0.885, cluster interval [0.853, 0.950] and delete-one sensitivity [0.576, 0.973]. [Committed cluster results](../data/sim/phaseD/study3_cluster_ci_results.json) contain six identities, not 30 independent devices. The wider leave-one sensitivity makes the small cohort visible; substituting the old point-bootstrap interval would ignore shared actuator identity.
2. **Do not change the deployed threshold retrospectively.** Keep τ=0.05 and its negative lead as the historical result. The τ=0.01 frontier was already inspected and is descriptive, not a newly held-out discovery. A lead-aware rule belongs in a prospectively frozen v2 design with training-only selection and new evaluation material. This prevents choosing a rule because it happens to look better on the six known test identities.
3. **Approve correction text before creating a deposit.** Preserve v1.3 bytes and prepare a separately versioned correction after reconciling the author's working drafts. Publication is not authorized by a green integrity check. Do not create a duplicate Zenodo record or assume an account action occurred.

## What changed from the archived interpretation

| Previous interpretation | Corrected scope and evidence |
| --- | --- |
| Noisy acquired P-V probe supports Study 3 | `health_trajectory` in [coupling.py](../pipeline/coupling.py) supplies an idealized analytic probe; noisy pose channels do not make the policy input noisy. |
| Rest/recovery robustness tested | Study 3 fixes rest input to zero; variable rest is a future intervention. |
| Meets accuracy throughout life | [run_study3.py](../scripts/run_study3.py) averages stage RMSE; the 0.159 mm budget is a train-derived macro-average, not an all-time safety bound. |
| 60% less operational cost | Counts are two versus five calibration events including initialization; downtime and total cost were not measured. |
| Transfers across physical actuators | All identities share one synthetic generator. New degradation families are proposed, not evaluated. |

The current script contains `tau_selection_alternatives`, but the committed Study 3 JSON does **not** contain that key. Do not present this code path as a committed comparison result or rerun the historical generator to silently fill it. The [prospective integrity core](specs/v2-integrity-core/design.md) remains a development design pending draft reconciliation.

## Bounded review sitting

- First 15 minutes: compare the candidate's abstract and methods with the [correction notice](corrections/v1.3-methods-2026-09-05.md). Record any retained claims that conflict with the code path above.
- Next 20 minutes: reconcile separate local author drafts. Record which exact files/commits supply accepted edits; no draft was silently adopted by this PR.
- Last 15 minutes: record approve-text / request-changes, reviewer identity and date, and requested separately versioned PDF route. Approval must bind the eventual corrected PDF and source hashes; this blank checklist is not approval.

## Reproduce before signing

Run `python -m scripts.check_manuscript_numbers` (now checks both historical and candidate Markdown), `python -m scripts.check_publication_fallback`, and `python -m scripts.check_publication_fallback --for-publication`. Expected: numeric check passes, archive integrity passes, publication remains BLOCKED and the publication-mode command exits 2. `python -m scripts.check_pdf_arxiv` inspects the historical PDF only, not a nonexistent corrected PDF.

The number checker validates required reported snippets, not every sentence or semantic claim. New regression tests prove that replacing the candidate's cluster interval or calibration saving is detected. Author review remains necessary.
