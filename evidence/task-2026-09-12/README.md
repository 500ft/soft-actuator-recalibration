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
