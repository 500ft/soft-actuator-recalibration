# Day-4 bounded work — 2026-09-14

Base: `9bc984829537b0a33ee1305a819bd13c3d3803c7` (main, PV-R04 merged). Branch for this plan: `plan/day-2026-09-14`; execution happens on a separate branch after the owner edits and approves this file. Status lives only in `docs/SPRINT_TASKS.csv`; nothing here is done because it is planned.

## Owner decisions needed before or during the day

| # | Decision | Default if the owner writes nothing |
|---|---|---|
| D1 | Are there author drafts outside this repository? (every local copy on this machine has none) | "none" — the PV-08 draft-reconciliation field is answered as none |
| D2 | Render the **unapproved** v1.4 candidate PDF into `build/` for the review sitting? | yes (task T1) |
| D3 | Apply ponytail audit item 4 (drop the eight unread phase-D dataset arrays and the contact loop; re-pin the dataset manifest)? | **no** — it changes the dataset SHA the committed results cite |
| D4 | Book the ~50-minute author review sitting (PV-08) today? | owner's call; the agent cannot do it |

## Tasks

### T1 — candidate PDF for the review sitting (Agent, ~0.5 h, needs D2)
Command: `python -m scripts.make_preprint_pdf --source docs/preprint_v1_4_candidate.md --output build/preprint_v1_4_candidate.pdf`, then `python -m scripts.check_pdf_arxiv build/preprint_v1_4_candidate.pdf`.
Deliverable: the PDF and its `.manifest.json` under the gitignored `build/`; the manifest's source/figure/renderer hashes copied into the evidence record. Nothing committed; `author_approval` stays null.
Acceptance: arXiv gate exit 0 on the candidate; `sha256 docs/preprint_v1.pdf` = `6a6681fe…` before and after; `docs/publication-readiness.json` byte-identical.

### T2 — retire the unsafe render instruction (Agent, ~0.2 h)
`docs/REVISION_PLAN.md` line 26 still says `python scripts/make_preprint_pdf.py`, which the safe route now refuses (no `--output`). Replace with the `--source/--output` form and a pointer to `evidence/task-2026-09-12/README.md`. Grep the tree for any other bare invocation.
Acceptance: no documented command targets `docs/preprint_v1.pdf`; presentation checks pass.

### T3 — PV-R04 follow-through (Agent, ~0.3 h)
Record in `docs/REVIEW_READY.md` that the ponytail refactor is merged and byte-identical, linking `evidence/ponytail-2026-09-14/`. Add the `/ponytail-review` step to `CONTRIBUTING.md` as the expected pre-PR check for code changes.
Acceptance: links resolve (`tools/check_presentation.py` passes); ledger unchanged.

### T4 — audit item 4, only if D3 = yes (Agent, ~1.5 h)
Drop the unread arrays and the contact loop in `scripts/phaseD_dataset.py` and `sim/sensors.py`; regenerate the dataset; re-pin `data/sim/phaseD/manifest.json`; regenerate studies 2, 3, cluster-CI and their figures; run `check_manuscript_numbers`. Any changed manuscript number is reported, not edited into the candidate.
Acceptance: per-array equality for the four consumed arrays against the previous dataset; all other outputs identical or their differences listed in the evidence record.

### T5 — author review sitting (Owner, ~0.8 h, PV-08)
Follow `docs/AUTHOR_REVIEW_DAY3.md`; return the fields at the bottom of `docs/COMPLETION_RECONCILIATION.md` (reviewer, date, candidate hash `d700684b…`, text decision, statistical and threshold wording decisions, PDF and posting decisions). If T1 ran, review that PDF and quote its manifest hash.

## Work order
1. Owner edits this file (decisions D1–D4, strike or add tasks) and approves the PR.
2. Agent executes T1–T3 (and T4 if D3 = yes) on `task/day-four-20260914`, one commit per task, evidence under `evidence/task-2026-09-14/`, ledger rows PV-D04a…, then a PR to main.
3. Owner runs T5 and returns the form; the agent applies text decisions, re-renders, and binds the approval to the new hashes in a further PR.

## Boundary
No publication, deposit, DOI, outreach, hardware, spending or approval field is touched by T1–T4. `docs/preprint_v1.pdf` and `docs/publication-readiness.json` stay byte-identical. The CAD pilot ledger and the prospective v2 study stay parked until PV-08 closes.
