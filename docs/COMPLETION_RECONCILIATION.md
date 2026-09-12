# Completion reconciliation and author return
Prepared 2026-09-11. This is a review handoff, not an author signature or a publication clearance. Task status authority: [SPRINT_TASKS.csv](SPRINT_TASKS.csv), especially PV-08 and PV-COR-01.

## Each recommendation, separately

| Recommendation | What is implemented | What is not completed |
| --- | --- | --- |
| Explain the correction and statistical choice | [Author packet](AUTHOR_REVIEW_DAY3.md), [candidate](preprint_v1_4_candidate.md), [correction notice](corrections/v1.3-methods-2026-09-05.md) | Actual author draft reconciliation and acceptance |
| Verify reported numbers | [Numeric checker](../scripts/check_manuscript_numbers.py) checks historical and candidate text; baseline passed | This does not judge every scientific sentence |
| Make a corrected submission artifact | Corrected Markdown candidate is present | Corrected PDF is absent; historical PDF is not the correction |
| Clear publication | [Readiness checker](../scripts/check_publication_fallback.py) correctly blocks publication | Artifact-bound author approval, corrected-PDF review, deposit decision and identifier |
| Improve the next research study | [Prospective integrity design](specs/v2-integrity-core/design.md) exists | No new v2 experiment or outcome is supplied by this correction |

Calling the packet complete must never be shortened to “PV-08 complete.” The unfilled response below cannot populate the approval fields in [publication-readiness.json](publication-readiness.json).

## Recommended decisions and why

Retain the actuator-cluster interval [0.853, 0.950] for the pooled r=0.885; keep delete-one Fisher-z sensitivity [0.576, 0.973] visible. The [committed result](../data/sim/phaseD/study3_cluster_ci_results.json) has six actuator identities and five life stages per identity, not 30 independent devices. The indicator-invariance diagnostic is a limitation, not evidence of device discrimination.

Preserve historical tau=0.05 and its nonpositive lead; do not replace it with the already-seen tau=0.01 frontier. A new lead-aware selection rule belongs in a prospective training-only study. This preserves the meaning of the existing held-out cohort rather than optimizing a story on inspected results.

Approve the corrected text only after reconciling the author's actual drafts; then render a separately versioned PDF, compare it to the accepted source, and obtain a PDF-bound approval. An approval of text is not an approval of a later file that was never seen.

## Artifact identity for this sitting

Base: `da647ff5af8c2c304a5089b016b8fd7f3a11c570`.

| Artifact | SHA-256 |
| --- | --- |
| docs/preprint_v1_4_candidate.md | d700684b2a08c4b9117a1aa2fbc7a0f0ef7085948e7a3cab971591041da51977 |
| docs/corrections/v1.3-methods-2026-09-05.md | 76e7faadc77b4decff5b3f7becba6412298c2f3ad1f92a291057fef053e91b79 |
| data/sim/phaseD/study3_cluster_ci_results.json | 8f7dfcdc81f42fa4cc449189886bf246cc98f00ba5d3670d9dd8161b2116285b |

If an artifact changes, rebind the review to its new hash; do not reuse an old approval.

## Owner response — not submitted

Use the existing approximately 50-minute review sequence in [AUTHOR_REVIEW_DAY3.md](AUTHOR_REVIEW_DAY3.md). Return these fields in a reply or separate reviewed record:

- Reviewer identity and actual review date: **unfilled**.
- Candidate source hash reviewed: **unfilled**.
- Other author draft paths/commits compared, or explicit confirmation there are none: **unfilled**.
- Text decision: **unfilled** (accept / request changes, with exact changes).
- Statistical wording decision and reasons: **unfilled**.
- Historical threshold wording decision and reasons: **unfilled**.
- Whether to prepare a separately versioned PDF after text acceptance: **unfilled**.
- Posting/deposit decision: **unfilled**; no publication account action is implied.
- Eventual PDF path/hash and approval: **not yet available**.

Smallest unblock action: supply the authoritative draft locations and a candidate-bound text decision. Agent can apply specified changes and prepare the next artifact; only an actual author decision closes author review.

## Verification

From repository root:

```sh
python -m scripts.check_manuscript_numbers
python -m scripts.check_publication_fallback
python -m scripts.check_publication_fallback --for-publication
```

Expected: first two exit 0; publication exits 2 until real approval and artifact requirements are satisfied. [Correction evidence](../evidence/correction-2026-09-11/README.md) records actual outputs. No paper, result, PDF, threshold or approval field was changed here.
