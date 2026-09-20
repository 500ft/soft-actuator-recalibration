"""R1 — forensic failure map for the committed Study C result (post-hoc, descriptive).

Asks which property of a held-out unit predicts its transfer error: how much of its life was
observed after the acceleration onset (a *schedule* property), or how far its rupture life sits
from the training median (a *clock-prior* property). Those two are collinear across the ten
held-out units, so the map reports both, their collinearity, and the partial associations.

This script does not refit, retune, re-split or re-threshold anything. It reproduces the
committed model bit-for-bit under the identical contract (same training units, same lambda, same
standardisation) purely to read its coefficients, and aborts unless the reproduced per-unit
errors equal the committed ones. Design: docs/specs/observability-program/studyC-failure-analysis.md
"""

from __future__ import annotations

import hashlib
import json
import os

import numpy as np

from pipeline.dispersion import SEED, sample_units
from scripts import figstyle
from scripts.run_studyC import (DATA, N_TRAIN, N_UNITS, PASS_RMSE, PROBE_START, PROBE_STEP,
                                ridge_fit, ridge_predict, rmse, stack, unit_records)

SOURCE = os.path.join(DATA, "studyC_results.json")
SCHEMA_VERSION = 1
SPARSE_MAX_POST_ONSET = 2          # 1-2 post-onset probes = sparse; >= 3 = adequate; 0 = none
REPRODUCTION_TOL = 1e-9            # committed vs reproduced per-unit u-RMSE
INPUT_GROUPS = {"pressure_now": slice(0, 5), "pressure_lag": slice(5, 10), "clock": slice(10, 11)}


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def probe_cycles(rupture_cycles):
    """The committed Study C schedule: every PROBE_STEP cycles from PROBE_START, stopping before rupture."""
    return np.arange(PROBE_START, rupture_cycles, PROBE_STEP)


def coverage(rupture_cycles, onset_fraction):
    """Where this unit's probes fall relative to its own acceleration onset."""
    cycles = probe_cycles(rupture_cycles)
    onset_cycles = onset_fraction * rupture_cycles
    post = cycles >= onset_cycles
    first_post = float(cycles[post][0]) if post.any() else None
    return {
        "n_probes": int(cycles.size),
        "first_probe_cycles": float(cycles[0]),
        "last_probe_cycles": float(cycles[-1]),
        "last_probe_life": float(cycles[-1] / rupture_cycles),
        "onset_cycles": float(onset_cycles),
        "n_pre_onset": int((~post).sum()),
        "n_post_onset": int(post.sum()),
        "fraction_pre_onset": float((~post).mean()),
        "fraction_post_onset": float(post.mean()),
        "first_post_onset_cycles": first_post,
        "first_post_onset_life": None if first_post is None else float(first_post / rupture_cycles),
        "onset_to_first_post_onset_cycles": None if first_post is None else float(first_post - onset_cycles),
        "onset_to_first_post_onset_life": None if first_post is None else float((first_post - onset_cycles) / rupture_cycles),
        "coverage_label": coverage_label(int(post.sum())),
    }


def coverage_label(n_post_onset):
    """Deterministic grouping declared before the numbers were computed."""
    if n_post_onset == 0:
        return "no_post_onset"
    return "sparse_post_onset" if n_post_onset <= SPARSE_MAX_POST_ONSET else "adequate_post_onset"


def reproduce_committed_model(committed):
    """Rebuild the exact committed model and verify it reproduces the committed held-out errors.

    Not a refit: same units, same seeded records, same training split, same lambda, same
    standardisation. Returns (model, per-unit records, train/test indices) or raises.
    """
    units = sample_units(N_UNITS, SEED)
    order = np.random.default_rng(SEED + 1).permutation(N_UNITS)
    train_idx, test_idx = sorted(order[:N_TRAIN].tolist()), sorted(order[N_TRAIN:].tolist())
    if train_idx != committed["train_units"] or test_idx != committed["test_units"]:
        raise SystemExit("R1 abort: reproduced train/test split differs from the committed split")
    records = [unit_records(u, i) for i, u in enumerate(units)]
    X, y = stack([r for i in train_idx for r in records[i]])
    model = ridge_fit(X, y, committed["lambda_selected"])
    model["lam"] = committed["lambda_selected"]
    for slot, i in enumerate(test_idx):
        Xi, yi = stack(records[i])
        got, want = rmse(ridge_predict(model, Xi), yi), committed["heldout"][slot]["rmse"]
        if abs(got - want) > REPRODUCTION_TOL:
            raise SystemExit(
                f"R1 abort: cannot reproduce the committed model. Held-out unit {i} u-RMSE "
                f"{got:.12g} vs committed {want:.12g} (tolerance {REPRODUCTION_TOL:g}). The "
                f"numeric environment or a generator input has changed; fix provenance before "
                f"interpreting any failure map.")
    return model, records, train_idx, test_idx, units


def channel_decomposition(model, records, test_idx, committed):
    """Split the committed model's prediction into pressure and clock channels.

    Every input is standardised, so the per-input contribution is ((x - mu)/sd) * w. Zeroing a
    channel means setting it to its training mean, which is the model's own no-information value
    for that channel. No weights are changed.
    """
    w = model["w"]
    groups = {g: float(np.abs(w[s]).sum()) for g, s in INPUT_GROUPS.items()}
    total = sum(groups.values())
    per_unit = []
    for slot, i in enumerate(test_idx):
        Xi, yi = stack(records[i])
        full = ridge_predict(model, Xi)
        X_noclock = Xi.copy()
        X_noclock[:, INPUT_GROUPS["clock"]] = model["mu"][INPUT_GROUPS["clock"]]
        X_nopressure = Xi.copy()
        for g in ("pressure_now", "pressure_lag"):
            X_nopressure[:, INPUT_GROUPS[g]] = model["mu"][INPUT_GROUPS[g]]
        full_e = rmse(full, yi)
        muted_clock_e = rmse(ridge_predict(model, X_noclock), yi)
        per_unit.append({
            "unit": i,
            "rmse_full": full_e,
            "rmse_clock_channel_muted": muted_clock_e,
            "rmse_pressure_channels_muted": rmse(ridge_predict(model, X_nopressure), yi),
            # A unit the clock channel actively harms: the model would do better on it with the
            # clock held at its no-information value.
            "clock_channel_harms_this_unit": bool(muted_clock_e < full_e),
        })
    return {
        "definition": ("absolute standardised ridge weight summed per input group, and held-out "
                       "u-RMSE when a channel is held at its training mean (its no-information "
                       "value). Weights are never changed."),
        "abs_weight_by_group": groups,
        "abs_weight_share_by_group": {g: v / total for g, v in groups.items()},
        "per_unit": per_unit,
        "mean_rmse_full": float(np.mean([p["rmse_full"] for p in per_unit])),
        "mean_rmse_clock_channel_muted": float(np.mean([p["rmse_clock_channel_muted"] for p in per_unit])),
        "mean_rmse_pressure_channels_muted": float(np.mean([p["rmse_pressure_channels_muted"] for p in per_unit])),
        "units_harmed_by_clock_channel": [p["unit"] for p in per_unit if p["clock_channel_harms_this_unit"]],
    }


def pearson(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if a.std() == 0 or b.std() == 0:
        return None
    return float(np.corrcoef(a, b)[0, 1])


RESIDUAL_FLOOR = 1e-9      # residual std, relative to the original, below which nothing is left


def partial_pearson(a, b, control):
    """corr(a, b) with the linear effect of ``control`` removed from both.

    Returns None when either residual is numerically negligible: a predictor fully explained by the
    control leaves only floating-point noise, and correlating that noise would manufacture a
    coefficient out of nothing. That case is real here, because schedule coverage and rupture
    deviation are strongly collinear.
    """
    a, b, c = (np.asarray(v, float) for v in (a, b, control))
    if c.std() == 0:
        return pearson(a, b)
    ra = a - np.polyval(np.polyfit(c, a, 1), c)
    rb = b - np.polyval(np.polyfit(c, b, 1), c)
    for residual, original in ((ra, a), (rb, b)):
        if residual.std() <= RESIDUAL_FLOOR * max(original.std(), 1e-300):
            return None
    return pearson(ra, rb)


def aggregate_by_label(rows):
    """Descriptive summary per coverage label; units with an empty segment are kept, not dropped."""
    out = {}
    for label in ("no_post_onset", "sparse_post_onset", "adequate_post_onset"):
        sel = [r for r in rows if r["coverage_label"] == label]
        out[label] = {
            "n_units": len(sel),
            "mean_rmse": float(np.mean([r["rmse"] for r in sel])) if sel else None,
            "median_rmse": float(np.median([r["rmse"] for r in sel])) if sel else None,
            "mean_rmse_clock": float(np.mean([r["rmse_clock"] for r in sel])) if sel else None,
            "n_within_target": int(sum(r["within_target"] for r in sel)),
            "n_beats_clock": int(sum(r["beats_clock"] for r in sel)),
            "n_missing_pre_onset_segment": int(sum(r["rmse_pre_onset"] is None for r in sel)),
            "n_missing_post_onset_segment": int(sum(r["rmse_post_onset"] is None for r in sel)),
        }
    assert sum(v["n_units"] for v in out.values()) == len(rows), "aggregate dropped units"
    return out


def build_rows(committed, units, test_idx):
    median_rupture = committed["median_training_rupture_cycles"]
    rows = []
    for slot, i in enumerate(test_idx):
        h = committed["heldout"][slot]
        rc, onset = h["rupture_cycles"], h["onset"]
        row = {"unit": i, "rupture_cycles": rc, "acceleration_onset_fraction": onset,
               "rupture_deviation_from_training_median": float(abs(rc - median_rupture) / median_rupture),
               **coverage(rc, onset),
               "rmse": h["rmse"], "rmse_clock": h["rmse_clock"],
               "rmse_minus_clock": float(h["rmse"] - h["rmse_clock"]),
               "rmse_pre_onset": h["rmse_pre_onset"], "rmse_post_onset": h["rmse_post_onset"],
               "within_target": bool(h["rmse"] <= PASS_RMSE),
               "beats_clock": bool(h["rmse"] < h["rmse_clock"])}
        if row["n_probes"] != h["n_probes"]:
            raise SystemExit(f"R1 abort: reconstructed probe count {row['n_probes']} != committed "
                             f"{h['n_probes']} for unit {i}")
        rows.append(row)
    return rows


def main():
    source_hash = sha256(SOURCE)
    committed = json.load(open(SOURCE))
    if committed.get("verdict") != "C-FAIL":
        raise SystemExit(f"R1 abort: committed verdict is {committed.get('verdict')!r}, expected C-FAIL")

    model, records, train_idx, test_idx, units = reproduce_committed_model(committed)
    rows = build_rows(committed, units, test_idx)
    channels = channel_decomposition(model, records, test_idx, committed)

    err = [r["rmse"] for r in rows]
    npost = [r["n_post_onset"] for r in rows]
    fpost = [r["fraction_post_onset"] for r in rows]
    dev = [r["rupture_deviation_from_training_median"] for r in rows]
    assoc = {
        "note": ("n = 10 held-out units. Pearson coefficients are descriptive; no p-values, no "
                 "inference. Schedule coverage and rupture-life deviation are strongly collinear "
                 "in this cohort, so the partial coefficients below are the only way to see which "
                 "one carries the association, and even they cannot separate them cleanly at n = 10."),
        "collinearity_post_onset_count_vs_rupture_deviation": pearson(npost, dev),
        "collinearity_post_onset_fraction_vs_rupture_deviation": pearson(fpost, dev),
        "error_vs_post_onset_count": pearson(err, npost),
        "error_vs_post_onset_fraction": pearson(err, fpost),
        "error_vs_rupture_deviation": pearson(err, dev),
        "error_vs_post_onset_count_controlling_rupture_deviation": partial_pearson(err, npost, dev),
        "error_vs_post_onset_fraction_controlling_rupture_deviation": partial_pearson(err, fpost, dev),
        "error_vs_rupture_deviation_controlling_post_onset_count": partial_pearson(err, dev, npost),
    }
    matched = {}
    for n in sorted({r["n_post_onset"] for r in rows}):
        same = [r for r in rows if r["n_post_onset"] == n]
        if len(same) >= 2:
            matched[str(n)] = [{"unit": r["unit"], "rupture_cycles": r["rupture_cycles"],
                                "rupture_deviation_from_training_median": r["rupture_deviation_from_training_median"],
                                "rmse": r["rmse"]} for r in sorted(same, key=lambda r: r["rupture_deviation_from_training_median"])]

    results = {
        "schema_version": SCHEMA_VERSION,
        "post_hoc_descriptive": True,
        "what_this_is_not": ("a new held-out evaluation, a refit, a re-tuning, or a change to the "
                             "Study C verdict, which remains C-FAIL"),
        "source": SOURCE, "source_sha256": source_hash,
        "preregistration": "docs/specs/observability-program/studyC-failure-analysis.md",
        "reproduction": {"tolerance": REPRODUCTION_TOL,
                         "verified": "every held-out u-RMSE reproduced within tolerance",
                         "lambda": committed["lambda_selected"]},
        "definitions": {
            "rupture_deviation_from_training_median": "|rupture_cycles - median(training rupture_cycles)| / median",
            "post_onset": "probe cycle >= acceleration_onset_fraction * rupture_cycles",
            "coverage_label": f"no_post_onset = 0 post-onset probes; sparse_post_onset = 1-{SPARSE_MAX_POST_ONSET}; adequate_post_onset >= {SPARSE_MAX_POST_ONSET + 1}",
            "within_target": f"u-RMSE <= {PASS_RMSE}", "beats_clock": "u-RMSE < clock-only u-RMSE",
        },
        "median_training_rupture_cycles": committed["median_training_rupture_cycles"],
        "per_unit": rows,
        "by_rupture_cycles": [r["unit"] for r in sorted(rows, key=lambda r: r["rupture_cycles"])],
        "by_rmse_minus_clock": [r["unit"] for r in sorted(rows, key=lambda r: r["rmse_minus_clock"])],
        "aggregate_by_coverage_label": aggregate_by_label(rows),
        "associations": assoc,
        "coverage_matched_comparisons": matched,
        "channel_decomposition": channels,
        "limitations": [
            "n = 10 held-out units; descriptive only, no inferential statistics.",
            "Reuses the committed Study C evaluation output; it is not a new evaluation.",
            "Post-onset coverage and rupture-life deviation are collinear by construction of the "
            "fixed-cycle schedule: a short-lived unit necessarily gets fewer probes.",
            "Channel muting holds an input at its training mean under unchanged weights; it bounds "
            "that channel's contribution to this model, not the information content of the features.",
        ],
    }

    os.makedirs(DATA, exist_ok=True)
    out = os.path.join(DATA, "studyC_failure_analysis.json")
    tmp = out + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(results, fh, indent=2)
    os.replace(tmp, out)

    print(f"R1 failure map — source {source_hash[:16]}…, model reproduced within {REPRODUCTION_TOL:g}")
    print(f"{'unit':>4} {'rupture':>8} {'onset':>6} {'post':>4} {'f_post':>6} {'|dev|':>6} {'rmse':>6} {'clock':>6}  label")
    for r in sorted(rows, key=lambda r: r["rupture_cycles"]):
        print(f"{r['unit']:4d} {r['rupture_cycles']:8.0f} {r['acceleration_onset_fraction']:6.2f} "
              f"{r['n_post_onset']:4d} {r['fraction_post_onset']:6.2f} "
              f"{r['rupture_deviation_from_training_median']:6.2f} {r['rmse']:6.3f} {r['rmse_clock']:6.3f}  {r['coverage_label']}")
    print(f"\nassociations (n=10, descriptive): error~post-onset count {assoc['error_vs_post_onset_count']:+.3f}, "
          f"error~rupture deviation {assoc['error_vs_rupture_deviation']:+.3f}")
    print(f"  controlling for rupture deviation, error~post-onset count = "
          f"{assoc['error_vs_post_onset_count_controlling_rupture_deviation']:+.3f}")
    print(f"  controlling for post-onset count, error~rupture deviation = "
          f"{assoc['error_vs_rupture_deviation_controlling_post_onset_count']:+.3f}")
    print(f"  collinearity of the two candidate explanations = {assoc['collinearity_post_onset_count_vs_rupture_deviation']:+.3f}")
    print(f"channel weights: {', '.join(f'{g} {v:.2f}' for g, v in channels['abs_weight_share_by_group'].items())}")
    print(f"  mean held-out u-RMSE: full {channels['mean_rmse_full']:.3f}, clock muted "
          f"{channels['mean_rmse_clock_channel_muted']:.3f}, pressure muted "
          f"{channels['mean_rmse_pressure_channels_muted']:.3f}")

    plt = figstyle.setup()
    if plt is None:  # pragma: no cover
        return
    fig, (a, b) = plt.subplots(1, 2, figsize=(9.6, 3.6))
    # units sharing a post-onset count collide on the left panel; stagger their labels vertically
    seen_x = {}
    for r in sorted(rows, key=lambda r: (r["n_post_onset"], r["rmse"])):
        ok = r["within_target"]
        a.scatter(r["n_post_onset"], r["rmse"], s=46, marker="o" if ok else "X",
                  color=figstyle.PALETTE[2] if ok else figstyle.PALETTE[1], zorder=3)
        k = seen_x.get(r["n_post_onset"], 0)
        seen_x[r["n_post_onset"]] = k + 1
        a.annotate(f"{r['rupture_cycles']:.0f}", (r["n_post_onset"], r["rmse"]),
                   textcoords="offset points", xytext=(6, 3 + 10 * k), fontsize=7)
    a.axhline(PASS_RMSE, ls="--", color="k", lw=0.8)
    a.set_xlabel("post-onset probes [count]"); a.set_ylabel("held-out u-RMSE [life]")
    a.set_title("error vs schedule coverage\n(labels: rupture cycles)", fontsize=9)
    for r in rows:
        ok = r["within_target"]
        b.scatter(r["rupture_deviation_from_training_median"], r["rmse"], s=46, marker="o" if ok else "X",
                  color=figstyle.PALETTE[2] if ok else figstyle.PALETTE[1], zorder=3)
        b.annotate(f"{r['n_post_onset']}", (r["rupture_deviation_from_training_median"], r["rmse"]),
                   textcoords="offset points", xytext=(5, 3), fontsize=7)
    b.axhline(PASS_RMSE, ls="--", color="k", lw=0.8)
    b.set_xlabel("|rupture − training median| / median"); b.set_ylabel("held-out u-RMSE [life]")
    b.set_title("error vs clock-prior mismatch\n(labels: post-onset probes)", fontsize=9)
    fig.suptitle("Study C diagnostic failure map; not a new held-out evaluation", fontsize=9, y=1.02)
    fig.tight_layout()
    figstyle.save(fig, os.path.join(DATA, "studyC_fig_failure_map"))
    plt.close(fig)
    print(f"analysis + figure -> {DATA}/")


if __name__ == "__main__":
    main()
