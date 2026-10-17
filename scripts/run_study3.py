"""Phase F study — P-V-triggered recalibration vs fixed vs always-on.

The Phase E headline: pressure-only proprioception is dominated by the fatigue compliance-scale
drift (a young calibration's pose error grows ~100x over life; ``scripts/run_study2.py``). The
operational question is *when to recalibrate*. The thesis: the observable P-V loop area
(``pipeline.coupling``) is a health indicator of that drift, so a P-V-health-triggered
recalibration can hold accuracy near an always-on policy at far fewer recalibrations.

Four policies, each starting from one calibration at the youngest life stage:
  * fixed       — never recalibrate.
  * always      — recalibrate at every life stage.
  * scheduled   — sensing-free clock baseline: recalibrate every ``period`` actuation cycles
                  (absolute cycles — a clock cannot know an actuator's rupture life, so the
                  period is global). **period is selected on TRAIN actuators only** by the
                  same budget rule as tau.
  * triggered   — recalibrate when fractional P-V loop-area growth since the last calibration
                  exceeds tau. **tau is selected on TRAIN actuators only**, then applied to the
                  held-out TEST actuators.

The scheduled baseline isolates what the *P-V measurement* buys over any monotone-with-time
signal: the clock misaligns with per-actuator degradation state whenever rupture life varies
across devices, while the trigger reads that state directly.

Honesty rule (non-negotiable): report estimation error **and** recalibration count together, so
a "savings" cannot hide degraded accuracy. The estimator is the static ridge (Phase E showed
the dynamic corrector adds nothing).

Writes ``study3_results.json`` and two figures under ``data/sim/phaseD/``.
Run: python -m scripts.run_study3
"""

from __future__ import annotations

import json
import os

import numpy as np

from pipeline.correctors import RidgeCorrector
from pipeline.coupling import (
    apply_schedule,
    bootstrap_correlation,
    cycle_schedule,
    health_trajectory,
    lead_time,
    per_group_correlations,
    recalibration_schedule,
)
from sim.plant import SLSParams
from scripts import figstyle
from scripts.phased import DATA, feats, load, pose_rmse

LIFE = [0.10, 0.30, 0.50, 0.70, 0.90]
ALPHA = 1.0
CAL_REPS = {0, 1, 2}        # calibration split
EVAL_REPS = {3, 4}          # evaluation split
TAU_GRID = np.round(np.linspace(0.0, 1.0, 21), 3)   # fractional loop-area growth thresholds
PERIOD_GRID = np.arange(0.0, 4001.0, 100.0)          # clock periods [cycles] for the baseline
LEAD_FRONTIER_TAU = [0.005, 0.01, 0.02, 0.03, 0.04, 0.05]
# Operational accuracy budget: tolerate this fraction of the way from the best-achievable
# (always-on) pose error toward the never-recalibrate (fixed) error. Selected on TRAIN
# actuators, then the triggering threshold is applied unchanged to held-out TEST actuators.
BUDGET_FRAC = 0.5


def idxs(d, aid, life, reps):
    mask = (d["actuator_id"] == aid) & np.isclose(d["life_frac"], life)
    mask &= np.isin(d["rep"], list(reps))
    return np.flatnonzero(mask)


def calibrate(d, aid, life):
    ix = idxs(d, aid, life, CAL_REPS)
    return RidgeCorrector(n_lags=0, alpha=ALPHA).fit(
        [feats(d, i) for i in ix], [d["true_kappa"][i] for i in ix])


def error_matrix(d, aid, act):
    """err[i][j] = pose RMSE at life i using the calibration fitted at life j (mm)."""
    models = [calibrate(d, aid, lf) for lf in LIFE]
    n = len(LIFE)
    err = [[pose_rmse(models[j], d, idxs(d, aid, LIFE[i], EVAL_REPS), act) * 1e3 for j in range(n)]
           for i in range(n)]
    return np.asarray(err)


def prepare(d, m):
    """Identity split, actuator table, and per-actuator error matrix / normalized health / cycles."""
    train_ids = m["split_by_actuator_identity"]["train_ids"]
    test_ids = m["split_by_actuator_identity"]["test_ids"]
    acts = {a["id"]: a for a in m["actuators"]}
    err, hn, cyc = {}, {}, {}
    for aid in train_ids + test_ids:
        a = acts[aid]
        err[aid] = error_matrix(d, aid, a)
        h = health_trajectory(SLSParams(k1=a["k1"], k2=a["k2"], tau=a["tau"]),
                              a["rupture_cycles"], LIFE)
        hn[aid] = h / h[0]                         # fractional growth, starts at 1.0
        cyc[aid] = np.asarray(LIFE) * a["rupture_cycles"]   # absolute cycles at each stage
    return train_ids, test_ids, acts, err, hn, cyc


def realized(err, flags):
    fresh = [err[i][i] for i in range(len(flags))]
    stale = [[err[i][j] for j in range(len(flags))] for i in range(len(flags))]
    return apply_schedule(flags, fresh, stale)


def policy_metrics(err, hn, policy, tau=None):
    """(mean realized pose RMSE, recalibration count) for one health-driven policy."""
    realized_err, n_recal = realized(err, recalibration_schedule(hn, policy, tau=tau))
    return float(np.mean(realized_err)), n_recal


def scheduled_metrics(err, cycles, period):
    """(mean realized pose RMSE, recalibration count) for the cycle-count clock policy."""
    realized_err, n_recal = realized(err, cycle_schedule(cycles, period))
    return float(np.mean(realized_err)), n_recal


def select_thresholds(train_ids, err, hn, cyc):
    """Accuracy budget, tau* and clock period* selected on TRAIN actuators only."""
    train_always = np.mean([policy_metrics(err[a], hn[a], "always")[0] for a in train_ids])
    train_fixed = np.mean([policy_metrics(err[a], hn[a], "fixed")[0] for a in train_ids])
    budget_mm = train_always + BUDGET_FRAC * (train_fixed - train_always)
    sweep = []
    for tau in TAU_GRID:
        em = [policy_metrics(err[a], hn[a], "triggered", tau) for a in train_ids]
        sweep.append({"tau": float(tau),
                      "train_error_mm": float(np.mean([x[0] for x in em])),
                      "train_recal": float(np.mean([x[1] for x in em]))})
    ok = [s for s in sweep if s["train_error_mm"] <= budget_mm]
    selected = max(ok, key=lambda s: s["tau"]) if ok else sweep[0]   # fewest recals within budget
    period_sweep = []
    for period in PERIOD_GRID:
        em = [scheduled_metrics(err[a], cyc[a], period) for a in train_ids]
        period_sweep.append({"period_cycles": float(period),
                             "train_error_mm": float(np.mean([x[0] for x in em])),
                             "train_recal": float(np.mean([x[1] for x in em]))})
    ok_p = [s for s in period_sweep if s["train_error_mm"] <= budget_mm]
    # fewest recals within budget -> longest period; tie-break toward lower error
    sel_p = (max(ok_p, key=lambda s: s["period_cycles"]) if ok_p else period_sweep[0])
    return {"train_always": train_always, "train_fixed": train_fixed, "budget_mm": budget_mm,
            "sweep": sweep, "selected": selected, "tau_star": selected["tau"],
            "period_sweep": period_sweep, "period_star": sel_p["period_cycles"]}


def heldout_policies(test_ids, err, hn, cyc, tau_star, period_star):
    """Per-held-out-actuator (pose RMSE list, recalibration-count list) for the four policies."""
    out = {}
    for name in ("fixed", "scheduled", "triggered", "always"):
        pairs = [scheduled_metrics(err[a], cyc[a], period_star) if name == "scheduled"
                 else policy_metrics(err[a], hn[a], name, tau_star if name == "triggered" else None)
                 for a in test_ids]
        out[name] = ([e for e, _ in pairs], [r for _, r in pairs])
    return out


def summarize_leads(records):
    finite = [r for r in records if r["lead_life"] is not None]
    out = {"per_actuator": records}
    for key, stats in (("lead_life", ("median", "min", "max")),
                       ("trigger_life", ("median", "min", "max")),
                       ("budget_violation_life", ("median", "min", "max")),
                       ("lead_cycles", ("min", "median", "max"))):
        vals = [r[key] for r in finite]
        for stat in stats:
            out[f"{stat}_{key}"] = float(getattr(np, stat)(vals)) if vals else None
    out["n_excluded"] = int(len(records) - len(finite))
    out["status_counts"] = {s: int(sum(r["status"] == s for r in records))
                            for s in ("ok", "never_triggers", "never_violates", "nonpositive_lead")}
    return out


def lead_records(tau, test_ids, err, hn, acts, budget_mm):
    """Per-held-out-actuator lead-time records plus triggered-policy error/recal lists at ``tau``."""
    records, errors, recals = [], [], []
    for aid in test_ids:
        fixed_err = [err[aid][i][0] for i in range(len(LIFE))]
        lt = lead_time(hn[aid], fixed_err, tau, budget_mm, LIFE)
        lead_life = lt["lead_life"]
        records.append({
            "actuator_id": int(aid),
            "rupture_cycles": float(acts[aid]["rupture_cycles"]),
            "trigger_life": lt["trigger_life"],
            "budget_violation_life": lt["budget_violation_life"],
            "lead_life": lead_life,
            "lead_cycles": float(lead_life * acts[aid]["rupture_cycles"]) if lead_life is not None else None,
            "status": lt["status"],
        })
        e, r = policy_metrics(err[aid], hn[aid], "triggered", tau)
        errors.append(e)
        recals.append(r)
    return records, errors, recals


def frontier_point(tau, test_ids, err, hn, acts, budget_mm):
    """Held-out lead/error/recalibration summary for one descriptive threshold."""
    records, errors, recals = lead_records(tau, test_ids, err, hn, acts, budget_mm)
    lead = summarize_leads(records)
    return {
        "tau": float(tau),
        "trigger_life_median": lead["median_trigger_life"],
        "trigger_life_min": lead["min_trigger_life"],
        "trigger_life_max": lead["max_trigger_life"],
        "lead_life_median": lead["median_lead_life"],
        "lead_life_min": lead["min_lead_life"],
        "lead_life_max": lead["max_lead_life"],
        "lead_cycles_median": lead["median_lead_cycles"],
        "lead_cycles_min": lead["min_lead_cycles"],
        "lead_cycles_max": lead["max_lead_cycles"],
        "recal_per_actuator": float(np.mean(recals)),
        "mean_pose_rmse_mm": float(np.mean(errors)),
        "budget_met": bool(float(np.mean(errors)) <= budget_mm),
        "n_positive_lead": int(sum(r["status"] == "ok" for r in records)),
        "n_nonpositive_lead": int(sum(r["status"] == "nonpositive_lead" for r in records)),
        "n_excluded": lead["n_excluded"],
        "status_counts": lead["status_counts"],
        "per_actuator": records,
    }


def lead_frontier(test_ids, err, hn, acts, budget_mm, tau_values=LEAD_FRONTIER_TAU):
    """Descriptive held-out lead/recalibration frontier; does not select a policy."""
    points = [frontier_point(tau, test_ids, err, hn, acts, budget_mm) for tau in tau_values]
    ranges = [float(np.max(hn[aid]) - hn[aid][0]) for aid in test_ids]
    return {
        "tau_values": [float(t) for t in tau_values],
        "signal_dynamic_range_median": float(np.median(ranges)),
        "signal_dynamic_range_min": float(np.min(ranges)),
        "signal_dynamic_range_max": float(np.max(ranges)),
        "points": points,
    }


def main():
    d, m = load()
    train_ids, test_ids, acts, err, hn, cyc = prepare(d, m)

    # --- threshold selection on TRAIN actuators only, against an accuracy budget ---
    sel = select_thresholds(train_ids, err, hn, cyc)
    train_always, train_fixed, budget_mm = sel["train_always"], sel["train_fixed"], sel["budget_mm"]
    sweep, selected, tau_star = sel["sweep"], sel["selected"], sel["tau_star"]
    period_sweep, period_star = sel["period_sweep"], sel["period_star"]
    ok = [s for s in sweep if s["train_error_mm"] <= budget_mm]

    # --- what the budget-only rule costs in lead time (TRAIN actuators only) ---------
    # The rule above maximizes tau within the accuracy budget, which minimizes
    # recalibrations but is indifferent to WHEN the threshold fires. A threshold that
    # trips after the budget is already violated schedules a recalibration that was
    # needed earlier, so it cannot support a prognostic claim however few times it
    # fires. This block measures lead for every tau on the grid and records what a
    # lead-aware rule would have selected instead.
    #
    # Reported, NOT deployed: tau_star is unchanged, so every downstream number in this
    # study is unaffected. Changing the operating point alters what the paper
    # recommends and is a decision for the author, not a side effect of an audit.
    # Lead is evaluated on TRAIN actuators only -- selecting on held-out lead would be
    # leakage, which is the whole reason the identity split exists.
    for s in sweep:
        leads = []
        for a in train_ids:
            fixed = [err[a][i][0] for i in range(len(LIFE))]
            lt = lead_time(hn[a], fixed, s["tau"], budget_mm, LIFE)
            leads.append(lt["lead_life"])
        usable = [v for v in leads if v is not None]
        s["train_lead_life_mean"] = float(np.mean(usable)) if usable else None
        s["train_lead_positive_count"] = int(sum(1 for v in usable if v > 0))
        s["train_lead_n_actuators"] = len(train_ids)

    warns = [s for s in ok if (s.get("train_lead_life_mean") or 0.0) > 0]
    lead_aware = max(warns, key=lambda s: s["tau"]) if warns else None
    tau_selection_alternatives = {
        "deployed_rule": {
            "name": "fewest recalibrations within the accuracy budget",
            "tau": tau_star,
            "train_recal": selected["train_recal"],
            "train_error_mm": selected["train_error_mm"],
            "train_lead_life_mean": selected.get("train_lead_life_mean"),
            "train_lead_positive_count": selected.get("train_lead_positive_count"),
        },
        "lead_aware_rule": ({
            "name": "fewest recalibrations AMONG thresholds that warn before the budget "
                    "is violated on training actuators",
            "tau": lead_aware["tau"],
            "train_recal": lead_aware["train_recal"],
            "train_error_mm": lead_aware["train_error_mm"],
            "train_lead_life_mean": lead_aware["train_lead_life_mean"],
            "train_lead_positive_count": lead_aware["train_lead_positive_count"],
        } if lead_aware is not None else None),
        "note": "The deployed rule is unchanged and produced every other number in this "
                "file. If the two rules disagree, the budget-only rule is buying fewer "
                "recalibrations with negative lead -- i.e. it is not warning in advance. "
                "Switching is a design decision; see docs/reviewer_backlog.md.",
        "rules_agree": (lead_aware is not None and lead_aware["tau"] == tau_star),
    }

    # --- apply to held-out TEST actuators ---
    heldout = heldout_policies(test_ids, err, hn, cyc, tau_star, period_star)

    results = {
        "estimator": "static ridge (Phase E: dynamic adds nothing)",
        "life_fractions": LIFE, "tau_selected": tau_star,
        "period_selected_cycles": period_star,
        "accuracy_budget_mm": float(budget_mm), "budget_frac": BUDGET_FRAC,
        "train_fixed_error_mm": float(train_fixed), "train_always_error_mm": float(train_always),
        "train_actuators": train_ids, "test_actuators": test_ids,
        "policies_on_heldout": {
            name: {"mean_pose_rmse_mm": float(np.mean(es)),
                   "total_recalibrations": int(np.sum(rs)),
                   "recal_per_actuator": float(np.mean(rs))}
            for name, (es, rs) in heldout.items()
        },
        "threshold_sweep_train": sweep,
        "tau_selection_alternatives": tau_selection_alternatives,
        "period_sweep_train": period_sweep,
    }

    # --- health indicator: P-V health drift vs fixed-calibration pose error (held-out) ---
    hx, ey = [], []
    corr_groups = []
    for a in test_ids:
        for i in range(len(LIFE)):
            hx.append(hn[a][i] - 1.0)           # fractional loop-area growth from young
            ey.append(err[a][i][0])             # fixed (young) calibration error at life i
            corr_groups.append(a)
    results["leading_indicator_corr"] = bootstrap_correlation(np.array(hx), np.array(ey),
                                                              n_boot=2000, seed=7)
    per_act = per_group_correlations(np.array(corr_groups), np.array(hx), np.array(ey))
    per_act["values"] = [{"actuator_id": rec["group"], "r": rec["r"], "n": rec["n"]}
                         for rec in per_act["values"]]
    results["per_actuator_r"] = per_act
    results["lead_time_heldout"] = summarize_leads(
        lead_records(tau_star, test_ids, err, hn, acts, budget_mm)[0])
    results["lead_frontier_heldout"] = lead_frontier(test_ids, err, hn, acts, budget_mm)

    os.makedirs(DATA, exist_ok=True)
    json.dump(results, open(os.path.join(DATA, "study3_results.json"), "w"), indent=2)

    pol = results["policies_on_heldout"]
    print(f"accuracy budget = {budget_mm:.3f} mm (train fixed {train_fixed:.2f} / always {train_always:.2f})")
    print(f"selected tau* = {tau_star} (fractional P-V loop-area growth; train-selected)")
    print(f"selected clock period* = {period_star:.0f} cycles (train-selected, same budget rule)")
    print("=== held-out actuators: error vs recalibration count ===")
    for name in ("fixed", "scheduled", "triggered", "always"):
        p = pol[name]
        print(f"  {name:9s} pose RMSE {p['mean_pose_rmse_mm']:.2f} mm | "
              f"recal/actuator {p['recal_per_actuator']:.1f} | total {p['total_recalibrations']}")
    lc = results["leading_indicator_corr"]
    print(f"health indicator (P-V growth vs fixed-cal error): "
          f"r={lc['r']:.3f} [{lc['ci_low']:.3f}, {lc['ci_high']:.3f}]")
    pa = results["per_actuator_r"]
    lt = results["lead_time_heldout"]
    print(f"per-actuator r median={pa['median']:.3f} "
          f"[{pa['min']:.3f}, {pa['max']:.3f}]")
    if lt["median_lead_life"] is None:
        print(f"lead time: no positive lead; statuses={lt['status_counts']}")
    else:
        print(f"lead time: median={lt['median_lead_life']:.3f} life "
              f"[{lt['min_lead_life']:.3f}, {lt['max_lead_life']:.3f}], "
              f"excluded={lt['n_excluded']}")

    plot(results, mean_curves(test_ids, err, hn))
    print(f"figures + results -> {DATA}/")



def mean_curves(test_ids, err, hn):
    """Held-out mean of normalized loop area and of young-calibration pose error at each life stage."""
    return {"loop_area": np.mean([hn[a] for a in test_ids], axis=0),
            "fixed_error_mm": np.mean([[err[a][i][0] for i in range(len(LIFE))] for a in test_ids], axis=0)}


def plot(results, curves):
    plt = figstyle.setup()
    if plt is None:  # pragma: no cover
        print("(matplotlib unavailable, skipped figures)")
        return
    C, S = figstyle.COLOR, figstyle.SIZE
    n = len(results["test_actuators"])
    life = results["life_fractions"]

    # Fig 3: health signal and young-calibration error over life, two aligned panels
    fig, (a, b) = plt.subplots(2, 1, figsize=(figstyle.SINGLE, 3.6), sharex=True, gridspec_kw={"hspace": 0.15})
    a.plot(life, curves["loop_area"], "o-", color=C["pv"], ms=4)
    a.set_ylabel("P-V loop area\n(× young)")
    b.plot(life, curves["fixed_error_mm"], "s-", color=C["fixed"], ms=4)
    b.set_ylabel("Pose RMSE, young\ncalibration (mm)")
    b.set_xticks(life)
    b.set_xlabel("Normalized life")
    for ax in (a, b):
        ax.margins(x=0.05, y=0.1)
    a.set_title("P-V loop area and young-calibration pose\nerror both rise with life")
    r = results["leading_indicator_corr"]
    figstyle.footnote(fig, f"Simulation: Phase D cohort, mean of {n} held-out actuators. Pooled r = {r['r']:.3f} "
                      "over actuator × stage points. One fatigue law drives both signals, so the association is "
                      "built in (matched_clock_audit.json).")
    figstyle.save(fig, os.path.join(DATA, "study3_fig3_leading_indicator"))
    plt.close(fig)

    # Fig 3 keeps the old style and is drawn first, before figure_style.apply() changes rcParams.
    plot_tradeoff(results)


FIG4 = "study3_fig4_recal_tradeoff"
# Policy key, label (None: built from the result), marker. Shared with run_study3_cluster_ci.
POLICIES = (("fixed", "Initial calibration only", "o"), ("scheduled", None, "^"),
            ("triggered", None, "D"), ("always", "Every life stage", "X"))
POLICY_WORDS = {"o": "circle", "^": "triangle", "D": "diamond", "X": "cross"}


def policy_labels(period, tau):
    """Legend label per policy key; mathtext tau because cmr10 has no Greek glyphs."""
    names = {"scheduled": f"Clock, {period:,.0f} cycles", "triggered": f"P-V trigger, $\\tau$ = {tau:g}"}
    return {key: label or names[key] for key, label, _ in POLICIES}


SHORT = {"fixed": "initial calibration only", "scheduled": "the clock", "triggered": "the P-V trigger",
         "always": "calibration at every stage"}


def policy_sentence(period, tau):
    """Plain-text policy list with marker names, for captions."""
    words = {"fixed": "initial calibration only", "scheduled": f"a cycle-count clock every {period:,.0f} cycles "
             "selected on the training actuators", "triggered": f"the P-V trigger at τ = {tau:g}",
             "always": "calibration at every life stage"}
    return ", ".join(f"{words[key]} ({POLICY_WORDS[marker]})" for key, _, marker in POLICIES)


def tradeoff_caption(results, audit):
    pol, budget = results["policies_on_heldout"], results["accuracy_budget_mm"]
    meets = [SHORT[k] for k, _, _ in POLICIES if pol[k]["mean_pose_rmse_mm"] <= budget]
    values = "; ".join(f"{SHORT[k]} {pol[k]['mean_pose_rmse_mm']:.3f} mm with {pol[k]['recal_per_actuator']:.1f}"
                       for k, _, _ in POLICIES)
    return (
        "Mean pose RMSE against calibrations per actuator over life on the "
        f"{len(results['test_actuators'])} held-out actuators of the Phase D cohort for four policies: "
        f"{policy_sentence(results['period_selected_cycles'], results['tau_selected'])}. Counts include the "
        "initial calibration; error averages life stages, then actuators. The dashed line is the train-derived "
        f"error budget, {budget:.3f} mm. A filled marker meets the budget; a hollow marker exceeds it. Values: "
        f"{values}. Only {' and '.join(meets)} meet the budget. This saved run has no matched-cost clock; at "
        f"{audit['clock_periods_matching_trigger_schedule_on_all_actuators'][0]:,.0f} cycles a clock ties the "
        "trigger (data/sim/summary/policy_comparison.png, matched_clock_audit.json). Simulation only. "
        "Source: study3_results.json."
    )


def policy_legend(fig, period, tau, extra, ncol, y=.995):
    """One framed legend above the panels: policy shapes, then the reference and state entries."""
    from matplotlib.lines import Line2D
    from scripts import figure_style as style

    labels = policy_labels(period, tau)
    handles = [Line2D([], [], marker=m, mfc=style.FILL[True], label=labels[k], **style.MARKER)
               for k, _, m in POLICIES]
    fig.legend(handles=handles + extra, loc="upper center", bbox_to_anchor=(.5, y), ncol=ncol,
               columnspacing=1.0, handletextpad=.5, borderaxespad=0)


def tradeoff_figure(results):
    from matplotlib.lines import Line2D
    import matplotlib.pyplot as plt
    from scripts import figure_style as style

    style.apply()
    pol, budget = results["policies_on_heldout"], results["accuracy_budget_mm"]
    fig, ax = plt.subplots(figsize=(style.SINGLE, 3.3))
    fig.subplots_adjust(left=.17, right=.96, top=.79, bottom=.14)
    ax.axhline(budget, zorder=1, **style.REFERENCE)
    for key, _, marker in POLICIES:
        p = pol[key]
        ax.plot(p["recal_per_actuator"], p["mean_pose_rmse_mm"], marker=marker, zorder=3,
                mfc=style.FILL[p["mean_pose_rmse_mm"] <= budget], **style.MARKER)
    ax.set_xlim(0.5, 5.7)
    ax.set_ylim(0, max(p["mean_pose_rmse_mm"] for p in pol.values()) * 1.12)
    ax.set_xlabel("Calibrations per actuator over life")
    ax.set_ylabel("Mean pose RMSE (mm)")
    extra = [Line2D([], [], label="Error budget", **style.REFERENCE),
             Line2D([], [], marker="s", mfc=style.FILL[False], label="Hollow: above budget", **style.MARKER)]
    policy_legend(fig, results["period_selected_cycles"], results["tau_selected"], extra, ncol=2)
    return fig


def plot_tradeoff(results):
    """Fig 4 from the saved result alone; the matched-cost audit supplies one caption number."""
    import matplotlib.pyplot as plt
    from scripts import figure_style as style

    audit = json.load(open(os.path.join(DATA, "matched_clock_audit.json")))
    fig = tradeoff_figure(results)
    style.save(fig, os.path.join(DATA, FIG4), caption=tradeoff_caption(results, audit))
    plt.close(fig)

def replot():
    """Redraw from the saved result. Fig 4 needs only the JSON; Fig 3 is redrawn only when the
    regenerated dataset is present, because its two mean curves come from it."""
    results = json.load(open(os.path.join(DATA, "study3_results.json")))
    if os.path.exists(os.path.join(DATA, "dataset.npz")):
        d, m = load()
        _, test_ids, _, err, hn, _ = prepare(d, m)
        plot(results, mean_curves(test_ids, err, hn))
    else:
        plot_tradeoff(results)
    print("replotted from the saved result")


if __name__ == "__main__":
    import sys
    if "--replot" in sys.argv:
        replot()
    else:
        main()
