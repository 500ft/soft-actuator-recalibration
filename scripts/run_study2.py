"""Phase E study — static ridge vs dynamic corrector, per-actuator life generalization.

Tests the Gate-0 prediction on the Phase D dataset (``data/sim/phaseD/dataset.npz``): a
*static* (memoryless) ridge map is blind to the fatigue-induced *dynamic* cross-talk under a
shared manifold, while a *dynamic* (lagged-input) corrector recovers it.

Proprioception features = [shared-manifold pressure, every chamber's valve command]
(all observable — you drive every valve); target = focal bending curvature.

Two experiments, both per-actuator to remove the cross-actuator geometry confound:
  A (drift):   a static ridge calibrated on each actuator's youngest stage -> curvature RMSE
               vs life, shared vs isolated. Isolates the compliance-scale drift.
  B (recover): static vs dynamic, each calibrated on YOUNG+MID life and tested on OLD life,
               per actuator -> RMSE by topology. The static-vs-dynamic GAP (controlling for
               the compliance drift) is the cross-talk signature: expect dynamic < static
               under shared, ~equal under isolated.

Writes ``study2_results.json`` and, if matplotlib is available, two figures under
``data/sim/phaseD/``. Run: python -m scripts.run_study2
"""

from __future__ import annotations

import json
import os

import numpy as np

from pipeline.correctors import RidgeCorrector, rmse
from scripts.phased import DATA, feats, load, pose_rmse

N_LAGS = 8
ALPHA = 1.0
YOUNG_MID = [0.10, 0.30, 0.50]
OLD = [0.70, 0.90]
LIFE_ALL = [0.10, 0.30, 0.50, 0.70, 0.90]


def idx_for(d, aid, lifes, topo=None):
    lifes = [round(x, 3) for x in lifes]
    mask = (d["actuator_id"] == aid) & np.isin(np.round(d["life_frac"], 3), lifes)
    if topo is not None:
        mask &= d["topology"] == topo
    return np.flatnonzero(mask)


def fit(d, idxs, n_lags):
    return RidgeCorrector(n_lags=n_lags, alpha=ALPHA).fit(
        [feats(d, i) for i in idxs], [d["true_kappa"][i] for i in idxs])


def k_rmse(model, d, idxs):
    return float(np.mean([rmse(model.predict(feats(d, i)), d["true_kappa"][i])
                          for i in idxs]))


def main():
    d, m = load()
    test_ids = m["split_by_actuator_identity"]["test_ids"]
    acts_by_id = {a["id"]: a for a in m["actuators"]}

    # --- Experiment B: per-actuator, static vs dynamic, young+mid -> old ---
    perB = {"isolated": {"static": [], "dynamic": [], "pos_static": [], "pos_dynamic": []},
            "shared": {"static": [], "dynamic": [], "pos_static": [], "pos_dynamic": []}}
    for aid in test_ids:
        tr = idx_for(d, aid, YOUNG_MID)
        static = fit(d, tr, 0)
        dynamic = fit(d, tr, N_LAGS)
        for topo, name in [(0, "isolated"), (1, "shared")]:
            te = idx_for(d, aid, OLD, topo)
            if te.size == 0:
                continue
            perB[name]["static"].append(k_rmse(static, d, te))
            perB[name]["dynamic"].append(k_rmse(dynamic, d, te))
            perB[name]["pos_static"].append(pose_rmse(static, d, te, acts_by_id[aid]))
            perB[name]["pos_dynamic"].append(pose_rmse(dynamic, d, te, acts_by_id[aid]))
    expB = {}
    for name, v in perB.items():
        expB[name] = {
            "static_kappa_rmse": float(np.mean(v["static"])),
            "dynamic_kappa_rmse": float(np.mean(v["dynamic"])),
            "static_position_rmse_m": float(np.mean(v["pos_static"])),
            "dynamic_position_rmse_m": float(np.mean(v["pos_dynamic"])),
        }
    for name in ("isolated", "shared"):
        s, dy = expB[name]["static_kappa_rmse"], expB[name]["dynamic_kappa_rmse"]
        expB[name]["dynamic_improvement"] = (s - dy) / s

    # --- Experiment A: per-actuator young-calibrated static, drift over life ---
    young_models = {aid: fit(d, idx_for(d, aid, [0.10]), 0) for aid in test_ids}
    expA = {"life_fractions": LIFE_ALL, "isolated": [], "shared": []}
    for life in LIFE_ALL:
        for topo, name in [(0, "isolated"), (1, "shared")]:
            vals = [k_rmse(young_models[aid], d, idx_for(d, aid, [life], topo))
                    for aid in test_ids if idx_for(d, aid, [life], topo).size]
            expA[name].append(float(np.mean(vals)))

    results = {"n_lags": N_LAGS, "alpha": ALPHA, "test_actuators": test_ids,
               "features": ["manifold_pressure", "all_chamber_commands"],
               "experimentB_static_vs_dynamic_young_to_old": expB,
               "experimentA_static_drift_over_life": expA}
    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, "study2_results.json"), "w") as fh:
        json.dump(results, fh, indent=2)

    print("=== Experiment B: per-actuator young+mid -> old, static vs dynamic ===")
    for name in ("isolated", "shared"):
        b = expB[name]
        print(f"  {name:9s} kappa RMSE  static {b['static_kappa_rmse']:.4f} | "
              f"dynamic {b['dynamic_kappa_rmse']:.4f}  "
              f"({100*b['dynamic_improvement']:+.1f}%)  | "
              f"pos {b['static_position_rmse_m']*1e3:.2f}->{b['dynamic_position_rmse_m']*1e3:.2f} mm")
    print("=== Experiment A: young-calibrated static ridge, curvature RMSE vs life ===")
    print("  life:    " + "  ".join(f"{lf:.2f}" for lf in LIFE_ALL))
    print("  shared:  " + "  ".join(f"{v:.3f}" for v in expA["shared"]))
    print("  isolated:" + "  ".join(f"{v:.3f}" for v in expA["isolated"]))

    plot(results)
    print(f"figures + results -> {DATA}/")



FIG1, FIG2 = "study2_fig1_drift", "study2_fig2_static_vs_dynamic"
TOPOLOGY = (("shared", "Shared manifold", "o", "-"), ("isolated", "Isolated supply", "s", "--"))
CORRECTOR = (("static_kappa_rmse", "Static ridge", {"facecolor": "white"}),
             ("dynamic_kappa_rmse", None, {"facecolor": "white", "hatch": "////"}))


def drift_caption(results):
    expA = results["experimentA_static_drift_over_life"]
    life = expA["life_fractions"]
    early = max(max(expA[k][:-1]) for k, *_ in TOPOLOGY)
    return (
        "Curvature RMSE of a static ridge calibrated on each actuator at "
        f"{life[0]:.2f} of life and held fixed while the actuator ages; mean over the "
        f"{len(results['test_actuators'])} held-out actuators of the Phase D cohort. Filled circles and "
        "solid line: shared manifold. Hollow squares and dashed line: isolated supply. The error stays at "
        f"or below {early:.3f} 1/m up to {life[-2]:.1f} of life, then reaches "
        f"{expA['shared'][-1]:.3f} 1/m (shared) and {expA['isolated'][-1]:.3f} 1/m (isolated) at "
        f"{life[-1]:.1f}, so the drift is similar under both supply topologies. Simulation only; no "
        "physical actuator was measured. Source: study2_results.json."
    )


def drift_figure(results):
    from scripts import figure_style as style
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    style.apply()
    expA = results["experimentA_static_drift_over_life"]
    life = expA["life_fractions"]
    fig, ax = plt.subplots(figsize=(style.SINGLE, 2.6))
    fig.subplots_adjust(left=.17, right=.96, top=.87, bottom=.17)
    handles = []
    for key, label, marker, ls in TOPOLOGY:
        # Hollow squares sit behind small filled circles so both show where the curves coincide.
        filled = key == "shared"
        ax.plot(life, expA[key], color=style.INK, ls=ls, marker=marker, ms=4 if filled else 6,
                mfc=style.FILL[filled], mew=.9, zorder=3 if filled else 2)
        handles.append(Line2D([], [], color=style.INK, ls=ls, marker=marker, ms=4 if filled else 6,
                              mfc=style.FILL[filled], mew=.9, label=label))
    ax.set_xticks(life)
    ax.set_xlim(life[0] - .05, life[-1] + .05)
    ax.set_ylim(0, max(max(expA[k]) for k, *_ in TOPOLOGY) * 1.08)
    ax.set_xlabel("Normalized life")
    ax.set_ylabel("Curvature RMSE (1/m)")
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(.55, .995), ncol=2,
               handlelength=2.4, columnspacing=1.2, borderaxespad=0)
    return fig


def corrector_caption(results):
    expB = results["experimentB_static_vs_dynamic_young_to_old"]
    values = "; ".join(f"{label.lower()}, {expB[key]['static_kappa_rmse']:.4f} 1/m static and "
                       f"{expB[key]['dynamic_kappa_rmse']:.4f} 1/m dynamic"
                       for key, label, *_ in reversed(TOPOLOGY))
    gains = " and ".join(f"{expB[key]['dynamic_improvement'] * 100:.3f} % ({label.lower()})"
                         for key, label, *_ in reversed(TOPOLOGY))
    return (
        "Old-life curvature RMSE of the static ridge (hollow bars) and of the dynamic corrector with "
        f"{results['n_lags']} lagged inputs (hatched bars) under each supply topology. Both correctors are "
        f"fitted per actuator on {YOUNG_MID[0]:g} to {YOUNG_MID[-1]:g} of life and tested at "
        f"{' and '.join(f'{x:g}' for x in OLD)}; mean over the {len(results['test_actuators'])} held-out "
        f"actuators of the Phase D cohort. Values: {values}. The lagged inputs lower the error by "
        f"{gains}, so the predicted shared-manifold cross-talk advantage does not appear. Simulation only. "
        "Source: study2_results.json."
    )


def corrector_figure(results):
    from scripts import figure_style as style
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    style.apply()
    expB = results["experimentB_static_vs_dynamic_young_to_old"]
    topo = [key for key, *_ in reversed(TOPOLOGY)]
    fig, ax = plt.subplots(figsize=(style.SINGLE, 2.6))
    fig.subplots_adjust(left=.17, right=.96, top=.87, bottom=.10)
    x = np.arange(len(topo)); w = 0.36
    handles = []
    for off, (key, label, fill) in zip((-w / 2, w / 2), CORRECTOR):
        label = label or f"Dynamic, {results['n_lags']} lags"
        ax.bar(x + off, [expB[t][key] for t in topo], w * 0.92, edgecolor=style.INK, lw=.8, **fill)
        handles.append(Patch(edgecolor=style.INK, lw=.8, label=label, **fill))
    ax.set_xticks(x, [label for _, label, *_ in reversed(TOPOLOGY)])
    ax.tick_params(axis="x", length=0)
    ax.set_ylabel("Curvature RMSE (1/m)")
    ax.set_ylim(0, max(expB[t]["static_kappa_rmse"] for t in topo) * 1.1)
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(.55, .995), ncol=2,
               columnspacing=1.2, borderaxespad=0)
    return fig


def plot(results):
    """Drift and corrector figures from a saved or fresh result dict."""
    from scripts import figure_style as style
    import matplotlib.pyplot as plt

    for stem, figure, caption in ((FIG1, drift_figure, drift_caption),
                                  (FIG2, corrector_figure, corrector_caption)):
        fig = figure(results)
        style.save(fig, os.path.join(DATA, stem), caption=caption(results))
        plt.close(fig)


if __name__ == "__main__":
    import sys
    if "--replot" in sys.argv:                      # redraw from the saved result, no recomputation
        plot(json.load(open(os.path.join(DATA, "study2_results.json"))))
        print("replotted from the saved result")
    else:
        main()
