"""Study B — identifiability map of the latent life coordinate from pressure-only features.

Preregistered in docs/specs/phd-program/studyB-identifiability.md. Writes data/sim/studyB/.
"""

from __future__ import annotations

import json
import os

import numpy as np
from scipy.linalg import block_diag

from pipeline.dispersion import SEED, sample_units
from pipeline.identifiability import (FEATURES, PARAMS, bound_u, fim, jacobian, noise_covariance,
                                      whitened_angles_deg)
from sim.fatigue import FatigueParams
from sim.plant import SLSParams
from scripts import figstyle

DATA = "data/sim/studyB"
U_GRID = [round(x, 2) for x in np.arange(0.1, 0.91, 0.1)]
U_BASE = 0.05
NOISE_SCALES = [0.5, 1.0, 4.0]
AMPS = [0.05, 0.1, 0.2]
N_REP = 24
SIGMA_TARGET, SIGMA_KILL = 0.10, 0.25


def theta_of(unit, u):
    fp, sls = unit.fatigue, unit.sls
    return np.array([u, sls.k1, sls.k2, sls.tau, fp.terminal_leak_multiplier,
                     fp.acceleration_onset_fraction, fp.fatigue_exponent])


def evaluate(unit, u, amp, noise, seed, J_base, sigma_base):
    th = theta_of(unit, u)
    J = jacobian(th, unit.fatigue, unit.sls, amp)
    sigma = noise_covariance(th, unit.fatigue, unit.sls, seed, N_REP, noise, amp)
    b1 = bound_u(J, sigma)
    Jb = J_base.copy(); Jb[:, 0] = 0.0                              # the young baseline does not move with u
    b2 = bound_u(np.vstack([Jb, J]), block_diag(sigma_base, sigma))
    F = fim(J, sigma)
    b3 = float(1.0 / np.sqrt(F[0, 0])) if F[0, 0] > 0 else float("inf")
    return {"u": u, "amp_frac": amp, "noise_scale": noise,
            "B1_sigma_u": b1[0], "B1_rank": b1[1], "B1_n_active": b1[2],
            "B2_sigma_u": b2[0], "B2_rank": b2[1], "B2_n_active": b2[2],
            "B3_sigma_u": b3,
            "aliasing_angle_deg": dict(zip(PARAMS[1:], whitened_angles_deg(J, sigma)))}


def main():
    units = [("canonical", type("U", (), {"fatigue": FatigueParams(), "sls": SLSParams()})())]
    units += [(f"dispersed_{i}", u) for i, u in enumerate(sample_units(5, SEED))]
    points = []
    for name, unit in units:
        for amp in AMPS:
            thb = theta_of(unit, U_BASE)
            J_base = jacobian(thb, unit.fatigue, unit.sls, amp)
            for noise in NOISE_SCALES:
                sigma_base = noise_covariance(thb, unit.fatigue, unit.sls, 7, N_REP, noise, amp)
                for u in U_GRID:
                    rec = evaluate(unit, u, amp, noise, 100 + int(1000 * u), J_base, sigma_base)
                    rec["unit"] = name
                    points.append(rec)
                    print(f"{name:12s} amp={amp:<5} noise={noise:<4} u={u:.1f} "
                          f"B1={rec['B1_sigma_u']:.3g} B2={rec['B2_sigma_u']:.3g} B3={rec['B3_sigma_u']:.3g}")

    def frac(pred, sel):
        rows = [p for p in points if sel(p)]
        return float(np.mean([pred(p) for p in rows])) if rows else float("nan")
    default = lambda p: p["noise_scale"] == 1.0 and p["amp_frac"] == 0.1
    per_unit_pass = {name: frac(lambda p: p["B2_sigma_u"] <= SIGMA_TARGET, lambda p, n=name: default(p) and p["unit"] == n)
                     for name, _ in units}
    kill_frac = frac(lambda p: p["B2_sigma_u"] > SIGMA_KILL, lambda p: True)
    dispersed_ok = sum(v >= 0.5 for k, v in per_unit_pass.items() if k != "canonical")
    if per_unit_pass["canonical"] >= 0.5 and dispersed_ok >= 3:
        v = "B-PASS"
    elif kill_frac >= 0.5:
        v = "B-KILL"
    else:
        v = "B-CONDITIONAL"
    out = {"preregistration": "docs/specs/phd-program/studyB-identifiability.md", "seed": SEED,
           "features": FEATURES, "parameters": PARAMS, "u_grid": U_GRID, "u_baseline": U_BASE,
           "noise_scales": NOISE_SCALES, "amplitude_fracs": AMPS, "n_rep": N_REP,
           "sigma_target": SIGMA_TARGET, "sigma_kill": SIGMA_KILL,
           "verdict": v, "per_unit_fraction_within_target_B2_default": per_unit_pass,
           "fraction_of_envelope_above_kill_B2": kill_frac, "points": points}
    os.makedirs(DATA, exist_ok=True)
    json.dump(out, open(os.path.join(DATA, "studyB_results.json"), "w"), indent=2,
              default=lambda x: None if isinstance(x, float) and not np.isfinite(x) else x)
    print(f"Study B verdict: {v} | per-unit fraction within target (B2, default): {per_unit_pass} | "
          f"envelope fraction above kill: {kill_frac:.2f}")

    plt = figstyle.setup()
    if plt is None:  # pragma: no cover
        return
    fig, (a, b) = plt.subplots(1, 2, figsize=(9.5, 3.4))
    for key, lab in (("B1_sigma_u", "B1 single snapshot"), ("B2_sigma_u", "B2 + young baseline"), ("B3_sigma_u", "B3 nuisance known")):
        ys = [next(p[key] for p in points if default(p) and p["unit"] == "canonical" and p["u"] == u) for u in U_GRID]
        a.semilogy(U_GRID, [y if np.isfinite(y) else np.nan for y in ys], "o-", label=lab)
    a.axhline(SIGMA_TARGET, ls="--", color="k", lw=0.8); a.axhline(SIGMA_KILL, ls=":", color="k", lw=0.8)
    a.set_xlabel("normalized life u"); a.set_ylabel("CRLB σ_u [life]"); a.set_title("canonical unit, default probe"); a.legend()
    grid = np.array([[next(p["B2_sigma_u"] for p in points if p["unit"] == "canonical" and p["noise_scale"] == 1.0
                           and p["amp_frac"] == amp and p["u"] == u) for u in U_GRID] for amp in AMPS])
    grid = np.where(np.isfinite(grid), grid, np.nan)
    im = b.imshow(np.log10(grid), aspect="auto", origin="lower", extent=[U_GRID[0] - 0.05, U_GRID[-1] + 0.05, -0.5, len(AMPS) - 0.5])
    b.set_yticks(range(len(AMPS))); b.set_yticklabels([f"{a_:g}·V0" for a_ in AMPS])
    b.set_xlabel("normalized life u"); b.set_title(f"B2 log10 σ_u, noise ×1 — verdict {v}")
    fig.colorbar(im, ax=b, label="log10 σ_u")
    fig.tight_layout(); figstyle.save(fig, os.path.join(DATA, "studyB_fig_identifiability_map")); plt.close(fig)
    print(f"results + figure -> {DATA}/")


if __name__ == "__main__":
    main()
