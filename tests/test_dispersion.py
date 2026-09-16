"""Study A dispersion sampler: canonical law unchanged, draws reproducible and within support."""
from pipeline.dispersion import AXES, sample_units
from sim.fatigue import FatigueParams, fatigue_state
from sim.plant import SLSParams


def test_default_fatigue_exponent_reproduces_canonical_law_exactly():
    p = FatigueParams()
    assert p.fatigue_exponent == 2.0
    for u in (0.1, 0.5, 0.75, 0.9, 1.0):
        s = fatigue_state(u * p.rupture_cycles, 0.0, p)
        z = max(0.0, (u - p.acceleration_onset_fraction) / (1.0 - p.acceleration_onset_fraction))
        assert s.fatigue_accelerating == p.accelerating_fatigue_amplitude * z**2


def test_no_axes_is_canonical_and_full_draw_is_reproducible():
    canon = sample_units(3, axes=())
    for unit in canon:
        assert unit.fatigue == FatigueParams() and unit.sls == SLSParams()
        assert unit.temperature_c == 25.0 and unit.thickness_ratio == 1.0
    a, b = sample_units(4), sample_units(4)
    assert a == b
    assert len({u.fatigue.rupture_cycles for u in a}) == 4


def test_ablation_reuses_the_same_realisations():
    only_tau = sample_units(5, axes=("tau",))
    assert all(t.fatigue == FatigueParams() for t in only_tau)
    # the tau draw is the same realisation whether or not the other axes are applied
    full_no_temp = sample_units(5, axes=tuple(a for a in AXES if a != "temperature"))
    assert [u.sls.tau for u in full_no_temp] == [u.sls.tau for u in only_tau]


def test_draws_stay_inside_preregistered_supports():
    for u in sample_units(200):
        fp, sls = u.fatigue, u.sls
        assert 0.45 <= fp.acceleration_onset_fraction <= 0.90
        assert 1.2 <= fp.fatigue_exponent <= 3.0
        assert 0.05 <= fp.mullins_permanent_fraction <= 0.70
        assert fp.terminal_leak_multiplier >= 1.0 and fp.rupture_cycles > 0
        assert 0.75 <= u.thickness_ratio <= 1.25 and 15.0 <= u.temperature_c <= 35.0
        assert sls.k1 > 0 and sls.k2 > 0 and sls.tau > 0
