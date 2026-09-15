# Day-4 tasks — executed 2026-09-15

Plan: `docs/DAY4_PLAN.md` (merged as PR #17, unedited, so its defaults apply: D1 none, D2 yes, D3 no).
Base: `e408f9d0cca0da05caf8fd355ec819e880794899`. Branch `task/day-four-20260914`.

## T1 — unapproved candidate PDF rendered for the review sitting (PV-D04a)
`python -m scripts.make_preprint_pdf --source docs/preprint_v1_4_candidate.md --output build/preprint_v1_4_candidate.pdf` → exit 0.
`python -m scripts.check_pdf_arxiv build/preprint_v1_4_candidate.pdf` → exit 0 (fonts embedded, no encryption, no JavaScript).

| artifact | SHA-256 |
|---|---|
| source `docs/preprint_v1_4_candidate.md` | `d700684b2a08c4b9117a1aa2fbc7a0f0ef7085948e7a3cab971591041da51977` (matches the readiness record's candidate pin) |
| `build/preprint_v1_4_candidate.pdf` | `d0819dee8cde49abe278bafb71b566acd59e6f8cb8557fb2e1b682cfc84adc3a` |
| `build/preprint_v1_4_candidate.manifest.json` (schema 3) | `d869b995eeaf735797613eb35518e0753b02b061948d88ac3ab64949aad6b73a` |
| renderer `scripts/make_preprint_pdf.py` | `d28cbfe3b87a5f96fc599e3b0c91cd99ba5269c692733bfc7485da2ff9d05652` at HEAD `e408f9d`, clean tree |

Manifest: 7 consumed figures hashed; 208 tracked files verified unchanged after the manifest write; `author_approval: null`.
`docs/preprint_v1.pdf` `6a6681fe…` and `docs/publication-readiness.json` `6b58769b…` identical before and after. `git status` clean apart from this branch's doc edits. **Nothing under `build/` is committed and nothing is approved**: the PDF exists so the PV-08 sitting can review a rendered artifact and quote its hash.

## T2 — unsafe render instruction retired (PV-D04b)
`docs/REVISION_PLAN.md` no longer instructs the bare `python scripts/make_preprint_pdf.py` (which the safe route refuses); it now shows the `--source/--output` form. Tree grep: no remaining documented command targets `docs/preprint_v1.pdf`.

## T3 — PV-R04 follow-through (PV-D04c)
`docs/REVIEW_READY.md` links the byte-identical ponytail evidence; `CONTRIBUTING.md` adds the `/ponytail-review` pre-PR step and the regenerate-and-compare requirement for study-runner refactors.

## Checks
`tools/check_presentation.py` OK · `tools/test_presentation.py` 4 passed · `tests/test_preprint_renderer.py` 16 passed · full `pytest -q` and the four publication checkers on the PR (CI).

## Not done
T4 (audit item 4) skipped per D3 default. T5 (author review sitting, PV-08) is the owner's; the D1 default "none" is recorded here, not signed.
