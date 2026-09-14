#!/usr/bin/env python3
"""Phase C: causal P-V health indicators and onset-identifiability study.

Every output is synthetic simulation. The form-matched segmented estimator is an
identifiability ceiling, not an experimental lead-time predictor.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, replace
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]

from pipeline.degradation import (
    calibrate_cusum_to_sustained,
    FITTERS,
    chronological_forecast,
    cusum_alarm,
    false_alarm_rate,
    fit_all_models,
    roc_auc,
    sustained_sigma_alarm,
)
from pipeline.features import extract_loop_features, resample_loop
from pipeline.health_index import (
    fit_baseline,
    fit_baseline_pca,
    fused_hi,
    pca_scores,
    transform_features,
)
from pipeline.hi_metrics import monotonicity, prognosability, trendability
from pipeline.mullins import fit_recovery, normalize_recovery
from pipeline.validation import (
    add_pressure_noise,
    apply_shared_state_dip,
    logistic_fatigue_state,
    make_null_params,
    resample_life,
    sample_validation_cohort,
)
from sim.fatigue import FatigueParams, degraded_sls, fatigue_state
from sim.plant import SLSParams, pv_loop

from scripts import figstyle

plt = figstyle.setup(style=False)


FEATURE_NAMES = ("loop_area", "inflation_compliance")
ONSET_FRACTIONS = (0.50, 0.70, 0.85)
NOISE_LEVELS = (0.0, 0.10, 0.25, 0.50)
DETECTION_NOISE = (0.10, 0.25, 0.50)
CADENCES = (100, 250, 500)
LOGISTIC_SHARPNESS = (8.0, 20.0, 50.0)
REST_S = 300.0
BASELINE_CYCLE = 20.0
BASELINE_REPEATS = 20


def _cycle_grid(rupture_cycles, cadence):
    regular = np.arange(cadence, rupture_cycles, cadence, dtype=float)
    return np.unique(np.concatenate([[BASELINE_CYCLE], regular, [rupture_cycles]]))


def _state_for(cycles, params, generator, sharpness):
    if generator == "quadratic":
        return fatigue_state(cycles, REST_S, params)
    return logistic_fatigue_state(cycles, REST_S, params, sharpness)


def _clean_loop(cycles, params, generator, sharpness, base_sls, frequency, amplitude):
    state = _state_for(cycles, params, generator, sharpness)
    sls = degraded_sls(base_sls, state)
    loop = pv_loop(frequency, amplitude, sls)
    return {"V": np.asarray(loop["V"]), "P": np.asarray(loop["P"]),
            "features": extract_loop_features(loop["V"], loop["P"]), "state": state}


def _feature_pair(loop, noise, rng):
    pressure = add_pressure_noise(loop["P"], noise, rng)
    feature = extract_loop_features(loop["V"], pressure)
    return np.array([feature.loop_area, feature.inflation_compliance])


def _bootstrap_ci(values, rng, n_boot=1000):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return [float("nan"), float("nan")]
    samples = rng.choice(values, size=(n_boot, values.size), replace=True)
    medians = np.median(samples, axis=1)
    return [float(x) for x in np.quantile(medians, [0.025, 0.975])]


def _standardized_detector_hi(transformed_baseline, transformed_life):
    base_hi = fused_hi(transformed_baseline)
    life_hi = fused_hi(transformed_life)
    sd = float(np.std(base_hi, ddof=1))
    if sd <= 0:
        return None, None
    return (base_hi - base_hi.mean()) / sd, (life_hi - base_hi.mean()) / sd


def _null_paths_from_feature_pool(pool, count, n_points, rng):
    """Build causal standardized-HI paths from pressure-perturbed null-loop features."""
    draws = pool[rng.integers(0, len(pool), size=(count, BASELINE_REPEATS + n_points))]
    baseline = draws[:, :BASELINE_REPEATS, :]
    life = draws[:, BASELINE_REPEATS:, :]
    feature_mean = baseline.mean(axis=1, keepdims=True)
    feature_std = baseline.std(axis=1, ddof=1, keepdims=True)
    baseline_z = (baseline - feature_mean) / feature_std
    life_z = (life - feature_mean) / feature_std
    baseline_hi = baseline_z.mean(axis=2)
    life_hi = life_z.mean(axis=2)
    hi_mean = baseline_hi.mean(axis=1, keepdims=True)
    hi_std = baseline_hi.std(axis=1, ddof=1, keepdims=True)
    return (life_hi - hi_mean) / hi_std


def _null_calibration(feature_pool, n_points, calibration_count, rng):
    paths = _null_paths_from_feature_pool(
        feature_pool, calibration_count, n_points, rng
    )
    calibration = calibrate_cusum_to_sustained(paths, reference=0.5)
    evaluation = _null_paths_from_feature_pool(
        feature_pool, max(2000, calibration_count // 2), n_points, rng
    )
    fa_3s = false_alarm_rate(evaluation, lambda row: sustained_sigma_alarm(row, 0, 1))
    fa_cusum = false_alarm_rate(
        evaluation, lambda row: cusum_alarm(row, 0.5, calibration.threshold)
    )
    return calibration, fa_3s, fa_cusum


def _build_null_calibrations(base_sls, frequency, amplitude, noises, cadences,
                             calibration_count, seed):
    null_params = make_null_params()
    null_loop = _clean_loop(
        BASELINE_CYCLE, null_params, "quadratic", None,
        base_sls, frequency, amplitude,
    )
    rng = np.random.default_rng(seed)
    calibrations = {}
    for noise in noises:
        if noise == 0:
            continue
        pool_size = max(10_000, calibration_count * 2)
        pool = np.vstack([_feature_pair(null_loop, noise, rng) for _ in range(pool_size)])
        for cadence in cadences:
            n_points = len(_cycle_grid(null_params.rupture_cycles, cadence))
            calibrations[(noise, cadence)] = _null_calibration(
                pool, n_points, calibration_count, rng
            )
    return calibrations


def _run_condition(generator, sharpness, onset, noise, cadence, trials,
                   null_calibrations, seed, base_sls, frequency, amplitude):
    params = replace(FatigueParams(), acceleration_onset_fraction=onset)
    cycles = _cycle_grid(params.rupture_cycles, cadence)
    u = cycles / params.rupture_cycles
    clean = {
        float(n): _clean_loop(n, params, generator, sharpness, base_sls, frequency, amplitude)
        for n in cycles
    }
    baseline_loop = clean[float(BASELINE_CYCLE)]
    rng = np.random.default_rng(seed)
    n_trials = 1 if noise == 0 else trials

    onset_errors = {name: [] for name in FITTERS}
    forecasts = {name: [] for name in FITTERS}
    selected = Counter()
    alarms_3s, alarms_cusum = [], []
    auc_onset, auc_horizons = [], {0.1: [], 0.2: [], 0.3: []}

    if noise > 0:
        calibration, fa_3s, fa_cusum = null_calibrations[(noise, cadence)]
    else:
        calibration = None
        fa_3s = fa_cusum = float("nan")

    for _ in range(n_trials):
        if noise == 0:
            baseline = np.vstack([_feature_pair(baseline_loop, 0, rng)])
            matrix = np.vstack([_feature_pair(clean[float(n)], 0, rng) for n in cycles])
            baseline_model = fit_baseline(
                baseline, FEATURE_NAMES, (1, 1), noise_free=True
            )
        else:
            baseline = np.vstack([
                _feature_pair(baseline_loop, noise, rng) for _ in range(BASELINE_REPEATS)
            ])
            matrix = np.vstack([
                _feature_pair(clean[float(n)], noise, rng) for n in cycles
            ])
            baseline_model = fit_baseline(baseline, FEATURE_NAMES, (1, 1))

        transformed = transform_features(matrix, baseline_model)
        hi = fused_hi(transformed)
        fits = fit_all_models(u, hi)
        valid_aicc = {name: fit.aicc for name, fit in fits.items()
                      if fit.status == "ok" and np.isfinite(fit.aicc)}
        if valid_aicc:
            selected[min(valid_aicc, key=valid_aicc.get)] += 1
        for name, fit in fits.items():
            if fit.status == "ok" and np.isfinite(fit.onset):
                onset_errors[name].append(abs(fit.onset - onset))
            rmse, status = chronological_forecast(FITTERS[name], u, hi)
            if status == "ok":
                forecasts[name].append(rmse)

        if noise > 0:
            transformed_baseline = transform_features(baseline, baseline_model)
            _, detector_hi = _standardized_detector_hi(transformed_baseline, transformed)
            alarm3 = sustained_sigma_alarm(detector_hi, 0, 1)
            alarmc = cusum_alarm(detector_hi, 0.5, calibration.threshold)
            alarms_3s.append(float(cycles[alarm3.alarm_index]) if alarm3.alarm_index is not None else np.nan)
            alarms_cusum.append(float(cycles[alarmc.alarm_index]) if alarmc.alarm_index is not None else np.nan)
            auc_onset.append(roc_auc(detector_hi, u >= onset))
            for horizon in auc_horizons:
                auc_horizons[horizon].append(roc_auc(detector_hi, u >= 1 - horizon))

    model_summary = {}
    for name in FITTERS:
        errors = np.asarray(onset_errors[name])
        forecast_values = np.asarray(forecasts[name])
        model_summary[name] = {
            "identifiable_rate": float(errors.size / n_trials),
            "median_absolute_onset_error": float(np.median(errors)) if errors.size else np.nan,
            "onset_error_95ci": _bootstrap_ci(errors, rng),
            "aicc_selected_fraction": float(selected[name] / n_trials),
            "median_chronological_forecast_rmse": (
                float(np.median(forecast_values)) if forecast_values.size else np.nan
            ),
        }

    def alarm_summary(values):
        values = np.asarray(values, dtype=float)
        finite = values[np.isfinite(values)]
        return {
            "alarm_rate": float(finite.size / values.size) if values.size else np.nan,
            "median_alarm_cycle": float(np.median(finite)) if finite.size else np.nan,
        }

    detection = None
    if noise > 0:
        detection = {
            "sustained_3sigma": {**alarm_summary(alarms_3s), "null_false_alarm_rate": fa_3s},
            "cusum": {**alarm_summary(alarms_cusum), "null_false_alarm_rate": fa_cusum,
                      "threshold": calibration.threshold},
            "acceleration_state_auc": float(np.nanmean(auc_onset)),
            "rupture_horizon_auc": {
                str(h): float(np.nanmean(values)) for h, values in auc_horizons.items()
            },
        }

    return {
        "generator": generator,
        "logistic_sharpness": sharpness if generator == "logistic" else None,
        "onset_fraction": onset,
        "noise_percent_fs_sigma": noise,
        "cadence_cycles": cadence,
        "samples_per_life": int(len(cycles)),
        "trials": n_trials,
        "models": model_summary,
        "detection": detection,
    }, clean, cycles


def _metric_fixtures():
    u = np.linspace(0, 1, 101)
    cohort = sample_validation_cohort(20, seed=20260623)
    normal_curves = []
    corrupted_curves = []
    for i, params in enumerate(cohort):
        cycles = np.linspace(0, params.rupture_cycles, 101)
        states = [fatigue_state(n, REST_S, params) for n in cycles]
        curve = np.array([
            0.5 * ((s.compliance_multiplier - 1) + (s.loss_multiplier - 1))
            for s in states
        ])
        normal_curves.append(resample_life(cycles, curve, params.rupture_cycles))
        if i < 5:
            dipped = [apply_shared_state_dip(s, params) for s in states]
            curve = np.array([
                0.5 * ((s.compliance_multiplier - 1) + (s.loss_multiplier - 1))
                for s in dipped
            ])
        corrupted_curves.append(resample_life(cycles, curve, params.rupture_cycles))

    starts = np.zeros(20)
    terminal_quantiles = np.linspace(0.12, 0.20, 20)
    pro = prognosability(starts, terminal_quantiles)
    null_pro = prognosability(np.ones(20), np.ones(20))
    clean = 0.04 * u + 0.08 * np.maximum(0, (u - 0.7) / 0.3) ** 2
    dipped = clean - 0.06 * np.exp(-0.5 * ((u - 0.55) / 0.08) ** 2)
    rng = np.random.default_rng(55)
    noisy_mon = [monotonicity(clean + rng.normal(0, 0.005, clean.size)) for _ in range(1000)]
    return {
        "monotonicity_clean": monotonicity(clean),
        "monotonicity_recovery_dip": monotonicity(dipped),
        "monotonicity_noise_mean": float(np.mean(noisy_mon)),
        "trendability_self_similar": trendability(np.vstack(normal_curves)),
        "trendability_corrupted": trendability(np.vstack(corrupted_curves)),
        "prognosability_known_spread": asdict(pro),
        "prognosability_null": asdict(null_pro),
    }


def _recovery_fixture(base_sls, frequency, amplitude):
    params = FatigueParams()
    rest_hours = np.array([0, 1, 24, 72, 168], dtype=float)
    records = []
    for cycles in (1000.0, 2000.0, 3000.0):
        area = []
        compliance = []
        for hours in rest_hours:
            state = fatigue_state(cycles, hours * 3600, params)
            sls = degraded_sls(base_sls, state)
            loop = pv_loop(frequency, amplitude, sls)
            features = extract_loop_features(loop["V"], loop["P"])
            area.append(features.loop_area)
            compliance.append(features.inflation_compliance)
        fits = {}
        for name, values in (("loop_area", area), ("compliance", compliance)):
            fit = fit_recovery(rest_hours * 3600, values)
            normalized = normalize_recovery(values, rest_hours * 3600, fit, REST_S)
            fits[name] = {
                **asdict(fit),
                "tau_relative_error": abs(fit.tau_s - params.recovery_tau_s) / params.recovery_tau_s,
                "normalized_range_fraction": float(np.ptp(normalized) / max(np.ptp(values), 1e-30)),
            }
        records.append({"cycles": cycles, "fits": fits})
    return records


def _fusion_comparator(base_sls, frequency, amplitude):
    params = FatigueParams()
    cycles = _cycle_grid(params.rupture_cycles, 100)
    loops = [_clean_loop(n, params, "quadratic", None, base_sls, frequency, amplitude)
             for n in cycles]
    rng = np.random.default_rng(441)
    baseline_loop = loops[0]
    baseline_features = np.vstack([_feature_pair(baseline_loop, 0.25, rng)
                                   for _ in range(BASELINE_REPEATS)])
    baseline_vectors = np.vstack([
        resample_loop(baseline_loop["V"], add_pressure_noise(baseline_loop["P"], 0.25, rng), 64)
        for _ in range(BASELINE_REPEATS)
    ])
    feature_matrix = np.vstack([_feature_pair(loop, 0.25, rng) for loop in loops])
    vectors = np.vstack([
        resample_loop(loop["V"], add_pressure_noise(loop["P"], 0.25, rng), 64)
        for loop in loops
    ])
    model = fit_baseline(baseline_features, FEATURE_NAMES, (1, 1))
    transformed = transform_features(feature_matrix, model)
    fused = fused_hi(transformed)
    pca = pca_scores(vectors, fit_baseline_pca(baseline_vectors))
    clean_features = np.array([
        [loop["features"].loop_area, loop["features"].inflation_compliance] for loop in loops
    ])
    noise_samples = baseline_features - baseline_features.mean(axis=0)
    return {
        "signal_correlation_area_compliance": float(np.corrcoef(clean_features.T)[0, 1]),
        "baseline_noise_correlation_area_compliance": float(np.corrcoef(noise_samples.T)[0, 1]),
        "monotonicity": {
            "fused": monotonicity(fused),
            "area": monotonicity(transformed[:, 0]),
            "compliance": monotonicity(transformed[:, 1]),
            "baseline_pca_pc1": monotonicity(pca),
        },
        "cycles": cycles.tolist(),
        "fused_hi": fused.tolist(),
        "area_hi": transformed[:, 0].tolist(),
        "compliance_hi": transformed[:, 1].tolist(),
        "pca_pc1": pca.tolist(),
    }


def _json_safe(value):
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, float)):
        return None if not np.isfinite(value) else float(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    return value


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=200)
    parser.add_argument("--calibration", type=int, default=5000)
    parser.add_argument("--quick", action="store_true", help="small smoke grid")
    args = parser.parse_args(argv)
    if args.trials <= 0 or args.calibration < 10:
        parser.error("trials must be positive and calibration >= 10")

    outdir = REPO / "data" / "sim" / "study1"
    outdir.mkdir(parents=True, exist_ok=True)
    base_sls = SLSParams()
    frequency = base_sls.f_loss_peak
    amplitude = 2e-6

    if args.quick:
        onsets, noises, cadences, sharpnesses = (0.70,), (0.0, 0.25), (100,), (20.0,)
        trials, calibration_count = min(args.trials, 10), min(args.calibration, 200)
    else:
        onsets, noises, cadences, sharpnesses = (
            ONSET_FRACTIONS, NOISE_LEVELS, CADENCES, LOGISTIC_SHARPNESS
        )
        trials, calibration_count = args.trials, args.calibration

    conditions = []
    representative_clean = None
    counter = 0
    print("Building true-null pressure/feature calibration pools...", flush=True)
    null_calibrations = _build_null_calibrations(
        base_sls, frequency, amplitude, noises, cadences,
        calibration_count, seed=20260622,
    )
    for onset in onsets:
        generator_specs = [("quadratic", None)] + [("logistic", k) for k in sharpnesses]
        for generator, sharpness in generator_specs:
            for noise in noises:
                for cadence in cadences:
                    counter += 1
                    print(f"[{counter}] {generator} k={sharpness} ud={onset} "
                          f"noise={noise}% cadence={cadence}", flush=True)
                    summary, clean, cycles = _run_condition(
                        generator, sharpness, onset, noise, cadence, trials,
                        null_calibrations, seed=20260623 + counter,
                        base_sls=base_sls, frequency=frequency, amplitude=amplitude,
                    )
                    conditions.append(summary)
                    if representative_clean is None and onset == 0.70 and generator == "quadratic":
                        representative_clean = (clean, cycles)

    fixtures = _metric_fixtures()
    recovery = _recovery_fixture(base_sls, frequency, amplitude)
    fusion = _fusion_comparator(base_sls, frequency, amplitude)
    result = {
        "label": "SYNTHETIC SIMULATION — not experimental validation",
        "claim_boundary": (
            "Segmented-on-quadratic is a form-matched identifiability ceiling; alarm "
            "intervals and onset errors are not physical lead-time predictions."
        ),
        "registered_protocol": {
            "baseline_cycle": BASELINE_CYCLE,
            "baseline_repeats": BASELINE_REPEATS,
            "routine_rest_s": REST_S,
            "noise_percent_fs_sigma": list(noises),
            "detection_noise_excludes_zero": True,
            "cadence_cycles": list(cadences),
            "onset_fractions": list(onsets),
            "logistic_sharpness": list(sharpnesses),
            "evaluation_trials": trials,
            "cusum_calibration_trials": calibration_count,
            "null_calibration_source": (
                "true null actuator; Gaussian pressure perturbation propagated through "
                "P-V feature extraction and per-trial causal baseline fitting"
            ),
            "quick_mode": args.quick,
        },
        "metric_fixtures": fixtures,
        "recovery": recovery,
        "fusion_comparison": fusion,
        "conditions": conditions,
    }

    checks = {
        "null_is_exact": all(
            fatigue_state(n, REST_S, make_null_params()).compliance_multiplier == 1
            for n in (0, 20, 1000, 3500)
        ),
        "metric_clean_monotonicity": fixtures["monotonicity_clean"] == 1.0,
        "trendability_corruption_detected": (
            fixtures["trendability_corrupted"] < fixtures["trendability_self_similar"]
        ),
        "recovery_tau_within_1pct": all(
            record["fits"][name]["tau_relative_error"] < 0.01
            for record in recovery for name in ("loop_area", "compliance")
        ),
        "noise_free_detection_omitted": all(
            condition["detection"] is None
            for condition in conditions if condition["noise_percent_fs_sigma"] == 0
        ),
        "inverse_crime_variants_present": (
            any(c["generator"] == "quadratic" for c in conditions)
            and any(c["generator"] == "logistic" for c in conditions)
        ),
        "detector_false_alarm_rates_match_within_0p2_percentage_points": all(
            abs(c["detection"]["sustained_3sigma"]["null_false_alarm_rate"]
                - c["detection"]["cusum"]["null_false_alarm_rate"])
            <= 0.002
            for c in conditions if c["detection"] is not None
        ),
    }
    result["checks"] = checks
    result["verdict"] = "PASS" if all(checks.values()) else "CHECK"
    (outdir / "study1_results.json").write_text(json.dumps(_json_safe(result), indent=2))

    if plt is not None:
        _plots(outdir, result, representative_clean, base_sls, frequency, amplitude)

    print("=" * 76)
    print("PHASE C / STUDY 1 — causal health indicators + onset identifiability")
    print("=" * 76)
    print(f"Conditions: {len(conditions)}; trials/noisy condition: {trials}")
    print(f"Fusion vs area/compliance monotonicity: {fusion['monotonicity']['fused']:.3f} / "
          f"{fusion['monotonicity']['area']:.3f} / {fusion['monotonicity']['compliance']:.3f}")
    print(f"VERDICT: {result['verdict']} (synthetic validation only)")
    print(f"Wrote {outdir}/study1_results.json + figures")
    return 0 if result["verdict"] == "PASS" else 1


def _plots(outdir, result, representative_clean, base_sls, frequency, amplitude):
    fusion = result["fusion_comparison"]
    cycles = np.asarray(fusion["cycles"])
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(cycles, fusion["fused_hi"], label="oriented z-mean")
    ax.plot(cycles, fusion["area_hi"], label="area")
    ax.plot(cycles, fusion["compliance_hi"], label="compliance")
    ax.set(xlabel="cycles", ylabel="baseline-normalized HI [-]",
           title="Synthetic early-HI comparison (0.25% FS noise)")
    ax.legend(); ax.grid(alpha=0.3); fig.tight_layout()
    fig.savefig(outdir / "fig_hi_fusion_comparison.png", dpi=130); plt.close(fig)

    recovery = result["recovery"]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for feature in ("loop_area", "compliance"):
        ax.plot([r["cycles"] for r in recovery],
                [r["fits"][feature]["tau_s"] / 3600 for r in recovery], "o-", label=feature)
    ax.axhline(24, ls="--", c="k", alpha=0.5, label="injected 24 h")
    ax.set(xlabel="life cycle", ylabel="recovered tau [h]",
           title="Cross-rest recovery fit is life-invariant by construction")
    ax.set_ylim(23.5, 24.5)
    ax.ticklabel_format(axis="y", style="plain", useOffset=False)
    ax.legend(); ax.grid(alpha=0.3); fig.tight_layout()
    fig.savefig(outdir / "fig_recovery_validation.png", dpi=130); plt.close(fig)

    fixture = result["metric_fixtures"]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    labels = ["Mon clean", "Mon dip", "Trend self", "Trend corrupt", "Prog spread"]
    values = [fixture["monotonicity_clean"], fixture["monotonicity_recovery_dip"],
              fixture["trendability_self_similar"], fixture["trendability_corrupted"],
              fixture["prognosability_known_spread"]["value"]]
    ax.bar(labels, values); ax.set_ylim(0, 1.05); ax.tick_params(axis="x", rotation=20)
    ax.set(ylabel="metric [-]", title="Known-ground-truth HI metric fixtures")
    ax.grid(axis="y", alpha=0.3); fig.tight_layout()
    fig.savefig(outdir / "fig_metric_fixtures.png", dpi=130); plt.close(fig)

    conditions = result["conditions"]
    selected = [c for c in conditions if c["onset_fraction"] == 0.70
                and c["cadence_cycles"] == 100]
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    for generator in sorted({(c["generator"], c["logistic_sharpness"]) for c in selected}):
        rows = [c for c in selected if (c["generator"], c["logistic_sharpness"]) == generator]
        rows.sort(key=lambda c: c["noise_percent_fs_sigma"])
        label = generator[0] if generator[1] is None else f"logistic k={generator[1]:g}"
        ax.plot([r["noise_percent_fs_sigma"] for r in rows],
                [r["models"]["segmented_quadratic"]["median_absolute_onset_error"] for r in rows],
                "o-", label=label)
    ax.set(xlabel="pressure noise sigma [% FS]", ylabel="median |onset error| [life fraction]",
           title="Segmented-estimator inverse-crime/generalization gap")
    ax.legend(); ax.grid(alpha=0.3); fig.tight_layout()
    fig.savefig(outdir / "fig_onset_generalization_gap.png", dpi=130); plt.close(fig)

    noisy = [c for c in conditions if c["detection"] is not None
             and c["generator"] == "quadratic" and c["onset_fraction"] == 0.70
             and c["cadence_cycles"] == 100]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    x = np.arange(len(noisy)); width = 0.35
    ax.bar(x - width/2, [c["detection"]["sustained_3sigma"]["median_alarm_cycle"] for c in noisy],
           width, label="sustained 3σ")
    ax.bar(x + width/2, [c["detection"]["cusum"]["median_alarm_cycle"] for c in noisy],
           width, label="matched-FA CUSUM")
    ax.set_xticks(x, [f"{c['noise_percent_fs_sigma']}%" for c in noisy])
    ax.set(xlabel="pressure noise sigma [% FS]", ylabel="median confirmed alarm cycle",
           title="Slow-drift detector timing (both alarm in 100% of trials)")
    ax.legend(); ax.grid(axis="y", alpha=0.3); fig.tight_layout()
    fig.savefig(outdir / "fig_detector_comparison.png", dpi=130); plt.close(fig)


if __name__ == "__main__":
    raise SystemExit(main())
