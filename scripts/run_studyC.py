"""Study C — unseen-unit transfer of a pressure-only life estimator (preregistered; amended 2026-09-16).

Writes data/sim/studyC/. Design: docs/specs/observability-program/studyC-transfer.md.
"""

from __future__ import annotations

import json
import os

import numpy as np
from matplotlib.lines import Line2D

from pipeline.dispersion import SEED, sample_units
from pipeline.identifiability import measured_features
from scripts import figure_style
from scripts.figure_style import plt
from scripts.run_studyB import theta_of

DATA = "data/sim/studyC"
N_UNITS, N_TRAIN = 30, 20
PROBE_START, PROBE_STEP = 100.0, 250.0
LAMBDAS = (0.01, 0.1, 1.0)
N_BOOT = 2000
ADVERSARIAL_SEED, ADVERSARIAL_N = 20260918, 200
PASS_RMSE = 0.10


def probes(unit):
    """(cycles, u) at every scheduled probe before rupture."""
    n = np.arange(PROBE_START, unit.fatigue.rupture_cycles, PROBE_STEP)
    return n, n / unit.fatigue.rupture_cycles


def unit_records(unit, index):
    """Per-probe rows: inputs x (11), target u, cycles, onset flag."""
    cycles, us = probes(unit)
    seed = lambda k: int(np.random.SeedSequence([SEED, 7, index, k]).generate_state(1)[0])
    base = measured_features(theta_of(unit, us[0]), unit.fatigue, unit.sls, seed(0))
    rows, prev = [], None
    for k, (n, u) in enumerate(zip(cycles, us)):
        y = measured_features(theta_of(unit, u), unit.fatigue, unit.sls, seed(k + 1))
        lr = np.log(y / base)
        lag = lr if prev is None else prev
        rows.append({"x": np.concatenate([lr, lag, [n / 1000.0]]), "u": float(u), "cycles": float(n),
                     "post_onset": bool(u >= unit.fatigue.acceleration_onset_fraction)})
        prev = lr
    return rows


def ridge_fit(X, y, lam, scaler=None):
    """Ridge on standardised inputs; ``scaler`` (mu, sd) reuses another fit's standardisation."""
    mu, sd = scaler if scaler else (X.mean(axis=0), X.std(axis=0) + 1e-12)
    Z = (X - mu) / sd
    A = Z.T @ Z + lam * np.eye(Z.shape[1])
    w = np.linalg.solve(A, Z.T @ (y - y.mean()))
    return {"mu": mu, "sd": sd, "w": w, "b": float(y.mean())}


def ridge_predict(model, X):
    return ((X - model["mu"]) / model["sd"]) @ model["w"] + model["b"]


def rmse(a, b):
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))


def stack(records):
    return np.array([r["x"] for r in records]), np.array([r["u"] for r in records])


def choose_lambda(train):
    """Leave-one-unit-out on the training units."""
    scores = {}
    for lam in LAMBDAS:
        errs = []
        for i in range(len(train)):
            X, y = stack([r for j, rows in enumerate(train) if j != i for r in rows])
            Xi, yi = stack(train[i])
            errs.append(rmse(ridge_predict(ridge_fit(X, y, lam), Xi), yi))
        scores[lam] = float(np.mean(errs))
    return min(scores, key=scores.get), scores


def evaluate(units, records, model, median_rupture):
    out = []
    for unit, rows in zip(units, records):
        X, y = stack(rows)
        pred = ridge_predict(model, X)
        clock = np.clip(np.array([r["cycles"] for r in rows]) / median_rupture, 0.0, 1.0)
        own = (ridge_fit(X[:3], y[:3], model["lam"], scaler=(model["mu"], model["sd"]))   # same ridge, own labels
               if len(rows) >= 3 else None)
        post = np.array([r["post_onset"] for r in rows])
        out.append({
            "rupture_cycles": unit.fatigue.rupture_cycles, "onset": unit.fatigue.acceleration_onset_fraction,
            "n_probes": len(rows),
            "rmse": rmse(pred, y), "rmse_clock": rmse(clock, y),
            "rmse_per_unit_calibration": rmse(ridge_predict(own, X), y) if own else None,
            "rmse_pre_onset": rmse(pred[~post], y[~post]) if (~post).any() else None,
            "rmse_post_onset": rmse(pred[post], y[post]) if post.any() else None,
        })
    return out


def main():
    units = sample_units(N_UNITS, SEED)
    order = np.random.default_rng(SEED + 1).permutation(N_UNITS)
    train_idx, test_idx = sorted(order[:N_TRAIN].tolist()), sorted(order[N_TRAIN:].tolist())
    records = [unit_records(u, i) for i, u in enumerate(units)]
    train = [records[i] for i in train_idx]
    lam, lam_scores = choose_lambda(train)
    X, y = stack([r for rows in train for r in rows])
    model = ridge_fit(X, y, lam); model["lam"] = lam
    median_rupture = float(np.median([units[i].fatigue.rupture_cycles for i in train_idx]))

    heldout = evaluate([units[i] for i in test_idx], [records[i] for i in test_idx], model, median_rupture)
    r = np.array([h["rmse"] for h in heldout]); rc = np.array([h["rmse_clock"] for h in heldout])
    n_within = int((r <= PASS_RMSE).sum()); n_beats_clock = int((r < rc).sum())
    verdict = "C-PASS" if (n_within >= 8 and n_beats_clock >= 8) else "C-FAIL"
    rng = np.random.default_rng(SEED + 2)
    boot = np.array([r[rng.integers(0, len(r), len(r))].mean() for _ in range(N_BOOT)])
    loo = [float(np.delete(r, i).mean()) for i in range(len(r))]

    adv_units = sample_units(ADVERSARIAL_N, ADVERSARIAL_SEED)
    adv = evaluate(adv_units, [unit_records(u, 10_000 + i) for i, u in enumerate(adv_units)], model, median_rupture)
    worst = max(range(len(adv)), key=lambda i: adv[i]["rmse"])
    wu = adv_units[worst]

    results = {
        "preregistration": "docs/specs/observability-program/studyC-transfer.md (amended 2026-09-16)",
        "seed": SEED, "train_units": train_idx, "test_units": test_idx,
        "probe_schedule_cycles": {"start": PROBE_START, "step": PROBE_STEP},
        "lambda_selected": lam, "lambda_loo_scores": lam_scores, "median_training_rupture_cycles": median_rupture,
        "heldout": heldout,
        "heldout_mean_rmse": float(r.mean()), "heldout_mean_rmse_clock": float(rc.mean()),
        "cluster_bootstrap_ci": [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))],
        "leave_one_unit_out_range": [min(loo), max(loo)],
        "n_within_target": n_within, "n_beats_clock": n_beats_clock, "verdict": verdict,
        "adversarial": {"n_units": ADVERSARIAL_N, "seed": ADVERSARIAL_SEED, "worst_rmse": adv[worst]["rmse"],
                        "worst_rmse_clock": adv[worst]["rmse_clock"], "fraction_within_target": float(np.mean([a["rmse"] <= PASS_RMSE for a in adv])),
                        "worst_unit": {"rupture_cycles": wu.fatigue.rupture_cycles, "onset": wu.fatigue.acceleration_onset_fraction,
                                       "fatigue_exponent": wu.fatigue.fatigue_exponent, "terminal_leak_multiplier": wu.fatigue.terminal_leak_multiplier,
                                       "mullins_amplitude": wu.fatigue.mullins_amplitude, "k1": wu.sls.k1, "k2": wu.sls.k2, "tau": wu.sls.tau,
                                       "temperature_c": wu.temperature_c, "thickness_ratio": wu.thickness_ratio}},
    }
    os.makedirs(DATA, exist_ok=True)
    json.dump(results, open(os.path.join(DATA, "studyC_results.json"), "w"), indent=2)
    print(f"Study C verdict: {verdict} | held-out u-RMSE mean {r.mean():.3f} (clock {rc.mean():.3f}); "
          f"{n_within}/10 within {PASS_RMSE}, {n_beats_clock}/10 beat the clock; lambda={lam}")
    print(f"  pre-onset mean {np.nanmean([h['rmse_pre_onset'] or np.nan for h in heldout]):.3f} | "
          f"post-onset mean {np.nanmean([h['rmse_post_onset'] or np.nan for h in heldout]):.3f} | "
          f"per-unit calibration mean {np.mean([h['rmse_per_unit_calibration'] for h in heldout]):.3f}")
    print(f"  adversarial worst RMSE {adv[worst]['rmse']:.3f} (clock {adv[worst]['rmse_clock']:.3f}); "
          f"{results['adversarial']['fraction_within_target']:.2f} of 200 within target")

    plot(results)
    print(f"results + figure -> {DATA}/")



PASS_COUNT = 8                 # the preregistered rule: 8 of 10 on both counts (see the verdict line in main)
STEM = os.path.join(DATA, "studyC_fig_transfer")
TRANSFER_LABEL, CLOCK_LABEL = "Pressure features + clock", "Clock only"
DODGE = 0.14                   # horizontal offset of each marker from its unit tick


def caption(results):
    heldout = results["heldout"]
    n = len(heldout)
    within, beats = results["n_within_target"], results["n_beats_clock"]
    rule = "C-PASS" if within >= PASS_COUNT and beats >= PASS_COUNT else "C-FAIL"
    assert rule == results["verdict"], (rule, results["verdict"])
    assert within == sum(h["rmse"] <= PASS_RMSE for h in heldout)
    assert beats == sum(h["rmse"] < h["rmse_clock"] for h in heldout)
    return (
        f"Study C transfer, simulation only. One ridge estimator on pressure features plus the cycle clock was "
        f"trained on {len(results['train_units'])} dispersed synthetic units and applied unchanged to {n} unseen "
        f"units. For each held-out unit, the circle is the transferred estimator's life-estimate RMSE and the "
        f"square, drawn just right of it, is the clock-only estimate; the thin line joins the pair. A filled marker meets the "
        f"{PASS_RMSE:.2f} life target (dashed line); a hollow marker misses it. Lower is better. The estimator "
        f"meets the target on {within} of {n} units and beats the clock on {beats}; mean RMSE "
        f"{results['heldout_mean_rmse']:.3f} life against {results['heldout_mean_rmse_clock']:.3f} for the clock. "
        f"The preregistered rule needs {PASS_COUNT} of {n} on both counts, so the verdict is {results['verdict']}. "
        "Source: data/sim/studyC/studyC_results.json."
    )


def figure(results):
    figure_style.apply()
    heldout, test_idx = results["heldout"], results["test_units"]
    r = np.array([h["rmse"] for h in heldout]); rc = np.array([h["rmse_clock"] for h in heldout])
    ids = np.arange(len(heldout))
    fig, ax = plt.subplots(figsize=(5.4, 2.8))
    fig.subplots_adjust(left=.12, right=.98, top=.83, bottom=.15)
    # The pair sits either side of the unit's tick so equal errors do not hide each other.
    for i in ids:
        ax.plot([i - DODGE, i + DODGE], [r[i], rc[i]], color=figure_style.INK, lw=0.6, zorder=1)
    for i in ids:
        ax.plot(i + DODGE, rc[i], marker="s", mfc=figure_style.FILL[bool(rc[i] <= PASS_RMSE)], zorder=2,
                **figure_style.MARKER)
        ax.plot(i - DODGE, r[i], marker="o", mfc=figure_style.FILL[bool(r[i] <= PASS_RMSE)], zorder=3,
                **figure_style.MARKER)
    ax.axhline(PASS_RMSE, zorder=0, **figure_style.REFERENCE)
    ax.set_xticks(ids, [str(i) for i in test_idx])
    ax.set_xlim(-0.6, len(ids) - 0.4)
    ax.set_ylim(0, max(rc.max(), r.max()) * 1.1)
    ax.set_xlabel("Held-out unit")
    ax.set_ylabel("Life-estimate RMSE (life)")
    handles = [Line2D([], [], marker="o", mfc=figure_style.FILL[True], label=TRANSFER_LABEL, **figure_style.MARKER),
               Line2D([], [], marker="s", mfc=figure_style.FILL[True], label=CLOCK_LABEL, **figure_style.MARKER),
               Line2D([], [], marker="o", mfc=figure_style.FILL[False], label="Hollow: misses target",
                      **figure_style.MARKER),
               Line2D([], [], label="Target", **figure_style.REFERENCE)]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(.55, .995), ncol=2, columnspacing=1.4,
               handletextpad=.5, borderaxespad=0)
    return fig


def plot(results):
    """Per-unit transfer figure and caption from a saved or fresh result dict."""
    fig = figure(results)
    figure_style.save(fig, STEM, caption=caption(results))
    plt.close(fig)


if __name__ == "__main__":
    import sys
    if "--replot" in sys.argv:                      # redraw from the saved result, no recomputation
        plot(json.load(open(os.path.join(DATA, "studyC_results.json"))))
        print("replotted from the saved result")
    else:
        main()
