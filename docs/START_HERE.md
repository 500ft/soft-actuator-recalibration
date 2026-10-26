# Start here: Soft Actuator Recalibration

The simulation study is closed and v1.4 is withdrawn. At matched recalibration
cost, a cycle-count clock ties the P-V trigger; see the
[withdrawal](corrections/v1.4-withdrawn-2026-10-02.md) and
[audit output](../data/sim/phaseD/matched_clock_audit.json). No physical actuator
was measured. The [repository overview](../README.md) gives the short version.

## Recruiter or prospective supervisor: two minutes

1. Read the [Study 3 trade-off and limits](results.md#study-3-recalibration-policy):
   the matched-cost audit removes the claimed advantage over counting cycles.
2. Inspect the [matched-cost comparison](../data/sim/summary/policy_comparison.png)
   and its [source tables and reproduction command](data-and-figures.md#active-summaries-and-retained-history).
   Both tied policies are visible; counts include initial calibration.
3. Read the [withdrawal decision](corrections/v1.4-withdrawn-2026-10-02.md).
   The earlier [author-review form](AUTHOR_REVIEW_DAY3.md) remains available;
   its acceptance was withdrawn.

The repository shows how the model, actuator-level test split, policy comparison
and result checks were built. It contains no physical sensor measurements,
early failure warning result or measured operating cost.

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

Expected after withdrawal: publication **BLOCKED**, exit **2**. No release is
planned. The [readiness record](publication-readiness.json) records that block;
the [withdrawal](corrections/v1.4-withdrawn-2026-10-02.md) supersedes the
historical author-review and deposit instructions.

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
new outputs over the committed results. See the [author-review form](AUTHOR_REVIEW_DAY3.md).

Reproduction uses known synthetic inputs and does not create a new held-out
evaluation. The [v2 claim outline](specs/robosoft-v2/claim-spine.md) remains as
a historical proposal outside the closed scope in [ROADMAP.md](../ROADMAP.md).

## Contributor: maintain retained evidence

Read [CONTRIBUTING.md](../CONTRIBUTING.md), then identify the relevant model,
runner, test, and [figure-manifest](figure-manifest.json) entry before editing.
For a defect, retain a failing reproduction and test the correction. The old
study is closed. Unrun C2 code and obsolete proposal instructions were removed;
see the [retirement record](history/README.md#retired-active-material). Successor
work belongs to the separate local repository and its dependency roadmap.

Keep historical manuscript titles and release artifacts intact during repository
maintenance. A name change is explained in [REPOSITORY_IDENTITY.md](REPOSITORY_IDENTITY.md),
not implemented by rewriting archival scientific metadata.

Prior work and the evidence for and against each current claim are in the
[literature folder](../literature/README.md); its [claim ledger](../literature/claim-ledger.md) lists
counter-evidence alongside support, and [gaps.md](../literature/gaps.md) records what no paper settles.

Where the *numbers* come from is a separate question from where the *claims* come from.
[Parameter provenance](PARAMETER_PROVENANCE.md) classifies every consequential value by what kind of
number it is and how well supported it is, and carries the traceability index linking each major decision
to its analysis and evidence. The [2026-09-25 engineering audit](ENGINEERING_AUDIT_2026-09-25.md) records
what that sweep found — in short, strong preregistration discipline over a synthetic world whose
parameters are largely unsourced. **No result in this repository is validated against physical
hardware.**

No manuscript-review or publication action remains in this scope. Any hardware
study requires a separate owner decision. Local successor software preparation
is recorded in the [decision](decisions/0002-successor-software-preparation.md);
see [ROADMAP.md](../ROADMAP.md) and the [history index](history/README.md).
The [review record](REVIEW_READY.md) links the historical execution records.

## September 11 completion correction

Read the [item-by-item correction](COMPLETION_RECONCILIATION.md) before interpreting a prepared protocol, software check, or search export as a completed research gate. It identifies actual deliverables and the remaining measurement, review, or source-reading work separately.
