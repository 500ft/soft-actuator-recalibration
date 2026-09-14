# Ponytail audit implementation — 2026-09-14

Base: `f3a71ff98efa7c0856338fe34881eabb2fb0ea1a` (main). Branch: `audit/ponytail-20260914`.

A whole-repo over-engineering audit (DietrichGebert/ponytail v4.10.0, `/ponytail-audit`) listed 19
findings. 18 were applied; the Python tree went from 7,967 to 7,475 lines (-492) with no change to any
numeric output, figure, threshold, dataset, or publication gate.

## Applied
- Orphan `scripts/generate_report.py` (other project; read files that do not exist; undeclared PyYAML) deleted.
- Eight copies of the matplotlib Agg guard -> `figstyle.setup()`; `sys.path` hacks and unused imports removed.
- `scripts/phased.py` holds the dataset access studies 2 and 3 both copied; `run_study3` exposes
  `prepare`, `select_thresholds`, `heldout_policies`, `lead_records`; the cluster-CI run and the
  study-3 main path call them instead of re-implementing tau*/T* selection and the frontier loop.
- `run_study4` imports `build_actuators`/`make_drive`/`all_commands` from the dataset generator.
- `sim.plant.steady_state` replaces the duplicate `_operating_volumes`; `sim.plant.first_crossing`
  replaces three hand-rolled interpolated crossings (lead time, half-life, log-x softness crossing).
- Removed dead flexibility: always-zero `NetworkParams.P_atm` and `PCCParams.pressure_threshold_pa`;
  four never-used `sample_validation_cohort` axes; keyword arguments no caller passes; the test-only
  inverse-kinematics trio (now local to `tests/test_kinematics.py`); `policy_metrics` third return value.
- `pipeline.degradation.FITTERS` replaces `run_study1._fitters()`; gate0 sweep reads its `Params` fields.

## Not applied, by design
- Item 4 (eight unread phase-D dataset arrays and the contact loop): dropping the contact loop changes
  sensor seeds and the dataset manifest SHA that the committed results were produced from. That is a
  dataset change for the author, not a refactor.
- `gate0_lumped_rc.py` keeps its own matplotlib guard: it is documented as directly runnable.

## Verification
| check | observed |
|---|---|
| `python -m pytest -q` | 213 passed (unchanged count; two tests now use local helpers) |
| `check_manuscript_numbers` / `check_pdf_arxiv` / `check_publication_fallback` / `--for-publication` | 0 / 0 / 0 (BLOCKED) / 2 |
| `tools/check_presentation.py`, `tools/test_presentation.py` | OK / 4 passed |
| `pyflakes` on every changed file | clean |
| byte identity | all 9 generators run on a clone of `main` and on a clone of this branch (same venv, `MPLBACKEND=Agg`); **50/50 regenerated files identical**: JSON and PNG by SHA-256, `dataset.npz` per array, PDF after stripping `/CreationDate` and `/ModDate` |
| `sha256 docs/preprint_v1.pdf` | `6a6681fe…` before and after |

Both clones show the same pre-existing drift between current-code regeneration and the committed
artifacts (documented in `docs/START_HERE.md`); this change neither adds to nor removes any of it. No
generated file is committed here.

Comparison script: `compare.py` in this directory (`python compare.py <clone-of-main> <clone-of-branch>`).
