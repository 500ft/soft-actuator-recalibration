#!/usr/bin/env python3
"""
Phase A demo + validation for sim/plant.py.

Produces:
  data/sim/phaseA/fig_pv_loops.png            P-V loops below/at/above the loss peak
  data/sim/phaseA/fig_loop_area_vs_freq.png   numerical vs analytical loop area
  data/sim/phaseA/fig_gate0_consistency.png   SLS network cross-talk vs Gate 0
  data/sim/phaseA/phaseA_results.json

Validation checks (printed):
  1. Numerical loop area matches the closed-form SLS dissipation across frequency.
  2. Loop area peaks at f = 1/(2*pi*tau) and -> 0 at both frequency extremes.
  3. The linearized SLS network with a CONSTANT compliance = 1/k1 reproduces the Gate 0
     cross-talk model to machine precision (regression tie-back to the validated core).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
from sim.plant import (SLSParams, NetworkParams, pv_loop,
                       sls_loss_energy_analytic, linear_network_crosstalk)
from scripts import gate0_lumped_rc as g0  # Gate 0 model for the consistency check

from scripts import figstyle

plt = figstyle.setup(style=False)


def main():
    outdir = REPO / "data" / "sim" / "phaseA"
    outdir.mkdir(parents=True, exist_ok=True)
    sls = SLSParams()
    net = NetworkParams()
    A = 2.0e-6  # 2 mL volume amplitude
    fpk = sls.f_loss_peak

    # ---- (1)+(2) loop area vs frequency: numerical vs analytic ----
    freqs = np.logspace(-1.5, 1.5, 25)
    area_num, area_ana = [], []
    for f in freqs:
        lp = pv_loop(f, A, sls)
        area_num.append(lp["area"])
        area_ana.append(sls_loss_energy_analytic(A, 2 * np.pi * f, sls))
    area_num = np.array(area_num); area_ana = np.array(area_ana)
    area_rel_err = np.abs(area_num - area_ana) / np.maximum(area_ana, 1e-30)
    f_peak_num = freqs[int(np.argmax(area_num))]

    # ---- (3) Gate 0 consistency: constant-compliance SLS network == Gate 0 ----
    test_freqs = np.logspace(-2, 2, 60)
    omegas = 2 * np.pi * test_freqs
    ct_const, ct_g0, ct_sls = [], [], []
    for w in omegas:
        ct_const.append(linear_network_crosstalk(w, net, sls,
                                                 compliance_override=sls.C_relaxed))
        A0, B0, C0o, D0, *_ = g0.build_state_space(g0.Params(C0=sls.C_relaxed), 1.0)
        ct_g0.append(g0.crosstalk_metric(g0.transfer_matrix(A0, B0, C0o, D0, w)))
        ct_sls.append(linear_network_crosstalk(w, net, sls))   # full SLS complex compliance
    ct_const = np.array(ct_const); ct_g0 = np.array(ct_g0); ct_sls = np.array(ct_sls)
    g0_max_err = float(np.max(np.abs(ct_const - ct_g0)))

    # ---- verdict ----
    pass_area = bool(float(np.median(area_rel_err)) < 0.02)
    pass_peak = bool(abs(np.log2(f_peak_num / fpk)) < 0.5)   # within a half-octave
    pass_g0 = bool(g0_max_err < 1e-9)
    verdict = "PASS" if (pass_area and pass_peak and pass_g0) else "CHECK"

    results = {
        "sls": {"k1": sls.k1, "k2": sls.k2, "tau": sls.tau,
                "C_relaxed": sls.C_relaxed, "C_instant": sls.C_instant,
                "f_loss_peak_hz": fpk},
        "loop_area": {"median_rel_err_vs_analytic": float(np.median(area_rel_err)),
                      "max_rel_err": float(np.max(area_rel_err)),
                      "f_peak_numeric_hz": float(f_peak_num),
                      "f_peak_analytic_hz": float(fpk)},
        "gate0_consistency": {"max_abs_crosstalk_err": g0_max_err,
                              "note": "constant-compliance(1/k1) SLS network vs Gate 0 model"},
        "checks": {"area_matches_analytic": pass_area, "peak_at_1over2pitau": pass_peak,
                   "reduces_to_gate0": pass_g0},
        "verdict": verdict,
    }
    (outdir / "phaseA_results.json").write_text(json.dumps(results, indent=2))

    if plt is not None:
        _plots(outdir, sls, A, fpk, freqs, area_num, area_ana,
               test_freqs, ct_const, ct_g0, ct_sls)

    print("=" * 68)
    print("PHASE A — viscoelastic (SLS) plant + P-V loops")
    print("=" * 68)
    print(f"SLS loss peak f = 1/(2*pi*tau)      : {fpk:.2f} Hz "
          f"(numeric peak {f_peak_num:.2f} Hz)")
    print(f"Loop area vs analytic, median err   : {np.median(area_rel_err)*100:.2f}%  "
          f"(max {np.max(area_rel_err)*100:.2f}%)")
    print(f"SLS-network(const C) vs Gate 0, err : {g0_max_err:.2e}  "
          f"(== reduces to validated core)")
    print(f"Relaxed/instant compliance          : {sls.C_relaxed:.2e} / {sls.C_instant:.2e} m^3/Pa")
    print("-" * 68)
    print(f"VERDICT: {verdict}  "
          f"[area:{pass_area} peak:{pass_peak} gate0:{pass_g0}]")
    print(f"Wrote {outdir}/phaseA_results.json + figures")


def _plots(outdir, sls, A, fpk, freqs, area_num, area_ana,
           tf, ct_const, ct_g0, ct_sls):
    # P-V loops at 0.1x, 1x, 10x the loss peak
    fig, ax = plt.subplots(figsize=(6, 5))
    for mult, c in [(0.1, "C0"), (1.0, "C3"), (10.0, "C2")]:
        lp = pv_loop(fpk * mult, A, sls)
        ax.plot(np.array(lp["V"]) * 1e6, np.array(lp["P"]) / 1e3, c,
                label=f"f = {fpk*mult:.2f} Hz  (area {lp['area']*1e3:.2f} mJ)")
    ax.set_xlabel("volume V  [mL]"); ax.set_ylabel("pressure P  [kPa]")
    ax.set_title("Synthetic P-V hysteresis loops (SLS wall)")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(outdir / "fig_pv_loops.png", dpi=130); plt.close(fig)

    # loop area vs frequency: numeric vs analytic
    fig, ax = plt.subplots(figsize=(6.5, 4.3))
    ax.semilogx(freqs, area_num * 1e3, "o", ms=4, label="numerical (∮P dV)")
    ax.semilogx(freqs, area_ana * 1e3, "-", label="analytic SLS dissipation")
    ax.axvline(fpk, ls="--", c="k", alpha=0.4, label=f"f_peak = 1/(2πτ) = {fpk:.2f} Hz")
    ax.set_xlabel("frequency [Hz]"); ax.set_ylabel("loop area [mJ/cycle]")
    ax.set_title("Loop area vs frequency (peaks at the viscoelastic corner)")
    ax.legend(fontsize=8); ax.grid(which="both", alpha=0.3)
    fig.tight_layout(); fig.savefig(outdir / "fig_loop_area_vs_freq.png", dpi=130); plt.close(fig)

    # Gate 0 consistency
    fig, ax = plt.subplots(figsize=(6.5, 4.3))
    ax.semilogx(tf, ct_g0 * 100, "k-", lw=2, label="Gate 0 model (constant C)")
    ax.semilogx(tf, ct_const * 100, "C1--", lw=2, label="SLS network, constant C=1/k1")
    ax.semilogx(tf, ct_sls * 100, "C3-", label="SLS network, full viscoelastic C(ω)")
    ax.set_xlabel("frequency [Hz]"); ax.set_ylabel("cross-talk |H21/H11| [%]")
    ax.set_title("Tie-back: SLS network reduces to Gate 0 in the constant-C limit")
    ax.legend(fontsize=8); ax.grid(which="both", alpha=0.3)
    fig.tight_layout(); fig.savefig(outdir / "fig_gate0_consistency.png", dpi=130); plt.close(fig)


if __name__ == "__main__":
    main()
