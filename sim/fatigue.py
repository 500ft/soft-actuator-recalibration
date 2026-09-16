"""Phase B synthetic fatigue trajectory and immutable plant-parameter adapters.

The laws in this module are deliberately transparent, deterministic assumptions. They
provide known ground truth for analysis-pipeline verification; they are not calibrated
fatigue predictions for a physical actuator.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import math

from sim.plant import NetworkParams, SLSParams


@dataclass(frozen=True)
class FatigueParams:
    """Canonical actuator-life parameters.

    Cycle counts are tied to one fixed loading protocol. ``recovery_tau_s`` uses a
    separate wall-clock time axis and applies only to the rest immediately before a
    state query.
    """

    rupture_cycles: float = 3500.0
    acceleration_onset_fraction: float = 0.70
    mullins_amplitude: float = 0.04
    mullins_cycles_tau: float = 3.0
    mullins_permanent_fraction: float = 0.30
    recovery_tau_s: float = 86_400.0
    slow_fatigue_amplitude: float = 0.04
    accelerating_fatigue_amplitude: float = 0.08
    mullins_loss_coupling: float = 1.0
    fatigue_loss_coupling: float = 1.0
    terminal_leak_multiplier: float = 20.0
    fatigue_exponent: float = 2.0     # power of the acceleration coordinate z in the accelerating term

    def __post_init__(self) -> None:
        positive = {
            "rupture_cycles": self.rupture_cycles,
            "mullins_cycles_tau": self.mullins_cycles_tau,
            "recovery_tau_s": self.recovery_tau_s,
        }
        for name, value in positive.items():
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and > 0")
        if not 0 < self.acceleration_onset_fraction < 1:
            raise ValueError("acceleration_onset_fraction must lie strictly between 0 and 1")
        if not 0 <= self.mullins_permanent_fraction <= 1:
            raise ValueError("mullins_permanent_fraction must lie in [0, 1]")
        nonnegative = {
            "mullins_amplitude": self.mullins_amplitude,
            "slow_fatigue_amplitude": self.slow_fatigue_amplitude,
            "accelerating_fatigue_amplitude": self.accelerating_fatigue_amplitude,
            "mullins_loss_coupling": self.mullins_loss_coupling,
            "fatigue_loss_coupling": self.fatigue_loss_coupling,
        }
        for name, value in nonnegative.items():
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and >= 0")
        if not math.isfinite(self.terminal_leak_multiplier) or self.terminal_leak_multiplier < 1:
            raise ValueError("terminal_leak_multiplier must be finite and >= 1")
        if not math.isfinite(self.fatigue_exponent) or self.fatigue_exponent <= 0:
            raise ValueError("fatigue_exponent must be finite and > 0")


@dataclass(frozen=True)
class FatigueState:
    """Decomposed ground-truth state at one cycle/rest query."""

    cycles: float
    rest_s: float
    normalized_life: float
    acceleration_coordinate: float
    mullins_permanent: float
    mullins_recoverable: float
    mullins_total: float
    fatigue_slow: float
    fatigue_accelerating: float
    fatigue_total: float
    compliance_multiplier: float
    loss_multiplier: float
    leak_multiplier: float


def fatigue_state(cycles: float, rest_s: float, params: FatigueParams) -> FatigueState:
    """Evaluate the canonical life law without retaining arbitrary loading history."""

    if not math.isfinite(cycles) or cycles < 0 or cycles > params.rupture_cycles:
        raise ValueError("cycles must be finite and within [0, rupture_cycles]")
    if not math.isfinite(rest_s) or rest_s < 0:
        raise ValueError("rest_s must be finite and >= 0")

    u = cycles / params.rupture_cycles
    onset = params.acceleration_onset_fraction
    z = max(0.0, (u - onset) / (1.0 - onset))

    mullins_saturated = params.mullins_amplitude * (
        1.0 - math.exp(-cycles / params.mullins_cycles_tau)
    )
    mullins_permanent = mullins_saturated * params.mullins_permanent_fraction
    mullins_recoverable = (
        mullins_saturated
        * (1.0 - params.mullins_permanent_fraction)
        * math.exp(-rest_s / params.recovery_tau_s)
    )
    mullins_total = mullins_permanent + mullins_recoverable

    fatigue_slow = params.slow_fatigue_amplitude * u
    fatigue_accelerating = params.accelerating_fatigue_amplitude * z**params.fatigue_exponent
    fatigue_total = fatigue_slow + fatigue_accelerating
    compliance_multiplier = 1.0 + mullins_total + fatigue_total
    loss_multiplier = (
        1.0
        + params.mullins_loss_coupling * mullins_total
        + params.fatigue_loss_coupling * fatigue_total
    )
    leak_multiplier = 1.0 + (params.terminal_leak_multiplier - 1.0) * z**2

    return FatigueState(
        cycles=float(cycles),
        rest_s=float(rest_s),
        normalized_life=u,
        acceleration_coordinate=z,
        mullins_permanent=mullins_permanent,
        mullins_recoverable=mullins_recoverable,
        mullins_total=mullins_total,
        fatigue_slow=fatigue_slow,
        fatigue_accelerating=fatigue_accelerating,
        fatigue_total=fatigue_total,
        compliance_multiplier=compliance_multiplier,
        loss_multiplier=loss_multiplier,
        leak_multiplier=leak_multiplier,
    )


def degraded_sls(base: SLSParams, state: FatigueState) -> SLSParams:
    """Return degraded SLS parameters; leave ``base`` unchanged."""

    return replace(
        base,
        k1=base.k1 / state.compliance_multiplier,
        k2=base.k2 * state.loss_multiplier,
    )


def degraded_network(base: NetworkParams, state: FatigueState) -> NetworkParams:
    """Return network parameters with increased leak conductance (reduced R_l)."""

    return replace(base, R_l=base.R_l / state.leak_multiplier)
