"""Phase A ground-truth tests for sim/plant.py. Run: python3 -m pytest tests/ -q"""
import numpy as np

from sim.plant import (SLSParams, NetworkParams, pv_loop, sls_pressure,
                       sls_loss_energy_analytic, linear_network_crosstalk)
from scripts import gate0_lumped_rc as g0


def test_quasistatic_modulus_is_relaxed():
    """Very slow drive -> P/x approaches the relaxed stiffness k1 (no hysteresis)."""
    sls = SLSParams()
    lp = pv_loop(frequency=1e-3, amplitude=2e-6, sls=sls)
    # slope of P vs (V-V0) approaches the relaxed stiffness k1
    x = lp["V"] - sls.V0
    slope = np.polyfit(x, lp["P"], 1)[0]
    assert abs(slope - sls.k1) / sls.k1 < 0.02
    # hysteresis is negligible vs the loss-peak loop (area scales ~ w at low frequency)
    peak = pv_loop(sls.f_loss_peak, 2e-6, sls)["area"]
    assert lp["area"] < 0.01 * peak


def test_loop_area_matches_analytic():
    """Numerical ∮P dV matches the closed-form SLS dissipation across frequency."""
    sls = SLSParams()
    for f in [0.3, 1.0, sls.f_loss_peak, 5.0]:
        num = pv_loop(f, 2e-6, sls)["area"]
        ana = sls_loss_energy_analytic(2e-6, 2 * np.pi * f, sls)
        assert abs(num - ana) / ana < 0.03, (f, num, ana)


def test_loss_peaks_at_corner():
    """Loop area is maximized near f = 1/(2*pi*tau)."""
    sls = SLSParams()
    freqs = np.logspace(-1, 1, 31)
    areas = [pv_loop(f, 2e-6, sls)["area"] for f in freqs]
    f_peak = freqs[int(np.argmax(areas))]
    assert abs(np.log2(f_peak / sls.f_loss_peak)) < 0.5


def test_reduces_to_gate0():
    """SLS network with constant compliance 1/k1 == Gate 0 cross-talk model."""
    sls = SLSParams(); net = NetworkParams()
    for f in [0.1, 1.0, 10.0, 50.0]:
        w = 2 * np.pi * f
        ct_sls = linear_network_crosstalk(w, net, sls, compliance_override=sls.C_relaxed)
        A, B, C, D, *_ = g0.build_state_space(g0.Params(C0=sls.C_relaxed), 1.0)
        ct_g0 = g0.crosstalk_metric(g0.transfer_matrix(A, B, C, D, w))
        assert abs(ct_sls - ct_g0) < 1e-9, (f, ct_sls, ct_g0)


def test_sls_pressure_limits():
    """Instantaneous (x_d=0) stiffness is k1+k2; fully relaxed (x_d=x) is k1."""
    sls = SLSParams()
    V = sls.V0 + 1e-6
    P_instant = sls_pressure(V, 0.0, sls)             # x_d = 0 -> (k1+k2) x
    P_relaxed = sls_pressure(V, V - sls.V0, sls)       # x_d = x -> k1 x
    assert np.isclose(P_instant, (sls.k1 + sls.k2) * 1e-6)
    assert np.isclose(P_relaxed, sls.k1 * 1e-6)
