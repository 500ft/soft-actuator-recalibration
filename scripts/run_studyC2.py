"""Study C2 — is the Study C limitation the clock prior, the probe schedule, or the signal?

Runs the frozen (input arm x schedule) grid from
docs/specs/observability-program/studyC2-preregistration.md. The design lives in
``pipeline.schedules``; this runner consumes it and does not redefine it.

Writes only to data/sim/studyC2/. Study C's artifacts are never touched, and the reference cell is
asserted against the committed Study C held-out rows before anything is interpreted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess

import numpy as np

from pipeline.dispersion import SEED, sample_units
from pipeline.identifiability import measured_features
from pipeline.schedules import (ARMS, SCHEDULES, arm_columns, below_median_subset,
                                interpretation_label, materially_reduced, passes_c_rule, probe_seed,
                                probes_for)
from scripts import figstyle
from scripts.run_studyC import (DATA as STUDYC_DATA, LAMBDAS, N_BOOT, N_TRAIN, N_UNITS, PASS_RMSE,
                                ridge_fit, ridge_predict, rmse)
from scripts.run_studyB import theta_of

DATA = "data/sim/studyC2"
PREREG = "docs/specs/observability-program/studyC2-preregistration.md"
STUDYC_RESULTS = os.path.join(STUDYC_DATA, "studyC_results.json")
REFERENCE_TOL = 1e-9
GENERATOR_FILES = ("scripts/run_studyC2.py", "pipeline/schedules.py", "pipeline/dispersion.py",
                   "pipeline/identifiability.py", "scripts/run_studyC.py")


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def git_head():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:                                            # pragma: no cover
        return None


def unit_records(unit, index, schedule_id):
    """Per-probe rows under one schedule. Mirrors Study C's construction exactly; only the probe
    cycles and the seed namespace vary. Normalised life is a target and a diagnostic, never an input."""
    cycles = probes_for(schedule_id, unit.fatigue.rupture_cycles, unit.fatigue.acceleration_onset_fraction)
    us = cycles / unit.fatigue.rupture_cycles
    base = measured_features(theta_of(unit, us[0]), unit.fatigue, unit.sls,
                             probe_seed(schedule_id, index, 0))
    rows, prev = [], None
    for k, (n, u) in enumerate(zip(cycles, us)):
        y = measured_features(theta_of(unit, u), unit.fatigue, unit.sls,
                              probe_seed(schedule_id, index, k + 1))
        lr = np.log(y / base)
        lag = lr if prev is None else prev
        rows.append({"x": np.concatenate([lr, lag, [n / 1000.0]]), "u": float(u), "cycles": float(n),
                     "post_onset": bool(u >= unit.fatigue.acceleration_onset_fraction)})
        prev = lr
    return rows


def stack(records, columns):
    """Design matrix restricted to one arm's columns, plus targets."""
    return np.array([r["x"][columns] for r in records]), np.array([r["u"] for r in records])


def choose_lambda(train_records, columns):
    """Leave-one-unit-out over training units only, for this (arm, schedule) cell."""
    scores = {}
    for lam in LAMBDAS:
        errs = []
        for i in range(len(train_records)):
            X, y = stack([r for j, rows in enumerate(train_records) if j != i for r in rows], columns)
            Xi, yi = stack(train_records[i], columns)
            errs.append(rmse(ridge_predict(ridge_fit(X, y, lam), Xi), yi))
        scores[str(lam)] = float(np.mean(errs))
    best = min(scores, key=scores.get)
    return float(best), scores


def evaluate_cell(units, records, test_idx, columns, model, median_rupture, reference_counts):
    rows = []
    for i in test_idx:
        unit, recs = units[i], records[i]
        X, y = stack(recs, columns)
        pred = ridge_predict(model, X)
        cycles = np.array([r["cycles"] for r in recs])
        post = np.array([r["post_onset"] for r in recs])
        clock = np.clip(cycles / median_rupture, 0.0, 1.0)
        e = rmse(pred, y)
        rows.append({
            "unit": i, "rupture_cycles": unit.fatigue.rupture_cycles,
            "onset": unit.fatigue.acceleration_onset_fraction,
            "n_probes": len(recs), "n_post_onset": int(post.sum()),
            "fraction_post_onset": float(post.mean()),
            "probe_cost_ratio_vs_reference": float(len(recs) / reference_counts[i]),
            "rmse": e, "rmse_clock": rmse(clock, y), "rmse_minus_clock": float(e - rmse(clock, y)),
            "rmse_pre_onset": rmse(pred[~post], y[~post]) if (~post).any() else None,
            "rmse_post_onset": rmse(pred[post], y[post]) if post.any() else None,
            "within_target": bool(e <= PASS_RMSE), "beats_clock": bool(e < rmse(clock, y)),
        })
    return rows


def summarise(rows, seed_offset):
    err = np.array([r["rmse"] for r in rows])
    n_within = int(sum(r["within_target"] for r in rows))
    n_beats = int(sum(r["beats_clock"] for r in rows))
    rng = np.random.default_rng(SEED + seed_offset)
    boot = np.array([err[rng.integers(0, err.size, err.size)].mean() for _ in range(N_BOOT)])
    loo = [float(np.delete(err, i).mean()) for i in range(err.size)]
    return {
        "n_units": len(rows), "mean_rmse": float(err.mean()),
        "mean_rmse_clock": float(np.mean([r["rmse_clock"] for r in rows])),
        "n_within_target": n_within, "n_beats_clock": n_beats,
        "passes_c_rule": passes_c_rule(n_within, n_beats, len(rows)),
        "cluster_bootstrap_ci": [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))],
        "leave_one_unit_out_range": [min(loo), max(loo)],
        "mean_probes_per_unit": float(np.mean([r["n_probes"] for r in rows])),
        "mean_post_onset_probes": float(np.mean([r["n_post_onset"] for r in rows])),
        "total_probe_cost_ratio_vs_reference": float(np.mean([r["probe_cost_ratio_vs_reference"] for r in rows])),
        "failing_units": [r["unit"] for r in rows if not r["within_target"]],
    }


def verify_reference_cell(rows, committed):
    """The reference schedule with the full arm must reproduce the committed Study C rows."""
    by_unit = {h["rupture_cycles"]: h for h in committed["heldout"]}
    for r in rows:
        want = by_unit[r["rupture_cycles"]]
        if abs(r["rmse"] - want["rmse"]) > REFERENCE_TOL:
            raise SystemExit(
                f"C2 abort: the reference cell does not reproduce Study C. Unit {r['unit']} u-RMSE "
                f"{r['rmse']:.12g} vs committed {want['rmse']:.12g}. Repair provenance before "
                f"interpreting any C2 result.")
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--overwrite", action="store_true",
                    help="replace an existing result from a different preregistration revision "
                         "(documented use: a disposable checkout)")
    args = ap.parse_args(argv)

    prereg_hash = sha256(PREREG)
    out_path = os.path.join(DATA, "studyC2_results.json")
    if os.path.exists(out_path) and not args.overwrite:
        prior = json.load(open(out_path)).get("preregistration_sha256")
        if prior != prereg_hash:
            raise SystemExit(f"C2 abort: {out_path} was produced under preregistration {prior} but this "
                             f"run uses {prereg_hash}. Re-run with --overwrite in a disposable checkout.")

    committed = json.load(open(STUDYC_RESULTS))
    studyc_hashes_before = {p: sha256(os.path.join(STUDYC_DATA, p)) for p in os.listdir(STUDYC_DATA)}

    units = sample_units(N_UNITS, SEED)
    order = np.random.default_rng(SEED + 1).permutation(N_UNITS)
    train_idx, test_idx = sorted(order[:N_TRAIN].tolist()), sorted(order[N_TRAIN:].tolist())
    if train_idx != committed["train_units"] or test_idx != committed["test_units"]:
        raise SystemExit("C2 abort: split differs from Study C's committed split")
    median_rupture = float(np.median([units[i].fatigue.rupture_cycles for i in train_idx]))
    below_median = below_median_subset({i: units[i].fatigue.rupture_cycles for i in test_idx}, median_rupture)

    records_by_schedule, reference_counts = {}, None
    for schedule_id in sorted(SCHEDULES):
        recs = [unit_records(u, i, schedule_id) for i, u in enumerate(units)]
        records_by_schedule[schedule_id] = recs
        if schedule_id == "reference":
            reference_counts = {i: len(recs[i]) for i in range(N_UNITS)}
        print(f"  probed {schedule_id}")

    cells, reference_verified = [], False
    for schedule_id in sorted(SCHEDULES):
        recs = records_by_schedule[schedule_id]
        for arm in ARMS:
            columns = arm_columns(arm)
            train = [recs[i] for i in train_idx]
            lam, lam_scores = choose_lambda(train, columns)
            X, y = stack([r for rows in train for r in rows], columns)
            model = ridge_fit(X, y, lam)
            rows = evaluate_cell(units, recs, test_idx, columns, model, median_rupture, reference_counts)
            if schedule_id == "reference" and arm == "full":
                reference_verified = verify_reference_cell(rows, committed)
            s = summarise(rows, seed_offset=2)
            cells.append({"schedule": schedule_id, "arm": arm,
                          "feasible": bool(SCHEDULES[schedule_id]["feasible"]),
                          "lambda_selected": lam, "lambda_loo_scores": lam_scores,
                          "summary": s, "per_unit": rows})
            print(f"{schedule_id:<24} {arm:<14} mean u-RMSE {s['mean_rmse']:.3f} "
                  f"(clock {s['mean_rmse_clock']:.3f})  within {s['n_within_target']}/10  "
                  f"beats clock {s['n_beats_clock']}/10  {'C-PASS' if s['passes_c_rule'] else 'C-FAIL'}")

    if not reference_verified:
        raise SystemExit("C2 abort: the reference cell was never verified against Study C")

    def cell(schedule_id, arm):
        return next(c for c in cells if c["schedule"] == schedule_id and c["arm"] == arm)

    feasible = [c for c in cells if c["feasible"]]
    full_oracle = cell("onset_anchored_oracle", "full")
    clock_only_ref, full_ref = cell("reference", "clock_only"), cell("reference", "full")
    lo, hi = full_ref["summary"]["leave_one_unit_out_range"]
    label = interpretation_label(
        pressure_only_feasible_pass=any(c["summary"]["passes_c_rule"] for c in feasible if c["arm"] == "pressure_only"),
        clock_only_indistinguishable_from_full=bool(lo <= clock_only_ref["summary"]["mean_rmse"] <= hi),
        full_feasible_pass=any(c["summary"]["passes_c_rule"] for c in feasible if c["arm"] == "full"),
        full_oracle_pass=bool(full_oracle["summary"]["passes_c_rule"]),
        oracle_failures_all_below_median=bool(full_oracle["summary"]["failing_units"])
        and set(full_oracle["summary"]["failing_units"]).issubset(set(below_median)),
    )

    ref_mean_below = float(np.mean([r["rmse"] for r in full_ref["per_unit"] if r["unit"] in below_median]))
    material = {"subset_units": below_median, "reference_mean_rmse": ref_mean_below, "by_cell": [
        {"schedule": c["schedule"], "arm": c["arm"], "feasible": c["feasible"],
         "mean_rmse_below_median": float(np.mean([r["rmse"] for r in c["per_unit"] if r["unit"] in below_median])),
         "materially_reduced": materially_reduced(
             ref_mean_below, float(np.mean([r["rmse"] for r in c["per_unit"] if r["unit"] in below_median])))}
        for c in cells]}

    results = {
        "preregistration": PREREG, "preregistration_sha256": prereg_hash,
        "base_commit": git_head(),
        "generator_hashes": {p: sha256(p) for p in GENERATOR_FILES},
        "seed": SEED, "train_units": train_idx, "test_units": test_idx,
        "median_training_rupture_cycles": median_rupture,
        "below_median_subset": below_median,
        "schedules": {k: dict(v) for k, v in SCHEDULES.items()}, "arms": list(ARMS),
        "reference_reproduces_study_c": reference_verified, "reference_tolerance": REFERENCE_TOL,
        "study_c_verdict_unchanged": committed["verdict"],
        "cells": cells, "material_reduction": material, "interpretation_label": label,
        "claim_language": ("Conditional on this synthetic generator and the tested schedules. Not a "
                           "transfer, prognosis, early-warning or physical claim. The oracle arm is a "
                           "mechanistic diagnostic upper bound and is never a deployable policy."),
    }
    os.makedirs(DATA, exist_ok=True)
    tmp = out_path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(results, fh, indent=2)
    os.replace(tmp, out_path)

    after = {p: sha256(os.path.join(STUDYC_DATA, p)) for p in os.listdir(STUDYC_DATA)}
    if after != studyc_hashes_before:
        raise SystemExit("C2 abort: Study C artifacts changed during the run")

    print(f"\nreference reproduces Study C: {reference_verified} | Study C verdict unchanged: "
          f"{committed['verdict']}")
    print(f"interpretation: {label}")
    print(f"below-median subset {below_median}: reference mean {ref_mean_below:.3f}")

    plt = figstyle.setup()
    if plt is None:                                              # pragma: no cover
        return
    # Order by probe cost so the cost/benefit reading is visual, and derive it from the schedules
    # actually present rather than hard-coding the set.
    present = {c["schedule"] for c in cells}
    order_s = sorted(present, key=lambda s: (SCHEDULES[s]["feasible"] is False,
                                             cell(s, "full")["summary"]["mean_probes_per_unit"]))
    fig, (a, b) = plt.subplots(1, 2, figsize=(10.4, 3.8))
    width = 0.26
    for j, arm in enumerate(ARMS):
        vals = [cell(s, arm)["summary"]["mean_rmse"] for s in order_s]
        a.bar(np.arange(len(order_s)) + (j - 1) * width, vals, width, label=arm,
              color=figstyle.PALETTE[j])
    a.axhline(PASS_RMSE, ls="--", color="k", lw=0.8)
    a.set_xticks(range(len(order_s)))
    a.set_xticklabels([s.replace("onset_anchored_oracle", "oracle*").replace("_", "\n") for s in order_s], fontsize=7)
    a.set_ylabel("mean held-out u-RMSE [life]"); a.legend(fontsize=7)
    a.set_title("input arm x schedule (*oracle = diagnostic only)", fontsize=9)
    for j, arm in enumerate(ARMS):
        vals = [cell(s, arm)["summary"]["n_within_target"] for s in order_s]
        b.bar(np.arange(len(order_s)) + (j - 1) * width, vals, width, label=arm,
              color=figstyle.PALETTE[j])
    b.axhline(8, ls="--", color="k", lw=0.8)
    b.set_xticks(range(len(order_s)))
    b.set_xticklabels([s.replace("onset_anchored_oracle", "oracle*").replace("_", "\n") for s in order_s], fontsize=7)
    b.set_ylabel("held-out units within 0.10 life"); b.set_ylim(0, 10)
    b.set_title(f"C rule needs 8/10 — reading: {label}", fontsize=9)
    fig.tight_layout()
    figstyle.save(fig, os.path.join(DATA, "studyC2_fig_schedule_sensitivity"))
    plt.close(fig)
    print(f"results + figure -> {DATA}/")


if __name__ == "__main__":
    main()
