"""Study 3, revisited: cluster-aware uncertainty for the P-V health-indicator claim.

Study 3 reports a pooled Pearson r between observable P-V loop-area growth and
fixed-calibration pose error, with a bootstrap interval produced by
``pipeline.coupling.bootstrap_correlation``. That interval resamples the 30 individual
(actuator, life-stage) points independently. The held-out sample is 6 actuators x 5 life
stages, so those 30 points are repeated measures on 6 clusters and the effective sample
size is the number of *actuators*, not the number of points.

This script changes nothing about the estimate or the pipeline. It re-estimates the
uncertainty with the actuator as the resampling unit, and adds the health-indicator
quality metrics (monotonicity / trendability / prognosability) that
``docs/reviewer_backlog.md`` item 1 asks for, each with the same cluster treatment.

Because there are only 6 clusters, the cluster bootstrap is *enumerated exhaustively*
(all 6**6 = 46,656 resamples) rather than Monte-Carlo sampled, so it carries no
simulation error.

Run after the dataset step:

    python -m scripts.phaseD_dataset
    python -m scripts.run_study3_cluster_ci

Evidence type: simulation. Synthetic actuator cohort; no physical measurement.
"""
from __future__ import annotations

import itertools
import json
import os
from dataclasses import asdict

import numpy as np
from scipy.stats import t as tdist

from pipeline.coupling import (
    bootstrap_correlation,
    health_trajectory,
    per_group_correlations,
)
from pipeline.hi_metrics import monotonicity, prognosability, trendability
from sim.plant import SLSParams

import scripts.run_study3 as S3
from scripts import figstyle

DATA = S3.DATA
LIFE = S3.LIFE
CI = 0.95


def _q(a, p):
    return float(np.quantile(np.asarray(a, float), p))


def fisher_ci(r, n_eff, alpha=1 - CI):
    """Fisher-z interval evaluated at a stated effective sample size."""
    from scipy.stats import norm

    if n_eff <= 3:
        return (None, None)
    z, se = np.arctanh(r), 1.0 / np.sqrt(n_eff - 3)
    zc = norm.ppf(1 - alpha / 2)
    return (float(np.tanh(z - zc * se)), float(np.tanh(z + zc * se)))


def main():
    d, m = S3.load()
    train_ids, test_ids, acts, err, hn, cyc = S3.prepare(d, m)

    # --- study 3's train-side selection, so tau*/T* match exactly ---
    sel = S3.select_thresholds(train_ids, err, hn, cyc)
    budget_mm, tau_star, period_star = sel["budget_mm"], sel["tau_star"], sel["period_star"]

    # --- the correlation sample, kept in cluster form ---
    per_act_xy = {}
    for a in test_ids:
        x = np.array([hn[a][i] - 1.0 for i in range(len(LIFE))])
        y = np.array([err[a][i][0] for i in range(len(LIFE))])
        per_act_xy[a] = (x, y)
    hx = np.concatenate([per_act_xy[a][0] for a in test_ids])
    ey = np.concatenate([per_act_xy[a][1] for a in test_ids])
    groups = np.concatenate([np.full(len(LIFE), a) for a in test_ids])

    k = len(test_ids)
    combos = list(itertools.product(range(k), repeat=k))  # exhaustive cluster resamples

    def pooled_r(ids):
        x = np.concatenate([per_act_xy[a][0] for a in ids])
        y = np.concatenate([per_act_xy[a][1] for a in ids])
        if x.std() < 1e-15 or y.std() < 1e-15:
            return np.nan
        return float(np.corrcoef(x, y)[0, 1])

    def within_r(ids):
        xs = np.concatenate([per_act_xy[a][0] - per_act_xy[a][0].mean() for a in ids])
        ys = np.concatenate([per_act_xy[a][1] - per_act_xy[a][1].mean() for a in ids])
        if xs.std() < 1e-15 or ys.std() < 1e-15:
            return np.nan
        return float(np.corrcoef(xs, ys)[0, 1])

    r_point = pooled_r(test_ids)
    committed = bootstrap_correlation(hx, ey, n_boot=2000, seed=7)

    boot_r = np.array([pooled_r([test_ids[j] for j in c]) for c in combos])
    fin = boot_r[np.isfinite(boot_r)]
    cluster_boot = {
        "method": "exhaustive nonparametric cluster bootstrap over actuator identities",
        "n_clusters": k,
        "n_resamples": len(combos),
        "n_degenerate": int(len(combos) - fin.size),
        "r": r_point,
        "ci_low": _q(fin, 0.025),
        "ci_high": _q(fin, 0.975),
        "se": float(fin.std(ddof=1)),
    }

    loao = []
    for a in test_ids:
        rest = [b for b in test_ids if b != a]
        loao.append(
            {
                "held_out_actuator": int(a),
                "r_without": pooled_r(rest),
                "r_within_that_actuator": float(np.corrcoef(*per_act_xy[a])[0, 1]),
            }
        )
    r_loao = np.array([e["r_without"] for e in loao])
    tc = float(tdist.ppf(1 - (1 - CI) / 2, k - 1))

    jack_se = float(np.sqrt((k - 1) / k * np.sum((r_loao - r_loao.mean()) ** 2)))
    loao_r = {
        "method": "delete-one-actuator jackknife on r (reported for transparency only)",
        "jackknife_se": jack_se,
        "ci_low": float(r_point - tc * jack_se),
        "ci_high": float(min(1.0, r_point + tc * jack_se)),
        "note": "r is bounded by 1, so this interval can reach the boundary; prefer the "
        "Fisher-z version below.",
    }
    z_loao = np.arctanh(r_loao)
    z_se = float(np.sqrt((k - 1) / k * np.sum((z_loao - z_loao.mean()) ** 2)))
    loao_z = {
        "method": "delete-one-actuator jackknife on Fisher z",
        "jackknife_se_z": z_se,
        "ci_low": float(np.tanh(np.arctanh(r_point) - tc * z_se)),
        "ci_high": float(np.tanh(np.arctanh(r_point) + tc * z_se)),
        "n_folds": k,
        "folds": loao,
    }

    wb = np.array([within_r([test_ids[j] for j in c]) for c in combos])
    wbf = wb[np.isfinite(wb)]
    within = {
        "r_within_actuator": within_r(test_ids),
        "ci_low": _q(wbf, 0.025),
        "ci_high": _q(wbf, 0.975),
        "note": "actuator-mean-centred x and y (actuator fixed effects removed); a different "
        "estimand from the pooled r, not a competing interval for it",
    }
    per_act = per_group_correlations(groups, hx, ey)
    per_act["values"] = [
        {"actuator_id": rec["group"], "r": rec["r"], "n": rec["n"]} for rec in per_act["values"]
    ]

    # --- health-indicator quality metrics (reviewer_backlog item 1) ---
    ind = {a: per_act_xy[a][0] for a in test_ids}          # fractional loop-area growth
    mono = np.array([monotonicity(ind[a]) for a in test_ids], float)
    mono_boot = np.array([mono[list(c)].mean() for c in combos])
    trend_all = trendability(np.vstack([ind[a] for a in test_ids]))
    trend_loao = [
        {
            "held_out_actuator": int(a),
            "trendability_without": trendability(
                np.vstack([ind[b] for b in test_ids if b != a])
            ),
        }
        for a in test_ids
    ]
    starts = np.array([ind[a][0] for a in test_ids], float)
    ends = np.array([ind[a][-1] for a in test_ids], float)
    prog = prognosability(starts, ends)
    prog_boot = [prognosability(starts[list(c)], ends[list(c)]) for c in combos]
    prog_vals = np.array([p.value for p in prog_boot], float)
    prog_fin = prog_vals[np.isfinite(prog_vals)]

    # --- structural check: is the normalised indicator actuator-specific at all? ---
    # hn is h / h[0]. If pv_loop_area scales linearly with the stiffness state, the
    # normalisation cancels every actuator parameter and the indicator collapses to a
    # deterministic function of life fraction. That would make all three HI quality
    # metrics degenerate and every actuator trigger at the same life fraction, so it is
    # checked here rather than assumed.
    ind_matrix = np.vstack([per_act_xy[a][0] for a in test_ids])
    across_cohort = float(np.max(np.abs(ind_matrix - ind_matrix[0])))
    probe_params = [
        (1.0, 1.0, 0.10, 4000.0), (3.7, 0.9, 0.05, 9000.0),
        (0.4, 5.0, 0.90, 1500.0), (12.0, 0.2, 0.30, 30000.0),
    ]
    probe_curves = []
    for k1, k2, tau_p, rup in probe_params:
        h = health_trajectory(SLSParams(k1=k1, k2=k2, tau=tau_p), rup, LIFE)
        probe_curves.append(h / h[0] - 1.0)
    probe_matrix = np.vstack(probe_curves)
    across_sweep = float(np.max(np.abs(probe_matrix - probe_matrix[0])))
    invariant = across_cohort < 1e-9 and across_sweep < 1e-9
    invariance = {
        "max_abs_indicator_deviation_across_heldout_actuators": across_cohort,
        "max_abs_indicator_deviation_across_wide_parameter_sweep": across_sweep,
        "swept_parameters_k1_k2_tau_rupture": [list(p) for p in probe_params],
        "indicator_is_actuator_invariant": bool(invariant),
        "distinct_x_values": int(np.unique(np.round(hx, 12)).size),
        "consequence": (
            "The normalised indicator is a deterministic function of life fraction: "
            "normalising by the young value cancels the actuator parameters. The 30-point "
            "correlation sample therefore has only 5 distinct x values, each repeated once "
            "per actuator, and all between-actuator variation lives in y (pose error). "
            "Every actuator crosses any threshold at the same life fraction, which is why "
            "the recalibration counts and the HI quality metrics below are degenerate. "
            "Claims about per-actuator prognostic discrimination are not supported by this "
            "cohort."
        ) if invariant else "Indicator varies across actuators; metrics below are informative.",
    }

    hi_status = "degenerate_actuator_invariant_indicator" if invariant else "ok"
    hi_metrics = {
        "status": hi_status,
        "interpretation_warning": (
            "All three metrics are computed on a single shared curve because the indicator is "
            "actuator-invariant (see indicator_invariance_check). Values at or near 1.0 "
            "describe the fatigue law's shape, NOT the indicator's ability to discriminate "
            "between actuators, and must not be reported as evidence of indicator quality."
        ) if invariant else None,
        "indicator": "fractional P-V loop-area growth from young (hn - 1)",
        "monotonicity": {
            "per_actuator": [float(v) for v in mono],
            "mean": float(mono.mean()),
            "min": float(mono.min()),
            "max": float(mono.max()),
            "ci_low": _q(mono_boot, 0.025),
            "ci_high": _q(mono_boot, 0.975),
            "definition": "|(#increasing - #decreasing)| / #steps; 1.0 = perfectly monotone",
        },
        "trendability": {
            "value": float(trend_all),
            "definition": "minimum absolute pairwise correlation across the 6 held-out "
            "indicator trajectories on the shared life grid",
            "leave_one_actuator_out": trend_loao,
            "loao_min": float(min(t["trendability_without"] for t in trend_loao)),
            "loao_max": float(max(t["trendability_without"] for t in trend_loao)),
            "note": "a minimum over pairs is not a mean, so it has no cluster-bootstrap "
            "interval; the delete-one-actuator range is reported instead",
        },
        "prognosability": {
            **asdict(prog),
            "ci_low": _q(prog_fin, 0.025) if prog_fin.size else None,
            "ci_high": _q(prog_fin, 0.975) if prog_fin.size else None,
            "n_degenerate_resamples": int(prog_vals.size - prog_fin.size),
            "definition": "exp(-std(end) / mean|end - start|) over actuators",
        },
    }

    # --- policy metrics with the same cluster treatment ---
    policies = {name: (np.array(es, float), np.array(rs, float))
                for name, (es, rs) in S3.heldout_policies(test_ids, err, hn, cyc, tau_star, period_star).items()}

    policy_ci = {}
    for name, (e_arr, r_arr) in policies.items():
        e_boot = np.array([e_arr[list(c)].mean() for c in combos])
        r_boot = np.array([r_arr[list(c)].mean() for c in combos])
        policy_ci[name] = {
            "mean_pose_rmse_mm": float(e_arr.mean()),
            "rmse_ci_low": _q(e_boot, 0.025),
            "rmse_ci_high": _q(e_boot, 0.975),
            "rmse_per_actuator": [float(v) for v in e_arr],
            "recal_per_actuator": float(r_arr.mean()),
            "recal_ci_low": _q(r_boot, 0.025),
            "recal_ci_high": _q(r_boot, 0.975),
            "recal_counts_per_actuator": [float(v) for v in r_arr],
            "recal_identical_across_actuators": bool(len(set(r_arr.tolist())) == 1),
        }

    e_t, r_t = policies["triggered"]
    e_a, r_a = policies["always"]
    sav_boot = np.array([1.0 - r_t[list(c)].mean() / r_a[list(c)].mean() for c in combos])
    savings = {
        "point": float(1.0 - r_t.mean() / r_a.mean()),
        "ci_low": _q(sav_boot, 0.025),
        "ci_high": _q(sav_boot, 0.975),
        "degenerate": bool(
            len(set(r_t.tolist())) == 1 and len(set(r_a.tolist())) == 1
        ),
        "note": "when both policies produce identical counts on every held-out actuator the "
        "ratio has no between-actuator variance and the interval is a point; report it as a "
        "deterministic consequence of the life grid, not as an estimate",
    }

    # --- lead-time frontier with cluster CIs ---
    frontier = []
    for tau in S3.LEAD_FRONTIER_TAU:
        recs, errs, recals = S3.lead_records(tau, test_ids, err, hn, acts, budget_mm)
        leads = np.array([np.nan if r["lead_life"] is None else r["lead_life"] for r in recs], float)
        errs = np.array(errs, float)
        recals = np.array(recals, float)
        lb = np.array([np.nanmean(leads[list(c)]) for c in combos])
        eb = np.array([errs[list(c)].mean() for c in combos])
        rb = np.array([recals[list(c)].mean() for c in combos])
        frontier.append(
            {
                "tau": float(tau),
                "mean_lead_life": float(np.nanmean(leads)),
                "lead_ci_low": float(np.nanquantile(lb, 0.025)),
                "lead_ci_high": float(np.nanquantile(lb, 0.975)),
                "lead_per_actuator": [None if np.isnan(v) else float(v) for v in leads],
                "n_nonpositive_lead": int(
                    sum(r["status"] == "nonpositive_lead" for r in recs)
                ),
                "mean_pose_rmse_mm": float(errs.mean()),
                "rmse_ci_low": _q(eb, 0.025),
                "rmse_ci_high": _q(eb, 0.975),
                "recal_per_actuator": float(recals.mean()),
                "recal_ci_low": _q(rb, 0.025),
                "recal_ci_high": _q(rb, 0.975),
                "budget_met_at_upper_ci": bool(_q(eb, 0.975) <= budget_mm),
            }
        )

    results = {
        "provenance": {
            "note": "Re-estimates study 3's uncertainty with the actuator as the resampling "
            "unit. Estimates and pipeline are unchanged.",
            "evidence_type": "simulation",
            "boundary": "synthetic actuator cohort; no physical measurement",
            "dataset_sha256": m.get("npz_sha256"),
            "dataset_sha256_note": (
                "Hash of the dataset.npz present when this ran, read from "
                "data/sim/phaseD/manifest.json. dataset.npz is gitignored and regenerated "
                "locally; the recorded hash is environment-dependent even at the same seed, "
                "so it may differ from the pin in a committed manifest while every downstream "
                "study result still reproduces exactly. Compare per-array values, not the hash."
            ),
            "dataset_seed": m.get("seed"),
            "train_actuators": train_ids,
            "test_actuators": test_ids,
            "tau_selected": tau_star,
            "period_selected_cycles": period_star,
            "accuracy_budget_mm": float(budget_mm),
            "confidence_level": CI,
        },
        "correlation": {
            "r": r_point,
            "n_points": int(hx.size),
            "n_clusters": k,
            "points_per_cluster": len(LIFE),
            "committed_point_level_bootstrap": committed,
            "actuator_cluster_bootstrap": cluster_boot,
            "leave_one_actuator_out_r": loao_r,
            "leave_one_actuator_out_fisher_z": loao_z,
            "within_actuator": within,
            "per_actuator_r": per_act,
            "fisher_ci_at_n_points": fisher_ci(r_point, hx.size),
            "fisher_ci_at_n_clusters": fisher_ci(r_point, k),
        },
        "indicator_invariance_check": invariance,
        "hi_quality_metrics": hi_metrics,
        "policies_on_heldout_with_cluster_ci": policy_ci,
        "recal_savings_triggered_vs_always": savings,
        "lead_frontier_with_cluster_ci": frontier,
    }

    os.makedirs(DATA, exist_ok=True)
    out_path = os.path.join(DATA, "study3_cluster_ci_results.json")
    with open(out_path, "w") as fh:
        json.dump(results, fh, indent=2)

    cb, lz = cluster_boot, loao_z
    print(f"pooled r = {r_point:.4f}   (n = {hx.size} points in {k} actuator clusters)")
    print(
        f"  point-level bootstrap (committed) [{committed['ci_low']:.4f}, "
        f"{committed['ci_high']:.4f}]  width {committed['ci_high'] - committed['ci_low']:.4f}"
    )
    print(
        f"  actuator-cluster bootstrap        [{cb['ci_low']:.4f}, {cb['ci_high']:.4f}]  "
        f"width {cb['ci_high'] - cb['ci_low']:.4f}  ({cb['n_resamples']} exhaustive resamples)"
    )
    print(
        f"  leave-one-actuator-out (Fisher z) [{lz['ci_low']:.4f}, {lz['ci_high']:.4f}]  "
        f"width {lz['ci_high'] - lz['ci_low']:.4f}"
    )
    print(
        f"  within-actuator r = {within['r_within_actuator']:.4f} "
        f"[{within['ci_low']:.4f}, {within['ci_high']:.4f}]   "
        f"per-actuator r median {per_act['median']:.4f}"
    )
    print(
        f"indicator invariance: max deviation across held-out actuators "
        f"{invariance['max_abs_indicator_deviation_across_heldout_actuators']:.2e}, "
        f"across a wide parameter sweep "
        f"{invariance['max_abs_indicator_deviation_across_wide_parameter_sweep']:.2e} -> "
        f"actuator-invariant = {invariance['indicator_is_actuator_invariant']} "
        f"({invariance['distinct_x_values']} distinct x values in {hx.size} points)"
    )
    hm = hi_metrics
    if hm["status"] != "ok":
        print(f"  HI metrics status: {hm['status']} - values below are NOT evidence of quality")
    print(
        f"HI quality: monotonicity {hm['monotonicity']['mean']:.3f} "
        f"[{hm['monotonicity']['ci_low']:.3f}, {hm['monotonicity']['ci_high']:.3f}] | "
        f"trendability {hm['trendability']['value']:.4f} "
        f"(LOAO {hm['trendability']['loao_min']:.4f}-{hm['trendability']['loao_max']:.4f}) | "
        f"prognosability {hm['prognosability']['value']:.4f} [{hm['prognosability']['ci_low']:.4f}, "
        f"{hm['prognosability']['ci_high']:.4f}] ({hm['prognosability']['status']})"
    )
    print(
        f"recal savings triggered vs always {savings['point']:.1%} "
        f"[{savings['ci_low']:.1%}, {savings['ci_high']:.1%}]"
        f"{'  (DEGENERATE - identical counts on every actuator)' if savings['degenerate'] else ''}"
    )
    for name in ("fixed", "scheduled", "triggered", "always"):
        v = policy_ci[name]
        print(
            f"  {name:9s} rmse {v['mean_pose_rmse_mm']:.4f} "
            f"[{v['rmse_ci_low']:.4f}, {v['rmse_ci_high']:.4f}] mm | recal "
            f"{v['recal_per_actuator']:.2f} [{v['recal_ci_low']:.2f}, {v['recal_ci_high']:.2f}]"
        )
    print(f"wrote {out_path}")

    _figures(results, per_act_xy, test_ids)


def _spread(values, gap):
    """Shift sorted label positions apart so neighbours sit at least ``gap`` apart (keeps order)."""
    order = np.argsort(values)
    out = np.asarray(values, dtype=float).copy()
    for prev, cur in zip(order[:-1], order[1:]):
        out[cur] = max(out[cur], out[prev] + gap)
    return out


def _figures(results, per_act_xy, test_ids):
    plt = figstyle.setup()
    if plt is None:  # pragma: no cover
        print("(matplotlib unavailable, skipped figures)")
        return
    COL, S = figstyle.COLOR, figstyle.SIZE
    C = results["correlation"]
    P = results["policies_on_heldout_with_cluster_ci"]
    FR = results["lead_frontier_with_cluster_ci"]
    budget = results["provenance"]["accuracy_budget_mm"]
    tau_star = results["provenance"]["tau_selected"]
    n = C["n_clusters"]

    # ---------- Fig 3b: correlation with cluster-aware intervals ----------
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(figstyle.FULL, 2.9), gridspec_kw={"width_ratios": [1.1, 1],
                                                                                    "wspace": 1.0})
    for a in test_ids:
        x, y = per_act_xy[a]
        ax.plot(x, y, "-", color=COL["unit"], lw=1.0, zorder=2)
        ax.plot(x, y, "o", color=COL["unit"], ms=3.5, mec="white", mew=0.5, zorder=3)
    ends = [per_act_xy[a][1][-1] for a in test_ids]
    ylo, yhi = min(min(per_act_xy[a][1]) for a in test_ids), max(ends)
    for a, y_end, y_lab in zip(test_ids, ends, _spread(ends, (yhi - ylo) * 0.055)):
        ax.annotate(f"#{a}", (per_act_xy[a][0][-1], y_end), xytext=(per_act_xy[a][0][-1] * 1.04, y_lab),
                    textcoords="data", fontsize=S["tick"], color=COL["muted"], va="center")
    X = np.concatenate([per_act_xy[a][0] for a in test_ids])
    Y = np.concatenate([per_act_xy[a][1] for a in test_ids])
    b1, b0 = np.polyfit(X, Y, 1)
    xs = np.linspace(X.min(), X.max(), 50)
    ax.plot(xs, b0 + b1 * xs, "--", color=COL["pv"], lw=1.2, zorder=1)
    ax.text(X.max(), 0.25, f"pooled fit\nr = {C['r']:.3f}", fontsize=S["note"], color=figstyle.ink(COL["pv"]),
            ha="right", va="center")
    ax.set_xlabel("P-V loop-area growth from young")
    ax.set_ylabel("Pose error, young calibration (mm)")
    inv = results.get("indicator_invariance_check", {})
    ax.set_title("Six actuators share one indicator\ntrajectory; only pose error differs"
                 if inv.get("indicator_is_actuator_invariant") else "Pose error against indicator growth")
    ax.margins(x=0.06, y=0.08)
    ax.set_xlim(None, X.max() * 1.18)

    rows = [("point-level bootstrap\n(superseded)", C["committed_point_level_bootstrap"], "#B0B0B0", C["r"], "o"),
            (f"actuator-cluster bootstrap\n(exhaustive, {n}{str(n).translate(str.maketrans('0123456789', '⁰¹²³⁴⁵⁶⁷⁸⁹'))})",
             C["actuator_cluster_bootstrap"], COL["always"],
             C["r"], "o"),
            ("leave-one-actuator-out\n(Fisher z)", C["leave_one_actuator_out_fisher_z"], COL["always"], C["r"], "o"),
            ("within-actuator r\n(different estimand)", C["within_actuator"], COL["muted"],
             C["within_actuator"]["r_within_actuator"], "s")]
    for yp, (lab, v, col, point, mk) in enumerate(rows):
        ax2.plot([v["ci_low"], v["ci_high"]], [yp, yp], "-", color=col, lw=2.2, solid_capstyle="butt")
        ax2.plot(point, yp, mk, color=col, ms=5.5, mec="white", mew=0.8, zorder=4)
        ax2.annotate(f"{v['ci_low']:.2f}–{v['ci_high']:.2f}", (v["ci_high"], yp), xytext=(5, 0),
                     textcoords="offset points", va="center", fontsize=S["note"], color=col)
    ax2.set_yticks(range(len(rows)), [r[0] for r in rows])
    ax2.set_ylim(len(rows) - 0.5, -0.6)
    ax2.tick_params(axis="y", length=0)
    ax2.set_xlim(0.5, 1.12)
    ax2.set_xticks([0.6, 0.7, 0.8, 0.9, 1.0])
    ax2.set_xlabel("Pearson r, point and 95 % interval")
    ax2.set_title("The interval depends on what is\nresampled; the estimate does not")
    figstyle.panel_letter(ax, "a", dx=-40)
    figstyle.panel_letter(ax2, "b", dx=-118)
    figstyle.footnote(fig, f"Simulation: {n} held-out actuators × {C['points_per_cluster']} life stages, but only "
                      f"{inv.get('distinct_x_values', '?')} distinct indicator values because the indicator is the "
                      "same for every actuator. Labels: actuator id.")
    figstyle.save(fig, os.path.join(DATA, "study3_fig3b_correlation_cluster_ci"))
    plt.close(fig)

    # Fig 4b keeps nothing of the old style; it is drawn after Fig 3b so figure_style.apply()
    # cannot change Fig 3b's rcParams.
    plot_cluster_tradeoff(results)


FIG4B = "study3_fig4b_recal_cluster_ci"


def cluster_tradeoff_caption(results):
    P, FR = results["policies_on_heldout_with_cluster_ci"], results["lead_frontier_with_cluster_ci"]
    prov = results["provenance"]
    budget, tau_star, n = prov["accuracy_budget_mm"], prov["tau_selected"], results["correlation"]["n_clusters"]
    level = f"{prov['confidence_level'] * 100:.0f} %"
    keys = [k for k, _, _ in S3.POLICIES]
    varies = [S3.SHORT[k] for k in keys if not P[k]["recal_identical_across_actuators"]]
    values = "; ".join(f"{S3.SHORT[k]} {P[k]['mean_pose_rmse_mm']:.3f} mm [{P[k]['rmse_ci_low']:.3f}, "
                       f"{P[k]['rmse_ci_high']:.3f}] with {P[k]['recal_per_actuator']:.1f} "
                       f"[{P[k]['recal_ci_low']:.2f}, {P[k]['recal_ci_high']:.2f}] calibrations" for k in keys)
    late = [p["tau"] for p in FR if p["mean_lead_life"] <= 0]
    last = FR[-1]
    return (
        f"Recalibration policies and the lead frontier on the {n} held-out actuators of the Phase D cohort, "
        f"with {level} actuator-cluster bootstrap intervals. (a) Mean pose RMSE against calibrations per actuator "
        f"over life, with intervals on both axes, for "
        f"{S3.policy_sentence(prov['period_selected_cycles'], tau_star)}. Counts include the initial calibration; "
        "an interval of zero width is not drawn. "
        f"The dashed line is the train-derived error budget, {budget:.3f} mm; a filled marker meets it and a "
        f"hollow marker exceeds it. Values with intervals: {values}. Only {' and '.join(varies)} varies in "
        "calibration count across actuators. (b) Lead of the trigger over the error-budget crossing, in life "
        "fraction, against the trigger threshold τ (loop-area growth). Circles and the solid line are the mean "
        f"over actuators, the grey band is its {level} interval and the thin grey lines are the individual "
        "actuators. A filled circle warns early (positive mean lead); a hollow circle warns late. The solid "
        "horizontal line is zero lead and the dash-dot line is the deployed threshold τ = "
        f"{tau_star:g}. Mean lead turns negative from τ = {min(late):g}; at the deployed threshold it is "
        f"{last['mean_lead_life']:.3f} [{last['lead_ci_low']:.3f}, {last['lead_ci_high']:.3f}] life, with "
        f"{last['n_nonpositive_lead']} of {n} actuators late. Simulation only. Source: "
        "study3_cluster_ci_results.json."
    )


def cluster_tradeoff_figure(results):
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    import matplotlib.pyplot as plt
    from scripts import figure_style as style

    style.apply()
    P, FR = results["policies_on_heldout_with_cluster_ci"], results["lead_frontier_with_cluster_ci"]
    prov = results["provenance"]
    budget, tau_star = prov["accuracy_budget_mm"], prov["tau_selected"]
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(style.FULL, 3.4))
    fig.subplots_adjust(left=.085, right=.985, top=.76, bottom=.14, wspace=.32)
    axA.axhline(budget, zorder=1, **style.REFERENCE)
    for key, _, marker in S3.POLICIES:
        v = P[key]
        x, y = v["recal_per_actuator"], v["mean_pose_rmse_mm"]
        # Intervals as plain capped lines (errorbar's LineCollection has no window extent for the
        # overlap audit); an interval of zero width is not drawn.
        for xs, ys, cap in (([v["recal_ci_low"], v["recal_ci_high"]], [y, y], "|"),
                            ([x, x], [v["rmse_ci_low"], v["rmse_ci_high"]], "_")):
            if xs[0] != xs[1] or ys[0] != ys[1]:
                axA.plot(xs, ys, color=style.INK, lw=.8, marker=cap, ms=5, mew=.8, zorder=2)
        axA.plot(x, y, marker=marker, mfc=style.FILL[y <= budget], zorder=3, **style.MARKER)
    axA.set_xlim(0.5, 5.7)
    axA.set_ylim(0, 0.62)
    axA.set_xlabel("Calibrations per actuator over life")
    axA.set_ylabel("Mean pose RMSE (mm)")

    taus = np.array([p["tau"] for p in FR])
    per = np.array([p["lead_per_actuator"] for p in FR])
    for j in range(per.shape[1]):
        axB.plot(taus, per[:, j], color=SINGLE_GREY, lw=.6, zorder=1)
    axB.fill_between(taus, [p["lead_ci_low"] for p in FR], [p["lead_ci_high"] for p in FR],
                     color=BAND_GREY, lw=0, zorder=0)
    axB.plot(taus, [p["mean_lead_life"] for p in FR], color=style.INK, lw=1.0, zorder=3)
    for p in FR:
        axB.plot(p["tau"], p["mean_lead_life"], marker="o", mfc=style.FILL[p["mean_lead_life"] > 0], zorder=4,
                 **style.MARKER)
    axB.axhline(0, color=style.INK, lw=.6, zorder=2)
    axB.axvline(tau_star, zorder=2, **DEPLOYED)
    axB.set_xlabel(r"Trigger threshold $\tau$ (loop-area growth)")
    axB.set_ylabel("Lead over the budget crossing (life)")
    axB.set_xlim(0, taus.max() * 1.08)
    axB.set_ylim(-0.36, 0.56)
    axB.set_xticks([0.01, 0.02, 0.03, 0.04, 0.05])
    for i, ax in enumerate((axA, axB)):
        style.letter(ax, i, x=-.14)
    level = f"{prov['confidence_level'] * 100:.0f} %"
    extra = [Line2D([], [], label="Error budget", **style.REFERENCE),
             Line2D([], [], color=style.INK, marker="o", ms=5, mew=.9, mfc=style.FILL[True], label="Mean lead"),
             Line2D([], [], color=SINGLE_GREY, lw=.6, label="Single actuator"),
             Patch(color=BAND_GREY, lw=0, label=f"{level} cluster interval"),
             Line2D([], [], label=r"Deployed $\tau$", **DEPLOYED),
             Line2D([], [], marker="s", mfc=style.FILL[False], label="Hollow: above budget (a), late (b)",
                    **style.MARKER)]
    S3.policy_legend(fig, prov["period_selected_cycles"], tau_star, extra, ncol=4)
    return fig


# Achromatic greys for context only: individual actuators and the interval band.
SINGLE_GREY, BAND_GREY = "0.6", "0.85"
DEPLOYED = {"color": "black", "lw": .8, "ls": "-."}


def plot_cluster_tradeoff(results):
    import matplotlib.pyplot as plt
    from scripts import figure_style as style

    fig = cluster_tradeoff_figure(results)
    style.save(fig, os.path.join(DATA, FIG4B), caption=cluster_tradeoff_caption(results))
    plt.close(fig)
    print(f"wrote {DATA}/{FIG4B}.(png|pdf)")


def replot():
    """Redraw from the saved result. Fig 4b needs only the JSON; Fig 3b is redrawn only when the
    regenerated dataset is present, because its per-actuator points come from it."""
    results = json.load(open(os.path.join(DATA, "study3_cluster_ci_results.json")))
    if os.path.exists(os.path.join(DATA, "dataset.npz")):
        d, m = S3.load()
        _, test_ids, _, err, hn, _ = S3.prepare(d, m)
        per_act_xy = {a: (np.array([hn[a][i] - 1.0 for i in range(len(LIFE))]),
                          np.array([err[a][i][0] for i in range(len(LIFE))])) for a in test_ids}
        _figures(results, per_act_xy, test_ids)
    else:
        plot_cluster_tradeoff(results)
    print("replotted from the saved result")


if __name__ == "__main__":
    import sys
    if "--replot" in sys.argv:
        replot()
    else:
        main()
