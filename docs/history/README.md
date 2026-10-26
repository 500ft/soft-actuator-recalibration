# Closed-study history

The recalibration study is finished. The [matched-cost audit](../../data/sim/phaseD/matched_clock_audit.json)
removed the claimed advantage over counting cycles; [v1.4 is withdrawn](../corrections/v1.4-withdrawn-2026-10-02.md).
Executed artifacts remain at their existing paths. The old sprint task ledger
is preserved byte-for-byte [here](SPRINT_TASKS.csv) as history, with no pending
work assigned by it.

| Historical material | Interpretation |
|---|---|
| [Results](../results.md), [figure lineage](../data-and-figures.md), [simulation outputs](../../data/sim/) | Synthetic results and their figures, redrawn without rerunning a study; the policy plot omits the clock that ties at matched cost |
| [Simulator](../../sim/), [pipeline](../../pipeline/), [runners](../../scripts/), [checks](../../tests/) | Reproducible software; see [commands](../START_HERE.md#reviewer-reproduce-the-checks) |
| [v1.3 source](../preprint_v1.md), [v1.3 correction](../corrections/v1.3-methods-2026-09-05.md), [v1.4 candidate](../preprint_v1_4_candidate.md), [review record](../REVIEW_READY.md) | Historical manuscript and decision records; no release action is pending |
| [Observability program](../specs/observability-program/program.md), [v2 claim spine](../specs/robosoft-v2/claim-spine.md), [gap inventory](../../literature/gaps.md) | Proposed extensions are superseded in active scope. Unrun questions remain unanswered; the frozen claims are preserved as written |
| [Reference-chamber CAD](../../cad/reference-volume/DESIGN_NOTES.md) | Nominal cavity geometry checked in the CAD model; manufacture, assembled-volume calibration and pressure suitability have not been verified |
| [Literature review](../A01_A04_Literature_Review.md), [claim ledger](../../literature/claim-ledger.md) | Source trail, including the corrected Libby measurement interpretation |

The [successor decision](../decisions/0002-successor-software-preparation.md)
records the new question and executed local software work. It does not reopen
these historical manuscript or simulation tasks. The [roadmap](../../ROADMAP.md)
is the only current plan.

## Retired active material

The [pre-cleanup tree](https://github.com/500ft/soft-actuator-recalibration/tree/f67118d2598910d9913ccd372c90a60cb8752e6b)
retains removed source and documents:

- `scripts/run_studyC2.py`, `pipeline/schedules.py` and their dedicated test
  files. Import and command scans found no other executable consumers. C2 has
  no committed study result; its stub tests were implementation checks only.
  Study C and every executed-result generator remain. The C2 preregistration
  remains as a historical scientific record; links to removed source now pin
  this pre-cleanup tree without changing its rules.
- `docs/REVISION_PLAN.md`, the original combined proposal, the RoboSoft v2 scope
  and manuscript outline, and the completed evidence-gap implementation plan.
  These were alternate instructions for retired or completed work. Scientific
  corrections, experimental caveats, executed phase reports and frozen claim
  spines remain in the tree.
- `docs/media/project-overview.svg`, an unused conceptual illustration for the
  retired proposal. Its artifact-specific presentation check was removed; link,
  identity, alternative-text and original result-figure checks remain active.

Historical references to removed paths describe the pre-cleanup tree. They are
not commands to resume that work. No stored study result, manuscript/PDF, source
license, holdout or CAD parameter was removed. CI workflows and dependencies
remain because they serve the retained reproducibility and integrity checks.
