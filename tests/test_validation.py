"""Tests for Phase C validation cohorts, null lives, noise, and onset variants."""

from dataclasses import asdict

import numpy as np

from pipeline.validation import (
    add_pressure_noise,
    logistic_fatigue_state,
    make_null_params,
    sample_validation_cohort,
)
from sim.fatigue import FatigueParams, fatigue_state


def test_true_null_is_constant_for_entire_life():
    params = make_null_params()
    for cycles in [0, 20, 1000, 2450, 3500]:
        state = fatigue_state(cycles, 300, params)
        assert state.compliance_multiplier == 1.0
        assert state.loss_multiplier == 1.0
        assert state.leak_multiplier == 1.0


def test_pressure_noise_is_seeded_and_zero_noise_is_exact():
    pressure = np.linspace(-60_000, 60_000, 100)
    exact = add_pressure_noise(pressure, 0, np.random.default_rng(1))
    a = add_pressure_noise(pressure, 0.25, np.random.default_rng(2))
    b = add_pressure_noise(pressure, 0.25, np.random.default_rng(2))
    assert np.array_equal(exact, pressure)
    assert np.array_equal(a, b)
    assert not np.array_equal(a, pressure)


def test_validation_cohort_is_reproducible_and_axis_isolated():
    a = sample_validation_cohort(20, seed=20260623)
    b = sample_validation_cohort(20, seed=20260623)
    assert [asdict(x) for x in a] == [asdict(x) for x in b]
    assert len({x.rupture_cycles for x in a}) == 20
    canonical = FatigueParams()
    for unit in a:
        assert unit.acceleration_onset_fraction == canonical.acceleration_onset_fraction
        assert unit.mullins_amplitude == canonical.mullins_amplitude


def test_weibull_fixture_has_registered_large_sample_mean_and_cv():
    cohort = sample_validation_cohort(20_000, seed=7)
    lives = np.array([x.rupture_cycles for x in cohort])
    assert abs(lives.mean() - 3500) / 3500 < 0.02
    assert abs(lives.std() / lives.mean() - 0.30) < 0.02


def test_logistic_onset_variant_preserves_endpoints_and_terminal_magnitude():
    params = FatigueParams()
    start = logistic_fatigue_state(0, 0, params, sharpness=20)
    end = logistic_fatigue_state(params.rupture_cycles, 0, params, sharpness=20)
    assert start.fatigue_accelerating == 0.0
    assert np.isclose(end.fatigue_accelerating, params.accelerating_fatigue_amplitude)
    assert np.isclose(end.compliance_multiplier, 1.16)


def test_sharpness_controls_transition_width():
    params = FatigueParams()
    onset = params.acceleration_onset_fraction
    before = (onset - 0.1) * params.rupture_cycles
    after = (onset + 0.1) * params.rupture_cycles
    gentle_change = (
        logistic_fatigue_state(after, 0, params, 8).fatigue_accelerating
        - logistic_fatigue_state(before, 0, params, 8).fatigue_accelerating
    )
    sharp_change = (
        logistic_fatigue_state(after, 0, params, 50).fatigue_accelerating
        - logistic_fatigue_state(before, 0, params, 50).fatigue_accelerating
    )
    assert sharp_change > gentle_change
