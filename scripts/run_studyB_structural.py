"""Study B follow-up — is the post-onset aliasing structural, or practical at this noise level?

Study B reported the latent life coordinate as "structurally aliased" with the acceleration-onset
fraction and the leak multiplier after onset, on the evidence of a rank-deficient Fisher information
matrix and small whitened angles. Wieland et al. 2021 argue a Fisher-based analysis is insensitive to
practical non-identifiability, and Chis et al. 2016 that an ill-conditioned information matrix is not
proof of non-identifiability. This script runs the two diagnostics the literature prescribes:

  1. Brun et al. 2001 collinearity index over parameter *subsets*, which names the aliasing group
     rather than reporting pairwise angles.
  2. A profile likelihood over u with the nuisance parameters re-optimised at each point, which
     separates a structurally flat direction (Raue et al. 2009) from one merely unconstrained by this
     data.

It does not change Study B's verdict. It decides which word the finding supports.
Task: literature/gaps.md item 3. Writes data/sim/studyB/studyB_structural.json.
"""

from __future__ import annotations

import json
import os

import numpy as np

from pipeline.dispersion import SEED, sample_units
from pipeline.identifiability import (COLLINEARITY_POOR, PARAMS, collinearity_index,
                                      collinearity_report, crossing_brackets, features, jacobian,
                                      json_safe, merge_profiles, noise_covariance, profile_interval,
                                      profile_likelihood_u, profile_verdict, measured_features)
from scripts import figure_style as style
from scripts.run_studyB import DATA, U_BASE, theta_of
from sim.fatigue import FatigueParams
from sim.plant import SLSParams

# The grid must reach the physical bounds on *both* sides, or a profile that stops rising is merely
# untested rather than unidentifiable. The earlier grid ended at 0.90 -- exactly the post-onset truth --
# so no upper crossing could exist and no resolution could honestly be read off it.
U_DOMAIN = (0.02, 0.98)
U_GRID = sorted({U_DOMAIN[0], U_DOMAIN[1]} | {round(x, 2) for x in np.arange(0.05, 0.96, 0.05)})
PROBE_U = [0.30, 0.50, 0.90]          # two pre-onset points and one post-onset, canonical onset is 0.70
N_REP = 24
AMP = 0.1
NOISE = 1.0
CHI2_95 = 1.92                         # 95% chi-square(1) cut on delta(-log L)
N_REFINE = 2                           # bisection passes at each threshold crossing

# Widened nuisance box for the bound-sensitivity check. The default box uses the dispersion support for
# the onset fraction and the fatigue exponent; these are the wider ranges that are still physically
# admissible (an onset must lie strictly inside life; an exponent must stay positive and finite). If a
# threshold crossing moves when the box is widened, the crossing was the box talking, not the data.
WIDE_BOUNDS = {"acceleration_onset_fraction": (0.30, 0.98), "fatigue_exponent": (1.0, 5.0)}

# the subsets the Study B finding names, plus controls
SUBSETS = {
    "u_alone": ("u",),
    "u+onset": ("u", "acceleration_onset_fraction"),
    "u+leak": ("u", "terminal_leak_multiplier"),
    "u+onset+leak": ("u", "acceleration_onset_fraction", "terminal_leak_multiplier"),
    "u+k1": ("u", "k1_0"),
    "u+k2": ("u", "k2_0"),
    "u+tau": ("u", "tau"),
    "all_seven": PARAMS,
}


def bounds_for(theta, wide=False):
    """Physically admissible ranges for the profile's nuisance optimisation."""
    b = [(0.02, 0.98)]                                        # u
    for v in theta[1:4]:                                      # k1, k2, tau: order of magnitude either way
        b.append((v * 0.1, v * 10.0))
    b.append((1.0, 200.0))                                    # terminal_leak_multiplier
    b.append(WIDE_BOUNDS["acceleration_onset_fraction"] if wide else (0.45, 0.90))
    b.append(WIDE_BOUNDS["fatigue_exponent"] if wide else (1.2, 3.0))
    return b


def main():
    canonical = type("U", (), {"fatigue": FatigueParams(), "sls": SLSParams()})()
    units = [("canonical", canonical)] + [(f"dispersed_{i}", u) for i, u in enumerate(sample_units(3, SEED))]

    collinearity, profiles = [], []
    for name, unit in units:
        for u in PROBE_U:
            th = theta_of(unit, u)
            J = jacobian(th, unit.fatigue, unit.sls, AMP)
            sigma = noise_covariance(th, unit.fatigue, unit.sls, 11, N_REP, NOISE, AMP)
            # B2's stacked design: the young baseline does not move with u, so its u-column is zeroed
            th_b = theta_of(unit, U_BASE)
            J_b = jacobian(th_b, unit.fatigue, unit.sls, AMP)
            J_b = J_b.copy(); J_b[:, 0] = 0.0
            sigma_b = noise_covariance(th_b, unit.fatigue, unit.sls, 7, N_REP, NOISE, AMP)
            from scipy.linalg import block_diag
            J2, sigma2 = np.vstack([J_b, J]), block_diag(sigma_b, sigma)

            # An infinite index has two very different causes. A parameter the observables do not
            # respond to at all is *irrelevant* at this operating point, not confounded with u; before
            # the acceleration onset the onset fraction, leak and exponent are exactly inert. Record
            # which parameters are inert so an infinity is never read as aliasing.
            from pipeline.identifiability import normalised_sensitivities
            _, norms = normalised_sensitivities(J2, sigma2)
            inert = [PARAMS[i] for i, n in enumerate(norms) if n == 0.0]
            row = {"unit": name, "u": u,
                   "post_onset": bool(u >= unit.fatigue.acceleration_onset_fraction),
                   "inert_parameters": inert}
            for label, names in SUBSETS.items():
                idx = [PARAMS.index(p) for p in names]
                value, status, _ = collinearity_report(J2, sigma2, idx, PARAMS)
                # value is None unless the index is numerically meaningful; the status says why. A
                # singular subset is never written as a magnitude -- all_seven moved 6.5e7 -> 8.3e7 under
                # a numerically better whitening, which is what a float64-noise-floor quantity does.
                row[label] = value
                row[label + "_status"] = status
                row[label + "_is_inert"] = bool(status == "undefined_inert_parameter")
            collinearity.append(row)
            def fmt(lab):
                v, st = row[lab], row[lab + "_status"]
                return f"{v:9.3g}" if v is not None else f"{st[:9]:>9s}"
            tag = "  [onset/leak inert here]" if row["u+onset+leak_is_inert"] else ""
            print(f"{name:12s} u={u:.2f} {'post' if row['post_onset'] else 'pre ':4s} "
                  f"u+onset {fmt('u+onset')}  u+leak {fmt('u+leak')}  "
                  f"u+onset+leak {fmt('u+onset+leak')}  all7 {fmt('all_seven')}{tag}")

    # Profile likelihood on the canonical unit, one pre-onset and one post-onset truth.
    # Both designs are run: B1 is one aged snapshot, B2 stacks a young baseline of the same unit under
    # shared nuisance parameters. B2 is what Study B's write-up describes, so B2 is what it is scored on;
    # B1 is kept alongside to show what the baseline observation is actually worth.
    from scipy.linalg import block_diag
    free = [1, 2, 3, 4, 5, 6]                                # every nuisance parameter re-optimised
    for u_true in (0.50, 0.90):
        th_true = theta_of(canonical, u_true)
        th_base = theta_of(canonical, U_BASE)
        sigma_s = noise_covariance(th_true, canonical.fatigue, canonical.sls, 11, N_REP, NOISE, AMP)
        sigma_b = noise_covariance(th_base, canonical.fatigue, canonical.sls, 7, N_REP, NOISE, AMP)
        y_snap = measured_features(th_true, canonical.fatigue, canonical.sls, 4242, NOISE, AMP)
        y_base = measured_features(th_base, canonical.fatigue, canonical.sls, 4243, NOISE, AMP)
        designs = {
            "B2": dict(y=np.concatenate([y_base, y_snap]), sigma=block_diag(sigma_b, sigma_s),
                       u_base=U_BASE,
                       note="young baseline at u=%.2f stacked with the aged snapshot, nuisance shared" % U_BASE),
            "B1": dict(y=y_snap, sigma=sigma_s, u_base=None, note="the aged snapshot alone"),
        }
        for design, cfg in designs.items():
            def run(grid):
                return profile_likelihood_u(grid, th_true, cfg["y"], cfg["sigma"], canonical.fatigue,
                                            canonical.sls, free, bounds_for(th_true), AMP,
                                            u_base=cfg["u_base"])
            prof = run(U_GRID)
            # Refine where the profile crosses the cut: the interval is read off those two crossings, so
            # a 0.05 grid would otherwise cap the reported precision at the grid spacing. Bisect twice on
            # each side, which locates each crossing to about 0.0125 life.
            for _ in range(N_REFINE):
                extra = sorted({round(0.5 * (a + b), 4)
                                for br in crossing_brackets(prof, CHI2_95).values() if br
                                for a, b in [br]})
                extra = [x for x in extra if all(abs(x - q["u"]) > 1e-6 for q in prof)]
                if not extra:
                    break
                prof = merge_profiles(prof, run(extra))
            verdict, flat = profile_verdict(prof, CHI2_95, domain=U_DOMAIN)
            iv = profile_interval(prof, CHI2_95)
            best = min(prof, key=lambda p: p["nll"])
            n_bad = sum(1 for q in prof if not q["converged"])
            profiles.append({"design": design, "design_note": cfg["note"], "u_true": u_true,
                             "verdict": verdict, "flat_fraction": flat, "interval": iv,
                             "n_features": int(np.asarray(cfg["y"]).size),
                             "n_grid_points": len(prof), "n_refinement_passes": N_REFINE,
                             "n_not_converged": n_bad,
                             "u_at_minimum": best["u"], "profile": prof})
            span = ("open" if iv["lower_open"] else f"{iv['lower']:.2f}") + " to " + \
                   ("open" if iv["upper_open"] else f"{iv['upper']:.2f}")
            print(f"\n{design} profile at true u={u_true:.2f} ({cfg['note']}): verdict {verdict}, "
                  f"minimum at u={best['u']:.2f}, 95% interval {span}, " +
                  ("flat fraction not computed" if np.isnan(flat)
                   else f"{flat:.0%} of the grid within the cut") +
                  (f", {n_bad} point(s) failed to converge" if n_bad else ""))

    post = [r for r in collinearity if r["post_onset"] and not r["u+onset+leak_is_inert"]]
    def med(label):
        vals = [r[label] for r in post if r[label] is not None]
        return float(np.median(vals)) if vals else None
    summary = {
        "note": ("Pre-onset the onset fraction, leak multiplier and exponent are exactly inert, so their "
                 "collinearity is undefined rather than infinite-because-aliased. Only post-onset points "
                 "where every subset member responds are aggregated below."),
        "n_post_onset_points": len(post),
        "median_u_onset_post_onset": med("u+onset"),
        "median_u_leak_post_onset": med("u+leak"),
        "median_u_onset_leak_post_onset": med("u+onset+leak"),
        "median_u_tau_post_onset": med("u+tau"),
        "poor_flag": COLLINEARITY_POOR,
        "reading": ("the triple is orders of magnitude above either pair, so the dependency is joint: "
                    "no pairwise angle reveals it, which is why a subset index was required"),
    }
    # --- bound sensitivity -------------------------------------------------------------------------
    # The post-onset B2 interval terminates at points where the nuisance fit is pinned to its box. That
    # makes the interval width a property of the box until proven otherwise, so re-profile the upper
    # region with the widened box and see whether the crossing moves.
    sens = None
    base = next((q for q in profiles if q["design"] == "B2" and q["u_true"] == 0.90), None)
    if base is not None:
        th_true = theta_of(canonical, 0.90)
        th_base = theta_of(canonical, U_BASE)
        sigma2 = block_diag(noise_covariance(th_base, canonical.fatigue, canonical.sls, 7, N_REP, NOISE, AMP),
                            noise_covariance(th_true, canonical.fatigue, canonical.sls, 11, N_REP, NOISE, AMP))
        y2 = np.concatenate([measured_features(th_base, canonical.fatigue, canonical.sls, 4243, NOISE, AMP),
                             measured_features(th_true, canonical.fatigue, canonical.sls, 4242, NOISE, AMP)])
        upper_grid = [0.90, 0.95, 0.965, 0.9725, 0.98]
        wide = profile_likelihood_u(upper_grid, th_true, y2, sigma2, canonical.fatigue, canonical.sls,
                                    free, bounds_for(th_true, wide=True), AMP, u_base=U_BASE)
        # re-reference to the same minimum as the committed profile so the two are comparable
        ref_min = min(q["nll"] for q in base["profile"])
        for q in wide:
            q["delta_nll"] = q["nll"] - ref_min
        narrow = {q["u"]: q for q in base["profile"]}
        rows = [{"u": q["u"],
                 "delta_nll_default_box": narrow[q["u"]]["delta_nll"] if q["u"] in narrow else None,
                 "delta_nll_wide_box": q["delta_nll"],
                 "at_bound_default": narrow[q["u"]]["at_bound"] if q["u"] in narrow else None,
                 "at_bound_wide": q["at_bound"], "converged_wide": q["converged"]} for q in wide]
        crossed_default = [r["u"] for r in rows if r["delta_nll_default_box"] is not None
                           and r["delta_nll_default_box"] > CHI2_95]
        crossed_wide = [r["u"] for r in rows if r["delta_nll_wide_box"] > CHI2_95]
        moved = crossed_default != crossed_wide
        sens = {
            "question": ("does the post-onset B2 upper crossing survive a widened but still physical "
                         "nuisance box, or is it the box terminating the interval?"),
            "widened": {k: list(v) for k, v in WIDE_BOUNDS.items()},
            "upper_grid": upper_grid, "rows": rows,
            "crossing_points_default_box": crossed_default,
            "crossing_points_wide_box": crossed_wide,
            "crossing_moved": bool(moved),
            "reading": ("BOUND-LIMITED: the crossing is a property of the nuisance box, not of the data, "
                        "so the interval width is not a measured precision"
                        if moved else
                        "the crossing survives the widened box, so it is not an artefact of these bounds "
                        "alone; that still does not make the plateau width a precision"),
        }
        print(f"\nbound sensitivity: crossings at {crossed_default} (default box) vs {crossed_wide} "
              f"(widened box) -> {'MOVED' if moved else 'unchanged'}")

    # Study B's write-up describes the stacked design, so the stacked design is what its wording is
    # scored on. The post-onset truth is the case the "structurally aliased" claim was about.
    post_profile = next(p for p in profiles if p["u_true"] == 0.90 and p["design"] == "B2")
    conclusion = post_profile["verdict"]
    iv = post_profile["interval"]
    open_side = iv["lower_open"] or iv["upper_open"]
    # A crossing that sits on a nuisance bound, or that moves when the bound is widened, is the box
    # terminating the interval rather than the data. A plateau far below the threshold is an interval the
    # profile never resolves within. Any of those disqualifies a half-width just as an open bound does.
    bound_terminated = bool(iv.get("lower_at_nuisance_bound") or iv.get("upper_at_nuisance_bound"))
    crossing_moved = bool(sens and sens.get("crossing_moved"))
    spread = iv.get("plateau_nll_spread")
    is_plateau = spread is not None and spread < 0.1 * CHI2_95
    if (conclusion in ("domain-limited", "unresolved") or open_side
            or bound_terminated or crossing_moved or is_plateau):
        # A half-width may only be quoted from a closed interval on a trustworthy profile. Quoting one
        # anyway was the original error, so each disqualifying reason is named rather than glossed.
        resolution = None
        reasons = []
        if conclusion == "unresolved":
            reasons.append(f"{post_profile['n_not_converged']} of {len(post_profile['profile'])} grid "
                           "points failed to converge, so the profile's shape is not trustworthy")
        if open_side:
            side = "lower" if iv["lower_open"] else "upper"
            reasons.append(f"the 95% interval is open at the {side} end: the profile never crosses the "
                           f"chi-square cut on that side within the physical domain "
                           f"[{U_DOMAIN[0]}, {U_DOMAIN[1]}], so it extends past what was tested")
        if conclusion == "domain-limited" and not open_side:
            reasons.append("the grid stopped short of the physical bound on the non-crossing side")
        if bound_terminated:
            sides = [w for w, k in (("lower", "lower_at_nuisance_bound"), ("upper", "upper_at_nuisance_bound"))
                     if iv.get(k)]
            reasons.append(f"the {' and '.join(sides)} termination(s) sit on a nuisance-parameter bound, so "
                           "the interval closes where the optimiser runs out of freedom to compensate, not "
                           "where the data run out")
        if crossing_moved:
            reasons.append("widening the nuisance box to a still-physical range removes the crossing "
                           f"entirely ({sens['crossing_points_default_box']} -> "
                           f"{sens['crossing_points_wide_box']}), so the interval width is a property of "
                           "the box and NOT a measured precision")
        if is_plateau:
            reasons.append(f"the likelihood varies by only {spread:.3g} across the points inside the cut "
                           f"(threshold {CHI2_95}), so the interval is a plateau the profile never resolves "
                           "within rather than a bound on an estimate")
        resolution_note = "No resolution is quoted: " + "; and ".join(reasons) + "."
    else:
        resolution = float(max(iv["upper"] - iv["u_at_minimum"], iv["u_at_minimum"] - iv["lower"]))
        resolution_note = (f"half-width of the closed 95% interval [{iv['lower']:.2f}, "
                           f"{iv['upper']:.2f}] about the minimum at u={iv['u_at_minimum']:.2f}")

    results = {
        "question": "Is Study B's post-onset aliasing structural, or practical at this noise level?",
        "task": "literature/gaps.md item 3",
        "method": {
            "collinearity": "Brun et al. 2001 gamma_K on unit-length whitened sensitivity columns; "
                            f"gamma above {COLLINEARITY_POOR} flags a poorly identifiable subset",
            "profile": "negative log-likelihood profiled over u with all six nuisance parameters "
                       f"re-optimised at each point; {CHI2_95} is the 95% chi-square(1) cut",
            "design": ("both designs are computed and stored: B2 stacks the young baseline at "
                       f"u={U_BASE} with the aged snapshot under shared nuisance parameters (ten "
                       "features); B1 is the snapshot alone (five). The verdict is taken from B2, "
                       "which is the design Study B's write-up describes. Noise scale 1, amplitude 0.1"),
            "domain": list(U_DOMAIN),
            "grid": "spans the full physical domain so that a non-crossing side is a real result "
                    "rather than an artefact of where the grid stopped",
        },
        "does_not_change": "Study B's B-PASS verdict and its reported bounds are unchanged",
        "subsets": {k: list(v) for k, v in SUBSETS.items()},
        "collinearity_by_point": collinearity,
        "collinearity_summary": summary,
        "profiles": profiles,
        "bound_sensitivity": sens,
        "conclusion": conclusion,
        "verdict_is_bound_dependent": bool(bound_terminated or crossing_moved),
        "resolution_life_fraction": resolution,
        "resolution_note": resolution_note,
        "wording_supported": {
            "structural": "structurally aliased",
            "practical": "practically aliased at this noise level",
            "identifiable": ("the profile crosses the cut on both sides under this design -- which is all "
                             "this label means. It is NOT a precision claim, and where the terminations are "
                             "bound-dependent (see verdict_is_bound_dependent) the crossing itself is a "
                             "property of the nuisance box"),
            "domain-limited": ("not determined by this calculation: the profile does not cross the "
                               "95% cut within the physical domain, so the data bound u on one side "
                               "only and the aliasing question stays open"),
            "unresolved": "not determined: an optimisation failed, so the profile is not trustworthy",
        }[conclusion],
    }
    os.makedirs(DATA, exist_ok=True)
    out = os.path.join(DATA, "studyB_structural.json")
    tmp = out + ".tmp"
    with open(tmp, "w") as fh:
        # json_safe, not default=: json.dump only consults default= for types it cannot serialise, and
        # float is not one of them, so bare Infinity/NaN would otherwise reach the file and break every
        # strict parser. Reasons live in the sibling *_status fields.
        json.dump(json_safe(results), fh, indent=2, allow_nan=False)
    os.replace(tmp, out)
    print(f"\nconclusion ({post_profile['design']}, true u=0.90): {conclusion}")
    print(f"  supported wording: \"{results['wording_supported']}\"")
    print(f"  resolution: {'none' if resolution is None else f'+/-{resolution:.2f} life'} -- {resolution_note}")

    plot(results)


SUBSET_ROWS = (("u+onset+leak", "life + onset + leak"), ("u+onset", "life + onset"), ("u+leak", "life + leak"),
               ("u+tau", r"life + $\tau$"))
# design -> (legend label, marker, line style)
PROFILE_STYLE = {"B2": ("B2 with young baseline", "o", "-"), "B1": ("B1 single snapshot", "s", (0, (5, 1.5, 1, 1.5)))}
TRUE_U_STYLE = {"color": "black", "lw": 0.8, "ls": ":"}
FLAT_SHADE = {"color": "#E6E6E6", "lw": 0}
FLOOR = 1e-11          # profile values below this are drawn at the floor of the log axis
PANEL_U = (0.5, 0.9)   # true life in panels (b) and (c)


def collinearity_points(results):
    """(row, value, post_onset) for every defined subset index on the canonical unit."""
    onset = FatigueParams().acceleration_onset_fraction
    pts = sorted((r for r in results["collinearity_by_point"] if r["unit"] == "canonical"), key=lambda r: r["u"])
    return [(y, r[key], r["u"] > onset, r["u"]) for y, (key, _) in enumerate(SUBSET_ROWS)
            for r in pts if r.get(key) is not None]


def profile_curves(results, u_true):
    """design -> (u, drawn delta NLL, at-bound flags) for one true life."""
    out = {}
    for p in (q for q in results["profiles"] if q["u_true"] == u_true):
        q = sorted(p["profile"], key=lambda r: r["u"])
        out[p["design"]] = ([r["u"] for r in q], [max(r["delta_nll"], FLOOR) for r in q],
                            [any(r.get("at_bound", [])) for r in q])
    return out


def flat_region(results):
    """(u_low, u_high, delta-NLL spread) where the B2 profile at true u = 0.9 sits under the cut past its minimum."""
    pp = next(q for q in results["profiles"] if q["design"] == "B2" and q["u_true"] == PANEL_U[1])
    flat = [q["u"] for q in pp["profile"] if q["delta_nll"] <= CHI2_95 and q["u"] >= pp["interval"]["u_at_minimum"]]
    spread = max(q["delta_nll"] for q in pp["profile"] if min(flat) <= q["u"] <= max(flat))
    return min(flat), max(flat), spread


def structural_caption(results):
    onset = FatigueParams().acceleration_onset_fraction
    post = {r["u"]: r for r in results["collinearity_by_point"] if r["unit"] == "canonical" and r["u"] > onset}
    assert len(post) == 1, post
    (u_post, row), = post.items()
    pre = sorted(r["u"] for r in results["collinearity_by_point"] if r["unit"] == "canonical" and r["u"] <= onset)
    prof = {(q["design"], q["u_true"]): q for q in results["profiles"]}
    lo, hi, spread = flat_region(results)
    tri, pair_on, pair_leak, tau = (row[k] for k, _ in SUBSET_ROWS)
    assert tri > 1e3 * max(pair_on, pair_leak)
    b2_mid, b2_late = prof[("B2", PANEL_U[0])], prof[("B2", PANEL_U[1])]
    return (f"Simulation: local diagnostics on the canonical synthetic unit, nuisance parameters re-optimised at "
            f"each u, {N_REP} sensor repeats, noise ×{NOISE:g}, amplitude {AMP:g} V0. Panel (a): Brun collinearity "
            f"index γ_K of four parameter subsets. Filled circles are after the onset at {onset:.2f} "
            f"(u = {u_post:g}); hollow circles are before it (u = {', '.join(f'{u:g}' for u in pre)}), where the onset "
            "and leak parameters are inert, so their collinearity is undefined and not drawn. The dashed line marks "
            f"γ_K = {COLLINEARITY_POOR:g}, above which a subset is poorly identifiable. After onset the life, onset and "
            f"leak triple reaches {tri:.3g}".replace("e+0", "e") + f", against {pair_on:.3g} for life and onset, {pair_leak:.3g} for life and "
            f"leak and {tau:.3g} for life and τ: the triple is far more collinear than any pair. Panels (b) and (c): "
            f"profile likelihood Δ(−log L) over u at true u = {PANEL_U[0]:g} and {PANEL_U[1]:g}; circles on a solid "
            "line are B2 (with young baseline), squares on a dash-dot line B1 (single snapshot), and crosses mark fits "
            f"that end on a nuisance-parameter bound; where the two profiles coincide, B1 is hidden under B2. The dashed line is the 95 % cut at {CHI2_95:g} and the dotted "
            f"line the true u. Values below {FLOOR:.0e} are drawn at that floor. At true u = {PANEL_U[0]:g} only B2 "
            f"dips near the truth (minimum at u = {b2_mid['u_at_minimum']:g}). At true u = {PANEL_U[1]:g} both "
            f"profiles stay flat; B2 (minimum at u = {b2_late['u_at_minimum']:g}) varies by only {spread:.0e} between "
            f"u = {lo:g} and {hi:g}, the grey band. Profile verdicts are recorded in studyB_structural.json, "
            "the source of every value.")


def structural_figure(results):
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    plt = style.plt
    style.apply()
    fig = plt.figure(figsize=(style.FULL, 3.3))
    outer = fig.add_gridspec(1, 2, width_ratios=[1, 2.05], wspace=0.3, left=0.165, right=0.985, top=0.76,
                             bottom=0.15)
    a = fig.add_subplot(outer[0])
    inner = outer[1].subgridspec(1, 2, wspace=0.08)
    b = fig.add_subplot(inner[0])
    c = fig.add_subplot(inner[1], sharey=b)

    for y, v, post, _ in collinearity_points(results):
        # hollow rings are see-through so a filled marker at the same value stays visible inside
        a.plot(v, y, marker="o", mfc=style.INK if post else "none", color=style.INK, ls="none", mew=0.9,
               ms=5 if post else 7.5, zorder=3 if post else 4)
    a.axvline(COLLINEARITY_POOR, **style.REFERENCE)
    a.set_xscale("log")
    a.set_xlim(0.3, 1e8)
    a.set_xticks([1, 1e2, 1e4, 1e6, 1e8], ["1", "100", r"$10^4$", r"$10^6$", r"$10^8$"])
    a.xaxis.set_minor_formatter(plt.NullFormatter())
    a.set_yticks(range(len(SUBSET_ROWS)), [lab for _, lab in SUBSET_ROWS])
    a.set_ylim(len(SUBSET_ROWS) - 0.5, -0.5)
    a.tick_params(axis="y", length=0)
    a.set_xlabel(r"Brun collinearity index $\gamma_K$")

    lo, hi, _ = flat_region(results)
    c.axvspan(lo, hi, zorder=0, **FLAT_SHADE)
    for ax, u_true in zip((b, c), PANEL_U):
        for design, (us, ys, pinned) in profile_curves(results, u_true).items():
            _, mk, ls = PROFILE_STYLE[design]
            ax.plot(us, ys, ls=ls, color=style.INK, lw=0.9, marker=mk, ms=2.8, mfc=style.FILL[True])
            pin = [(x, y) for x, y, at in zip(us, ys, pinned) if at]
            if pin:
                ax.plot(*zip(*pin), "x", color=style.INK, ms=5, mew=0.9, ls="none")
        ax.axvline(u_true, **TRUE_U_STYLE)
        ax.axhline(CHI2_95, **style.REFERENCE)
        ax.set_yscale("log")
        ax.set_xlim(0, 1)
        ax.set_xlabel(r"Normalized life $u$")
    b.set_ylim(FLOOR / 3, 3e6)
    b.set_yticks([1e-10, 1e-6, 1e-2, 1e2, 1e6], [r"$10^{-10}$", r"$10^{-6}$", r"$10^{-2}$", r"$10^{2}$", r"$10^{6}$"])
    b.yaxis.set_minor_formatter(plt.NullFormatter())
    plt.setp(c.get_yticklabels(), visible=False)
    b.set_ylabel(r"$\Delta(-\log L)$")
    b.set_xticks([0, 0.2, 0.4, 0.6, 0.8])
    for i, ax in enumerate((a, b, c)):
        style.letter(ax, i)
    handles = [Line2D([], [], marker=mk, ls=ls, color=style.INK, lw=0.9, ms=2.8, label=lab)
               for lab, mk, ls in PROFILE_STYLE.values()]
    handles += [Line2D([], [], marker="x", ls="none", color=style.INK, ms=5, mew=0.9, label="Fit at a nuisance bound"),
                Patch(label="B2 flat region", **FLAT_SHADE),
                Line2D([], [], marker="o", ls="none", color=style.INK, ms=5, mew=0.9, mfc=style.FILL[True],
                       label="After onset"),
                Line2D([], [], marker="o", ls="none", color=style.INK, ms=7.5, mew=0.9, mfc="none",
                       label="Before onset"),
                Line2D([], [], label="Threshold", **style.REFERENCE),
                Line2D([], [], label="True $u$", **TRUE_U_STYLE)]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.995), ncol=4, columnspacing=1.3,
               handletextpad=0.5, handlelength=2.6, borderaxespad=0)
    return fig


def plot(results):
    fig = structural_figure(results)
    style.save(fig, os.path.join(DATA, "studyB_fig_structural"), caption=structural_caption(results))
    style.plt.close(fig)
    print(f"results + figure -> {DATA}/")


if __name__ == "__main__":
    import sys
    if "--replot" in sys.argv:                      # redraw from the saved result, no recomputation
        plot(json.load(open(os.path.join(DATA, "studyB_structural.json"))))
        print("replotted from the saved result")
    else:
        main()
