"""Study B — identifiability map of the latent life coordinate from pressure-only features.

Preregistered in docs/specs/observability-program/studyB-identifiability.md. Writes data/sim/studyB/.
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
from scripts import figure_style as style

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
    out = {"preregistration": "docs/specs/observability-program/studyB-identifiability.md", "seed": SEED,
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

    plot(out)
    print(f"results + figure -> {DATA}/")



CRAMER_RAO = r"Cram$\acute{\rm e}$r-Rao"
# design key -> (legend label, marker, line style, marker size); the shape names the design
DESIGNS = {"B1_sigma_u": ("B1 single snapshot", "s", "none", 6.5),
           "B2_sigma_u": ("B2 with young baseline", "o", "-", 5),
           "B3_sigma_u": ("B3 nuisance known", "^", (0, (5, 1.5, 1, 1.5)), 5)}
KILL_STYLE = {"color": "black", "lw": 0.8, "ls": ":"}
TOP = 1.0     # infinite bounds are drawn at the top of panel (a)


def _default(p):
    return p["noise_scale"] == 1.0 and p["amp_frac"] == 0.1 and p["unit"] == "canonical"


def design_curves(out):
    """design key -> sigma_u along u_grid for the canonical unit at default noise and amplitude."""
    pts = out["points"]
    return {key: np.array([next(p[key] for p in pts if _default(p) and p["u"] == u) for u in out["u_grid"]],
                          dtype=float) for key in DESIGNS}


def amplitude_grid(out):
    """[amplitude, u] array of the B2 bound for the canonical unit at default noise."""
    pts = out["points"]
    return np.array([[next(p["B2_sigma_u"] for p in pts if p["unit"] == "canonical" and p["noise_scale"] == 1.0
                           and p["amp_frac"] == amp and p["u"] == u) for u in out["u_grid"]]
                     for amp in out["amplitude_fracs"]], dtype=float)


def map_caption(out):
    curves, grid, u = design_curves(out), amplitude_grid(out), np.array(out["u_grid"])
    onset = FatigueParams().acceleration_onset_fraction
    b2 = curves["B2_sigma_u"]
    pre = np.isfinite(b2)
    inf_u = u[~np.isfinite(grid).any(axis=0)]
    assert np.isinf(curves["B1_sigma_u"]).all() and np.isclose(u[pre].max(), onset) and (inf_u > onset).all()
    finite = np.isfinite(grid).all(axis=0)
    halving = [float(np.mean(grid[i, finite] / grid[i + 1, finite])) for i in range(len(grid) - 1)]
    amps = out["amplitude_fracs"]
    steps = " and ".join(f"{h:.2f} from {a:g} to {b:g} V0" for h, a, b in zip(halving, amps, amps[1:]))
    return (f"Simulation: local Cramér-Rao bounds σ_u on normalised life from pressure-only features of the "
            f"canonical synthetic unit, {out['n_rep']} sensor repeats per point, noise ×1. Panel (a): the three "
            "designs at 0.1 V0 probe amplitude; squares are B1 (single snapshot), circles on a solid line B2 "
            "(with young baseline), triangles on a dash-dot line B3 (nuisance known). Filled markers are finite "
            "bounds; hollow markers at the top tick are infinite bounds. The dashed line is the "
            f"{out['sigma_target']:g} life target and the dotted line the {out['sigma_kill']:g} life kill "
            f"criterion. B1 is infinite at every life. With a young baseline σ_u stays between "
            f"{b2[pre].min():.3f} and {b2[pre].max():.3f} life up to the onset at u = {onset:.2f}. Panel (b): the B2 bound for three probe amplitudes, colour and cell number σ_u × 100; "
            f"grey cells marked ∞ are infinite. On average σ_u falls by a factor of {steps}, so doubling the "
            f"amplitude roughly halves it; after onset (u = {', '.join(f'{x:.1f}' for x in inf_u)}) no amplitude "
            f"bounds it. Study B verdict {out['verdict']} (preregistered rule). Source: studyB_results.json.")


def map_figure(out):
    import matplotlib.colors as mcolors
    from matplotlib.lines import Line2D
    plt = style.plt
    style.apply()
    u_grid, amps = out["u_grid"], out["amplitude_fracs"]
    u = np.array(u_grid)
    fig, (a, b) = plt.subplots(1, 2, figsize=(style.FULL, 3.3), gridspec_kw={"width_ratios": [1, 1.15]})
    fig.subplots_adjust(left=0.105, right=0.9, top=0.78, bottom=0.14, wspace=0.42)
    for key, ys in design_curves(out).items():
        _, mk, ls, ms = DESIGNS[key]
        fin = np.isfinite(ys)
        if fin.any():
            a.plot(u[fin], ys[fin], marker=mk, ls=ls, color=style.INK, ms=ms, mew=0.9, mfc=style.FILL[True])
        if (~fin).any():
            a.plot(u[~fin], np.full((~fin).sum(), TOP), marker=mk, ls="none", color=style.INK, ms=ms, mew=0.9,
                   mfc=style.FILL[False], clip_on=False)
    a.axhline(out["sigma_target"], **style.REFERENCE)
    a.axhline(out["sigma_kill"], **KILL_STYLE)
    a.set_yscale("log")
    a.set_ylim(1e-4, TOP)
    a.set_yticks([1e-4, 1e-3, 1e-2, 1e-1, 1], [r"$10^{-4}$", r"$10^{-3}$", r"$10^{-2}$", r"$10^{-1}$", r"$\infty$"])
    a.yaxis.set_minor_formatter(plt.NullFormatter())
    a.set_xlabel(r"Normalized life $u$")
    a.set_ylabel(CRAMER_RAO + r" bound $\sigma_u$ (life)")
    a.margins(x=0.05)

    grid = amplitude_grid(out)
    shown = np.ma.masked_invalid(grid)
    norm = mcolors.LogNorm(vmin=shown.min(), vmax=shown.max())
    cmap = plt.get_cmap("cividis").with_extremes(bad="#E3E3E3")
    im = b.imshow(shown, aspect="auto", origin="lower", cmap=cmap, norm=norm,
                  extent=[u_grid[0] - 0.05, u_grid[-1] + 0.05, -0.5, len(amps) - 0.5])
    for i in range(len(amps)):
        for j, uj in enumerate(u_grid):
            val = grid[i, j]
            if np.isfinite(val):   # heatmap cell numbers: the one text allowed inside the data area
                b.text(uj, i, f"{val * 100:.2g}", ha="center", va="center", size=style.TICK_SIZE,
                       color="black" if norm(val) > 0.55 else "white")
            else:
                b.text(uj, i, r"$\infty$", ha="center", va="center", size=style.TICK_SIZE, color="black")
    b.set_yticks(range(len(amps)), [rf"${a_:g}\,V_0$" for a_ in amps])
    b.set_xticks(u_grid, [f"{x:.1f}" for x in u_grid])
    b.tick_params(length=0)
    for s in b.spines.values():
        s.set_visible(False)
    b.set_xlabel(r"Normalized life $u$")
    b.set_ylabel("Probe amplitude")
    cb = fig.colorbar(im, ax=b, fraction=0.05, pad=0.03)
    cticks = [x for x in (0.015, 0.02, 0.03, 0.04, 0.06) if norm.vmin <= x <= norm.vmax]
    cb.set_ticks(cticks, labels=[f"{x * 100:g}" for x in cticks])
    cb.ax.yaxis.set_minor_formatter(plt.NullFormatter())
    cb.set_label(r"B2 bound $\sigma_u$ ($10^{-2}$ life)")
    cb.ax.tick_params(labelsize=style.TICK_SIZE)
    style.letter(a, 0)
    style.letter(b, 1)
    handles = [Line2D([], [], marker=mk, ls=ls, color=style.INK, ms=ms, mew=0.9, mfc=style.FILL[True], label=lab)
               for lab, mk, ls, ms in DESIGNS.values()]
    handles += [Line2D([], [], marker="o", ls="none", color=style.INK, ms=5, mew=0.9, mfc=style.FILL[False],
                       label="Hollow: bound infinite"),
                Line2D([], [], label="Target", **style.REFERENCE), Line2D([], [], label="Kill", **KILL_STYLE)]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.995), ncol=3, columnspacing=1.4,
               handletextpad=0.5, handlelength=2.6, borderaxespad=0)
    return fig


def plot(out):
    """Identifiability map from a saved or fresh result dict; infinite bounds are drawn as 'not identifiable'."""
    fig = map_figure(out)
    style.save(fig, os.path.join(DATA, "studyB_fig_identifiability_map"), caption=map_caption(out))
    style.plt.close(fig)


if __name__ == "__main__":
    import sys
    if "--replot" in sys.argv:                      # redraw from the saved result, no recomputation
        plot(json.load(open(os.path.join(DATA, "studyB_results.json"))))
        print("replotted from the saved result")
    else:
        main()
