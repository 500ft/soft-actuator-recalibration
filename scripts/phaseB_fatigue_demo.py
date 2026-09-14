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

from scripts import figstyle

plt = figstyle.setup(style=False)


LIFE_STAGES = [0, 5, 10, 250, 1000, 2000, 2450, 2800, 3200, 3500]
RECOVERY_HOURS = [0, 1, 24, 72, 168]
ONSET_SWEEP = [0.50, 0.70, 0.85]
LEAK_SWEEP = [10.0, 20.0, 40.0]


def main():
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
    (outdir / "phaseB_results.json").write_text(json.dumps(results, indent=2))

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
    fig, ax = plt.subplots(figsize=(7, 5))
    for n in [0, 10, 2000, 2450, 3200, 3500]:
        loop = loops[n]
        ax.plot(loop["V"] * 1e6, loop["P"] / 1e3, label=f"N={n}")
    ax.set(xlabel="volume [mL]", ylabel="pressure [kPa]",
           title="Synthetic P-V loops over life (imposed volume; leak not observable)")
    ax.legend(fontsize=8); ax.grid(alpha=0.3); fig.tight_layout()
    fig.savefig(outdir / "fig_pv_loops_over_life.png", dpi=130); plt.close(fig)

    fig, axes = plt.subplots(3, 1, figsize=(7, 8), sharex=True)
    axes[0].plot(cycles, (compliance - 1) * 100)
    axes[0].set_ylabel("compliance rise [%]")
    axes[1].plot(cycles, (loop_area / base_area - 1) * 100)
    axes[1].set_ylabel("loop-area rise [%]")
    axes[2].plot(cycles, leak)
    axes[2].set_ylabel("latent leak multiplier [x]"); axes[2].set_xlabel("cycles")
    for ax in axes:
        ax.axvline(params.rupture_cycles * params.acceleration_onset_fraction,
                   ls="--", c="k", alpha=0.4)
        ax.grid(alpha=0.3)
    fig.suptitle("Canonical synthetic life trajectory (consistency output)")
    fig.tight_layout(); fig.savefig(outdir / "fig_fatigue_trajectory.png", dpi=130)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for n, decay in decays.items():
        ax.plot(decay["t"], decay["P"] / decay["P"][0], label=f"N={n}")
    ax.axhline(0.5, ls="--", c="k", alpha=0.4)
    ax.set(xlabel="hold time [s]", ylabel="normalized pressure [-]",
           title="Closed-valve pressure decay: explicit leak observable")
    ax.legend(); ax.grid(alpha=0.3); fig.tight_layout()
    fig.savefig(outdir / "fig_pressure_decay_over_life.png", dpi=130); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    hours = [r["rest_hours"] for r in recovery_records]
    permanent = [r["mullins_permanent"] * 100 for r in recovery_records]
    recoverable = [r["mullins_recoverable"] * 100 for r in recovery_records]
    ax.stackplot(hours, permanent, recoverable, labels=["permanent floor", "recoverable"])
    ax.set_xscale("symlog", linthresh=1)
    ax.set(xlabel="rest time [hours]", ylabel="Mullins compliance contribution [%]",
           title="Partial Mullins recovery at N=2000")
    ax.legend(); ax.grid(alpha=0.3); fig.tight_layout()
    fig.savefig(outdir / "fig_rest_recovery.png", dpi=130); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for onset, trajectory in onset_sensitivity.items():
        ax.plot(cycles, np.asarray(trajectory) * 100, label=f"u_d={onset}")
    ax.set(xlabel="cycles", ylabel="accelerating contribution [%]",
           title="Injected acceleration-onset sensitivity (not detected lead time)")
    ax.legend(); ax.grid(alpha=0.3); fig.tight_layout()
    fig.savefig(outdir / "fig_onset_sensitivity.png", dpi=130); plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    multipliers = [r["terminal_multiplier"] for r in leak_sensitivity]
    half_lives = [r["rupture_half_life_s"] for r in leak_sensitivity]
    ax.plot(multipliers, half_lives, "o-")
    ax.set(xlabel="terminal leak conductance multiplier [x]",
           ylabel="pressure half-life at rupture [s]",
           title="Leak-magnitude sensitivity")
    ax.grid(alpha=0.3); fig.tight_layout()
    fig.savefig(outdir / "fig_leak_sensitivity.png", dpi=130); plt.close(fig)


if __name__ == "__main__":
    main()
