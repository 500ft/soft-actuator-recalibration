# Observability program — Studies A and B execution evidence (2026-09-16)

Branch `research/observability-program-20260916` from main `151683b`. Preregistration commit **`9e71a3f`** (novelty
check, program, Study A/B/C specs) precedes the generator change (`e828596`) and every run below.
Environment: Python 3.11.8; numpy 2.4.6, scipy 1.17.1, matplotlib 3.11.2; `MPLBACKEND=Agg`.

## PV-OBS-00 — novelty check
[docs/reviews/novelty-check-2026-09-16.md](../../docs/reviews/novelty-check-2026-09-16.md): 6 searches + the
60-entry literature base; two full texts fetched; claim ledger with graded evidence. Verdict: the identifiability
and unseen-unit-transfer question is open within retrieved evidence; a Scopus/IEEE Xplore pass is still required.

## Generator change and byte identity
`FatigueParams.fatigue_exponent` (default 2.0) replaces the hard-coded square in the accelerating term. A
test asserts the canonical law is reproduced exactly. Byte identity of all committed generators: see the
"Regeneration" section at the end (filled after the background run).

## PV-OBS-A — Study A (`python -m scripts.run_studyA`, 51 s, seed 20260916, N = 30 units, 19 stages, 5 repeats)

**Verdict under the preregistered rules: `A-FAIL`** (criteria i and ii pass; criterion iii fails).

| criterion (preregistered) | threshold | observed | pass? |
|---|---|---|---|
| ideal SD_between at end of life (degeneracy check) | ≥ 1e-6 | 0.0141 at u = 0.95 | not degenerate |
| (i) median ratio SD_between/SD_within, u ≥ 0.30 | ≥ 2 | **6.71** (2.68 at u = 0.30 → 17.3 at 0.95) | yes |
| (ii) median ICC(1), u ≥ 0.30 | ≥ 0.5 | **0.978** | yes |
| (iii) SD of trigger life at τ = 0.05 across units | ≥ 0.10 | **0.044** (range 0.769–0.928; 0 units never trigger) | **no** |

Reading: assumed dispersion does break the invariance of the *indicator value* (between-unit spread is
5–17× the measurement noise from mid-life on), but the *timing* at the deployed threshold barely spreads:
the normalised loop area only grows 6–11 % over life in this generator, so a 5 % threshold is crossed by
every unit within ~0.16 life. Criterion iii was fixed before the run and is not amended here. Whether a
timing criterion at the deployed τ is the right gate for "the cohort can pose the cross-unit question" is
an owner decision to record as a dated amendment; without it, Study C stays blocked.

One-axis ablation (ideal indicator, SD between units at u = 0.9) — prediction confirmed exactly:

| axis | SD_between | | axis | SD_between |
|---|---|---|---|---|
| none (canonical) | 4.5e-16 | | tau | 7.2e-15 |
| rupture life | 4.2e-13 | | stiffness (k1, k2) | 7.5e-15 |
| Mullins | 7.1e-4 | | wall thickness | 9.6e-15 |
| **fatigue law** (amplitudes, onset, exponent) | **1.31e-2** | | temperature | 9.3e-15 |
| leak | 4.5e-16 | | | |

Only the degradation-law axes move the normalised indicator; plant-level dispersion is cancelled by
young-normalisation (and τ does not evolve with life in this generator). Consequence for Study B/C: the
level information that normalisation discards is exactly what distinguishes units.

Outputs: `data/sim/studyA/studyA_results.json`, `studyA_fig_indicator_spread.(png|pdf)`, `studyA_fig_ablation.(png|pdf)`;
declared in `docs/figure-manifest.json`. Dispersion magnitudes are assumed (see the preregistration table).

## PV-OBS-B — Study B (`python -m scripts.run_studyB`, ~32 min, 486 envelope points, 24 sensor repeats each)

**Verdict under the preregistered rules: `B-PASS`** — B2 (snapshot + young baseline) σ_u ≤ 0.10 for 7/9 u-points on the
canonical unit and for 5/9 to 7/9 on all five dispersed units (rule: ≥ 50 % on canonical and ≥ 3 of 5 dispersed).
Envelope fraction above the kill level 0.31 (rule for B-KILL: ≥ 0.50).

The map has a structure the pass/fail rule does not express, and it is the finding:

| regime (canonical unit, default probe) | B1 single snapshot | B2 + young baseline | B3 nuisance known |
|---|---|---|---|
| u ≤ 0.7 (before the acceleration onset, canonical 0.70) | singular (rank 3 of 4 active parameters: u aliases with k2₀, angle 13–23°) | **σ_u = 0.022–0.029 life**, full rank | 0.013–0.024 |
| u ≥ 0.8 (after onset; leak, onset fraction and exponent become active) | singular (rank 5 of 7) | **singular (rank 6 of 7)** | 2.2e-4–2.4e-4 |

After onset the whitened sensitivity of u is almost parallel to the onset fraction (0.7–0.8°) and to the terminal
leak multiplier (4–8°): the features see "how far past onset" and "how leaky", not u itself, so **the latent life
coordinate is structurally unidentifiable from one probe plus a young baseline once degradation accelerates**, even
though the information is present when the unit's law parameters are known (B3). Before onset it is identifiable to
about two life-grid steps at default noise. Scaling: σ_u ∝ noise / probe amplitude (0.0119 at ×0.5 noise, 0.098 at ×4;
0.047 at 0.05·V₀, 0.012 at 0.2·V₀, u = 0.5). Dispersed units lose identifiability at their own onset (0.6–0.8).

Consequence for Study C: a single-snapshot estimator cannot work post-onset on this generator; C must use trajectory
information (several stages per unit) or accept the pre-onset regime only. Limits: local (Fisher) bounds from
finite-difference sensitivities; a synthetic generator; five features chosen by the preregistration; the B1 curve is
absent from the figure because every B1 point is singular.

Outputs: `data/sim/studyB/studyB_results.json` (all 486 points, ranks, angles), `studyB_fig_identifiability_map.(png|pdf)`;
declared in `docs/figure-manifest.json`.

## Regeneration after the generator change
All nine generators run on a clone of the pre-refactor baseline (`f3a71ff`, equal to main's generator code) and on a
clone of this branch (`e828596`), same venv: **49/50 regenerated files identical** (JSON/PNG by SHA-256, dataset per
array, PDFs modulo timestamps). The one difference is `data/sim/phaseB/phaseB_results.json`, whose
`canonical_parameters` block serialises `FatigueParams` and now carries the added field `"fatigue_exponent": 2.0`;
a key-by-key walk shows **no numeric value changed** in that file. No regenerated file is committed; the committed
artifacts are untouched (they retain the documented current-code drift on both sides).
Comparison script: `evidence/ponytail-2026-09-14/compare.py`.
