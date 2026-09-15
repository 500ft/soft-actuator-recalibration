# Day-4 execution evidence — 2026-09-15

Plan: [docs/DAY4_PLAN.md](../../docs/DAY4_PLAN.md), accepted as PR #18 (head `8f499da`, merged `e05a044`); PR #17 superseded.
Base: `e05a04433c227184b561f18cbe2c480206ca456a`. Branch `task/day-four-20260914`. Order T0 → T2 → T3 → T1.
Environment: Python 3.11.8; numpy 2.4.6, scipy 1.17.1, matplotlib 3.11.2, reportlab 5.0.1, pypdf 6.18.1; `MPLBACKEND=Agg`; repo root as cwd.
Decisions: D1 **unknown** (no author statement; see the search-scope note under T0), D2 include T1, D3 defer, D4 unscheduled.

## T0 — baseline (recorded, no commit of its own)
`git status --short` empty at base. Checks: `check_manuscript_numbers` 0 · `check_publication_fallback` 0 (integrity PASS, publication BLOCKED) · `check_pdf_arxiv` 0 (historical PDF) · `--for-publication` 2 (expected).
Pins in `docs/publication-readiness.json` vs observed SHA-256: archive `6a6681fe1a77f7d972048dddc99a0a07b55e5d89dca1a83c11ba5b5cefd0777d` MATCH · correction notice `76e7faad…` MATCH · candidate `d700684b2a08c4b9117a1aa2fbc7a0f0ef7085948e7a3cab971591041da51977` MATCH. Readiness record digest `6b58769bdb6b696da120f813ccb9bdbe636fe232177f208e2e4c25424a70b533`; status blocked, corrected_pdf null, author_approval null.
D1 search scope (agent, 2026-09-13): the six checkouts of this project on this machine under ~/Developer and ~/Documents/Codex had no uncommitted changes beyond a `.DS_Store`. That is the extent of the search; it is not a statement that no drafts exist elsewhere, and draft reconciliation stays open.

## T2 — current render instruction corrected (PV-D04a)
`docs/REVISION_PLAN.md` "Ground rules": the bare `python scripts/make_preprint_pdf.py` (refused by the safe route, which requires `--output`) is replaced by the explicit `--source docs/preprint_v1_4_candidate.md --output build/day4/…` form with the note that rendering prepares a review copy, never updates the archive, and confers no approval; links `evidence/task-2026-09-12/README.md`.
Search `rg -n -g '*.md' 'make_preprint_pdf' README.md CONTRIBUTING.md docs evidence` — disposition:
- docs/REVISION_PLAN.md:28:  `python -m scripts.make_preprint_pdf --source docs/preprint_v1_4_candidate.md --output build/day4/preprint_v1_4_candidate.pdf`.  → current instruction (corrected here)
- docs/DAY4_PLAN.md:82:   `rg -n -g '*.md' 'make_preprint_pdf' README.md CONTRIBUTING.md docs evidence`.
- docs/DAY4_PLAN.md:127:   python -m scripts.make_preprint_pdf --source docs/preprint_v1_4_candidate.md --output build/day4/preprint_v1_4_candidate.pdf
- evidence/task-2026-09-12/README.md:6:`python -m scripts.make_preprint_pdf` as documented on `main` wrote to `docs/preprint_v1.pdf` and produced **different bytes** (`6a6681fe…` → `c734259a…`): one routine run would have broken the archive-integrity gate in `check_publication_fallback`. Restored from git before proceeding.  → dated evidence / refusal example; intact
- evidence/task-2026-09-12/README.md:9:- `scripts/make_preprint_pdf.py`: `--source` (default: historical md), `--output` (**required**; the archived PDF path is refused with exit 2), `--manifest`. Verifies the historical PDF's SHA-256 against `docs/publication-readiness.json` before AND after each render. Writes `<output>.manifest.json` with source/output SHA-256, renderer identity, reportlab/pypdf/matplotlib versions and `author_approval: null`.  → dated evidence / refusal example; intact
- evidence/task-2026-09-12/README.md:21:| `make_preprint_pdf --source docs/preprint_v1_4_candidate.md --output docs/preprint_v1.pdf` | **REFUSED**, exit 2, archive bytes unchanged |  → dated evidence / refusal example; intact
- docs/SUBMISSION.md:63:- In `scripts/make_preprint_pdf.py`: register `DejaVuSansMono.ttf` (bundled  → font-embedding note about the script, not a run instruction; unchanged
`git diff --check` clean.

## T3 — review index and contributor guidance (PV-D04b)
`docs/REVIEW_READY.md`: dated current entry for merged PR #16 stating the comparison's actual scope (50/50 regenerated outputs matched between pre-refactor and refactored code, per-array dataset equality, PDFs compared after removing date metadata, both runs retaining pre-existing drift from committed artifacts; no fresh reproduction of archived results claimed). Historical entries retained below.
`CONTRIBUTING.md`: pre-PR simplicity review, `/ponytail-review` when available, otherwise a manual diff read; findings recorded in the PR; no tool install required.
Checks: `tools/check_presentation.py` exit 0 · `tools/test_presentation.py` exit 0 (4 tests). The presentation checker does not scan `REVIEW_READY.md`; the two added local links were resolved by hand relative to `docs/`: `../evidence/ponytail-2026-09-14/README.md` exists; `START_HERE.md#reviewer-inspect-or-regenerate-the-study` exists (heading "Reviewer: inspect or regenerate the study"). PR #16 state confirmed MERGED via GitHub.

## T1 — unapproved preview rendered and inspected (PV-D04c) — **partial: preview prepared, one text-rendering defect found**
Start: clean T3 commit `33556773182b44e3bc428cb78a1ea7893afc5fa8`; T0 pins re-verified unchanged; `build/day4/` confirmed ignored (`.gitignore:17`); no prior output at the path.
Commands (repo root, venv above): `python -m scripts.make_preprint_pdf --source docs/preprint_v1_4_candidate.md --output build/day4/preprint_v1_4_candidate.pdf` → exit 0 · `python -m scripts.check_pdf_arxiv build/day4/preprint_v1_4_candidate.pdf` → exit 0 (fonts embedded as outlines, no encryption, no JavaScript).

| artifact | SHA-256 |
|---|---|
| source `docs/preprint_v1_4_candidate.md` | `d700684b2a08c4b9117a1aa2fbc7a0f0ef7085948e7a3cab971591041da51977` (= readiness pin) |
| **`build/day4/preprint_v1_4_candidate.pdf`** (11 pages) | **`746448862bfa7377d5b210228ea2a005f4dedbaa8135ee8dfaa7adaa7866056c`** |
| `build/day4/preprint_v1_4_candidate.manifest.json` (schema 3) | `a1759e5e92f1bb069c71373cbc86dc744630c24b0f21afaf8d323d056be43e35` |
| renderer `scripts/make_preprint_pdf.py` | `d28cbfe3b87a5f96fc599e3b0c91cd99ba5269c692733bfc7485da2ff9d05652` at git HEAD `3355677`, clean |

Manifest verified against the actual files: source, output and renderer-script hashes match; all 7 consumed figures match their recorded SHA-256; `author_approval: null`; archive `6a6681fe…` and readiness record `6b58769b…` equal T0 before and after. Library versions in manifest: reportlab 5.0.1, pypdf 6.18.1, matplotlib 3.11.2.
Absolute local path for the owner: `/Users/redhose/Developer/repo-professionalization-20260910/soft-actuator-recalibration/build/day4/preprint_v1_4_candidate.pdf` (not committed; regenerate with the command above, then compare the PDF hash).

Page inspection: all 11 pages rasterized with `pdftoppm 26.08.0` at 55 dpi (`page-01..11.png`) and pages 7 and 9 at 120 dpi; every page viewed. Title, author, status line, abstract, corrected methods (§3.5 sensor corruptions not applied to the Study 3 signal; §3.9 idealized model-derived signal, zero rest), key policy table (0.40 / 0.21 / 0.06 / 0.02 mm; 1 / 1.5 / 2 / 5 events — equal to the source table), §5 limitations and references all present and match the source; the seven figures render with legible axes and annotations.
Findings:
1. **Text-rendering defect (renderer, not source):** `inline()` in `scripts/make_preprint_pdf.py` has no handling for Markdown `\*` escapes; its italic regex then pairs an escaped asterisk with a later lone one. Result: 5 spots where a literal backslash appears and the asterisk is lost, e.g. page 7 §4.5 "τ\ = 0.05 fractional loop-area growth … T\ = 2,700 cycles" where the source says τ\* and *T*\*. Full list: `build/day4/t1_backslash_artifacts.txt` (reproduce with pypdf text extraction). The same construct occurs 7 times in the historical `docs/preprint_v1.md`, so the archived v1.3 PDF is expected to carry it too; the archive is frozen and untouched. **Renderer repair is a separately scoped follow-up** (plan T1 rule); no re-render was made.
2. Cosmetic: the Figure 2 caption falls at the top of page 6, separated from its plot at the bottom of page 5 (page-break placement).
3. Cosmetic, in the committed figure file (not the renderer): Figure 4b panel (b) annotation "τ = 0.01 … 95% CI [0.273, 0.351]" is crossed by the dashed τ = 0.05 line.
4. For the author (source content, not a defect): §7 cites the pre-rename URL `github.com/500ft/P-V-Fatigue-Manifold-Proprioception`; GitHub redirects it to `500ft/soft-actuator-recalibration` (verified via the API), consistent with `docs/REPOSITORY_IDENTITY.md`.
Status: **preview prepared, not approved, PV-08 not complete.** The PDF is usable for the text-review sitting with finding 1 noted; a corrected render for any exact-bytes decision needs the renderer follow-up first.

## Final handoff checks (after T1)
`pytest -q` 213 passed · `check_manuscript_numbers` 0 · `check_publication_fallback` 0 (PASS, BLOCKED) · `--for-publication` 2 · `check_pdf_arxiv` 0 (historical) · presentation checks 0 / 4 passed · `git diff --check` clean. T4 deferred per D3; T5 is the owner's. Temporary logs: `build/day4/t0_*.log`, `t2_search.txt`, `t3_*.log`, `t1_render.log` (ignored).

## Delivery note
PR #19 was merged at `1ad4cb7`, the execution under the superseded #17 defaults, because the force-push of the rebuilt branch (`6bebec0`) was rejected and the merge proceeded anyway. This file, `docs/REVIEW_READY.md`, `CONTRIBUTING.md`, `docs/REVISION_PLAN.md` and the three ledger rows were replaced with the #18 execution in the follow-up PR; the superseded rows (which mapped PV-D04a to T1 and recorded D1 as "none") are not retained because they never described completed work under the accepted plan. The earlier local render `build/preprint_v1_4_candidate.pdf` (`d0819dee…`, rendered 2026-09-15 from `e408f9d` before #18, format-gated only, pages never inspected) was deleted locally; the inspected preview is the one in `build/day4/`.
