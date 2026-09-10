# PV-D03 — bounded preparation evidence

Date: 2026-09-09. Base (both reviewed PR layers merged): `d8b1e7eaef817394e169e16dabcc97c1efee3e88`.
Branch: `task/day-three-20260909`. Scope: Prepare artifact-bound author review, without author approval.

## Delivered change

Number-checker regression: two intentionally altered candidate values passed the original checker (2 failed tests). After extending the same numeric requirements to the correction candidate, 193 tests and both manuscript numeric checks pass. The corrected text uses the deliberately narrower train-derived budget wording. No manuscript/PDF/result bytes or readiness approval fields changed.

See [plan](../../docs/DAY3_PLAN.md) and [primary deliverable](../../docs/AUTHOR_REVIEW_DAY3.md). Status is maintained only in [SPRINT_TASKS.csv](../../docs/SPRINT_TASKS.csv); original research/CAD gates remain unchanged. Delivery is a new PR, not an automatic merge or scientific release.

## Verification and reproducibility

Tool `wall_time_seconds` fields describe individual output/poll waits, not total command runtime; use the test runner's printed duration where available. All new/modified Markdown local links and the 13-column task ledger were checked successfully before commit. No separate independent reviewer participated in this task.

[checks.json](checks.json) records commands, observed exit statuses and selected outputs. Baseline source identity, command and outputs are in [baseline.json](baseline.json). Local Python is 3.11.8; CAD tests use the registered isolated Python 3.11.16/CadQuery toolchain. On another machine use the repository's existing workflow/dependency setup, not this machine's absolute interpreter path. The local pytest readline stub is recorded explicitly.

The listed relevant local checks completed. The P-V publication-mode exit 2, where present, is the expected blocked state, not a test failure.

No separate type/lint task was added: existing configured compile/tests and source-specific checks were used. Tests use synthetic developer cases; they are not independent human review, experimental results, adoption or held-out research evaluation. Source checks distinguish read sections from whole-paper review. Initial missing-module test failures for new tooling reflect tests written before implementation, not a defect in the old product. Prior scientific artifacts were not regenerated as new evidence.

## Remaining project work

PV-08 remains blocked on actual draft reconciliation, reviewed PDF and author posting decision.

The only research findings here come from identified external sources; no downloaded third-party full text or sensitive raw data is committed. AI review and declared metadata do not substitute for authorship, permission, calibrated measurement or independent assessment.
