# PhD program — Studies A and B execution evidence (2026-09-16)

Branch `research/phd-program-20260916` from main `151683b`. Preregistration commit **`e0543be`** (novelty
check, program, Study A/B/C specs) precedes the generator change (`6e82307`) and every run below.
Environment: Python 3.11.8; numpy 2.4.6, scipy 1.17.1, matplotlib 3.11.2; `MPLBACKEND=Agg`.

## PV-PHD-00 — novelty check
[docs/reviews/novelty-check-2026-09-16.md](../../docs/reviews/novelty-check-2026-09-16.md): 6 searches + the
60-entry literature base; two full texts fetched; claim ledger with graded evidence. Verdict: the identifiability
and unseen-unit-transfer question is open within retrieved evidence; a Scopus/IEEE Xplore pass is still required.

## Generator change and byte identity
`FatigueParams.fatigue_exponent` (default 2.0) replaces the hard-coded square in the accelerating term. A
test asserts the canonical law is reproduced exactly. Byte identity of all committed generators: see the
"Regeneration" section at the end (filled after the background run).

## PV-PHD-A — Study A (`python -m scripts.run_studyA`, 51 s, seed 20260916, N = 30 units, 19 stages, 5 repeats)

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
