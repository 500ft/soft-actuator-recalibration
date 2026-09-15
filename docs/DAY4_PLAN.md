# Day-4 plan — prepare the corrected manuscript for author review

Planned date: 2026-09-14; revised 2026-09-15. Status: **proposed; execution has not started**.
This plan supersedes [PR #17](https://github.com/500ft/soft-actuator-recalibration/pull/17)
at `d22fff94b629d8a685088387bd391b99d3599200`. Reviewed main:
`9bc984829537b0a33ee1305a819bd13c3d3803c7`, including merged
[PR #16](https://github.com/500ft/soft-actuator-recalibration/pull/16) (PV-R04).

Outcome: a locally inspectable **unapproved** correction preview, accurate render
instructions, and a clear author handoff. This PR changes this plan only. Proposed
tasks become executable when the owner accepts the plan or instructs execution;
publishing this plan does not execute it. Execution status remains solely in
[SPRINT_TASKS.csv](SPRINT_TASKS.csv); PV-08 remains the author-review task.

## Critique of the original plan

| Gap in PR #17 | Revision |
| --- | --- |
| D1 turns silence into an author statement that no other drafts exist. | Leave reconciliation unanswered until the author identifies drafts or explicitly confirms none. Preview preparation can continue. |
| T1 checks PDF format but not rendered content, and says both “nothing committed” and “one commit per task.” | Inspect every page; keep the PDF and render manifest local, commit the evidence and task status. |
| T2 requires no archive-targeting command anywhere, including historical failure examples. | Repair current operating instructions; preserve dated evidence and deliberate refusal examples. |
| T3 overstates byte identity and relies on a checker that does not scan the review index. | State the comparison's actual scope; explicitly verify the changed index links. |
| T4 treats a dataset/RNG change as optional cleanup with an undefined comparison baseline. | Defer it to a separate data-versioning proposal; do not regenerate frozen artifacts in this work. |
| T5 implies approval can be rebound after edits and re-rendering. | Separate text acceptance, inspection of exact PDF bytes, and the eventual release decision. A changed PDF requires a new decision. |

## Decisions and defaults

Blank fields never become author evidence. These defaults select proposed work;
they do not fill [the owner response](COMPLETION_RECONCILIATION.md#owner-response--not-submitted).

| ID | Decision | If unanswered |
| --- | --- | --- |
| D1 | Identify authoritative author drafts, or explicitly confirm there are none outside the candidate. | **Unknown.** Record the search scope if any local search is made; do not claim all copies were searched. T1–T3 may proceed; draft reconciliation remains open. |
| D2 | Prepare a local preview of the current candidate before text acceptance? | **Include T1** when this plan is accepted. Label it unapproved and retain its full source/PDF hashes. |
| D3 | Pursue audit item 4 later? | **Defer.** A yes requests a separate migration plan; it does not add dataset changes to this dayplan. |
| D4 | When can the author review the packet? | **Unscheduled.** Offer the existing approximately 50-minute sitting; do not book a calendar event or mark review complete. Agent preparation does not wait for a booking. |

## Execution order and evidence

Use a new branch from freshly fetched `main`, suggested name
`task/day-four-20260914`; retain the original plan branch. If the accepted plan is
not merged, identify its exact PR/head in the execution record and carry this file
as a separate plan commit. Recheck the base if `main` has changed.

Order: **T0 → T2 → T3 → T1 → T5**. Documentation commits precede the render so
the manifest can identify a clean source revision. T2 and T3 do not depend on an
author reply or a successful preview. T4 is excluded from this sequence.

Write concise, cumulative evidence to `evidence/task-2026-09-14/README.md` (new):
task, source revision, command, environment, observed exit/result, and unresolved
limits. Capture temporary logs under gitignored `build/day4/` first. Use one
commit per completed agent task, including its evidence and ledger row; do not
make empty commits for T0, deferred T4, or an unperformed author sitting. Proposed
ledger IDs are PV-D04a (T2), PV-D04b (T3), PV-D04c (T1); check for collisions first.
Append rows only when execution starts and retain all historical statuses.

### T0 — establish the baseline (Agent, 5–10 minutes)

Files: temporary records under `build/day4/`; final summary accompanies T2.

1. Record `git rev-parse HEAD`, `git status --short`, Python version and installed
   dependency versions. Use Python 3.11 and the existing [CI dependencies](../.github/workflows/ci.yml).
2. Run the three artifact checks in the verification table below. Record the
   expected publication exit separately; exit 2 is not a failed integrity check.
3. Read full SHA-256 pins from [publication-readiness.json](publication-readiness.json)
   and compare them with the candidate, correction notice and archived PDF.
   Snapshot the readiness record's own digest. Retain these observed values in evidence.

Done when: the starting tree and artifact identities are recorded, integrity and
numbers pass, and publication is blocked as expected. A mismatch is a finding to
resolve before rendering, not permission to rewrite a pin. Do not invent a new
lint/typecheck/build requirement for this documentation-and-preview task.

### T2 — correct the current render instruction (Agent, 5–10 minutes)

Files: [REVISION_PLAN.md](REVISION_PLAN.md), evidence README, task ledger.

1. Replace the obsolete bare command under “Ground rules” with an explicit
   candidate source and separate output path, following T1. Explain that rendering
   prepares a review copy; it does not update the archive or confer approval.
2. Search tracked Markdown instructions with
   `rg -n -g '*.md' 'make_preprint_pdf' README.md CONTRIBUTING.md docs evidence`.
   Classify remaining hits as current instructions, dated evidence, or refusal
   examples. Correct other current instructions only if found, listing exact
   paths in the evidence. Link the existing [renderer evidence](../evidence/task-2026-09-12/README.md).

Done when: actionable render examples use the intended source and an explicit
output outside the archive; historical records and negative examples are intact.
Record the search disposition and pass `git diff --check`. Do not add a new
command-scanning framework or rewrite historical publication decisions.

### T3 — update the review index and contributor guidance (Agent, 10–15 minutes)

Files: [REVIEW_READY.md](REVIEW_READY.md), [CONTRIBUTING.md](../CONTRIBUTING.md),
evidence README, task ledger.

1. Add a dated current entry linking merged PR #16 and its
   [comparison evidence](../evidence/ponytail-2026-09-14/README.md). Describe the
   result precisely: 50/50 regenerated outputs matched between the pre-refactor
   and refactored code; dataset equality was per array and generated PDFs were
   compared after removing date metadata. Both runs retained pre-existing drift
   from committed artifacts. This does not establish fresh reproduction of the
   archived results. Retain the dated historical entries below it.
2. Add a short pre-PR simplicity review for code changes: `/ponytail-review` when
   available, otherwise an equivalent manual review of the diff for unnecessary
   complexity. Record findings or no findings in the PR. It supplements correctness
   review and tests; it does not require installing a tool or changing research scope.
3. Run both presentation commands below. Separately resolve each added local link
   in `REVIEW_READY.md` relative to that file: the presentation checker does **not**
   include the review index. Record the checked targets.

Done when: the current entry has accurate comparison limits and working links,
the contributor step is usable without a local skill installation, and checks pass.
No ledger status outside the new task row changes.

### T1 — render and inspect the unapproved preview (Agent, 20–30 minutes; D2)

Files: local PDF, manifest and page images under `build/day4/`; evidence README,
review-index preview entry, and task ledger. No manuscript or renderer edit.

1. Start from the clean T3 commit. Verify the T0 pins still match. If the output
   already exists, use a fresh suffixed filename and record it; do not overwrite a
   review copy. Confirm the chosen paths are ignored with `git check-ignore`.
2. Run from the repository root, with the selected environment active:

   ```sh
   python -m scripts.make_preprint_pdf --source docs/preprint_v1_4_candidate.md --output build/day4/preprint_v1_4_candidate.pdf
   python -m scripts.check_pdf_arxiv build/day4/preprint_v1_4_candidate.pdf
   ```

3. Verify the generated `preprint_v1_4_candidate.pdf.manifest.json` against the
   actual source, PDF, figures and renderer. Record full source/PDF/manifest
   SHA-256 values, renderer revision and library versions. Confirm
   `author_approval` is null and the archive/readiness digests still equal T0.
4. Render every PDF page to images with an available PDF renderer and inspect all
   pages. Record tool/version, page count and any clipping, missing figures,
   broken symbols, unreadable tables or mismatched captions. Check that the title,
   abstract, corrected methods, key policy table and limitations match the source.
   A font-check pass alone is insufficient. If inspection cannot be performed or
   defects remain, record T1 as partial/blocked; keep T2/T3 deliverable.
5. Commit the evidence and a current review-index entry pointing to it, then the
   task row. Keep the PDF, manifest and page images ignored. Give the owner a
   working absolute local PDF link and its hashes in the handoff; a GitHub reader
   receives the reproduction command and evidence, not a broken build-file link.

Done when: the candidate passes format and page inspection, pins are unchanged,
and the owner can open the exact inspected PDF. The manifest identifies the
pre-evidence render commit; do not re-render just to include the evidence commit,
because that can change PDF bytes. Label this **preview prepared**, never author
approval or PV-08 completion. If D2 is declined, record T1 as skipped and hand off
the Markdown packet. Renderer repairs require a separately scoped follow-up.

### T4 — defer audit item 4 (no execution or commit)

The [audit evidence](../evidence/ponytail-2026-09-14/README.md) says removing the
contact loop changes sensor seeds, not just the dataset container's checksum.
The [reproduction guide](START_HERE.md#reviewer-inspect-or-regenerate-the-study)
also documents current-code drift from frozen results. “Re-pin and list differences”
is therefore not an adequate acceptance rule for a cleanup.

If D3 is yes, prepare a separate proposal that names the exact baseline revision,
data schema and consumers; distinguishes dropping saved arrays from changing RNG
consumption; and defines permitted differences before running anything. Any
comparison must use disposable checkouts and versioned output locations, preserve
the historical manifest/results, and reject unexpected changes in consumed arrays.
It must decide how new data and derived results will be versioned together. No
dataset regeneration, hash re-pinning or study rerun belongs to this dayplan.

### T5 — author review and exact-artifact decision (Owner, about 50 minutes; D1/D4)

Use [AUTHOR_REVIEW_DAY3.md](AUTHOR_REVIEW_DAY3.md) and return the existing
[completion response](COMPLETION_RECONCILIATION.md#owner-response--not-submitted):
identity/date, actual drafts compared or explicit none, full candidate source hash,
text decision, statistical/threshold wording decisions, and separate PDF/posting
decisions. If T1 ran, also identify the local PDF and its **PDF** SHA-256; the
manifest hash alone does not state which bytes the author approved.

Text acceptance without edits and an explicit review of the same preview can
support a decision on that exact PDF. If the author requests edits, apply them in
a later implementation PR, render a new version, and return it for review. Never
copy an earlier approval onto new hashes. Record partial decisions honestly;
neither a scheduled sitting nor accepted text alone closes PV-08.

The current [publication checker](../scripts/check_publication_fallback.py) is an
intentional hard stop, not a metadata-driven release engine. A corrected release
will need a separate reviewed change covering PDF, metadata and checker behavior;
flipping approval fields cannot clear it. T5 does not authorize an account action.

## Verification and delivery

| Check | Expected result / timing |
| --- | --- |
| `python -m scripts.check_manuscript_numbers` | Exit 0 at T0 and final handoff; checks historical and candidate text. |
| `python -m scripts.check_publication_fallback` | Exit 0 and historical integrity PASS at T0 and final handoff. |
| `python -m scripts.check_publication_fallback --for-publication` | Exit **2**, publication BLOCKED, at both points. Do not suppress unexpected exits. |
| `python -m scripts.check_pdf_arxiv` | Exit 0 for the historical PDF at final handoff; T1 separately checks its explicit candidate path. |
| `python tools/check_presentation.py . "Soft Actuator Recalibration" soft-actuator-recalibration` | Exit 0 after T3 and final documentation edits. |
| `python tools/test_presentation.py` | Exit 0 with the presentation check. |
| `python -m pytest -q` | Run the existing suite once before the execution PR, following the documented local startup workaround only if needed. No new tests for prose. |
| `git diff --check` and branch diff against the recorded base | No whitespace errors; only planned documentation, evidence and new ledger rows change. |

Include actual commands/exits, full artifact hashes, page-review findings and the
limits of each check in the evidence. Never regenerate studies as a verification
shortcut. Review the complete diff for correctness and unnecessary process before
pushing the execution branch and opening its PR; report CI's actual state.
After meaningful fixes, rerun affected checks rather than blindly repeating all work.

Preparation is complete when T2/T3 and included T1 meet their done-conditions and
the execution PR plus local preview are delivered. Author review may still be
pending. Historical results, figures, archive, candidate source, readiness record
and approval fields remain unchanged throughout T0–T3. No publication, deposit,
outreach, spending, hardware work or new v2 experiment is part of this plan.
CAD retains its own [entry decision](CAD_PLAN.md); v2 retains its
[draft-reconciliation and prospective-specification requirements](specs/v2-integrity-core/design.md).
Neither is newly made dependent on completing a publication account action.

| Requirement | Task |
| --- | --- |
| Preserve artifact identity and honest defaults | T0, D1–D4, T5 |
| Usable, inspected correction preview | T1 |
| Accurate operating and contributor instructions | T2, T3 |
| Keep dataset migration separate from review preparation | T4 |
| Obtain explicit decisions on the source and exact PDF | T5 |
