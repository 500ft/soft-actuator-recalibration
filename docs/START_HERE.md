# Start here: Soft Actuator Recalibration

This is a simulation-methodology repository with an unresolved publication
correction, not a validated fatigue-monitoring device. Choose a reading path
below. The [repository overview](../README.md) gives the short version.

## Recruiter or prospective supervisor: two minutes

1. Read the [Study 3 trade-off and limits](results.md#study-3-recalibration-policy):
   a state-dependent signal can reduce calibration events within the simulator.
2. Inspect the [recalibration plot](../data/sim/phaseD/study3_fig4_recal_tradeoff.png)
   and its [lineage](data-and-figures.md#study-3-recalibration-policy).
3. Read the [author-review decisions](AUTHOR_REVIEW_DAY3.md). Retaining a negative
   lead result and correcting an overstated method are part of the engineering
   work, not completed hardware evidence.

The work demonstrates model construction, actuator-identity evaluation,
policy comparison, and reproducible artifact checks. It does not establish
physical sensor accuracy, early failure warning, or reduced operating cost.

## Reviewer: reproduce the checks

Use the [README setup](../README.md#quick-start), Python 3.11, and the dependency
installation in the [CI workflow](../.github/workflows/ci.yml). The requirements
use lower version bounds, not a complete environment lock; record your installed
versions if investigating numerical differences.

From the repository root:

```bash
git rev-parse HEAD
git status --short
python --version
python -m pip freeze
python -m pytest -q
python -m scripts.check_manuscript_numbers
python -m scripts.check_pdf_arxiv
python -m scripts.check_publication_fallback
```

The [day-3 check record](../evidence/task-day3-2026-09-09/checks.json) records
193 passing tests and the numeric/artifact checks at that source state. Counts
can change; compare the assertions and source revision, not just the total.

| Check | What a pass establishes | What it does not establish |
| --- | --- | --- |
| Tests and figure-manifest checks | Registered developer cases pass; declared computational outputs and lineage remain consistent | Independent validation or physical accuracy |
| Manuscript numbers | Required reported snippets match committed values in both Markdown versions | Every scientific claim is correct |
| PDF preflight | The historical PDF satisfies its checked format constraints | A corrected PDF exists or has been approved |
| Fallback integrity | The archived bytes and metadata remain consistent | Permission to deposit a preprint |

Check the separate publication gate:

```bash
python -m scripts.check_publication_fallback --for-publication
```

Expected while author review is unresolved: publication **BLOCKED**, exit **2**.
Do not weaken that gate to make a release appear ready. The governing files are
[publication-readiness.json](publication-readiness.json), the
[correction](corrections/v1.3-methods-2026-09-05.md), and the
[author packet](AUTHOR_REVIEW_DAY3.md).

### Local pytest startup workaround

The recorded local Python environment can crash when importing `readline` before
pytest starts. The documented workaround is limited to that environment:

```bash
PYTHONPATH=. python -c 'import sys, types; sys.modules["readline"] = types.ModuleType("readline"); import pytest; raise SystemExit(pytest.main(["-q"]))'
```

CI uses normal `python -m pytest`. A startup failure is not a product-test
failure; record the environment and command actually used.

## Reviewer: inspect or regenerate the study

Start with committed [Study 3 results](../data/sim/phaseD/study3_results.json),
[cluster uncertainty](../data/sim/phaseD/study3_cluster_ci_results.json), and
[dataset manifest](../data/sim/phaseD/manifest.json). Trace the policy input through
[`health_trajectory`](../pipeline/coupling.py) and
[run_study3.py](../scripts/run_study3.py). The health signal is an analytic probe,
not the noisy Phase D volume observations.

The large Phase D arrays are intentionally uncommitted. For a regeneration
audit, use a **disposable clone at the revision being reviewed**, record its
original manifest and hashes, then follow [data-and-figures.md](data-and-figures.md).
The runnable sequence is:

```bash
python -m scripts.phaseD_dataset
python -m scripts.run_study2
python -m scripts.run_study3
python -m scripts.run_study4
git diff --stat
```

These commands **write dataset manifests, JSON, and figures under `data/`**.
They are not part of the first-run checks. A code path in the current Study 3
runner includes `tau_selection_alternatives`, absent from the committed Study 3
JSON; current-code regeneration and exact historical-artifact reproduction are
therefore different tasks. Preserve differences for review instead of copying
new outputs over the frozen source state. See the [packet](AUTHOR_REVIEW_DAY3.md).

Reproduction uses known synthetic inputs and does not create a new held-out
evaluation. Prospective v2 intervention studies remain separate from archived
v1.x claims and must follow their [claim spine](specs/robosoft-v2/claim-spine.md).

## Contributor: pick a bounded change

Read [CONTRIBUTING.md](../CONTRIBUTING.md), then identify the relevant model,
runner, test, and [figure-manifest](figure-manifest.json) entry before editing.
For a defect, retain a failing reproduction and test the correction. For a
research change, record the hypothesis and selection rule before new evaluation.

Keep historical manuscript titles and release artifacts intact during repository
maintenance. A name change is explained in [REPOSITORY_IDENTITY.md](REPOSITORY_IDENTITY.md),
not implemented by rewriting archival scientific metadata.

The next bounded owner action is the [author review](AUTHOR_REVIEW_DAY3.md).
There is no DOI, corrected-PDF approval, independent hardware validation, or
prospective v2 result implied by a completed code review. The
[review index](REVIEW_READY.md) links the supporting execution records.

## September 11 completion correction

Read the [item-by-item correction](COMPLETION_RECONCILIATION.md) before interpreting a prepared protocol, software check, or search export as a completed research gate. It identifies actual deliverables and the remaining measurement, review, or source-reading work separately.
