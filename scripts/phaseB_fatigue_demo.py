#!/usr/bin/env python3
"""Phase B canonical-fatigue demonstration and consistency report.

Produces separate observables for (a) volumetric P-V probing and (b) closed-valve
pressure decay. All trajectories are synthetic model outputs, not experimental data.
"""

from __future__ import annotations

from dataclasses import asdict, replace
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]

from sim.fatigue import FatigueParams, degraded_network, degraded_sls, fatigue_state
from sim.plant import (
    NetworkParams,
    SLSParams,
    operational_half_life,
    pv_loop,
    simulate_pressure_decay,
    sls_loss_energy_analytic,
)

from scripts import figstyle, figure_style

plt = figstyle.setup(style=False)


LIFE_STAGES = [0, 5, 10, 250, 1000, 2000, 2450, 2800, 3200, 3500]
RECOVERY_HOURS = [0, 1, 24, 72, 168]
ONSET_SWEEP = [0.50, 0.70, 0.85]
LEAK_SWEEP = [10.0, 20.0, 40.0]


def main(write_results=True):
    outdir = REPO / "data" / "sim" / "phaseB"
    outdir.mkdir(parents=True, exist_ok=True)
    params = FatigueParams()
    base_sls = SLSParams()
    base_net = NetworkParams()
    frequency = base_sls.f_loss_peak
    amplitude = 2.0e-6
    initial_pressure = 60_000.0

    cycles = np.linspace(0, params.rupture_cycles, 141)
    states = [fatigue_state(float(n), 0, params) for n in cycles]
    compliance = np.array([s.compliance_multiplier for s in states])
    loss = np.array([s.loss_multiplier for s in states])
    leak = np.array([s.leak_multiplier for s in states])
    base_area = sls_loss_energy_analytic(amplitude, 2 * np.pi * frequency, base_sls)
    loop_area = base_area * loss

    life_records = []
    loops = {}
    for n in LIFE_STAGES:
        state = fatigue_state(float(n), 0, params)
        sls = degraded_sls(base_sls, state)
        loop = pv_loop(frequency, amplitude, sls)
        loops[n] = loop
        life_records.append(
            {
                "cycles": n,
                **asdict(state),
                "relaxed_compliance_m3_per_pa": sls.C_relaxed,
                "pv_loop_area_j": float(loop["area"]),
            }
        )

    decay_t = np.linspace(0, 3.0, 3001)
    decay_cycles = [0, 2450, 2975, 3500]
    decays = {}
    decay_records = []
    for n in decay_cycles:
        state = fatigue_state(float(n), 0, params)
        sls = degraded_sls(base_sls, state)
        net = degraded_network(base_net, state)
        decay = simulate_pressure_decay(decay_t, initial_pressure, sls, net.R_l)
        half_life = operational_half_life(decay["t"], decay["P"], initial_pressure)
        decays[n] = decay
        decay_records.append(
            {
                "cycles": n,
                "leak_multiplier": state.leak_multiplier,
                "half_life_s": half_life,
            }
        )

    recovery_cycle = 2000.0
    recovery_records = []
    for hours in RECOVERY_HOURS:
        state = fatigue_state(recovery_cycle, hours * 3600, params)
        recovery_records.append(
            {
                "rest_hours": hours,
                "mullins_permanent": state.mullins_permanent,
                "mullins_recoverable": state.mullins_recoverable,
                "compliance_multiplier": state.compliance_multiplier,
            }
        )

    onset_sensitivity = {}
    for onset in ONSET_SWEEP:
        p = replace(params, acceleration_onset_fraction=onset)
        onset_sensitivity[str(onset)] = [
            fatigue_state(float(n), 0, p).fatigue_accelerating for n in cycles
        ]

    leak_sensitivity = []
    for terminal in LEAK_SWEEP:
        p = replace(params, terminal_leak_multiplier=terminal)
        end = fatigue_state(params.rupture_cycles, 0, p)
        end_sls = degraded_sls(base_sls, end)
        end_net = degraded_network(base_net, end)
        decay = simulate_pressure_decay(decay_t, initial_pressure, end_sls, end_net.R_l)
        leak_sensitivity.append(
            {
                "terminal_multiplier": terminal,
                "rupture_half_life_s": operational_half_life(
                    decay["t"], decay["P"], initial_pressure
                ),
            }
        )

    rupture = fatigue_state(params.rupture_cycles, 0, params)
    at_three_tau = fatigue_state(100, 3 * params.recovery_tau_s, params)
    at_no_rest = fatigue_state(100, 0, params)
    leak_sweep_half_lives = [record["rupture_half_life_s"] for record in leak_sensitivity]
    checks = {
        "cycle_zero_identity": fatigue_state(0, 0, params).compliance_multiplier == 1.0,
        "mullins_stable_by_cycle_10": (
            fatigue_state(10, 0, params).mullins_total / params.mullins_amplitude >= 0.95
        ),
        "three_tau_removes_95pct_recoverable": (
            at_three_tau.mullins_recoverable <= 0.05 * at_no_rest.mullins_recoverable
        ),
        "canonical_compliance_rise_16pct": bool(
            np.isclose(rupture.compliance_multiplier, 1.16)
        ),
        "canonical_loop_area_rise_16pct": bool(np.isclose(rupture.loss_multiplier, 1.16)),
        "terminal_leak_20x": bool(np.isclose(rupture.leak_multiplier, 20.0)),
        "compliance_monotone_by_construction": bool(np.all(np.diff(compliance) >= 0)),
        "loop_area_monotone_by_construction": bool(np.all(np.diff(loop_area) >= 0)),
        "pressure_half_life_decreases_with_conductance_at_fixed_sls": bool(
            np.all(np.diff(leak_sweep_half_lives) < 0)
        ),
    }
    verdict = "PASS" if all(checks.values()) else "CHECK"

    results = {
        "label": "SYNTHETIC SIMULATION — not experimental validation",
        "canonical_parameters": asdict(params),
        "parameter_anchor": {
            "target_no_rest_terminal_compliance_rise_fraction": 0.16,
            "target_no_rest_terminal_loop_area_rise_fraction": 0.16,
            "note": (
                "Order-of-magnitude synthetic anchor motivated by Libby's 96% to 80% "
                "FEM-agreement change; not a conversion from accuracy to compliance."
            ),
        },
        "rupture_cycle": params.rupture_cycles,
        "acceleration_onset_cycle": (
            params.rupture_cycles * params.acceleration_onset_fraction
        ),
        "injected_acceleration_window_cycles": (
            params.rupture_cycles * (1 - params.acceleration_onset_fraction)
        ),
        "injected_acceleration_window_note": (
            "Structural model interval only; not a warning time or predicted lead time."
        ),
        "probe": {
            "frequency_hz": frequency,
            "volume_amplitude_m3": amplitude,
            "pv_leak_observability": (
                "None under imposed-volume probing; leakage is measured by pressure decay."
            ),
            "pressure_decay_initial_pa": initial_pressure,
        },
        "life_stages": life_records,
        "pressure_decay": decay_records,
        "recovery": recovery_records,
        "sensitivity": {
            "acceleration_onset_fractions": ONSET_SWEEP,
            "terminal_leak_multipliers": leak_sensitivity,
        },
        "checks_kind": "numerical and model-consistency checks, not empirical validation",
        "checks": checks,
        "verdict": verdict,
    }
    if write_results:
        (outdir / "phaseB_results.json").write_text(json.dumps(results, indent=2))
    # The two figures the saved result holds are drawn from the JSON bytes, so a
    # rerun and a --replot draw the same values.
    saved = json.loads((outdir / "phaseB_results.json").read_text())

    if plt is not None:
        _plots(
            outdir,
            params,
            cycles,
            states,
            compliance,
            loop_area,
            leak,
            loops,
            decays,
            recovery_records,
            onset_sensitivity,
            leak_sensitivity,
            base_area,
        )
        plot_saved(saved, outdir)

    print("=" * 72)
    print("PHASE B — synthetic fatigue + partial recovery + leak observability")
    print("=" * 72)
    print(f"Rupture / acceleration onset       : {params.rupture_cycles:.0f} / "
          f"{params.rupture_cycles * params.acceleration_onset_fraction:.0f} cycles")
    print(f"No-rest terminal compliance/area  : +{(rupture.compliance_multiplier-1)*100:.1f}% / "
          f"+{(rupture.loss_multiplier-1)*100:.1f}%")
    print(f"Recovery tau / permanent floor     : {params.recovery_tau_s/3600:.0f} h / "
          f"{params.mullins_permanent_fraction*100:.0f}%")
    print(f"Terminal leak conductance          : {rupture.leak_multiplier:.0f}x baseline")
    print("-" * 72)
    print(f"VERDICT: {verdict} (consistency only; no empirical validation)")
    print(f"Wrote {outdir}/phaseB_results.json + figures")


def _plots(
    outdir,
    params,
    cycles,
    states,
    compliance,
    loop_area,
    leak,
    loops,
    decays,
    recovery_records,
    onset_sensitivity,
    leak_sensitivity,
    base_area,
):
    figstyle.apply()
    C, S = figstyle.COLOR, figstyle.SIZE
    onset_cycle = params.rupture_cycles * params.acceleration_onset_fraction
    model = (f"Simulation: deterministic fatigue laws (sim/fatigue.py), rupture at {params.rupture_cycles:,.0f} "
             f"cycles,\nacceleration onset at {params.acceleration_onset_fraction:.2f} of life, no rest unless stated.")

    # P-V loops over life (imposed volume): ordered life stages on one vermillion ramp
    shown = [0, 10, 2000, 2450, 3200, 3500]
    fig, ax = plt.subplots(figsize=(figstyle.SINGLE, 3.0))
    for n, col in zip(shown, figstyle.ramp(C["pv"], len(shown))):
        loop = loops[n]
        ax.plot(loop["V"] * 1e6, loop["P"] / 1e3, color=col, lw=1.0, label=f"{n:,}")
    ax.set_xlabel("Chamber volume (mL)")
    ax.set_ylabel("Chamber pressure (kPa)")
    ax.set_title("At imposed volume the loop barely changes")
    ax.legend(title="Cycles", loc="upper left", alignment="left", handlelength=1.2)
    ax.margins(0.05)
    figstyle.footnote(fig, model + "\nImposed-volume probing cannot see the leak; pressure decay measures it.")
    figstyle.save(fig, outdir / "fig_pv_loops_over_life", formats=("png",)); plt.close(fig)

    # life trajectory: three stacked panels sharing the cycle axis
    fig, axes = plt.subplots(3, 1, figsize=(figstyle.SINGLE, 4.6), sharex=True,
                             gridspec_kw={"hspace": 0.18})
    series = [((compliance - 1) * 100, "Compliance\nrise (%)", C["compliance"]),
              ((loop_area / base_area - 1) * 100, "Loop area\nrise (%)", C["pv"]),
              (leak, "Leak conductance\n(× healthy)", C["leak"])]
    for ax, (y, lab, col) in zip(axes, series):
        ax.plot(cycles, y, color=col)
        ax.axvline(onset_cycle, ls="--", lw=0.8, color=C["ref"])
        ax.set_ylabel(lab)
        ax.margins(x=0.02, y=0.08)
    axes[0].annotate(f"onset {onset_cycle:,.0f} cycles", (onset_cycle, 1), xycoords=("data", "axes fraction"),
                     xytext=(-4, -2), textcoords="offset points", ha="right", va="top",
                     fontsize=S["note"], color=C["ref"])
    axes[-1].set_xlabel("Cycles")
    axes[0].set_title("Compliance and loop area rise together;\nthe leak grows only after onset")
    figstyle.footnote(fig, model)
    figstyle.save(fig, outdir / "fig_fatigue_trajectory", formats=("png",)); plt.close(fig)

    # closed-valve pressure decay at four life stages
    fig, ax = plt.subplots(figsize=(figstyle.SINGLE, 2.6))
    shades = figstyle.ramp(C["leak"], len(decays) + 1)[1:]
    for (n, decay), col in zip(decays.items(), shades):
        ax.plot(decay["t"], decay["P"] / decay["P"][0], color=col, label=f"{n:,}")
    ax.axhline(0.5, ls="--", lw=0.8, color=C["ref"])
    ax.text(0.35, 0.52, "half pressure", ha="left", va="bottom", fontsize=S["note"], color=C["ref"])
    ax.set_xlabel("Hold time with valve closed (s)")
    ax.set_ylabel("Pressure / initial pressure")
    ax.set_title("Hold pressure falls faster once the leak grows")
    ax.legend(title="Cycles", loc="upper right", alignment="left", bbox_to_anchor=(1.0, 1.04))
    ax.margins(x=0.02, y=0.04)
    figstyle.footnote(fig, model + " Initial pressure 60 kPa.")
    figstyle.save(fig, outdir / "fig_pressure_decay_over_life", formats=("png",)); plt.close(fig)

    # injected acceleration-onset sensitivity
    fig, ax = plt.subplots(figsize=(figstyle.SINGLE, 2.6))
    blues = figstyle.ramp(C["onset"], len(onset_sensitivity) + 2)[2:]
    for (onset, trajectory), col in zip(onset_sensitivity.items(), blues):
        y = np.asarray(trajectory) * 100
        ax.plot(cycles, y, color=col, label=f"{float(onset):.2f}")
    ax.set_xlabel("Cycles")
    ax.set_ylabel("Accelerating compliance term (%)")
    ax.set_title("A later onset packs the same rise into fewer cycles")
    ax.legend(title="Onset (fraction of life)", loc="upper left", alignment="left")
    ax.margins(x=0.02, y=0.05)
    figstyle.footnote(fig, model.split(",\n")[0] + ". The onset is an injected model\n"
                      "parameter; the curves are not detected lead times.")
    figstyle.save(fig, outdir / "fig_onset_sensitivity", formats=("png",)); plt.close(fig)



def recovery_cycles(result: dict) -> float:
    """Cycle count of the recovery runs: the no-rest life stage whose state equals the zero-rest recovery record."""
    first = result["recovery"][0]
    assert first["rest_hours"] == 0, first
    match = [s["cycles"] for s in result["life_stages"]
             if s["rest_s"] == 0 and s["compliance_multiplier"] == first["compliance_multiplier"]
             and s["mullins_permanent"] == first["mullins_permanent"]
             and s["mullins_recoverable"] == first["mullins_recoverable"]]
    assert len(match) == 1, match
    return match[0]


def recovery_caption(result: dict) -> str:
    p, rec = result["canonical_parameters"], result["recovery"]
    total = [(r["mullins_permanent"] + r["mullins_recoverable"]) * 100 for r in rec]
    hours = ", ".join(f"{r['rest_hours']:g}" for r in rec[:-1]) + f" and {rec[-1]['rest_hours']:g}"
    return (
        f"Rest recovers Mullins softening down to its permanent floor. Mullins compliance rise against rest "
        f"time after {recovery_cycles(result):,.0f} cycles, split into the permanent part (grey) and the "
        f"recoverable part (hatched); markers are the {len(rec)} sampled rest times ({hours} h) and give the "
        f"total. The total falls from {total[0]:.2f} % with no rest to {total[-1]:.2f} % after "
        f"{rec[-1]['rest_hours']:g} h, close to the permanent floor of {rec[0]['mullins_permanent'] * 100:.2f} % "
        f"({p['mullins_permanent_fraction'] * 100:.0f} % of the Mullins amplitude). Recovery time constant "
        f"{p['recovery_tau_s'] / 3600:.0f} h. The horizontal axis is linear below 1 h and logarithmic above. "
        f"Simulation: deterministic fatigue laws (sim/fatigue.py), rupture at {p['rupture_cycles']:,.0f} cycles. "
        "Source: phaseB_results.json."
    )


def recovery_figure(result: dict):
    rec = result["recovery"]
    hours = [r["rest_hours"] for r in rec]
    permanent = np.array([r["mullins_permanent"] * 100 for r in rec])
    recoverable = np.array([r["mullins_recoverable"] * 100 for r in rec])
    fig, ax = plt.subplots(figsize=(figure_style.SINGLE, 2.6))
    fig.subplots_adjust(left=.15, right=.96, top=.86, bottom=.19)
    ax.stackplot(hours, permanent, recoverable, colors=["#BDBDBD", "white"], edgecolor=figure_style.INK,
                 lw=0.6, hatch=["", "////"], labels=["Permanent", "Recoverable"])
    ax.plot(hours, permanent + recoverable, marker="o", label="Total, sampled", clip_on=False, zorder=3,
            **figure_style.MARKER)
    ax.set_xscale("symlog", linthresh=1)
    ax.set_xticks([0, 1, 10, 100], ["0", "1", "10", "100"])
    ax.set_xlim(0, max(hours) * 1.4)
    ax.set_ylim(0, (permanent + recoverable).max() * 1.12)
    ax.set_xlabel("Rest time (h)")
    ax.set_ylabel("Mullins compliance rise (%)")
    fig.legend(loc="upper center", bbox_to_anchor=(.53, .995), ncol=3, columnspacing=.8, handletextpad=.4,
               handlelength=1.3, borderaxespad=0)
    return fig


def leak_caption(result: dict) -> str:
    p, probe = result["canonical_parameters"], result["probe"]
    rows = result["sensitivity"]["terminal_leak_multipliers"]
    pairs = "; ".join(f"{r['terminal_multiplier']:g}× gives {r['rupture_half_life_s'] * 1e3:.1f} ms" for r in rows)
    return (
        "Doubling the terminal leak halves the hold half-life. Closed-valve pressure half-life at rupture "
        f"against the leak conductance at rupture, as a multiple of healthy: {pairs}. Initial hold pressure "
        f"{probe['pressure_decay_initial_pa'] / 1e3:g} kPa. Simulation: deterministic fatigue laws "
        f"(sim/fatigue.py), rupture at {p['rupture_cycles']:,.0f} cycles. Source: phaseB_results.json."
    )


def leak_figure(result: dict):
    rows = result["sensitivity"]["terminal_leak_multipliers"]
    multipliers = [r["terminal_multiplier"] for r in rows]
    half_lives = [r["rupture_half_life_s"] * 1e3 for r in rows]
    fig, ax = plt.subplots(figsize=(figure_style.SINGLE, 2.4))
    fig.subplots_adjust(left=.17, right=.95, top=.95, bottom=.2)
    ax.plot(multipliers, half_lives, marker="o", ms=4, color=figure_style.INK, mfc=figure_style.INK, lw=1.0)
    ax.set_xticks(multipliers, [f"{m:g}" for m in multipliers])
    ax.set_xlabel(r"Leak conductance at rupture ($\times$ healthy)")
    ax.set_ylabel("Hold half-life at rupture (ms)")
    ax.set_ylim(0, max(half_lives) * 1.2)
    ax.margins(x=0.08)
    return fig


def plot_saved(result: dict, outdir: Path) -> None:
    """Draw the two Phase B figures whose values the saved result holds."""
    with plt.rc_context():
        figure_style.apply()
        for stem, figure, caption in (("fig_rest_recovery", recovery_figure, recovery_caption),
                                      ("fig_leak_sensitivity", leak_figure, leak_caption)):
            fig = figure(result)
            figure_style.save(fig, outdir / stem, formats=("png",), caption=caption(result))
            plt.close(fig)


if __name__ == "__main__":
    import sys
    # --replot recomputes the deterministic curves and redraws the figures without
    # rewriting phaseB_results.json (a full run would also record fatigue_exponent there).
    main(write_results="--replot" not in sys.argv)
