"""Phase E/D study 4 — parameter-sensitivity of shared-manifold cross-talk.

Phase E retained an honest negative result: under a shared manifold the inter-chamber
cross-talk is *second-order* — a dynamic (lagged-input) corrector buys ~0% over a static
ridge (``scripts/run_study2.py``). The weakness of that statement is that it is "true at
THESE network parameters." This study converts the null into a *characterized regime* by
sweeping the network parameters that set the cross-talk magnitude, so the paper can say
"cross-talk is second-order across this envelope, and would only become first-order beyond
it."

Physics of the knob (see ``sim.network`` / ``sim.plant``)
---------------------------------------------------------
Driving one valve pulls the shared manifold node ``P_m``; how much the *neighbours* feel that
pull is the cross-talk. The dominant knob is the **supply softness**:

  * ``R_s`` (supply resistance). Larger ``R_s`` = a more throttled / more *shared* supply: the
    regulator cannot refill the manifold fast enough when a valve draws on it, so the node sags
    and neighbours are dragged along -> **more** cross-talk. This is the primary softness axis.
  * ``C_m`` (manifold compliance). Larger ``C_m`` = a bigger buffer reservoir on the node, so a
    valve transient moves ``P_m`` *less* -> **less** cross-talk. (Weaker knob over this range.)
  * ``R_v`` (valve resistance). Larger ``R_v`` decouples the chamber from the manifold -> less
    cross-talk. Reported for completeness.

Cross-talk strength is measured with ``sim.network.probe_coupling`` — a single-chamber
sinusoidal valve probe returning ``|neighbour response| / |driven response|`` at the actuation
band. We sweep each knob as a multiple of its default, locate the multiple at which coupling
crosses 10 % and 20 % (the "becomes first-order" threshold), and — at a few representative
softness settings — regenerate a small per-actuator dataset and check whether a dynamic
corrector starts to beat a static ridge (reusing ``pipeline.correctors``).

Deterministic / seeded throughout (same style as ``scripts.phaseD_dataset``). Writes
``study4_results.json`` and one figure (coupling vs supply softness) under ``data/sim/phaseD/``.
Run: python -m scripts.run_study4
"""

from __future__ import annotations

import dataclasses
import json
import os

import numpy as np

from pipeline.correctors import RidgeCorrector, rmse
from sim.fatigue import FatigueParams, degraded_sls, fatigue_state
from sim.kinematics import PCCParams, curvature_from_pressure
from sim.network import _conductances, probe_coupling, simulate_network
from sim.plant import NetworkParams, SLSParams
from scripts import figstyle

DATA = "data/sim/phaseD"

# --- sweep grid (multiples of the default network parameter) ------------------
# log-spaced so the 10 %/20 % crossings are well resolved; default (x1.0) is included.
SWEEP_MULT = np.round(np.geomspace(0.25, 32.0, 28), 4)
THRESHOLDS = [0.10, 0.20]                 # "cross-talk becomes first-order" markers
CORRECTOR_MULTS = [1.0, 4.0, 16.0]        # representative softness settings for the corrector check

# --- small per-actuator dataset for the corrector check (seeded, self-contained) ---
GLOBAL_SEED = 20260623
N_ACTUATORS = 6                            # small regenerated set (full study uses 20)
N_NEIGHBORS = 2
EXCITE_FREQS = [1.0, 2.0, 3.5]
EXCITE_DEPTH = 0.30
T_DURATION = 4.0
T_POINTS = 240
LIFE_FRACTIONS = [0.10, 0.30, 0.50, 0.70, 0.90]
YOUNG_MID = [0.10, 0.30, 0.50]
OLD = [0.70, 0.90]
N_LAGS = 8
ALPHA = 1.0


# --------------------------------------------------------------------------- #
# Coupling sweep
# --------------------------------------------------------------------------- #
def coupling_curve(base, sls_list, field):
    """Coupling ratio vs ``SWEEP_MULT`` for a single network ``field`` (e.g. 'R_s')."""
    out = []
    for mult in SWEEP_MULT:
        net = dataclasses.replace(base, **{field: getattr(base, field) * float(mult)})
        out.append(float(probe_coupling(sls_list, net, "shared")))
    return np.asarray(out)


def first_crossing_mult(mults, coupling, threshold):
    """Multiple of the default at which a *monotone-increasing* coupling curve crosses
    ``threshold`` (log-linear interpolation). ``None`` if it never reaches it on the grid."""
    coupling = np.asarray(coupling)
    if coupling[-1] < threshold or coupling[0] >= threshold:
        # never reaches it, or already above it at the softest-buffered end of the grid
        if coupling[0] >= threshold:
            return float(mults[0])
        return None
    k = int(np.searchsorted(coupling, threshold))
    lm0, lm1 = np.log(mults[k - 1]), np.log(mults[k])
    c0, c1 = coupling[k - 1], coupling[k]
    return float(np.exp(lm0 + (threshold - c0) / (c1 - c0) * (lm1 - lm0)))


# --------------------------------------------------------------------------- #
# Corrector check (does dynamic start to beat static as the supply softens?)
# --------------------------------------------------------------------------- #
def _build_actuators(n=N_ACTUATORS):
    acts = []
    for aid in range(n):
        r = np.random.default_rng(1000 + aid)
        pcc = PCCParams(
            length_m=0.08 + 0.06 * r.random(),
            kappa_gain=1.5e-5 + 1.0e-5 * r.random(),
            plane_azimuth_rad=2.0 * np.pi * r.random(),
        )
        sls = SLSParams(
            k1=2.0e10 * (0.9 + 0.2 * r.random()),
            k2=2.0e10 * (0.9 + 0.2 * r.random()),
            tau=0.10 * (0.8 + 0.4 * r.random()),
        )
        acts.append({"pcc": pcc, "sls": sls, "rupture": 3000.0 + 1000.0 * r.random()})
    return acts


def _dataset_for(net):
    """Regenerate a small shared-manifold per-actuator dataset under network ``net``.

    Returns a list of ``(actuator_id, life, features (T,F), kappa (T,))`` records. Features =
    [shared-manifold pressure, every chamber's valve command] — identical to study 2.
    """
    nb = net.n_chambers
    _, _, gv0 = _conductances(nb, net, None)
    t = np.linspace(0.0, T_DURATION, T_POINTS)
    acts = _build_actuators()
    freqs = np.asarray(EXCITE_FREQS, dtype=float)
    recs = []
    for aid in range(len(acts)):
        focal = acts[aid]
        pcc = focal["pcc"]
        fp = FatigueParams(rupture_cycles=focal["rupture"])
        neigh = [(aid + 1 + j) % len(acts) for j in range(N_NEIGHBORS)]
        for life in LIFE_FRACTIONS:
            fs = fatigue_state(life * focal["rupture"], 0.0, fp)
            sls_list = [degraded_sls(acts[i]["sls"], fs) for i in [aid] + neigh]
            leak = np.full(nb, fs.leak_multiplier)
            phases = np.array([
                np.random.default_rng([GLOBAL_SEED, aid, 0, ch]).uniform(0.0, 2.0 * np.pi, freqs.size)
                for ch in range(nb)])

            def gv(tt, phases=phases):
                s = np.sin(2.0 * np.pi * freqs[None, :] * tt + phases).mean(axis=1)
                return gv0 * (1.0 + EXCITE_DEPTH * s)

            arg = 2.0 * np.pi * freqs[None, None, :] * t[:, None, None] + phases[None, :, :]
            cmd_all = EXCITE_DEPTH * np.sin(arg).mean(axis=2)               # (T, nb)
            res = simulate_network(t, gv, "shared", sls_list, net, leak_multiplier=leak)
            kappa = curvature_from_pressure(res["P"][0], fs.compliance_multiplier, pcc)
            feats = np.concatenate([res["P_m"][:, None], cmd_all], axis=-1)
            recs.append((aid, round(life, 3), feats, kappa))
    return recs


def corrector_gap(net):
    """Per-actuator static-vs-dynamic curvature RMSE (young+mid -> old) under ``net``.

    Mirrors ``scripts.run_study2`` Experiment B on the regenerated dataset; the
    ``dynamic_improvement`` is ``(static - dynamic)/static`` (positive = dynamic helps)."""
    recs = _dataset_for(net)
    ym = [round(x, 3) for x in YOUNG_MID]
    old = [round(x, 3) for x in OLD]
    ids = sorted({r[0] for r in recs})
    s_list, d_list = [], []
    for aid in ids:
        tr = [(f, k) for (a, l, f, k) in recs if a == aid and l in ym]
        te = [(f, k) for (a, l, f, k) in recs if a == aid and l in old]
        if not tr or not te:
            continue
        static = RidgeCorrector(n_lags=0, alpha=ALPHA).fit([f for f, _ in tr], [k for _, k in tr])
        dynamic = RidgeCorrector(n_lags=N_LAGS, alpha=ALPHA).fit([f for f, _ in tr], [k for _, k in tr])
        s_list.append(float(np.mean([rmse(static.predict(f), k) for f, k in te])))
        d_list.append(float(np.mean([rmse(dynamic.predict(f), k) for f, k in te])))
    s = float(np.mean(s_list))
    d = float(np.mean(d_list))
    return {"static_kappa_rmse": s, "dynamic_kappa_rmse": d,
            "dynamic_improvement": (s - d) / s}


# --------------------------------------------------------------------------- #
def main():
    base = NetworkParams(n_chambers=1 + N_NEIGHBORS)
    sls_list = [SLSParams() for _ in range(base.n_chambers)]
    default_coupling = float(probe_coupling(sls_list, base, "shared"))

    # --- coupling vs each knob ------------------------------------------------
    c_Rs = coupling_curve(base, sls_list, "R_s")   # softer supply (larger R_s) -> more cross-talk
    c_Cm = coupling_curve(base, sls_list, "C_m")   # bigger buffer (larger C_m) -> less cross-talk
    c_Rv = coupling_curve(base, sls_list, "R_v")   # stiffer valves (larger R_v) -> less cross-talk

    # --- physical sanity: cross-talk must increase monotonically with supply softness ---
    # Softness axis 1: R_s up. Softness axis 2: C_m DOWN (so reverse before checking increase).
    d_Rs = np.diff(c_Rs)
    d_Cm_soft = np.diff(c_Cm[::-1])
    assert np.all(d_Rs > 0), f"coupling not monotone increasing in R_s: min d={d_Rs.min():.2e}"
    assert np.all(d_Cm_soft > 0), \
        f"coupling not monotone increasing as C_m softens (decreases): min d={d_Cm_soft.min():.2e}"
    monotonic_ok = True

    crossings = {
        "R_s": {f"{th:.2f}": first_crossing_mult(SWEEP_MULT, c_Rs, th) for th in THRESHOLDS},
        "C_m": {f"{th:.2f}": first_crossing_mult(SWEEP_MULT, c_Cm[::-1], th) for th in THRESHOLDS},
    }

    # --- corrector check at representative softness settings ------------------
    corrector = {}
    for mult in CORRECTOR_MULTS:
        net = dataclasses.replace(base, R_s=base.R_s * float(mult))
        gap = corrector_gap(net)
        gap["coupling"] = float(probe_coupling(sls_list, net, "shared"))
        corrector[f"R_s_x{mult:g}"] = gap

    results = {
        "description": "Parameter-sensitivity of shared-manifold inter-chamber cross-talk.",
        "default_params": {
            "R_s": base.R_s, "R_v": base.R_v, "R_l": base.R_l, "C_m": base.C_m,
            "n_chambers": base.n_chambers,
        },
        "default_coupling": default_coupling,
        "probe": {"freq_hz": 2.0, "depth": 0.1, "driven": 0, "neighbor": 1},
        "sweep_multiplier": SWEEP_MULT.tolist(),
        "coupling_vs_multiplier": {
            "R_s": c_Rs.tolist(),     # supply resistance (primary softness knob)
            "C_m": c_Cm.tolist(),     # manifold compliance (buffer; opposite sign)
            "R_v": c_Rv.tolist(),     # valve resistance (for completeness)
        },
        "thresholds": THRESHOLDS,
        "softness_multiplier_at_threshold": crossings,
        "monotonic_increase_with_supply_softness": monotonic_ok,
        "corrector_check_static_vs_dynamic": corrector,
    }
    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, "study4_results.json"), "w") as fh:
        json.dump(results, fh, indent=2)

    # --- console summary ------------------------------------------------------
    print("=== Study 4: parameter-sensitivity of shared-manifold cross-talk ===")
    print(f"default coupling (R_s={base.R_s:.2e}, C_m={base.C_m:.2e}) = "
          f"{default_coupling*100:.2f}%  -> second-order")
    print("supply softness needed to reach threshold (multiple of default R_s):")
    for th in THRESHOLDS:
        m = crossings["R_s"][f"{th:.2f}"]
        print(f"  coupling = {th*100:.0f}%  at  R_s x {m:.2f}" if m else
              f"  coupling = {th*100:.0f}%  not reached on grid")
    print("monotone increase with supply softness (R_s up, C_m down): "
          f"{'PASS' if monotonic_ok else 'FAIL'}")
    print("corrector check (static vs dynamic, young+mid -> old):")
    for key, g in corrector.items():
        print(f"  {key:10s} coupling={g['coupling']*100:5.2f}%  "
              f"static kRMSE={g['static_kappa_rmse']:.4f}  dynamic={g['dynamic_kappa_rmse']:.4f}  "
              f"dyn_improvement={100*g['dynamic_improvement']:+.1f}%")

    # --- figure: coupling vs supply softness ---------------------------------
    plt = figstyle.setup()
    if plt is None:  # pragma: no cover
        print("(matplotlib unavailable, skipped figure)")
        print(f"results -> {DATA}/study4_results.json")
        return

    fig, ax = plt.subplots()
    ax.plot(SWEEP_MULT, np.asarray(c_Rs) * 100.0, "o-",
            label="softer supply  (R_s up)")
    ax.plot(SWEEP_MULT, np.asarray(c_Cm) * 100.0, "s--",
            label="bigger node buffer  (C_m up)", alpha=0.85)
    # default operating point
    ax.scatter([1.0], [default_coupling * 100.0], color="#000000", zorder=5, s=45)
    ax.annotate(f"default\n{default_coupling*100:.1f}% (2nd-order)",
                xy=(1.0, default_coupling * 100.0), xytext=(1.15, default_coupling * 100.0 + 9),
                fontsize=8.5, ha="left",
                arrowprops=dict(arrowstyle="->", lw=0.8))
    # first-order regime markers (on the R_s curve)
    for th in THRESHOLDS:
        m = crossings["R_s"][f"{th:.2f}"]
        if m is not None:
            ax.axhline(th * 100.0, color="#D55E00", lw=0.8, ls=":", alpha=0.6)
            ax.annotate(f"{th*100:.0f}%  (R_s x{m:.1f})",
                        xy=(SWEEP_MULT[-1], th * 100.0), xytext=(SWEEP_MULT[-1], th * 100.0 + 1.0),
                        fontsize=8, ha="right", color="#D55E00")
    # shade the "would-become-first-order" band (>= 10 %)
    ax.axhspan(THRESHOLDS[0] * 100.0, max(np.max(c_Rs) * 100.0, THRESHOLDS[-1] * 100.0 + 5),
               color="#D55E00", alpha=0.06)
    ax.set_xscale("log")
    ax.set_xlabel("supply softness  (parameter / default)")
    ax.set_ylabel("cross-talk coupling ratio  [%]")
    ax.set_title("Cross-talk vs shared-supply softness")
    ax.legend(loc="upper left")
    fig.tight_layout()
    figstyle.save(fig, os.path.join(DATA, "study4_fig_crosstalk_sensitivity"))
    plt.close(fig)
    print(f"figure + results -> {DATA}/")


if __name__ == "__main__":
    main()
