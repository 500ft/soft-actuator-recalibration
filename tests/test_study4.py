"""Sanity checks for the cross-talk parameter-sensitivity sweep (scripts/run_study4).

These are physical-monotonicity guards, not result assertions: cross-talk must increase as
the shared supply gets softer (larger R_s, or smaller manifold buffer C_m), and the default
operating point must sit in the second-order regime.
"""

import numpy as np

from scripts.run_study4 import SWEEP_MULT, coupling_curve, first_crossing_mult
from sim.network import probe_coupling
from sim.plant import NetworkParams, SLSParams


def _base():
    base = NetworkParams(n_chambers=3)
    sls = [SLSParams() for _ in range(base.n_chambers)]
    return base, sls


def test_coupling_increases_with_supply_softness_Rs():
    base, sls = _base()
    c = coupling_curve(base, sls, "R_s")
    # softer supply (larger R_s) -> strictly more cross-talk
    assert np.all(np.diff(c) > 0)


def test_coupling_increases_as_manifold_buffer_shrinks_Cm():
    base, sls = _base()
    c = coupling_curve(base, sls, "C_m")
    # bigger buffer (larger C_m) -> less cross-talk, so coupling strictly decreases with C_m,
    # i.e. strictly increases as the node softens (C_m down).
    assert np.all(np.diff(c) < 0)


def test_default_operating_point_is_second_order():
    base, sls = _base()
    coupling = probe_coupling(sls, base, "shared")
    # the frozen claim: at the default params cross-talk is a few percent (second-order)
    assert 0.0 < coupling < 0.10


def test_threshold_crossing_requires_softer_supply():
    base, sls = _base()
    c = coupling_curve(base, sls, "R_s")
    m10 = first_crossing_mult(SWEEP_MULT, c, 0.10)
    m20 = first_crossing_mult(SWEEP_MULT, c, 0.20)
    # reaching the first-order band needs a supply softer than default, and 20% needs more than 10%
    assert m10 is not None and m10 > 1.0
    assert m20 is not None and m20 > m10
