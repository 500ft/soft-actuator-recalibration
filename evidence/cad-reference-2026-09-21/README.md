# CAD tooling reference — verification, 2026-09-21

The owner added [`docs/CAD_PLANNING_ADDENDUM_2026-09-21.txt`](../../docs/CAD_PLANNING_ADDENDUM_2026-09-21.txt)
and a pointer to it from the [week plan](../../docs/WEEKLY_RESEARCH_PLAN_2026-09-21.txt). This records what
was checked before accepting it, and the one integration gap that was fixed.

## Claims checked

| claim in the addendum | check | result |
|---|---|---|
| reviewed revision `cf56cdff50b09c9a266292006cbf5b2a0f2e8ac6` | `git -C ~/Developer/engineering-audit rev-parse HEAD` | matches |
| "local checkout and remote main matched this revision" | `git log -1 origin/main` in that repo, clean tree | matches, `cf56cdf` |
| the three referenced docs exist | `cad_agent_briefing.md`, `host_setup.md`, `solidworks_api_findings.md` | all present |
| the GitHub URLs resolve for a reader | `gh repo view 500ft/engineering-audit` | **public**, so the pinned links work |
| "CAD_PLAN.md currently selects CadQuery plus Onshape for some fixtures" | `docs/CAD_PLAN.md` "Tool and verification decision" | accurate |
| the PV-CAD-02 → 01 → 08 → 03/04/05/06 → 07 mapping | `docs/CAD_TASKS.csv` `depends_on` column | matches the ledger's dependency order exactly |
| no CAD task status changes | all eight CAD rows | still `deferred` |

## Gap found and fixed

The addendum instructs a future session to "read this addendum plus docs/CAD_PLAN.md, docs/CAD_ITEMS.md and
docs/CAD_TASKS.csv", but **none of those files pointed back to it**. Its only inbound link was from the week
plan, a document dated to the week of 2026-09-21, while the CAD pilot is conditional and may be activated
much later. A reader arriving through the CAD documents — the route the addendum itself prescribes — would
not have found it.

Added pointers from `docs/CAD_PLAN.md` (in the tooling-decision section the addendum qualifies) and from
Study D in the observability program, which is the other route into the CAD entry gate. Both state that the
reference selects no tooling and proves no host access.

## Gates confirmed unchanged

CAD branch still parked behind the PV-CAD-02 owner entry decision; PV-OBS-D still blocked on PV-OBS-C and
that decision; PV-08 untouched; publication still BLOCKED. No CAD, FEA, host operation, hardware, spending
or measurement was performed or authorized. Study C remains the priority, and the addendum explicitly does
not amend the C2 preregistration (`docs/specs/observability-program/studyC2-preregistration.md`, which
lands with the separate R2 pull request and is therefore not linked from this branch).

## Noted, not changed

- The addendum and the week plan are `.txt`; every other document under `docs/specs/` and `docs/reviews/` is
  `.md` and is link-checked. `.txt` files are outside that check, so their internal paths are unverified by CI.
- The pinned external revision has no machine-readable record in this repository, so nothing detects drift if
  `500ft/engineering-audit` moves. That is acceptable for a planning reference; it should become a pinned
  dependency record if CAD is activated, as the addendum's own PV-CAD-08 mapping requires.
