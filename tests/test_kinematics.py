import math

import numpy as np
import pytest

from sim.fatigue import FatigueParams, FatigueState, fatigue_state
from sim.kinematics import PCCParams, curvature_from_pressure, pcc_transform


def _state(compliance: float) -> FatigueState:
    """A FatigueState carrying only the field the kinematics use."""
    return FatigueState(
        cycles=0.0, rest_s=0.0, normalized_life=0.0, acceleration_coordinate=0.0,
        mullins_permanent=0.0, mullins_recoverable=0.0, mullins_total=0.0,
        fatigue_slow=0.0, fatigue_accelerating=0.0, fatigue_total=0.0,
        compliance_multiplier=compliance, loss_multiplier=1.0, leak_multiplier=1.0,
    )


def tip_pose(pressure_pa, state, params):
    kappa = float(curvature_from_pressure(pressure_pa, state.compliance_multiplier, params))
    return pcc_transform(kappa, params.plane_azimuth_rad, params.length_m)


def invert_tip_position(position_xyz, length_m):
    """Exact inverse of the position part of pcc_transform -> (kappa, phi)."""
    x, y, z = position_xyz
    d = math.hypot(x, y)              # = r (1 - cos theta); z = r sin theta
    if d <= 0.0:
        return 0.0, 0.0
    return 2.0 * math.atan2(d, z) / length_m, math.atan2(y, x)


def test_straight_segment_when_no_pressure():
    params = PCCParams(length_m=0.10)
    T = tip_pose(0.0, _state(1.0), params)
    np.testing.assert_array_equal(T[:3, 3], [0.0, 0.0, 0.10])
    np.testing.assert_array_equal(T[:3, :3], np.eye(3))


def test_quarter_turn_matches_closed_form():
    L = 0.10
    params = PCCParams(length_m=L, kappa_gain=1.0, plane_azimuth_rad=0.0)
    kappa = (math.pi / 2) / L
    P = kappa  # kappa = kappa_gain * compliance * P = P here
    T = tip_pose(P, _state(1.0), params)
    r = 1.0 / kappa
    np.testing.assert_allclose(T[:3, 3], [r, 0.0, r], rtol=1e-12, atol=1e-12)
    # backbone tangent (R @ z_hat) points along +x after a quarter turn
    np.testing.assert_allclose(T[:3, :3] @ [0, 0, 1], [1.0, 0.0, 0.0], atol=1e-12)


@pytest.mark.parametrize("phi", [0.0, 0.7, 2.5, -1.1])
@pytest.mark.parametrize("P", [1.0e3, 1.0e4, 5.0e4])
@pytest.mark.parametrize("compliance", [1.0, 1.2, 1.5])
def test_forward_inverse_roundtrip_machine_precision(phi, P, compliance):
    params = PCCParams(length_m=0.12, kappa_gain=2.0e-5, plane_azimuth_rad=phi)
    kappa = float(curvature_from_pressure(P, compliance, params))
    T = pcc_transform(kappa, phi, params.length_m)
    kappa_rec, phi_rec = invert_tip_position(T[:3, 3], params.length_m)
    assert abs(kappa_rec - kappa) <= 1e-9 * max(1.0, kappa)
    # azimuth equality up to wrap -> compare via sin/cos
    assert abs(math.cos(phi_rec) - math.cos(phi)) < 1e-9
    assert abs(math.sin(phi_rec) - math.sin(phi)) < 1e-9
    # pose -> "effective pressure" recovery (the proprioception ground truth)
    P_rec = kappa_rec / (params.kappa_gain * compliance)
    assert abs(P_rec - P) <= 1e-6 * P


def test_curvature_drifts_up_with_fatigue_at_fixed_pressure():
    params = PCCParams(length_m=0.10, kappa_gain=2.0e-5)
    fp = FatigueParams()
    P = 4.0e4
    cycles = [10.0, 1000.0, 2000.0, 3000.0]
    kappas = [
        float(curvature_from_pressure(
            P, fatigue_state(c, 0.0, fp).compliance_multiplier, params))
        for c in cycles
    ]
    assert all(b > a for a, b in zip(kappas, kappas[1:]))
