# Sprint progress — P-V-Fatigue-Manifold-Proprioception

## 2026-09-16 — Observability program preregistered; Studies A and B executed

A cross-unit observability program ([specs/observability-program/program.md](specs/observability-program/program.md)) was preregistered at
`e0543be` after a [novelty check](reviews/novelty-check-2026-09-16.md), then executed on the same branch.
Study A (assumed between-unit dispersion vs the normalised-indicator invariance) records **A-FAIL** under
its own rules: indicator-value spread is 5–17× measurement noise from mid-life (criteria i, ii pass) but the
trigger-life spread at τ = 0.05 is 0.044 life (< 0.10, criterion iii). The one-axis ablation confirms that
only degradation-law dispersion moves the normalised indicator; plant-level dispersion is cancelled by
young-normalisation. Study B (Cramér–Rao identifiability map) verdict and the byte-identity check of the
generator change are in the [evidence](../evidence/observability-2026-09-16/README.md). Study C stays blocked on
A; Studies D/E are owner- and funding-gated. The RoboSoft candidate, PV-08 and the archive are untouched.

## 2026-09-15 — Day-4 executed under the reviewed plan (PR #18); T1 partial

[DAY4_PLAN.md](DAY4_PLAN.md) (PR #18, superseding #17) was executed in order T0 → T2 → T3 → T1.
The render instruction is corrected (PV-D04a), the review index carries an accurately scoped
entry for PR #16 and CONTRIBUTING a simplicity-review step (PV-D04b), and an **unapproved** v1.4
preview was rendered into the ignored `build/day4/`, gated and inspected page by page (PV-D04c,
partial): the renderer drops Markdown `\*` escapes, leaving backslash artifacts in §4.4–4.5, so a
renderer repair precedes any exact-bytes decision. D1 stays unknown; D3 deferred; nothing is
approved and PV-08 is not complete. [Evidence](../evidence/task-2026-09-14/README.md).

Correction: PR #19 was first merged at its pre-rebuild head (the #17-default execution) because a
force-push failed silently; the follow-up PR replaced that evidence, ledger rows and index entry
with the #18 execution. No result, PDF, manifest or approval field was affected either way.

## 2026-09-14 — PV-R04: ponytail audit applied, outputs byte-identical

An over-engineering audit of the Python tree was applied on `audit/ponytail-20260914`: duplicated
study-runner logic, a duplicate steady-state solver, three hand-rolled interpolated crossings, dead
parameter axes and keyword arguments, an orphan report script and boilerplate guards. 492 lines
removed. Every generator was rerun on clones of `main` and of the branch; all 50 regenerated files are
identical (per array for the dataset, PDFs modulo timestamps). No result, figure, threshold, manifest,
PDF or approval field changed; 213 tests and all publication checkers unchanged. The one audit item
that would alter the dataset (unread arrays and the contact loop) is left for the author.
[Evidence](../evidence/ponytail-2026-09-14/README.md). PV-08 remains the gate.

## 2026-09-11 — evidence-gap correction

The [current correction](COMPLETION_RECONCILIATION.md) supersedes any interpretation that earlier preparation closed a physical, approval, or source-review gate. Work is on `fix/evidence-gaps-20260911` from current renamed main; historical entries below retain their original dates and PR snapshots. The original day-3 and presentation PRs are now merged, but this correction is a new reviewable change, not an asserted merge or publication.

Each omitted or incomplete recommendation is accounted for separately in the current correction and existing task ledgers. No owner signature, measurement, PI conversation, imagery judgment, disclosure approval or independent review was fabricated. Exact tests, scope and next inputs are linked from the correction record; actual delivery state is established by its PR.

## Day-3 work — 2026-09-09

Delivery update: the preparation was committed as 500ft and pushed; [day-3 PR](https://github.com/500ft/P-V-Fatigue-Manifold-Proprioception/pull/10) is open against main. Initial implementation source: `3b2bfb52cc4476c7cbb6cbd90aea0c075118d400` (later review/documentation commits are visible in the PR). This supersedes the pre-push stopping state below. Original day-1/day-2 PRs are merged; this new PR is not merged. Resume from the named unresolved project gates in [DAY3_PLAN.md](DAY3_PLAN.md), not from the already completed push step.

Both reviewed PR layers merged into main; new work starts from `d8b1e7eaef817394e169e16dabcc97c1efee3e88` on `task/day-three-20260909`. Number-checker regression: two intentionally altered candidate values passed the original checker (2 failed tests). After extending the same numeric requirements to the correction candidate, 193 tests and both manuscript numeric checks pass. The corrected text uses the deliberately narrower train-derived budget wording. No manuscript/PDF/result bytes or readiness approval fields changed.

The [evidence record](../evidence/task-day3-2026-09-09/README.md) contains checks and limits. Work is locally verified and not yet recorded here as pushed/merged. Current edits belong to this task; original checkouts were preserved. Next: finish verification, commit the bounded change and open the new PR; preserve all stated external gates.

## Review amendment — 2026-09-09

Read [the reproduced findings, corrections and current checks](../evidence/review-2026-09-09/README.md)
before the historical day-2 counts below. Review branch `review/day-two-20260909`;
amendment targets the existing day-2 PR, not main. No owner/measurement gate closes.


## 2026-09-09 — PV-D02 figure manifest becomes a gate

[7 tests](../tests/test_figure_manifest.py) now hold `docs/figure-manifest.json` and the tree to each
other in both directions, declare the results JSON behind each figure, and declare the uncommitted
phase-D dataset as a generated input with the command that produces it. Four negative controls fail as
required; 184 tests pass. No figure or number changes; PV-08 remains the gate.
[Verification](../evidence/task-2026-09-09/README.md). Branch `task/priority-two-20260909`.

## 2026-09-08 — PV-D01: optimization-safe historical integrity gate

Completed one bounded P1 follow-up: the historical publication checker no longer
uses removable `assert` statements. Before correction, 11 independently mutated
payload fields/bytes falsely produced integrity PASS under `python -O`; normal
execution caught them. Explicit runtime checks now reject these inputs in both
modes, and malformed inputs report integrity FAIL with exit 1. This fixes the
archive-integrity verdict, not publication approval.

[Task evidence and reproducible commands](../evidence/task-2026-09-08/README.md)
record the clean base `3dba7aeb664c93bfc6c1a74d7c3462ea1cc96738`, interpreter
selection, original red test results, final 177 passing tests and unchanged PDF
SHA. Manuscript-number, PDF and historical-integrity checks pass. No configured
standalone typecheck/lint/build was omitted or invented. Historical sprint rows
and their 30-hour allocation are unchanged; PV-D01 is a separate 2-hour estimate.

Branch `task/priority-one-20260908`; work prepared for a 500ft-authored commit and
PR. The commit/PR provides final identity; this entry does not assert publication,
push or merge in advance. Owner task PV-08 remains blocked. No v2 research run or
CAD pilot was started. Next check: `python -O -m scripts.check_publication_fallback
--for-publication` (expected exit 2); next project task is author reconciliation
and review of `docs/preprint_v1_4_candidate.md`.

## 2026-09-06 — Main-branch placement authorized

Owner explicitly requested these PRs be merged to their respective main branches. This supersedes earlier placement-blocked/draft-only entries for the current changes. The combined main-targeted PR retains prerequisite integrity work, unchanged task ledgers and all actual hardware/disclosure gates. No CAD or experiment is marked complete. Merge completion and resulting main commit are verified by GitHub rather than asserted in advance here.

## 2026-09-06 — Reviewer-driven CAD amendment

This entry supersedes the earlier CAD allocation and readiness wording. The same CAD PR is now draft, pending the owner planning-ledger placement decision. [Review disposition](CAD_REVIEW_DISPOSITION.md) records that block; [CAD_PLAN.md](CAD_PLAN.md) and [CAD_TASKS.csv](CAD_TASKS.csv) contain revised priorities, separate tooling estimates and explicit parked work. No CAD model or new measurement was produced. Original integrity-sprint tasks/evidence remain unchanged. Next work is limited to active input-register tasks and unresolved owner decisions, not the parked portfolio-wide CAD program.

## 2026-09-06 — CAD task amendment

Added [individual CAD work orders](CAD_PLAN.md) and [CAD_TASKS.csv](CAD_TASKS.csv), separating component modeling, fixtures, inspection and release deliverables. This is planning only: no CAD or physical task is complete. The original sprint ledger and evidence are unchanged. CAD branch: `plan/cad-tasks-20260906`; the PR supplies the committed source identity. Next CAD action: the first input-register task in the CAD ledger; owner-gated successors remain blocked. Verification of this amendment is recorded in [CAD_PLAN_CHECKS.md](CAD_PLAN_CHECKS.md).

## 2026-09-06 — Partial handoff

- Sprint start2026-09-05; canonical checkout `/Users/redhose/Developer/research-sprints/2026-09-05/P-V-Fatigue-Manifold-Proprioception`.
- Branch `sprint/evidence-integrity-20260905`; HEAD/base `88d24358bc385dc66c2c0a9ab3c295b059d13427`.
- Seven Agent tasks done with linked evidence; PV-08 blocked on: Author reconciliation of dirty drafts, final PDF approval and publication account action. Existing local v2 documents are reported uncommitted, not adopted as preregistration.
- 141 tests passed; manuscript-number and historical PDF checks passed; deposit check exits2 intentionally.
- [Final checks](../evidence/sprint-2026-09-05/final-checks.json), [candidate](../evidence/sprint-2026-09-05/candidate.json), [original expectations](../evidence/sprint-2026-09-05/evaluation-plan.md), [outcomes](../evidence/sprint-2026-09-05/evaluation.json).
- These are developer software checks; no physical/new scientific results. Catan's real-data arm, where applicable, stays blocked despite its software fallback evaluation.
- Handoff was prepared before commit; the PR records the final commit and push. Original user changes remain untouched.
- Next verification command: `python evidence/sprint-2026-09-05/evaluate_candidate.py`.
- Exact next task: PV-08: author review of docs/preprint_v1_4_candidate.md; no deposit of archived v1.3.

## Baseline and interrupted execution

Baseline commands, outputs and identity remain in [evidence](../evidence/sprint-2026-09-05/baseline.json). Plans were saved before behavior changes. Runtime-limit pauses were followed by resuming the existing worktree; no baseline or external reply was invented. Original failing cases and corrected behavior are linked in [REVIEW_READY.md](REVIEW_READY.md).
