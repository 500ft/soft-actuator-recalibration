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
from pipeline.identifiability import (COLLINEARITY_POOR, PARAMS, collinearity_index, crossing_brackets,
                                      features, jacobian, merge_profiles, noise_covariance,
                                      profile_interval, profile_likelihood_u, profile_verdict,
                                      measured_features)
from scripts import figstyle
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


def bounds_for(theta):
    """Physically admissible ranges for the profile's nuisance optimisation."""
    b = [(0.02, 0.98)]                                        # u
    for v in theta[1:4]:                                      # k1, k2, tau: order of magnitude either way
        b.append((v * 0.1, v * 10.0))
    b.append((1.0, 200.0))                                    # terminal_leak_multiplier
    b.append((0.45, 0.90))                                    # acceleration_onset_fraction (dispersion support)
    b.append((1.2, 3.0))                                      # fatigue_exponent (dispersion support)
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
                g = collinearity_index(J2, sigma2, idx)
                row[label] = g
                # mark the infinities that are inertness rather than collinearity
                row[label + "_is_inert"] = bool(any(PARAMS[i] in inert for i in idx))
            collinearity.append(row)
            tag = "  [onset/leak inert here]" if row["u+onset+leak_is_inert"] else ""
            print(f"{name:12s} u={u:.2f} {'post' if row['post_onset'] else 'pre ':4s} "
                  f"u+onset {row['u+onset']:9.3g}  u+leak {row['u+leak']:9.3g}  "
                  f"u+onset+leak {row['u+onset+leak']:9.3g}  all7 {row['all_seven']:9.3g}{tag}")

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
    summary = {
        "note": ("Pre-onset the onset fraction, leak multiplier and exponent are exactly inert, so their "
                 "collinearity is undefined rather than infinite-because-aliased. Only post-onset points "
                 "where every subset member responds are aggregated below."),
        "n_post_onset_points": len(post),
        "median_u_onset_post_onset": float(np.median([r["u+onset"] for r in post])) if post else None,
        "median_u_leak_post_onset": float(np.median([r["u+leak"] for r in post])) if post else None,
        "median_u_onset_leak_post_onset": float(np.median([r["u+onset+leak"] for r in post])) if post else None,
        "median_u_tau_post_onset": float(np.median([r["u+tau"] for r in post])) if post else None,
        "poor_flag": COLLINEARITY_POOR,
        "reading": ("the triple is orders of magnitude above either pair, so the dependency is joint: "
                    "no pairwise angle reveals it, which is why a subset index was required"),
    }
    # Study B's write-up describes the stacked design, so the stacked design is what its wording is
    # scored on. The post-onset truth is the case the "structurally aliased" claim was about.
    post_profile = next(p for p in profiles if p["u_true"] == 0.90 and p["design"] == "B2")
    conclusion = post_profile["verdict"]
    iv = post_profile["interval"]
    open_side = iv["lower_open"] or iv["upper_open"]
    if conclusion in ("domain-limited", "unresolved") or open_side:
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
        "conclusion": conclusion,
        "resolution_life_fraction": resolution,
        "resolution_note": resolution_note,
        "wording_supported": {
            "structural": "structurally aliased",
            "practical": "practically aliased at this noise level",
            "identifiable": "identifiable under this design",
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
        json.dump(results, fh, indent=2, default=lambda x: None if isinstance(x, float) and not np.isfinite(x) else x)
    os.replace(tmp, out)
    print(f"\nconclusion ({post_profile['design']}, true u=0.90): {conclusion}")
    print(f"  supported wording: \"{results['wording_supported']}\"")
    print(f"  resolution: {'none' if resolution is None else f'+/-{resolution:.2f} life'} -- {resolution_note}")

    plot(results)


def plot(results):
    collinearity, profiles = results["collinearity_by_point"], results["profiles"]
    plt = figstyle.setup()
    if plt is None:  # pragma: no cover
        return
    fig, (a, b) = plt.subplots(1, 2, figsize=(10.0, 3.8))
    for label, marker in (("u+onset", "o"), ("u+leak", "s"), ("u+onset+leak", "^"), ("u+tau", "x")):
        pts = [r for r in collinearity if r["unit"] == "canonical" and not r.get(label + "_is_inert")]
        if pts:
            a.semilogy([r["u"] for r in pts], [r[label] for r in pts], marker=marker, ls="-", label=label)
    a.text(0.31, 3e3, "onset fraction and leak are\ninert before onset:\ncollinearity undefined, not infinite",
           fontsize=6.5, color="grey", va="center")
    a.axhline(COLLINEARITY_POOR, ls="--", color="k", lw=0.8)
    a.axvline(FatigueParams().acceleration_onset_fraction, ls=":", color="grey", lw=1.0)
    a.set_xlabel("normalized life u"); a.set_ylabel("Brun collinearity index $\\gamma_K$")
    a.set_title("subset collinearity (dashed = poor flag, dotted = onset)", fontsize=9)
    a.legend(fontsize=7)
    for p in profiles:
        # a linear axis is useless here: the pre-onset misfit is ~1e6 while the region of interest is ~1
        ys = [max(q["delta_nll"], 1e-3) for q in p["profile"]]
        style = "o-" if p["design"] == "B2" else "s--"
        b.semilogy([q["u"] for q in p["profile"]], ys, style, ms=3, lw=1.0,
                   label=f"{p['design']}, true u = {p['u_true']:.2f} ({p['verdict']})")
        b.axvline(p["u_true"], ls=":", lw=0.8, color="grey")
    b.axhline(CHI2_95, ls="--", color="k", lw=0.8)
    b.set_xlabel("normalized life u"); b.set_ylabel(r"$\Delta(-\log L)$  (log scale)")
    b.set_title("profile likelihood, nuisance re-optimised (solid B2, dashed B1)", fontsize=9)
    b.legend(fontsize=6)
    fig.tight_layout()
    figstyle.save(fig, os.path.join(DATA, "studyB_fig_structural"))
    plt.close(fig)
    print(f"results + figure -> {DATA}/")


if __name__ == "__main__":
    import sys
    if "--replot" in sys.argv:                      # redraw from the saved result, no recomputation
        plot(json.load(open(os.path.join(DATA, "studyB_structural.json"))))
        print("replotted from the saved result")
    else:
        main()
