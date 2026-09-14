#!/usr/bin/env python3
"""
Gate 0 — Lumped-parameter R-C simulation of shared-manifold pneumatic cross-talk.

Purpose
-------
Pre-test the SPINE of the proposal *in software, for $0*, before any silicone is
cast. The central hypothesis is:

    fatigue -> chamber compliance C(1) up -> manifold redistribution gain up
            -> inter-chamber cross-talk drifts -> pressure-only proprioception degrades

This script builds the lumped pneumatic R-C network (Stanley et al. 2021 framework:
pneumatic resistance R = dP/dQ, pneumatic capacitance/compliance C = dV/dP), forms
the linearized state-space model around a realistic operating point, and asks one
question:

    When chamber 1's compliance rises (fatigue softening), does the measured
    inter-chamber cross-talk coupling drift *monotonically* with that compliance?

Key finding the gate is designed to surface
-------------------------------------------
The DC (steady-state) cross-talk gain is **independent of compliance** (the chamber
and manifold capacitances cancel out of the static gain). Therefore the coupling
drift the proposal depends on is a *dynamic* phenomenon, governed by the RC time
constants. This has a direct experimental consequence: the fatigue->cross-talk
signal lives in the pressure *transients*, so the proprioception model must use
history-dependent (dynamic) features (ARX / ESN), and the gripper must be actuated
in the frequency band where the coupling is compliance-sensitive. A purely static
ridge map on instantaneous pressure would be blind to it.

Model
-----
Nodes: three chamber pressures P_1..P_3 and one manifold node P_m (all gauge).
  Regulated supply  --R_s-->  manifold node  --R_v_i-->  chamber i  --R_l_i--> atm
  chamber i has compliance C_i to atmosphere; manifold has small compliance C_m.

  C_i dP_i/dt = (P_m - P_i)/R_v_i - P_i/R_l_i
  C_m dP_m/dt = (P_s - P_m)/R_s - sum_i (P_m - P_i)/R_v_i

Actuation input u_i = modulation of valve-i conductance (delta g_v_i). Linearized
about the operating point, a conductance modulation injects a flow proportional to
the standing valve pressure drop (P_m0 - P_i0), which is non-zero because of the
bleed path R_l. Output y = the three chamber pressures (what a pressure-only
proprioception pipeline actually sees).

Outputs
-------
  data/gate0/gate0_results.json     machine-readable verdict + metrics
  data/gate0/fig_crosstalk_vs_freq.png
  data/gate0/fig_crosstalk_vs_compliance.png
  data/gate0/fig_dc_independence.png
and a printed PASS / FAIL / WEAK verdict.

Run:  python3 scripts/gate0_lumped_rc.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

# matplotlib is optional at run time; degrade gracefully if headless/missing.
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _HAVE_MPL = True
except Exception:  # pragma: no cover
    _HAVE_MPL = False


# --------------------------------------------------------------------------- #
# Physical parameters (realistic Dragon Skin PneuNet-class soft pneumatics)
# --------------------------------------------------------------------------- #
@dataclass
class Params:
    n_chambers: int = 3
    P_s: float = 80_000.0          # regulated supply, gauge [Pa] (0.8 bar)
    R_s: float = 2.0e8             # supply line resistance [Pa*s/m^3]
    R_v: float = 8.0e8             # nominal valve resistance (partially open) [Pa*s/m^3]
    R_l: float = 8.0e9             # chamber bleed/leak to atmosphere [Pa*s/m^3]
    C0: float = 5.0e-11            # nominal chamber compliance [m^3/Pa] (dV/dP)
    C_m: float = 5.0e-12           # manifold node compliance [m^3/Pa] (small volume)
    # fatigue sweep: chamber-1 compliance multiplier (1.0 = healthy, 2.0 = heavily softened)
    fatigue_min: float = 1.0
    fatigue_max: float = 2.0
    fatigue_steps: int = 11
    # representative actuation frequency for the headline metric [Hz]
    f_actuation_hz: float = 3.0
    # pass thresholds
    monotonic_rho_min: float = 0.99   # |Spearman| across the compliance sweep
    rel_drift_min: float = 0.10       # min fractional change in cross-talk over the sweep


def operating_point(p: Params, gv: np.ndarray, gl: np.ndarray, gs: float):
    """Steady-state node pressures with nominal valves. Capacitance-independent."""
    n = p.n_chambers
    # Unknowns: [P_1..P_n, P_m]; solve K x = b for the static balance.
    K = np.zeros((n + 1, n + 1))
    b = np.zeros(n + 1)
    for i in range(n):
        K[i, i] = -(gv[i] + gl[i])
        K[i, n] = gv[i]
    K[n, n] = -(gs + gv.sum())
    for j in range(n):
        K[n, j] = gv[j]
    b[n] = -gs * p.P_s
    x = np.linalg.solve(K, b)
    return x[:n], x[n]  # chamber pressures, manifold pressure


def build_state_space(p: Params, fatigue: float):
    """Linearized A, B, C, D about the operating point for a given fatigue level."""
    n = p.n_chambers
    gv = np.full(n, 1.0 / p.R_v)
    gl = np.full(n, 1.0 / p.R_l)
    gs = 1.0 / p.R_s

    # chamber 1 (index 0) is the fatiguing chamber: compliance rises with fatigue.
    C = np.full(n, p.C0)
    C[0] = p.C0 * fatigue

    Pi0, Pm0 = operating_point(p, gv, gl, gs)

    A = np.zeros((n + 1, n + 1))
    for i in range(n):
        A[i, i] = (-(gv[i] + gl[i])) / C[i]
        A[i, n] = gv[i] / C[i]
    A[n, n] = (-(gs + gv.sum())) / p.C_m
    for j in range(n):
        A[n, j] = gv[j] / p.C_m

    # input u_i = delta-conductance of valve i; standing drop (Pm0 - Pi0) sets authority
    B = np.zeros((n + 1, n))
    for k in range(n):
        drop = Pm0 - Pi0[k]
        B[k, k] = drop / C[k]
        B[n, k] = -drop / p.C_m

    Cout = np.zeros((n, n + 1))
    for i in range(n):
        Cout[i, i] = 1.0
    D = np.zeros((n, n))
    return A, B, Cout, D, Pi0, Pm0


def transfer_matrix(A, B, Cout, D, omega: float):
    """H(jw) = C (jwI - A)^-1 B + D, returned as an (n x n) complex matrix."""
    n1 = A.shape[0]
    H = Cout @ np.linalg.solve(1j * omega * np.eye(n1) - A, B) + D
    return H


def dc_gain(A, B, Cout, D):
    """Static gain G = -C A^-1 B + D (well-posed because the bleed makes A stable)."""
    return (-Cout @ np.linalg.solve(A, B) + D).real


def crosstalk_metric(H: np.ndarray, driven: int = 0, neighbor: int = 1) -> float:
    """Relative cross-talk: |H[neighbor, driven]| / |H[driven, driven]|."""
    return float(abs(H[neighbor, driven]) / abs(H[driven, driven]))


def crosstalk_abs(H: np.ndarray, driven: int = 0, neighbor: int = 1) -> float:
    """Absolute cross-talk transfer magnitude |H[neighbor, driven]| -- the actually
    measurable neighbor-pressure response that corrupts pose estimation."""
    return float(abs(H[neighbor, driven]))


# --------------------------------------------------------------------------- #
# Gate 0 experiment
# --------------------------------------------------------------------------- #
def run_gate(p: Params) -> dict:
    fatigue_levels = np.linspace(p.fatigue_min, p.fatigue_max, p.fatigue_steps)
    freqs_hz = np.logspace(-2, 2, 400)
    omegas = 2 * np.pi * freqs_hz
    w_act = 2 * np.pi * p.f_actuation_hz

    # ---- (a) DC-gain compliance-independence check ----
    A0, B0, C0o, D0, *_ = build_state_space(p, p.fatigue_min)
    Af, Bf, Cfo, Dfo, *_ = build_state_space(p, p.fatigue_max)
    G_healthy = dc_gain(A0, B0, C0o, D0)
    G_fatigued = dc_gain(Af, Bf, Cfo, Dfo)
    dc_ct_healthy = crosstalk_metric(G_healthy.astype(complex))
    dc_ct_fatigued = crosstalk_metric(G_fatigued.astype(complex))
    dc_rel_change = abs(dc_ct_fatigued - dc_ct_healthy) / dc_ct_healthy

    # ---- (b) cross-talk vs frequency, per compliance level ----
    # ct_vs_freq  : relative ratio |H21/H11| (fraction of self-signal)
    # ctabs_vs_freq: absolute |H21| (the measurable neighbor-pressure response)
    ct_vs_freq = np.zeros((len(fatigue_levels), len(freqs_hz)))
    ctabs_vs_freq = np.zeros((len(fatigue_levels), len(freqs_hz)))
    for i, fat in enumerate(fatigue_levels):
        A, B, Cout, D, *_ = build_state_space(p, fat)
        for j, w in enumerate(omegas):
            H = transfer_matrix(A, B, Cout, D, w)
            ct_vs_freq[i, j] = crosstalk_metric(H)
            ctabs_vs_freq[i, j] = crosstalk_abs(H)

    # ---- (c) headline metric: cross-talk at actuation freq vs compliance ----
    ct_at_act = np.zeros(len(fatigue_levels))
    for i, fat in enumerate(fatigue_levels):
        A, B, Cout, D, *_ = build_state_space(p, fat)
        ct_at_act[i] = crosstalk_metric(transfer_matrix(A, B, Cout, D, w_act))

    rho_act, pval_act = spearmanr(fatigue_levels, ct_at_act)
    rel_drift_act = abs(ct_at_act[-1] - ct_at_act[0]) / abs(ct_at_act[0])

    # ---- (d) which frequency is most fatigue-sensitive? ----
    # The relative ratio |H21/H11| saturates with frequency, so ranking on it pins the
    # answer to the sweep edge. The experimentally meaningful quantity is the ABSOLUTE
    # measurable cross-talk |H21| and how much it MOVES with fatigue, since that is the
    # neighbor-pressure error a pose estimator actually has to contend with.
    rel_drift_spectrum = np.abs(ct_vs_freq[-1] - ct_vs_freq[0]) / np.abs(ct_vs_freq[0])
    abs_drift_spectrum = np.abs(ctabs_vs_freq[-1] - ctabs_vs_freq[0])  # change in |H21|
    # require monotonicity (of the absolute cross-talk) at each frequency
    rho_spectrum = np.array(
        [spearmanr(fatigue_levels, ctabs_vs_freq[:, j])[0] for j in range(len(freqs_hz))]
    )
    sensitive_mask = np.abs(rho_spectrum) >= p.monotonic_rho_min
    if sensitive_mask.any():
        # rank by absolute drift in |H21| -> lands in the physically actuatable band
        best_j = int(np.nanargmax(np.where(sensitive_mask, abs_drift_spectrum, np.nan)))
        best_freq = float(freqs_hz[best_j])
        best_drift = float(rel_drift_spectrum[best_j])      # report relative drift there
        best_abs_drift = float(abs_drift_spectrum[best_j])
        best_rho = float(rho_spectrum[best_j])
        # usable band: monotone AND absolute cross-talk drift >= 25% of its spectral peak
        # (keeps the band where the signal is actually measurable, not just monotone)
        band_mask = sensitive_mask & (abs_drift_spectrum >= 0.25 * abs_drift_spectrum.max())
        band_freqs = freqs_hz[band_mask]
        band = [float(band_freqs.min()), float(band_freqs.max())] if band_mask.any() else None
    else:
        best_freq = best_drift = best_abs_drift = best_rho = None
        band = None

    # ---- verdict ----
    monotone_ok = abs(rho_act) >= p.monotonic_rho_min
    drift_ok = rel_drift_act >= p.rel_drift_min
    if monotone_ok and drift_ok:
        verdict = "PASS"
    elif monotone_ok and best_drift is not None and best_drift >= p.rel_drift_min:
        verdict = "PASS (off-band)"  # monotone everywhere, strong signal at a better freq
    elif monotone_ok:
        verdict = "WEAK"             # monotone but small signal -> coupling may be benign
    else:
        verdict = "FAIL"             # not monotone -> spine does not hold in sim

    results = {
        "params": asdict(p),
        "dc_independence": {
            "crosstalk_healthy": dc_ct_healthy,
            "crosstalk_fatigued": dc_ct_fatigued,
            "relative_change": dc_rel_change,
            "note": "DC cross-talk is compliance-independent by construction; "
                    "near-zero change confirms the coupling drift is purely dynamic.",
        },
        "headline_metric": {
            "actuation_freq_hz": p.f_actuation_hz,
            "crosstalk_vs_fatigue": ct_at_act.tolist(),
            "fatigue_levels": fatigue_levels.tolist(),
            "spearman_rho": float(rho_act),
            "spearman_p": float(pval_act),
            "relative_drift": float(rel_drift_act),
            "monotone_ok": bool(monotone_ok),
            "drift_ok": bool(drift_ok),
        },
        "most_sensitive_frequency": {
            "freq_hz": best_freq,
            "relative_drift": best_drift,
            "abs_crosstalk_drift": best_abs_drift if best_freq else None,
            "spearman_rho": best_rho,
            "usable_band_hz": band,
            "selection_note": "ranked by absolute change in |H21| (measurable neighbor-"
                              "pressure response), not the saturating |H21/H11| ratio.",
        },
        "verdict": verdict,
        "interpretation": _interpretation(verdict, p, best_freq, band),
    }
    # stash arrays for plotting (not serialized)
    results["_plot"] = {
        "freqs_hz": freqs_hz,
        "fatigue_levels": fatigue_levels,
        "ct_vs_freq": ct_vs_freq,
        "ctabs_vs_freq": ctabs_vs_freq,
        "ct_at_act": ct_at_act,
        "rel_drift_spectrum": rel_drift_spectrum,
        "abs_drift_spectrum": abs_drift_spectrum,
        "G_healthy": G_healthy,
        "G_fatigued": G_fatigued,
    }
    return results


def robustness_sweep(n: int = 400, seed: int = 0) -> dict:
    """Monte-Carlo over plausible R/C/P decades to confirm the PASS verdict is not an
    artifact of the hand-picked nominal parameters. Returns summary stats."""
    rng = np.random.default_rng(seed)
    d = Params()
    fats = np.linspace(d.fatigue_min, d.fatigue_max, d.fatigue_steps)
    rhos, drifts = [], []
    for _ in range(n):
        p = Params(
            R_s=10 ** rng.uniform(7.5, 8.7), R_v=10 ** rng.uniform(8.0, 9.2),
            R_l=10 ** rng.uniform(9.0, 10.3), C0=10 ** rng.uniform(-11.0, -10.0),
            C_m=10 ** rng.uniform(-12.3, -11.3), P_s=rng.uniform(40e3, 120e3),
            f_actuation_hz=10 ** rng.uniform(np.log10(0.5), np.log10(8)))
        w = 2 * np.pi * p.f_actuation_hz
        ct = np.array([crosstalk_metric(transfer_matrix(*build_state_space(p, f)[:4], w))
                       for f in fats])
        rhos.append(spearmanr(fats, ct)[0])
        drifts.append(abs(ct[-1] - ct[0]) / ct[0])
    rhos, drifts = np.array(rhos), np.array(drifts)
    mono = np.abs(rhos) >= d.monotonic_rho_min
    return {
        "n": n,
        "frac_monotone": float(mono.mean()),
        "frac_pass": float((mono & (drifts >= d.rel_drift_min)).mean()),
        "all_same_sign_positive": bool(np.all(rhos > 0)),
        "median_abs_rho": float(np.median(np.abs(rhos))),
        "drift_median": float(np.median(drifts)),
        "drift_p10": float(np.percentile(drifts, 10)),
        "drift_p90": float(np.percentile(drifts, 90)),
    }


def _interpretation(verdict, p: Params, best_freq, band) -> str:
    if verdict.startswith("PASS"):
        band_txt = f"{band[0]:.2g}-{band[1]:.2g} Hz" if band else "the actuation band"
        return (
            f"Spine holds in simulation: inter-chamber cross-talk drifts monotonically "
            f"with chamber-1 compliance. The signal is dynamic (DC gain is "
            f"compliance-independent), strongest near {best_freq:.2g} Hz, usable across "
            f"{band_txt}. EXPERIMENTAL IMPLICATION: actuate/probe in this band and use "
            f"history-dependent (ARX/ESN) features; a static ridge map on instantaneous "
            f"pressure will not see the fatigue->cross-talk coupling. Green-light the "
            f"Week-3 hardware gate."
        )
    if verdict == "WEAK":
        return (
            "Cross-talk is monotone in compliance but the magnitude of drift is small "
            "over a realistic fatigue range. The coupling may be benign (an online "
            "corrector could track it out). Still publishable as Studies 1+2, but the "
            "coupling 'spine' (Study 3) is at risk -- treat the hardware gate as decisive."
        )
    return (
        "Cross-talk does NOT vary monotonically with compliance in the lumped model. "
        "The proposed fatigue->cross-talk mechanism is not supported in simulation. "
        "Re-examine the topology/parameters before committing hardware; consider the "
        "G02 kirigami pivot."
    )


# --------------------------------------------------------------------------- #
# Plots
# --------------------------------------------------------------------------- #
def make_plots(results: dict, outdir: Path):
    if not _HAVE_MPL:
        return []
    pl = results["_plot"]
    freqs = pl["freqs_hz"]
    fat = pl["fatigue_levels"]
    saved = []

    # 1) cross-talk vs frequency for a few compliance levels (ratio + absolute)
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11, 4.4))
    idxs = np.linspace(0, len(fat) - 1, 5).astype(int)
    f_act = results["params"]["f_actuation_hz"]
    for i in idxs:
        axL.semilogx(freqs, pl["ct_vs_freq"][i] * 100, label=f"C1 = {fat[i]:.2f}x")
        axR.loglog(freqs, pl["ctabs_vs_freq"][i], label=f"C1 = {fat[i]:.2f}x")
    for ax in (axL, axR):
        ax.axvline(f_act, ls="--", c="k", alpha=0.4)
        ax.set_xlabel("frequency [Hz]")
        ax.grid(True, which="both", alpha=0.3)
    axL.set_ylabel("relative cross-talk |H21/H11|  [%]")
    axL.set_title("Relative cross-talk (saturates with freq)")
    axR.set_ylabel("absolute cross-talk |H21|  [Pa per unit dg]")
    axR.set_title("Measurable cross-talk (peaks in actuation band)")
    axL.legend(fontsize=8)
    fig.suptitle("Inter-chamber cross-talk vs frequency, by chamber-1 compliance "
                 f"(dashed = {f_act:.0f} Hz)", fontsize=11)
    fig.tight_layout()
    f1 = outdir / "fig_crosstalk_vs_freq.png"
    fig.savefig(f1, dpi=130); plt.close(fig); saved.append(f1)

    # 2) headline: cross-talk at actuation freq vs compliance
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    ax.plot(fat, pl["ct_at_act"] * 100, "o-", c="C3")
    ax.set_xlabel("chamber-1 compliance multiplier (fatigue ->)")
    ax.set_ylabel(f"cross-talk at {results['params']['f_actuation_hz']:.0f} Hz  [%]")
    rho = results["headline_metric"]["spearman_rho"]
    dr = results["headline_metric"]["relative_drift"] * 100
    ax.set_title(f"Cross-talk vs fatigue   (Spearman rho={rho:.3f}, drift={dr:.0f}%)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    f2 = outdir / "fig_crosstalk_vs_compliance.png"
    fig.savefig(f2, dpi=130); plt.close(fig); saved.append(f2)

    # 3) DC independence: healthy vs fatigued static gain matrices
    fig, axes = plt.subplots(1, 2, figsize=(8.5, 3.8))
    for ax, G, ttl in zip(axes, [pl["G_healthy"], pl["G_fatigued"]],
                          ["DC gain (healthy)", "DC gain (fatigued, C1=2x)"]):
        im = ax.imshow(np.abs(G), cmap="viridis")
        ax.set_title(ttl, fontsize=10)
        ax.set_xlabel("driven valve i"); ax.set_ylabel("chamber pressure j")
        for (r, c), v in np.ndenumerate(G):
            ax.text(c, r, f"{v:.1e}", ha="center", va="center",
                    color="w", fontsize=7)
        fig.colorbar(im, ax=ax, fraction=0.046)
    fig.suptitle("Static (DC) gain is compliance-independent -> coupling drift is dynamic",
                 fontsize=10)
    fig.tight_layout()
    f3 = outdir / "fig_dc_independence.png"
    fig.savefig(f3, dpi=130); plt.close(fig); saved.append(f3)
    return saved


# --------------------------------------------------------------------------- #
def main():
    repo = Path(__file__).resolve().parents[1]
    outdir = repo / "data" / "gate0"
    outdir.mkdir(parents=True, exist_ok=True)

    p = Params()
    results = run_gate(p)
    figs = make_plots(results, outdir)

    print("Running robustness sweep (400 randomized parameter sets)...")
    results["robustness"] = robustness_sweep()

    serial = {k: v for k, v in results.items() if k != "_plot"}
    (outdir / "gate0_results.json").write_text(json.dumps(serial, indent=2))

    # console report
    hm = results["headline_metric"]
    dci = results["dc_independence"]
    sf = results["most_sensitive_frequency"]
    print("=" * 70)
    print("GATE 0 — shared-manifold cross-talk vs fatigue (lumped R-C sim)")
    print("=" * 70)
    print(f"DC cross-talk change over C1=1x..2x : {dci['relative_change']*100:.4f}%  "
          f"(~0 => coupling is dynamic, not static)")
    print(f"Cross-talk @ {p.f_actuation_hz:.0f} Hz, Spearman rho : {hm['spearman_rho']:+.3f}  "
          f"(p={hm['spearman_p']:.1e})")
    print(f"Cross-talk relative drift @ {p.f_actuation_hz:.0f} Hz : {hm['relative_drift']*100:.1f}%")
    if sf["freq_hz"]:
        print(f"Most fatigue-sensitive frequency    : {sf['freq_hz']:.2g} Hz  "
              f"(|H21| ratio drift {sf['relative_drift']*100:.0f}%, rho {sf['spearman_rho']:+.2f})")
        if sf["usable_band_hz"]:
            print(f"Usable / measurable cross-talk band : "
                  f"{sf['usable_band_hz'][0]:.2g}–{sf['usable_band_hz'][1]:.2g} Hz")
    rb = results["robustness"]
    print(f"Robustness (N={rb['n']} random configs)  : "
          f"{rb['frac_monotone']*100:.0f}% monotone, {rb['frac_pass']*100:.0f}% PASS, "
          f"all positive-sign={rb['all_same_sign_positive']}")
    print("-" * 70)
    print(f"VERDICT: {results['verdict']}")
    print(results["interpretation"])
    print("-" * 70)
    print(f"Wrote: {outdir/'gate0_results.json'}")
    for f in figs:
        print(f"Wrote: {f}")


if __name__ == "__main__":
    main()
