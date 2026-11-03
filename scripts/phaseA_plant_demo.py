#!/usr/bin/env python3
"""
Phase A demo + validation for sim/plant.py.

Produces:
  data/sim/phaseA/phaseA_results.json
  data/sim/phaseA/figdata/*.csv and *.caption.md, the inputs and captions of
    fig_pv_loops (P-V loops below/at/above the loss peak),
    fig_loop_area_vs_freq (numerical vs analytical loop area) and
    fig_gate0_consistency (SLS network cross-talk vs Gate 0).
  The figures are drawn by figures/matlab/render_figures.m.
  --replot writes only the figure inputs and captions, not phaseA_results.json.

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

from scripts import figure_data


def main(write_results=True):
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
    if write_results:
        (outdir / "phaseA_results.json").write_text(json.dumps(results, indent=2))

    _figdata(outdir, sls, A, fpk, freqs, area_num, area_ana,
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
    print(f"Wrote {outdir}/phaseA_results.json + figure data" if write_results else f"Wrote {outdir}/figdata")


def _figdata(outdir, sls, A, fpk, freqs, area_num, area_ana, tf, ct_const, ct_g0, ct_sls):
    """Plotted series of the three Phase A figures, in SI units, plus their captions."""
    fd = outdir / "figdata"
    note = (f"Simulation: standard-linear-solid wall, {A * 1e6:.0f} mL volume amplitude, τ = {sls.tau:g} s. "
            "No physical measurement.")
    rows, areas = [], {}
    for mult in (0.1, 1.0, 10.0):
        lp = pv_loop(fpk * mult, A, sls)
        areas[mult] = lp["area"]
        rows += [[mult, float(fpk * mult), float(v), float(p)] for v, p in zip(lp["V"], lp["P"])]
    figure_data.write_csv(fd / "fig_pv_loops.csv", ["freq_multiple", "freq_hz", "volume_m3", "pressure_pa"], rows)
    loops = "; ".join(f"{fpk * m:.2f} Hz, {areas[m] * 1e3:.1f} mJ" for m in (0.1, 1.0, 10.0))
    figure_data.write_caption(outdir / "fig_pv_loops", (
        "The loop is widest at the viscoelastic corner. Chamber pressure against chamber volume over one cycle "
        f"at 0.1, 1 and 10 times the corner frequency f = 1/(2πτ) = {fpk:.2f} Hz: dashed orange, solid blue and "
        f"dotted grey. Drive frequency and loop area: {loops}. {note} Values: figdata/fig_pv_loops.csv."))
    figure_data.write_csv(fd / "fig_loop_area_vs_freq.csv", ["freq_hz", "area_numeric_j", "area_analytic_j"],
                          [[float(f), float(n), float(a)] for f, n, a in zip(freqs, area_num, area_ana)])
    rel = np.abs(area_num - area_ana) / np.maximum(area_ana, 1e-30)
    figure_data.write_caption(outdir / "fig_loop_area_vs_freq", (
        "Numerical loop area matches the analytic dissipation. Loop area per cycle against drive frequency: blue "
        "circles are the numerical ∮P dV and the grey line is the analytic standard-linear-solid dissipation. The "
        f"dotted line marks the corner frequency {fpk:.2f} Hz. {note} {len(freqs)} frequencies; largest relative "
        f"error {rel.max() * 100:.2f} %. Values: figdata/fig_loop_area_vs_freq.csv."))
    figure_data.write_csv(fd / "fig_gate0_consistency.csv", ["freq_hz", "crosstalk_gate0", "crosstalk_sls_constant_c",
                                                             "crosstalk_sls"],
                          [[float(f), float(g), float(c), float(x)] for f, g, c, x in zip(tf, ct_g0, ct_const, ct_sls)])
    err = float(np.max(np.abs(ct_const - ct_g0)))
    figure_data.write_caption(outdir / "fig_gate0_consistency", (
        "With constant compliance the SLS network is Gate 0. Relative cross-talk |H21/H11| against drive "
        "frequency for the Gate 0 model (wide grey line), the SLS network with constant compliance C = 1/k1 "
        "(dashed blue, on top of the grey line) and the SLS network with frequency-dependent compliance C(ω) "
        "(solid orange). Simulation: three-chamber network with an SLS wall. Largest gap between Gate 0 and the "
        f"constant-C network: {err:.1e} (cross-talk ratio). Values: figdata/fig_gate0_consistency.csv."))


if __name__ == "__main__":
    import sys
    main(write_results="--replot" not in sys.argv)
