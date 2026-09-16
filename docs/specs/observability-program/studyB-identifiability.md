# Study B — observability / identifiability of the latent fatigue state (preregistration)

Committed before the run. Method anchor: Fisher information matrices as observability Gramians bounding
estimator error through Cramér–Rao (Boyacıoğlu & van Breugel 2024, arXiv:2410.19975).

## Latent state and nuisance

Latent coordinate: **u**, normalised life of the generator (the mechanism multipliers c(u) compliance,
l(u) loss, g(u) leak are deterministic functions of u for a given unit). Nuisance ν, unknown per unit
unless stated: (k1₀, k2₀, τ, terminal_leak_multiplier, acceleration_onset_fraction, fatigue_exponent).
Everything else canonical.

## Pressure-only feature vector y(u, ν) (5 features)

1. loop area at 1 Hz; 2. loop area at 4 Hz (rate dependence); 3. secant stiffness of the 1 Hz loop,
(P_max − P_min)/(V_max − V_min); 4. pressure-decay half-life of a closed-inlet hold from 40 kPa
(`simulate_pressure_decay`, leak through R_l/g); 5. residual pressure fraction at 0.3 s of the same decay.
Probe amplitude 0.1·V₀ unless swept.

## Information and bounds

J = ∂y/∂(u, ν) by central finite differences (relative step 1e-3). Σ = feature noise covariance from
K = 24 seeded sensor-model repeats at the operating point. FIM = Jᵀ Σ⁻¹ J. Three conditions:

- **B1 single snapshot, ν unknown**: expected structurally singular (k1₀/c and k2₀·l enter only as
  products); report rank and the null-space directions.
- **B2 snapshot + young baseline of the same unit (u₁ = 0.05)**: stacked 10-feature vector; report
  CRLB σ_u = sqrt([FIM⁺]_uu) with rank check.
- **B3 ν known (oracle)**: σ_u = 1/sqrt(FIM_uu).

Aliasing: for each nuisance ν_j the angle between ∂y/∂u and ∂y/∂ν_j in the Σ^-1/2-whitened metric; the
smallest angle names the most confounded mechanism (prediction: leak, since only features 4–5 see it).

## Envelope

u ∈ {0.1, 0.2, …, 0.9} × noise scale {0.5, 1, 4} × probe amplitude {0.05, 0.1, 0.2}·V₀, evaluated on
the canonical unit and on 5 dispersed units from the Study A cohort (seeds 0–4).

## Verdict rules (fixed now)

- Resolution target: σ_u ≤ 0.10 life (two Study A grid steps).
- **B-PASS**: under B2 at noise scale 1 and amplitude 0.1, σ_u ≤ 0.10 for ≥ 50 % of u-points, on the
  canonical unit and on ≥ 3 of the 5 dispersed units.
- **B-KILL**: under B2, σ_u > 0.25 for ≥ 50 % of the envelope points → the pressure-only thesis is dead
  on this generator; report.
- Otherwise **B-CONDITIONAL**: report the identifiable region as the map.

## Outputs

`data/sim/studyB/studyB_results.json`, `studyB_fig_identifiability_map.png/.pdf` via
`python -m scripts.run_studyB`. Tests: FIM of a linear toy model equals the analytic value; singular
condition detected; whitened angle of an orthogonal pair is 90°.
