# P-V-Fatigue-Manifold-Proprioception — partial handoff, local software ready for review

## Day-3 preparation — 2026-09-09

Number-checker regression: two intentionally altered candidate values passed the original checker (2 failed tests). After extending the same numeric requirements to the correction candidate, 193 tests and both manuscript numeric checks pass. The corrected text uses the deliberately narrower train-derived budget wording. No manuscript/PDF/result bytes or readiness approval fields changed.

Review [DAY3_PLAN.md](DAY3_PLAN.md), [deliverable](AUTHOR_REVIEW_DAY3.md), and [commands/evidence](../evidence/task-day3-2026-09-09/README.md). Base: `d8b1e7eaef817394e169e16dabcc97c1efee3e88`; new PR branch: `task/day-three-20260909`. No original Owner/External gate is closed. Final source identity is the PR head, reported in its delivery record rather than embedded circularly here.

PV-08 remains blocked on actual draft reconciliation, reviewed PDF and author posting decision.

## Review amendment — 2026-09-09

Read [the reproduced findings, corrections and current checks](../evidence/review-2026-09-09/README.md)
before the historical day-2 counts below. Review branch `review/day-two-20260909`;
amendment targets the existing day-2 PR, not main. No owner/measurement gate closes.


Prepared 2026-09-05; resumed and checked 2026-09-06. Budget: six workload days,
30 focused hours per repository; estimates are not recorded time spent.

Canonical checkout: `/Users/redhose/Developer/research-sprints/2026-09-05/P-V-Fatigue-Manifold-Proprioception`.
Remote: https://github.com/500ft/P-V-Fatigue-Manifold-Proprioception.
Branch: `sprint/evidence-integrity-20260905`.
Base commit: `88d24358bc385dc66c2c0a9ab3c295b059d13427`.
Final commit: this review packet's containing commit; its SHA is reported in the PR
because a commit cannot embed its own identity. No deployment, publication,
outreach or spending occurred. Original checkout/user changes were preserved.

[Roadmap](SPRINT_ROADMAP.md) · [Authoritative ledger](SPRINT_TASKS.csv) ·
[Progress](SPRINT_PROGRESS.md) · [Selected candidate hashes](../evidence/sprint-2026-09-05/candidate.json).

## Latest follow-up — 2026-09-09

[PV-D02](../evidence/task-2026-09-09/README.md): the figure manifest is now tested against the tree in both directions (184 tests pass). Hygiene only; the author-review gate PV-08 is unchanged.

## Completed deliverables and evidence

Archived PDF remains unchanged. Active text now identifies the analytic, zero-rest health probe and macro-averaged stage RMSE. The new readiness gate cannot clear archived v1.3 through a metadata flag.

Implementation: [publication checker](../scripts/check_publication_fallback.py), [tests](../tests/test_publication_readiness.py), [correction](corrections/v1.3-methods-2026-09-05.md), [candidate manuscript](preprint_v1_4_candidate.md), [bounded future design](specs/v2-integrity-core/design.md).

- [Baseline identity, commands and outputs](../evidence/sprint-2026-09-05/baseline.json).
- [Original failing evidence](../evidence/sprint-2026-09-05/publication-red.json).
- [Implementation checks](../evidence/sprint-2026-09-05/implementation-green.json).
- [Final verification](../evidence/sprint-2026-09-05/final-checks.json).
- [Predeclared evaluation procedure](../evidence/sprint-2026-09-05/evaluation-plan.md),
  [retained replay](../evidence/sprint-2026-09-05/evaluate_candidate.py),
  [actual outputs](../evidence/sprint-2026-09-05/evaluation.json).


141 tests passed; manuscript-number and historical PDF checks passed; deposit check exits2 intentionally.

Corrected Markdown only; no rendered/reviewed v1.4 PDF, DOI or new research result. The publication checker is intentionally a release-specific hard stop, not a general approval engine.

## Reproduce

Run from the canonical checkout using the recorded Python3.11 environment and
repository dependencies. The local pytest workaround stubs readline before import;
it is not a skipped test or changed product requirement.

```sh
python -c 'import sys, types; sys.modules["readline"] = types.ModuleType("readline"); import pytest; raise SystemExit(pytest.main(["-q"]))'
python -m scripts.check_manuscript_numbers
python -m scripts.check_pdf_arxiv
python -m scripts.check_publication_fallback
python evidence/sprint-2026-09-05/evaluate_candidate.py
git diff --check
```

`python -m scripts.check_publication_fallback --for-publication` must exit2; the default integrity command exits0 while explicitly reporting publication BLOCKED. Historical numerical/PDF checks still address v1.3; they do not approve the correction.



No separate configured lint/typecheck is claimed. Syntax checks are compilation,
not static typing. Saved output truncation, if present, is indicated by the tool
result metadata; no omitted output is called a full log.

## Evaluation meaning and remaining work

Selected implementation/protocol hashes and expectations were saved before the
additional cases ran. Existing tests, reviewed fixtures and reviewer-discovered
bugs are development material. All additional cases were retained. These small
developer-selected checks establish behavior on those inputs, not independent
scientific validation or general accuracy. Another agent is not a human reviewer.
External feedback: pending.

1. Author reconciles separate uncommitted drafts and reviews the correction candidate.
2. Produce a separately versioned, rendered and reviewed PDF with matching metadata before any posting decision.
3. Commit a reconciled prospective v2 specification before new confirmatory results; no backdated preregistration.

Next action: PV-08: author review of docs/preprint_v1_4_candidate.md; no deposit of archived v1.3.

Evidence-supported portfolio bullet: “Corrected simulation evidence lineage and hardened publication checks to separate archived artifact integrity from scientific readiness.”
This concerns engineering quality, not adoption or measured scientific performance.

## Ready-to-send review request

“Review P-V-Fatigue-Manifold-Proprioception against docs/SPRINT_ROADMAP.md. Repository: /Users/redhose/Developer/research-sprints/2026-09-05/P-V-Fatigue-Manifold-Proprioception. Base commit: 88d24358bc385dc66c2c0a9ab3c295b059d13427. Final commit: PR head (see GitHub PR). Review index: docs/REVIEW_READY.md. Incomplete work: Author reconciles separate uncommitted drafts and reviews the correction candidate. Produce a separately versioned, rendered and reviewed PDF with matching metadata before any posting decision. Commit a reconciled prospective v2 specification before new confirmatory results; no backdated preregistration. Reproduce the changed behaviors and counterexamples, rerun appropriate checks, and assess the code and evidence independently. Review first; make further changes only if requested.”
