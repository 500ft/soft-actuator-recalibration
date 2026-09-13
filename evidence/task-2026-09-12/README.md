# PV-R03 — safe, separately versioned PDF-rendering route — 2026-09-12

Branch `audit/pdf-render-route-20260912` off `main` 67b9ee1. Sprint order task 3.

## The hazard, verified before changing anything
`python -m scripts.make_preprint_pdf` as documented on `main` wrote to `docs/preprint_v1.pdf` and produced **different bytes** (`6a6681fe…` → `c734259a…`): one routine run would have broken the archive-integrity gate in `check_publication_fallback`. Restored from git before proceeding.

## What changed
- `scripts/make_preprint_pdf.py`: `--source` (default: historical md), `--output` (**required**; the archived PDF path is refused with exit 2), `--manifest`. Verifies the historical PDF's SHA-256 against `docs/publication-readiness.json` before AND after each render. Writes `<output>.manifest.json` with source/output SHA-256, renderer identity, reportlab/pypdf/matplotlib versions and `author_approval: null`.
- `scripts/check_pdf_arxiv.py`: optional path argument so a candidate render is gated by the same font-embedding rules; default unchanged.
- `tests/test_preprint_renderer.py`: 6 tests — refusal (API and CLI), explicit-output requirement, manifest hashes match the files and the readiness record's candidate pin, arXiv gate passes on the candidate, readiness JSON untouched, archive bytes unchanged after every case.
- `.gitignore`: `build/`, so rendered candidates are never committed by accident.

## Checks observed (repo root on PYTHONPATH, MPLBACKEND=Agg)
| command | observed |
|---|---|
| `python -m pytest -q` | 203 passed (6 new) |
| `python -m scripts.check_manuscript_numbers` | 0 |
| `python -m scripts.check_pdf_arxiv` / `… build/preprint_v1_4_candidate.pdf` | 0 / 0 |
| `python -m scripts.check_publication_fallback` / `--for-publication` | 0 BLOCKED / 2 |
| `make_preprint_pdf --source docs/preprint_v1_4_candidate.md --output docs/preprint_v1.pdf` | **REFUSED**, exit 2, archive bytes unchanged |
| `sha256 docs/preprint_v1.pdf` before / after all runs | `6a6681fe1a77f7d9` both |

## Not done, by design
No corrected PDF is committed. `docs/publication-readiness.json` is byte-identical: status `blocked`, `corrected_pdf: null`, `author_approval: null`. PV-08 is unchanged — the author's review sitting (`docs/AUTHOR_REVIEW_DAY3.md`) decides which source is rendered and whether the result is approved; this route only makes that render safe and hash-bound when it happens.

## Review repair (PV-R03b, same day)
The review reproduced two bypasses in the first version: `--manifest` was not validated, so pointing it at `docs/preprint_v1.pdf` overwrote the archive with JSON while the manifest still claimed it unchanged (the final hash check ran *before* the manifest write); and `--output` equal to the `--source` markdown was accepted. Both reproduced here on the sandbox clone (restored from git; the pushed archive was never touched).

Fix: `validate_destinations()` checks `--output` **and** `--manifest` against the archive, the readiness record, the historical markdown, every tracked `docs/*.md|pdf|json|txt`, the source, and each other — following symlinks and case-insensitive aliases — **before** any write; `--output` must be `.pdf`; the archive, readiness record and source are hash-verified **after the manifest write**, i.e. after the last write, so the manifest's claim is true when it is made. Seven new regression tests cover manifest→archive, manifest→readiness, manifest→source, output→source/other docs, output==manifest, symlink and case aliases, and the manifest-stem default. 13 renderer tests, 210 total, all other gates unchanged.

## Review repair 2 (PV-R03c, 2026-09-13)
Review 2 overwrote temporary copies of a nested spec, `docs/SPRINT_TASKS.csv` and a figure the renderer had just consumed via `--manifest`: the protected set scanned only `.md/.pdf/.json/.txt` directly inside `docs/`. Reproduced on a temp copy. Now `protected_paths()` = **every `git ls-files` path** (fallback: a filesystem walk, recorded as `protection.basis`) ∪ archive ∪ readiness record ∪ historical markdown ∪ source ∪ **every figure the source references**. The same set is hashed before any write and re-verified after the manifest write; a missing referenced figure is an error, not a silent skip. The manifest (schema 3) now carries per-figure SHA-256 and a `renderer_revision` (script SHA-256, repo HEAD, dirty flag). Three new tests; 16 renderer tests; 213 total; all four checkers unchanged; archive hash identical.
