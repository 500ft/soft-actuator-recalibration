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


def _figures(results, per_act_xy, test_ids):
    plt = figstyle.setup()
    if plt is None:  # pragma: no cover
        print("(matplotlib unavailable, skipped figures)")
        return

    C = results["correlation"]
    P = results["policies_on_heldout_with_cluster_ci"]
    FR = results["lead_frontier_with_cluster_ci"]
    budget = results["provenance"]["accuracy_budget_mm"]
    tau_star = results["provenance"]["tau_selected"]
    pal = figstyle.PALETTE
    act_col = [pal[0], pal[4], pal[2], pal[3], pal[5], pal[1]]
    grey = "#5A5A5A"
    S_LAB, S_NOTE = 8.0, 7.0

    # ---------- Fig 3b: correlation with cluster-aware intervals ----------
    fig = plt.figure(figsize=(7.4, 3.3))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.15, 1.0], wspace=0.42)
    ax = fig.add_subplot(gs[0, 0])
    label_dy = {0: 2, 1: 0, 2: 3.5, 3: 1, 4: 1, 5: -4.5}
    for i, a in enumerate(test_ids):
        x, y = per_act_xy[a]
        ax.plot(x, y, "-", color=act_col[i], lw=1.0, alpha=0.85, zorder=2)
        ax.plot(x, y, "o", color=act_col[i], ms=4.2, mec="white", mew=0.6, zorder=3)
        ax.annotate(
            f"#{a}", (x[-1], y[-1]), textcoords="offset points",
            xytext=(4, label_dy[i]), fontsize=S_NOTE, color=act_col[i], va="center",
        )
    X = np.concatenate([per_act_xy[a][0] for a in test_ids])
    Y = np.concatenate([per_act_xy[a][1] for a in test_ids])
    b1, b0 = np.polyfit(X, Y, 1)
    xs = np.linspace(X.min(), X.max(), 50)
    ax.plot(xs, b0 + b1 * xs, "--", color=grey, lw=1.3, zorder=1)
    ax.annotate(
        f"pooled fit\nr = {C['r']:.3f}",
        (xs[len(xs) // 2], b0 + b1 * xs[len(xs) // 2]),
        textcoords="offset points", xytext=(-6, 26), fontsize=S_LAB, color=grey, ha="right",
    )
    ax.set_xlabel("fractional P-V loop-area growth from young  [–]", fontsize=S_LAB + 1)
    ax.set_ylabel("pose error at young calibration  [mm]", fontsize=S_LAB + 1)
    inv = results.get("indicator_invariance_check", {})
    if inv.get("indicator_is_actuator_invariant"):
        title_a = "All six actuators share one indicator\ntrajectory; only the pose error differs"
        note_a = (f"{C['n_clusters']} held-out actuators x {C['points_per_cluster']} life stages, "
                  f"but only {inv['distinct_x_values']} distinct x values\n"
                  f"(indicator is actuator-invariant, so the x positions coincide)")
    else:
        title_a = "Each actuator traces the same tight\ntrend; pooling them loosens it"
        note_a = f"{C['n_clusters']} held-out actuators x {C['points_per_cluster']} life stages"
    ax.set_title(title_a, loc="left", fontsize=S_LAB + 1)
    ax.margins(0.11)
    ax.set_ylim(-0.30, None)
    ax.xaxis.labelpad = 7
    ax.tick_params(labelsize=S_NOTE)
    fig.text(0.005, -0.03, note_a.replace("\n", " "), fontsize=S_NOTE, color=grey,
             va="top", ha="left")

    ax2 = fig.add_subplot(gs[0, 1])
    rows = [
        ("point-level bootstrap\n(as previously reported)", C["committed_point_level_bootstrap"], "#B0B0B0"),
        ("actuator-cluster bootstrap\n(exhaustive, 6\u2076 resamples)", C["actuator_cluster_bootstrap"], pal[0]),
        ("leave-one-actuator-out\njackknife (Fisher z)", C["leave_one_actuator_out_fisher_z"], pal[1]),
    ]
    for (lab, v, col), yp in zip(rows, [2.6, 1.6, 0.6]):
        ax2.plot([v["ci_low"], v["ci_high"]], [yp, yp], "-", color=col, lw=2.4, solid_capstyle="round")
        ax2.plot([v["ci_low"], v["ci_high"]], [yp, yp], "|", color=col, ms=7, mew=1.6)
        ax2.plot(C["r"], yp, "o", color=col, ms=6, mec="white", mew=0.8, zorder=4)
        ax2.text(0.245, yp + 0.22, lab, fontsize=S_LAB - 0.5, va="bottom", ha="left", color="black")
        ax2.text(v["ci_high"] + 0.014, yp, f"[{v['ci_low']:.2f}, {v['ci_high']:.2f}]",
                 fontsize=S_NOTE, va="center", color=col)
    w = C["within_actuator"]
    ax2.plot([w["ci_low"], w["ci_high"]], [-0.45, -0.45], "-", color=pal[2], lw=2.4, solid_capstyle="round")
    ax2.plot([w["ci_low"], w["ci_high"]], [-0.45, -0.45], "|", color=pal[2], ms=7, mew=1.6)
    ax2.plot(w["r_within_actuator"], -0.45, "s", color=pal[2], ms=5.5, mec="white", mew=0.8, zorder=4)
    ax2.text(0.245, -0.30, "within-actuator r — different estimand\n(actuator offsets removed)",
             fontsize=S_LAB - 0.5, va="bottom", color=pal[2])
    ax2.text(w["ci_high"] + 0.014, -0.45, f"[{w['ci_low']:.2f}, {w['ci_high']:.2f}]",
             fontsize=S_NOTE, va="center", color=pal[2])
    ax2.set_xlim(0.24, 1.20)
    ax2.set_ylim(-0.72, 3.6)
    ax2.set_yticks([])
    ax2.spines["left"].set_visible(False)
    ax2.set_xticks([0.4, 0.6, 0.8, 1.0])
    ax2.grid(axis="y", visible=False)
    ax2.tick_params(labelsize=S_NOTE)
    ax2.xaxis.labelpad = 7
    ax2.set_xlabel("Pearson r  (point and 95% interval)", fontsize=S_LAB + 1)
    ax2.set_title("The interval depends on what you resample,\nnot on the estimate",
                  loc="left", fontsize=S_LAB + 1)
    for a_, L in ((ax, "a"), (ax2, "b")):
        a_.text(-0.14, 1.06, L, transform=a_.transAxes, fontsize=11, fontweight="bold", va="bottom")
    figstyle.save(fig, os.path.join(DATA, "study3_fig3b_correlation_cluster_ci"))
    plt.close(fig)

    # ---------- Fig 4b: recalibration trade-off + lead frontier ----------
    fig2 = plt.figure(figsize=(7.6, 3.4))
    gs2 = fig2.add_gridspec(1, 2, wspace=0.34)
    axA = fig2.add_subplot(gs2[0, 0])
    order = [
        ("fixed", "never recalibrate", pal[1]),
        ("scheduled", f"fixed clock (every {results['provenance']['period_selected_cycles']:.0f} cycles)", pal[4]),
        ("triggered", f"P-V triggered (\u03c4* = {tau_star})", pal[0]),
        ("always", "recalibrate at every stage", pal[2]),
    ]
    for key, lab, col in order:
        v = P[key]
        axA.errorbar(
            v["recal_per_actuator"], v["mean_pose_rmse_mm"],
            xerr=[[v["recal_per_actuator"] - v["recal_ci_low"]], [v["recal_ci_high"] - v["recal_per_actuator"]]],
            yerr=[[v["mean_pose_rmse_mm"] - v["rmse_ci_low"]], [v["rmse_ci_high"] - v["mean_pose_rmse_mm"]]],
            fmt="o", color=col, ms=6.5, mec="white", mew=0.8, elinewidth=1.6, capsize=3,
            zorder=3, label=lab,
        )
    axA.axhline(budget, color=grey, lw=1.0, ls="--")
    axA.text(0.98, budget + 0.010, f"accuracy budget {budget:.3f} mm",
             fontsize=S_NOTE, color=grey, ha="left", va="bottom")
    axA.legend(loc="upper right", frameon=False, fontsize=S_LAB - 0.5,
               handletextpad=0.4, borderaxespad=0.2, labelspacing=0.45)
    axA.set_xlabel("recalibrations per actuator over life  [count]", fontsize=S_LAB + 1)
    axA.set_ylabel("mean pose RMSE  [mm]", fontsize=S_LAB + 1)
    axA.set_title("Only the fixed-clock baseline varies\nacross actuators", loc="left", fontsize=S_LAB + 1)
    axA.set_xlim(0.3, 5.7)
    axA.set_ylim(0.0, 0.66)
    axA.xaxis.labelpad = 7
    axA.tick_params(labelsize=S_NOTE)
    fig2.text(0.005, -0.03,
              "Bars are 95% actuator-cluster bootstrap intervals; in panel a lower-left is better.",
              fontsize=S_NOTE, color=grey, va="top", ha="left")

    axB = fig2.add_subplot(gs2[0, 1])
    taus = np.array([p["tau"] for p in FR])
    lead = np.array([p["mean_lead_life"] for p in FR])
    lo = np.array([p["lead_ci_low"] for p in FR])
    hi = np.array([p["lead_ci_high"] for p in FR])
    axB.fill_between(taus, lo, hi, color=pal[0], alpha=0.18, lw=0)
    axB.plot(taus, lead, "-o", color=pal[0], lw=1.5, ms=4.5, mec="white", mew=0.6, zorder=3)
    axB.axhline(0, color="black", lw=0.9)
    axB.axvline(tau_star, color=pal[1], lw=1.2, ls="--")
    best = min(FR, key=lambda p: abs(p["tau"] - 0.01))
    axB.text(
        0.97, 0.97,
        f"\u03c4 = {best['tau']}: mean lead {best['mean_lead_life']:+.3f} life\n"
        f"95% CI [{best['lead_ci_low']:.3f}, {best['lead_ci_high']:.3f}]\n"
        f"{best['recal_per_actuator']:.0f} recalibrations, within budget",
        transform=axB.transAxes, fontsize=S_LAB - 0.5, color=pal[0],
        ha="right", va="top", linespacing=1.4,
    )
    axB.text(taus.max() * 0.976, -0.255,
             f"deployed \u03c4* = {tau_star}: lead {FR[-1]['mean_lead_life']:+.3f} life,\n"
             f"{FR[-1]['n_nonpositive_lead']}/{C['n_clusters']} actuators negative",
             fontsize=S_LAB - 0.5, color=pal[1], ha="right", va="bottom")
    axB.text(0.0012, 0.028, "warns before breach", fontsize=S_NOTE, color=grey, va="bottom")
    axB.text(0.0012, -0.030, "warns after breach", fontsize=S_NOTE, color=grey, va="top")
    axB.set_xlabel("trigger threshold \u03c4  [–]", fontsize=S_LAB + 1)
    axB.set_ylabel("mean lead over budget violation  [life fraction]", fontsize=S_LAB + 1)
    axB.set_title("The deployed threshold fires after the\nerror budget is already breached",
                  loc="left", fontsize=S_LAB + 1)
    axB.set_xlim(0.0, taus.max() * 1.11)
    axB.set_ylim(-0.30, 0.66)
    axB.set_xticks([t for t in taus if abs(t * 1000 % 10) < 1e-9])   # drop the 0.005 tick
    axB.xaxis.labelpad = 7
    axB.tick_params(labelsize=S_NOTE)
    for a_, L in ((axA, "a"), (axB, "b")):
        a_.text(-0.17, 1.06, L, transform=a_.transAxes, fontsize=11, fontweight="bold", va="bottom")
    figstyle.save(fig2, os.path.join(DATA, "study3_fig4b_recal_cluster_ci"))
    plt.close(fig2)
    print(f"wrote {DATA}/study3_fig3b_correlation_cluster_ci.(png|pdf) and "
          f"{DATA}/study3_fig4b_recal_cluster_ci.(png|pdf)")


if __name__ == "__main__":
    main()
