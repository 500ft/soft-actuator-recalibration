"""Study A — physically motivated between-unit dispersion of the plant and the degradation law.

Every unit draws all axes in a fixed order so that ablations (``axes`` subset) reuse the same
realisations and differ only in which draws are applied. Magnitudes are assumed with a cited
order of magnitude (docs/specs/phd-program/studyA-preregistration.md), not measured.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import math

import numpy as np
from scipy.special import gamma
from scipy.stats import truncnorm

from pipeline.validation import _weibull_shape_for_cv
from sim.fatigue import FatigueParams
from sim.plant import SLSParams

SEED = 20260916
AXES = ("rupture", "mullins", "fatigue_law", "leak", "tau", "stiffness", "thickness", "temperature")
T0_K = 298.15            # reference 25 °C
EA_OVER_R = 40e3 / 8.314  # Arrhenius activation energy / gas constant [K], assumed


@dataclass(frozen=True)
class Unit:
    fatigue: FatigueParams
    sls: SLSParams
    temperature_c: float
    thickness_ratio: float


def _lognormal(rng, mean, cv):
    s2 = math.log(1.0 + cv * cv)
    return float(rng.lognormal(math.log(mean) - s2 / 2.0, math.sqrt(s2)))


def _truncnorm(rng, mean, sd, low, high):
    return float(truncnorm.rvs((low - mean) / sd, (high - mean) / sd, loc=mean, scale=sd, random_state=rng))


def sample_unit(rng: np.random.Generator, axes=AXES) -> Unit:
    """One unit: draws every axis in a fixed order, applies only those in ``axes``."""
    fp, sls = FatigueParams(), SLSParams()
    shape = _weibull_shape_for_cv(0.30)
    d = {
        "rupture": float(rng.weibull(shape) * 3500.0 / gamma(1 + 1 / shape)),
        "mullins_amplitude": _lognormal(rng, fp.mullins_amplitude, 0.25),
        "mullins_permanent_fraction": _truncnorm(rng, 0.30, 0.08, 0.05, 0.70),
        "mullins_cycles_tau": _lognormal(rng, fp.mullins_cycles_tau, 0.30),
        "slow_fatigue_amplitude": _lognormal(rng, fp.slow_fatigue_amplitude, 0.25),
        "accelerating_fatigue_amplitude": _lognormal(rng, fp.accelerating_fatigue_amplitude, 0.25),
        "acceleration_onset_fraction": _truncnorm(rng, 0.70, 0.08, 0.45, 0.90),
        "fatigue_exponent": _truncnorm(rng, 2.0, 0.35, 1.2, 3.0),
        "terminal_leak_multiplier": _lognormal(rng, fp.terminal_leak_multiplier, 0.35),
        "tau": _lognormal(rng, sls.tau, 0.25),
        "k1": _lognormal(rng, sls.k1, 0.10),
        "k2": _lognormal(rng, sls.k2, 0.10),
        "thickness": _truncnorm(rng, 1.0, 0.08, 0.75, 1.25),
        "temperature_c": float(rng.uniform(15.0, 35.0)),
    }
    if "rupture" in axes:
        fp = replace(fp, rupture_cycles=d["rupture"])
    if "mullins" in axes:
        fp = replace(fp, mullins_amplitude=d["mullins_amplitude"],
                     mullins_permanent_fraction=d["mullins_permanent_fraction"],
                     mullins_cycles_tau=d["mullins_cycles_tau"])
    if "fatigue_law" in axes:
        fp = replace(fp, slow_fatigue_amplitude=d["slow_fatigue_amplitude"],
                     accelerating_fatigue_amplitude=d["accelerating_fatigue_amplitude"],
                     acceleration_onset_fraction=d["acceleration_onset_fraction"],
                     fatigue_exponent=d["fatigue_exponent"])
    if "leak" in axes:
        fp = replace(fp, terminal_leak_multiplier=d["terminal_leak_multiplier"])
    if "tau" in axes:
        sls = replace(sls, tau=d["tau"])
    if "stiffness" in axes:
        sls = replace(sls, k1=d["k1"], k2=d["k2"])
    thickness = d["thickness"] if "thickness" in axes else 1.0
    temperature_c = d["temperature_c"] if "temperature" in axes else 25.0
    t_k = temperature_c + 273.15
    scale = thickness * t_k / T0_K                                   # k ∝ thickness, k ∝ T (entropic)
    sls = replace(sls, k1=sls.k1 * scale, k2=sls.k2 * scale,
                  tau=sls.tau * math.exp(EA_OVER_R * (1.0 / t_k - 1.0 / T0_K)))   # Arrhenius shift
    return Unit(fp, sls, temperature_c, thickness)


def sample_units(n: int, seed: int = SEED, axes=AXES) -> list[Unit]:
    """``n`` independent units; unit ``i`` always uses the ``i``-th spawned stream."""
    return [sample_unit(np.random.default_rng(child), axes)
            for child in np.random.SeedSequence(seed).spawn(n)]
