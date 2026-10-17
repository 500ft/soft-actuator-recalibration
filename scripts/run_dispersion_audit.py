"""Audit the generator's dispersion assumption — literature/gaps.md item 1.

Two questions, one raised by the literature and one a correction to how that item was written.

A. **Is there an implicit random failure threshold?** The item as filed said to "compute the implied
   rupture-life distribution from the dispersed degradation-law parameters and compare against the
   imposed Weibull", citing Bae, Kuo & Kvam 2007. On reading the generator that framing is not
   well-posed: rupture life here is *definitional*, not a threshold crossing. `fatigue_state` takes
   `rupture_cycles` as an input and expresses every multiplier in normalised life u = cycles/rupture,
   so there is no absolute failure threshold to invert. Bae/Kuo/Kvam applies to threshold-crossing
   models and this is not one.

   The real, checkable version: because rupture is imposed rather than derived, the *degradation state
   reached at rupture* is free to vary across units. If it does, the generator contains an implicit
   random failure threshold (Wang, Chen & Cai 2020), which is a modelling choice worth stating rather
   than an inconsistency.

B. **Does the transfer result survive lower dispersion?** Study A assumes rupture-life CV 0.30,
   citing Torzini 2024 as its order of magnitude, but Torzini measures CoV 3.9 % and 6.1 % and the
   highest measured value found anywhere is 17.5 %. Since R1 found transfer error tracks a unit's
   distance from the training median, an overstated CV would inflate that effect. This re-runs the
   Study C evaluation at several CVs and reports whether the verdict and the effect survive.

   None of the three CVs is "the realistic one". The published values are small cohorts of particular
   materials, geometries and loading protocols, and none of them measures this project's future
   apparatus; they anchor a *lower* end, they do not establish a universal lifetime CV. 0.30 stays an
   assumed stress case. The result worth having is the direction of travel across the sweep, not a
   verdict at any single CV.

Writes data/sim/dispersion_audit/. Changes no committed study output.
"""

from __future__ import annotations

import json
import os

import numpy as np
from matplotlib.lines import Line2D

from pipeline.dispersion import RUPTURE_CV, SEED, sample_units
from scripts import figure_style
from scripts.figure_style import plt
from scripts.run_studyC import (LAMBDAS, N_TRAIN, N_UNITS, PASS_RMSE, choose_lambda, evaluate,
                                ridge_fit, rmse, stack, unit_records)
from sim.fatigue import fatigue_state

DATA = "data/sim/dispersion_audit"
# two literature-anchored low values and Study A's assumed stress case; see the docstring on why none
# of them is "the realistic" dispersion for this project's apparatus
CV_GRID = [0.05, 0.15, RUPTURE_CV]
MEASURED = {"Torzini 2024 TPU": 0.039, "Torzini 2024 silicone": 0.061, "Du 2025 composite": 0.175}
N_STATE = 200                            # cohort size for the failure-state question (cheap, no simulation)


def state_at_rupture(n=N_STATE, cv=RUPTURE_CV):
    """Degradation state each unit has reached at u = 1, i.e. at its own rupture."""
    rows = []
    for i, unit in enumerate(sample_units(n, SEED, rupture_cv=cv)):
        fp = unit.fatigue
        s = fatigue_state(fp.rupture_cycles, 0.0, fp)
        rows.append({"unit": i, "rupture_cycles": fp.rupture_cycles,
                     "compliance_multiplier": s.compliance_multiplier,
                     "loss_multiplier": s.loss_multiplier,
                     "leak_multiplier": s.leak_multiplier,
                     "fatigue_total": s.fatigue_total})
    return rows


def spread(rows, key):
    v = np.array([r[key] for r in rows], float)
    return {"mean": float(v.mean()), "sd": float(v.std(ddof=1)),
            "cv": float(v.std(ddof=1) / v.mean()) if v.mean() else None,
            "min": float(v.min()), "max": float(v.max()),
            "range_over_mean": float((v.max() - v.min()) / v.mean()) if v.mean() else None}


def transfer_at_cv(cv):
    """Re-run the Study C transfer evaluation on a cohort drawn with this rupture-life CV."""
    units = sample_units(N_UNITS, SEED, rupture_cv=cv)
    order = np.random.default_rng(SEED + 1).permutation(N_UNITS)
    train_idx, test_idx = sorted(order[:N_TRAIN].tolist()), sorted(order[N_TRAIN:].tolist())
    records = [unit_records(u, i) for i, u in enumerate(units)]
    train = [records[i] for i in train_idx]
    lam, _ = choose_lambda(train)
    X, y = stack([r for rows in train for r in rows])
    model = ridge_fit(X, y, lam)
    model["lam"] = lam
    median_rupture = float(np.median([units[i].fatigue.rupture_cycles for i in train_idx]))
    heldout = evaluate([units[i] for i in test_idx], [records[i] for i in test_idx], model, median_rupture)

    err = np.array([h["rmse"] for h in heldout])
    clk = np.array([h["rmse_clock"] for h in heldout])
    dev = np.array([abs(h["rupture_cycles"] - median_rupture) / median_rupture for h in heldout])
    n_within, n_beats = int((err <= PASS_RMSE).sum()), int((err < clk).sum())
    r_dev = float(np.corrcoef(err, dev)[0, 1]) if err.std() > 0 and dev.std() > 0 else None
    return {
        "rupture_cv": cv, "lambda_selected": lam, "median_training_rupture_cycles": median_rupture,
        "rupture_spread_heldout": {"min": float(min(h["rupture_cycles"] for h in heldout)),
                                   "max": float(max(h["rupture_cycles"] for h in heldout))},
        "mean_rmse": float(err.mean()), "mean_rmse_clock": float(clk.mean()),
        "n_within_target": n_within, "n_beats_clock": n_beats,
        "verdict": "C-PASS" if (n_within >= 8 and n_beats >= 8) else "C-FAIL",
        "error_vs_rupture_deviation": r_dev,
        "mean_abs_rupture_deviation": float(dev.mean()),
        "per_unit": [{"rupture_cycles": h["rupture_cycles"], "rmse": h["rmse"],
                      "rmse_clock": h["rmse_clock"], "deviation": float(d)} for h, d in zip(heldout, dev)],
    }


def main():
    print("A. degradation state reached at rupture (u = 1), %d units\n" % N_STATE)
    rows = state_at_rupture()
    state = {k: spread(rows, k) for k in ("compliance_multiplier", "loss_multiplier",
                                          "leak_multiplier", "fatigue_total")}
    for k, v in state.items():
        print(f"   {k:24s} mean {v['mean']:8.4f}  sd {v['sd']:8.4f}  CV {v['cv']:6.3f}  "
              f"range {v['min']:.4f}-{v['max']:.4f}")
    implicit = state["compliance_multiplier"]["cv"] > 1e-9
    print(f"\n   implicit random failure threshold: {implicit} "
          f"(the state at rupture is {'not ' if implicit else ''}constant across units)")

    print("\nB. transfer sensitivity to the assumed rupture-life CV")
    print(f"   published cohorts for reference: " + ", ".join(f"{k} {v:.3f}" for k, v in MEASURED.items())
          + "  (specific designs, not this project's apparatus)")
    transfer = []
    for cv in CV_GRID:
        t = transfer_at_cv(cv)
        transfer.append(t)
        print(f"   CV {cv:.2f}: {t['verdict']}  within {t['n_within_target']}/10  "
              f"beats clock {t['n_beats_clock']}/10  mean u-RMSE {t['mean_rmse']:.3f} "
              f"(clock {t['mean_rmse_clock']:.3f})  corr(error, deviation) "
              f"{t['error_vs_rupture_deviation']:+.3f}")

    baseline = next(t for t in transfer if t["rupture_cv"] == RUPTURE_CV)
    lower_cv = [t for t in transfer if t["rupture_cv"] < RUPTURE_CV]
    verdict_stable = all(t["verdict"] == baseline["verdict"] for t in lower_cv)
    effect_weakens = all((t["error_vs_rupture_deviation"] or 0) < (baseline["error_vs_rupture_deviation"] or 0)
                         for t in lower_cv)

    results = {
        "task": "literature/gaps.md item 1",
        "correction_to_the_filed_item": (
            "The item asked for the rupture-life distribution 'implied' by the dispersed degradation-law "
            "parameters, citing Bae, Kuo & Kvam 2007. That framing does not apply here: rupture life is an "
            "input to fatigue_state and every multiplier is expressed in normalised life, so the generator "
            "has no absolute failure threshold to invert. Bae/Kuo/Kvam concerns threshold-crossing models. "
            "The well-posed version, reported below, is whether the degradation state reached at rupture "
            "varies across units, i.e. whether the generator has an implicit random failure threshold."),
        "A_state_at_rupture": {"n_units": N_STATE, "spread": state,
                               "implicit_random_failure_threshold": bool(implicit),
                               "reading": ("rupture is imposed rather than derived, so the state at rupture "
                                           "is free to vary; the spread above is that variation")},
        "B_transfer_sensitivity": {
            "cv_grid": CV_GRID, "measured_reference_values": MEASURED,
            "study_a_assumption": RUPTURE_CV,
            "results": transfer,
            "verdict_stable_at_lower_cv": bool(verdict_stable),
            "distance_from_median_effect_weakens_at_lower_cv": bool(effect_weakens),
            "dispersion_interpretation": (
                "0.05 and 0.15 are anchored to published cohorts (Torzini 2024, Du 2025); 0.30 is Study A's "
                "assumed stress case. None is a measurement of this project's apparatus, and three small "
                "cohorts of particular materials and loading protocols do not establish a universal "
                "lifetime CV. Read the trend across the sweep, not a verdict at any one CV."),
        },
        "does_not_change": "no committed study output; Study A/B/C verdicts and artifacts are untouched",
    }
    os.makedirs(DATA, exist_ok=True)
    out = os.path.join(DATA, "dispersion_audit.json")
    tmp = out + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(results, fh, indent=2)
    os.replace(tmp, out)
    print(f"\n   verdict stable at the lower CVs: {verdict_stable} | "
          f"distance-from-median effect weakens: {effect_weakens}")
    plot(results)
    print(f"results + figure -> {DATA}/")


STEM = os.path.join(DATA, "dispersion_audit_fig")
PASS_COUNT = 8                 # the Study C rule: 8 of 10 on both counts (see the verdict in transfer_at_cv)
NEAR_RMSE = 0.005              # caption names the CVs where the two markers in (a) overlap
PUBLISHED = {"color": figure_style.INK, "lw": 0.35, "ls": "-"}
SERIES = (("a", "mean_rmse", "o", "-", "Estimator RMSE"), ("a", "mean_rmse_clock", "s", ":", "Clock RMSE"),
          ("b", "n_within_target", "^", "-", "Units within target"),
          ("b", "n_beats_clock", "D", ":", "Units beating clock"))


def _and(items):
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def _meets(panel, value):
    return value <= PASS_RMSE if panel == "a" else value >= PASS_COUNT


def caption(results):
    sweep = results["B_transfer_sensitivity"]
    t, refs = sweep["results"], sweep["measured_reference_values"]
    n = {len(x["per_unit"]) for x in t}
    assert len(n) == 1, n
    n = n.pop()
    for x in t:
        rule = "C-PASS" if x["n_within_target"] >= PASS_COUNT and x["n_beats_clock"] >= PASS_COUNT else "C-FAIL"
        assert rule == x["verdict"], (rule, x["verdict"])
    clock_ok = [x["rupture_cv"] for x in t if x["mean_rmse_clock"] <= x["mean_rmse"]]
    per_cv = "; ".join(f"CV {x['rupture_cv']:.2f}: {x['n_within_target']} within target, {x['n_beats_clock']} "
                       f"beat the clock, {x['verdict']}" for x in t)
    overlap = "".join(f" At CV {x['rupture_cv']:.2f} the two markers in (a) overlap ({x['mean_rmse']:.3f} and "
                      f"{x['mean_rmse_clock']:.3f})." for x in t if abs(x["mean_rmse"] - x["mean_rmse_clock"]) < NEAR_RMSE)
    passed = [x for x in t if x["verdict"] == "C-PASS"]
    outcome = ("No dispersion level passes both counts" if not passed else
               "The rule passes at CV " + _and([f"{x['rupture_cv']:.2f}" for x in passed]))
    return (
        f"Dispersion audit, simulation only. The Study C evaluation is repeated on cohorts drawn at each assumed "
        f"rupture-life coefficient of variation (CV), {n} held-out units each; CV {sweep['study_a_assumption']:.2f} "
        f"is Study A's assumption. (a) Mean held-out life-estimate RMSE of the transferred estimator (circles, solid "
        f"line) and of the clock alone (squares, dotted line); the dashed horizontal line is the {PASS_RMSE:.2f} life "
        f"target. (b) Held-out units within the target (triangles, solid line) and units where the estimator beats "
        f"the clock (diamonds, dotted line); the dashed horizontal line is the rule of {PASS_COUNT} of {n} on both "
        f"counts. A filled marker meets the target in (a) or the rule count in (b); a hollow marker does not. The "
        f"clock is as good as or better than the estimator at CV "
        + _and([f"{c:.2f}" for c in clock_ok])
        + f".{overlap} {outcome}: {per_cv}. Thin vertical lines mark coefficients of variation measured in published cohorts ("
        + "; ".join(f"{k} {v:g}" for k, v in refs.items())
        + "); they are specific materials and designs, not this apparatus. "
        "Source: data/sim/dispersion_audit/dispersion_audit.json."
    )


def figure(results):
    figure_style.apply()
    sweep = results["B_transfer_sensitivity"]
    t, refs = sweep["results"], sweep["measured_reference_values"]
    cvs = [x["rupture_cv"] for x in t]
    fig, axes = plt.subplots(1, 2, figsize=(figure_style.FULL, 3.2))
    fig.subplots_adjust(left=.09, right=.985, top=.77, bottom=.14, wspace=.3)
    panels = dict(zip("ab", axes))
    for ax in axes:
        for v in refs.values():
            ax.axvline(v, zorder=0, **PUBLISHED)
        ax.set_xticks(cvs)
        ax.set_xlim(0, 0.33)
        ax.set_xlabel("Assumed rupture-life CV")
    for panel, key, marker, ls, _ in SERIES:
        ax, ys = panels[panel], [x[key] for x in t]
        ax.plot(cvs, ys, color=figure_style.INK, ls=ls, lw=1.0, zorder=2)
        for cv, y in zip(cvs, ys):
            ax.plot(cv, y, marker=marker, mfc=figure_style.FILL[bool(_meets(panel, y))], zorder=3,
                    **figure_style.MARKER)
    panels["a"].axhline(PASS_RMSE, zorder=1, **figure_style.REFERENCE)
    panels["a"].set_ylim(0, 0.14)
    panels["a"].set_ylabel("Mean held-out life-estimate\nRMSE (life)")
    n = len(t[0]["per_unit"])
    panels["b"].axhline(PASS_COUNT, zorder=1, **figure_style.REFERENCE)
    panels["b"].set_ylim(0, n + 0.5)
    panels["b"].set_yticks(range(0, n + 1, 2))
    panels["b"].set_ylabel(f"Held-out units (of {n})")
    for i, ax in enumerate(axes):
        figure_style.letter(ax, i)
    handles = [Line2D([], [], marker=m, ls=ls, mfc=figure_style.FILL[True], label=label,
                      **{k: v for k, v in figure_style.MARKER.items() if k != "ls"})
               for _, _, m, ls, label in SERIES]
    handles.append(Line2D([], [], marker="o", mfc=figure_style.FILL[False], label="Hollow: misses target or rule",
                          **figure_style.MARKER))
    handles.append(Line2D([], [], label="Target or rule", **figure_style.REFERENCE))
    handles.append(Line2D([], [], label="Published CV", **PUBLISHED))
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(.5, .995), ncol=4, columnspacing=1.2,
               handletextpad=.5, borderaxespad=0)
    return fig


def plot(results):
    fig = figure(results)
    figure_style.save(fig, STEM, caption=caption(results))
    plt.close(fig)


if __name__ == "__main__":
    import sys
    if "--replot" in sys.argv:
        plot(json.load(open(os.path.join(DATA, "dispersion_audit.json"))))
        print("replotted from the saved result")
    else:
        main()
