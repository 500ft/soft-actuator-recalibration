"""Study A — does between-unit dispersion break the normalised-indicator invariance?

Preregistered in docs/specs/observability-program/studyA-preregistration.md. Writes data/sim/studyA/.
"""

from __future__ import annotations

import json
import os

import numpy as np

from pipeline.dispersion import AXES, SEED, sample_units
from sim.fatigue import degraded_sls, fatigue_state
from sim.plant import first_crossing, loop_area, pv_loop
from sim.sensors import SensorModel, SensorParams
from scripts import figstyle

DATA = "data/sim/studyA"
N_UNITS = 30
LIFE = [round(x, 3) for x in np.arange(0.05, 0.951, 0.05)]
F_PROBE_HZ = 2.0          # fixed: the operator does not know each unit's loss peak
AMP_FRAC = 0.1
TAU_TRIGGER = 0.05
REPEATS = 5


def probe_loop(unit, u):
    fs = fatigue_state(u * unit.fatigue.rupture_cycles, 0.0, unit.fatigue)
    sls = degraded_sls(unit.sls, fs)
    lp = pv_loop(F_PROBE_HZ, AMP_FRAC * sls.V0, sls)
    return lp["V"], lp["P"]


def measured_area(V, P, seed):
    m = SensorModel(SensorParams(), seed).measure(pressure=P, volume=V)
    return loop_area(m["volume"], m["pressure"])


def trajectories(unit, index):
    """(ideal normalised indicator [S], measured normalised indicator [S, R]) for one unit."""
    ideal, meas = [], []
    for s, u in enumerate(LIFE):
        V, P = probe_loop(unit, u)
        ideal.append(loop_area(V, P))
        meas.append([measured_area(V, P, int(np.random.SeedSequence([SEED, index, s, r]).generate_state(1)[0]))
                     for r in range(REPEATS)])
    ideal, meas = np.asarray(ideal), np.asarray(meas)
    return ideal / ideal[0], meas / meas[0].mean()


def spread_metrics(h):
    """h: [units, stages, repeats] -> per-stage between/within SD, ratio, ICC(1)."""
    means = h.mean(axis=2)
    sd_between = means.std(axis=0, ddof=1)
    within_var = h.var(axis=2, ddof=1)
    sd_within = np.sqrt(within_var.mean(axis=0))
    r = h.shape[2]
    ms_b, ms_w = r * means.var(axis=0, ddof=1), within_var.mean(axis=0)
    icc = (ms_b - ms_w) / (ms_b + (r - 1) * ms_w)
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(sd_within > 0, sd_between / sd_within, np.inf)
    return {"sd_between": sd_between, "sd_within": sd_within, "ratio": ratio, "icc": icc}


def verdict(ideal_sd_between_end, ratio, icc, trigger_sd, amended=False):
    """Preregistered rule (criteria i, ii, iii); ``amended=True`` applies the 2026-09-16 owner amendment
    that withdraws criterion iii (see the preregistration's amendment section)."""
    late = np.asarray(LIFE) >= 0.30
    if ideal_sd_between_end < 1e-6:
        return "A-DEGENERATE"
    ok = np.median(ratio[late]) >= 2.0 and np.median(icc[late]) >= 0.5 and (amended or trigger_sd >= 0.10)
    return "A-PASS" if ok else "A-FAIL"


def main():
    units = sample_units(N_UNITS, SEED)
    ideal, meas = zip(*(trajectories(unit, i) for i, unit in enumerate(units)))
    ideal, meas = np.asarray(ideal), np.asarray(meas)                  # [N,S], [N,S,R]
    m = spread_metrics(meas)
    trig = [first_crossing(LIFE, h, 1.0 + TAU_TRIGGER) for h in meas.mean(axis=2)]
    finite = [t for t in trig if t is not None]
    trigger_sd = float(np.std(finite, ddof=1)) if len(finite) > 1 else 0.0
    ideal_sd = ideal.std(axis=0, ddof=1)

    ablation = {}
    for axis in ("none",) + AXES:
        axes = () if axis == "none" else (axis,)
        ab = np.asarray([trajectories(u, i)[0] for i, u in enumerate(sample_units(N_UNITS, SEED, axes))])
        ablation[axis] = {"ideal_sd_between_u050": float(ab[:, LIFE.index(0.5)].std(ddof=1)),
                          "ideal_sd_between_u090": float(ab[:, LIFE.index(0.9)].std(ddof=1))}

    v = verdict(ideal_sd[-1], m["ratio"], m["icc"], trigger_sd)
    results = {
        "preregistration": "docs/specs/observability-program/studyA-preregistration.md",
        "seed": SEED, "n_units": N_UNITS, "life_fractions": LIFE, "probe_hz": F_PROBE_HZ,
        "amplitude_frac": AMP_FRAC, "repeats": REPEATS, "tau_trigger": TAU_TRIGGER,
        "ideal_sd_between": ideal_sd.tolist(),
        "measured": {k: [None if not np.isfinite(x) else float(x) for x in val] for k, val in m.items()},
        "trigger_life_per_unit": trig, "trigger_life_sd": trigger_sd,
        "trigger_life_range": [float(min(finite)), float(max(finite))] if finite else None,
        "n_never_trigger": int(sum(t is None for t in trig)),
        "ablation_one_axis": ablation,
        "verdict": v,
        "verdict_amended_2026_09_16": verdict(ideal_sd[-1], m["ratio"], m["icc"], trigger_sd, amended=True),
        "verdict_inputs": {"ideal_sd_between_u095": float(ideal_sd[-1]),
                           "median_ratio_u_ge_030": float(np.median(m["ratio"][np.asarray(LIFE) >= 0.3])),
                           "median_icc_u_ge_030": float(np.median(m["icc"][np.asarray(LIFE) >= 0.3]))},
        "units": [{"rupture_cycles": u.fatigue.rupture_cycles, "onset": u.fatigue.acceleration_onset_fraction,
                   "fatigue_exponent": u.fatigue.fatigue_exponent, "k1": u.sls.k1, "k2": u.sls.k2,
                   "tau": u.sls.tau, "temperature_c": u.temperature_c, "thickness_ratio": u.thickness_ratio}
                  for u in units],
    }
    os.makedirs(DATA, exist_ok=True)
    json.dump(results, open(os.path.join(DATA, "studyA_results.json"), "w"), indent=2)
    print(f"Study A verdict: {v} (preregistered rule) | {results['verdict_amended_2026_09_16']} (2026-09-16 amendment)")
    print(f"  ideal SD_between at u=0.95: {ideal_sd[-1]:.4g} | median ratio (u>=0.3): "
          f"{results['verdict_inputs']['median_ratio_u_ge_030']:.2f} | median ICC: "
          f"{results['verdict_inputs']['median_icc_u_ge_030']:.2f} | trigger-life SD: {trigger_sd:.3f} "
          f"(range {results['trigger_life_range']}, never: {results['n_never_trigger']})")
    for axis, ab in ablation.items():
        print(f"  ablation {axis:12s} SD_between(u=0.9) = {ab['ideal_sd_between_u090']:.3g}")

    plt = figstyle.setup()
    if plt is None:  # pragma: no cover
        return
    fig, (a, b) = plt.subplots(1, 2, figsize=(9.5, 3.4))
    for h in meas.mean(axis=2):
        a.plot(LIFE, h, "-", lw=0.8, alpha=0.6)
    a.axhline(1.0 + TAU_TRIGGER, ls="--", color="k", lw=0.8)
    a.set_xlabel("normalized life"); a.set_ylabel("measured P-V loop area / young")
    a.set_title(f"{N_UNITS} dispersed units, fixed {F_PROBE_HZ:g} Hz probe")
    b.plot(LIFE, m["ratio"], "o-", label="SD between / SD within")
    b.plot(LIFE, m["icc"], "s-", label="ICC(1)")
    b.axhline(2.0, ls=":", color="k", lw=0.8); b.axhline(0.5, ls=":", color="k", lw=0.8)
    b.set_xlabel("normalized life"); b.set_title(f"verdict: {v}"); b.legend()
    fig.tight_layout(); figstyle.save(fig, os.path.join(DATA, "studyA_fig_indicator_spread")); plt.close(fig)
    fig, ax = plt.subplots(figsize=(6.0, 3.2))
    names = list(ablation); ax.bar(names, [ablation[n]["ideal_sd_between_u090"] for n in names])
    ax.set_ylabel("ideal SD between units at u = 0.9"); ax.set_title("one-axis ablation (others canonical)")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout(); figstyle.save(fig, os.path.join(DATA, "studyA_fig_ablation")); plt.close(fig)
    print(f"results + figures -> {DATA}/")


if __name__ == "__main__":
    main()
