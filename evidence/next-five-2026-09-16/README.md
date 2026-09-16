# Five follow-up tasks — 2026-09-16

Branch `task/next-five-20260916` from main `c8bbaf4`. Owner instruction (2026-09-16): do all five, including the
Study A criterion-iii amendment; deliver as a PR for review. Environment as in the observability-program evidence.

## 1. Renderer escape fix (PV-R05)
Cause: `inline()` in `scripts/make_preprint_pdf.py` ran the emphasis regexes before honouring `\*`, so an escaped
asterisk paired with a later lone one (five artifacts in §4.4–4.5 of the 2026-09-15 preview). Fix: escapes are
protected with placeholders before any regex and restored last. `InlineEscapeTests` (3 assertions) covers the
τ\*/\*T\*\* pattern, table cells and `\[ \]`. Re-render from the clean commit `aac842f`:
`python -m scripts.make_preprint_pdf --source docs/preprint_v1_4_candidate.md --output build/day4/preprint_v1_4_candidate_r2.pdf`
→ exit 0; arXiv gate exit 0; pypdf text scan: **0 backslashes**, "τ* = 0.05" and "T* = 2,700" present; page 7
rasterised and inspected. Archive `6a6681fe…` and readiness record `6b58769b…` unchanged; `author_approval: null`.

| artifact | SHA-256 |
|---|---|
| **`build/day4/preprint_v1_4_candidate_r2.pdf`** (11 pages) | **`0345c5dc457a8c3892df91f93d11d3eabc27546c8ebc5837d2bde4a288f20a7c`** |
| its manifest | `4eadf1525e750d93de5fca83bb835aebd8d1f10aba6c9e1d00bcef0312c813a7` |
| renderer `scripts/make_preprint_pdf.py` | `90692bb479171cee42f601c226077a9f800a9c8e2e6827be20a083b92cc6cd68` at `aac842f`, clean |
| source | `d700684b…` (= readiness pin) |

The earlier preview (`74644886…`) is superseded for any exact-bytes decision; nothing under `build/` is committed,
nothing is approved, PV-08 unchanged.

## 2. Database pass for the novelty check (PV-OBS-01)
Three IEEE Xplore–restricted searches, graded and appended to `docs/reviews/novelty-check-2026-09-16.md`: no hit on
identifiability of a latent fatigue state from pressure-only features under dispersion or on unseen-unit transfer;
the method anchor (Boyacıoğlu & van Breugel) has an IEEE journal version. **Scopus not searched** (institutional
login); the owner runs the same three queries before any submission.

## 3–4. Study A amendment (PV-OBS-A2, owner) and Study C (PV-OBS-C)
Amendment text in the Study A preregistration; `run_studyA` now records `verdict` (preregistered rule, still
`A-FAIL`) and `verdict_amended_2026_09_16` (`A-PASS`); rerun 2026-09-16, all numbers unchanged. Study C's design
was fixed in an amendment section **before** its first run (probe schedule in cycles; ridge on baseline-normalised
features + lag + clock; clock-only, per-unit-calibration and oracle baselines; 200-unit adversarial draw).
Result: see the Study C section below.

## 5. Cleanup (PV-H01)
Removed `docs/report.md`, six `data/results/*.json`, `data/fields.yaml`, `data/outline.yaml` (portfolio-wide
deep-research artifacts, referenced only in prose of `REVISION_PLAN.md`). Repo-wide local-link check and the
presentation checks pass after removal.

## Study C result (PV-OBS-C) — `python -m scripts.run_studyC`, 3.7 min, seed 20260916, 20 train / 10 held-out units

**Verdict under the amended-but-fixed rule: `C-FAIL`** — 6 of 10 held-out units within u-RMSE 0.10 (rule ≥ 8) and
7 of 10 below the clock-only baseline (rule ≥ 8). Mean held-out u-RMSE 0.093 (clock-only 0.123); actuator-cluster
bootstrap [0.064, 0.131]; leave-one-unit-out range [0.079, 0.099]; ridge λ = 1.0 (LOO scores 0.0919 / 0.0915 / 0.0911
for 0.01 / 0.1 / 1, i.e. insensitive).

| held-out unit (rupture cycles, onset) | probes | transferred | clock-only | pre-/post-onset |
|---|---|---|---|---|
| 4165, 0.60 | 17 | 0.061 | 0.074 | 0.057 / 0.067 |
| **1416, 0.78** | 6 | **0.227** | 0.362 | 0.248 / 0.015 |
| **2205, 0.74** | 9 | **0.130** | 0.227 | 0.146 / 0.044 |
| **2471, 0.72** | 10 | **0.131** | 0.183 | 0.106 / 0.176 |
| 3671, 0.67 | 15 | 0.056 | **0.007** | 0.044 / 0.075 |
| 3857, 0.67 | 16 | 0.054 | **0.034** | 0.062 / 0.033 |
| 4248, 0.60 | 17 | 0.080 | 0.085 | 0.055 / 0.107 |
| 4121, 0.65 | 17 | 0.041 | 0.069 | 0.049 / 0.023 |
| 3930, 0.61 | 16 | 0.053 | **0.045** | 0.064 / 0.027 |
| 4775, 0.74 | 19 | 0.101 | 0.140 | 0.081 / 0.142 |

Reading: the estimator transfers, and it beats the clock exactly where the clock is wrong — units whose rupture
life is far from the training median (the three short-lived units, and the 4775-cycle unit) — but on the
short-lived units it is still 0.13–0.23 life off, because most of their probes fall pre-onset where (Study B) the
features carry little unit-specific information about u and the clock's rupture prior dominates. On units near
the median life the clock alone is as good or better. Per-unit calibration on the unit's own first three probes
(u ≈ 0.02–0.2, true labels) is 0.41–0.53: three early probes do not span the target and extrapolate poorly, so this
baseline, as specified, is not an upper bound in practice and is reported as such. Adversarial draw (200 units,
seed 20260918): worst u-RMSE 0.222 (clock 0.407) on a 987-cycle unit; 57.5 % of the 200 within target.

Consequence: the transfer claim is not supported at the preregistered bar on this generator; the information the
pressure features add is concentrated post-onset and in atypical-life units. No re-tuning was done after seeing
held-out results. Outputs `data/sim/studyC/studyC_results.json`, `studyC_fig_transfer.(png|pdf)`; declared in the
figure manifest.

## Checks (final)
`pytest -q` all passed (count in the PR) · numbers 0 · arXiv 0 (historical) and 0 (r2 preview) · fallback 0 /
`--for-publication` 2 · presentation 0 / 4 passed · repo-wide local links resolve · `git diff --check` clean.
