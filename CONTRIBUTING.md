# Contributing

Contributions should keep the simulation, generated artifacts, and manuscript
numbers synchronized.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install pytest reportlab pypdf
```

## Before changing a study

1. Identify the study runner in `scripts/` and its output directory under
   `data/`.
2. Update the model or pipeline code before regenerating outputs.
3. Do not hand-edit generated JSON, figures, or manuscript numbers.
4. Keep `docs/result_spine.md` frozen unless the release process explicitly
   replaces it.
5. Keep physical-test statements separate from simulation results.

## Checks

Run the complete release gate before submitting a change:

```bash
python -m pytest
python -m scripts.check_manuscript_numbers
python -m scripts.check_pdf_arxiv
python -m scripts.check_publication_fallback
```

If a study output changes, include the regenerated data, figures, and affected
manuscript text in the same commit.

For code changes, also run `/ponytail-review` (the ponytail Claude Code plugin) on the
diff before opening the PR and act on its delete-list; a refactor that touches a study
runner must show its committed outputs regenerate byte-identical
(`evidence/ponytail-2026-09-14/compare.py`).

## Pull requests

Describe:

- the model, study, or document that changed;
- the command used to regenerate outputs;
- the tests and publication checks run; and
- whether the change affects the frozen v1.3 release or only future work.

Keep unrelated local research notes and outreach material out of project
commits.
