"""Study B — Fisher information of the latent life coordinate from pressure-only features.

Feature vector y(theta) with theta = (u, k1_0, k2_0, tau, terminal_leak_multiplier,
acceleration_onset_fraction, fatigue_exponent). FIM = J^T Sigma^-1 J with J by central differences
and Sigma from seeded sensor-model repeats. Preregistered in docs/specs/observability-program/studyB-identifiability.md.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from sim.fatigue import FatigueParams, degraded_sls, fatigue_state
from sim.plant import (NetworkParams, SLSParams, loop_area, operational_half_life, pv_loop,
                       simulate_pressure_decay)
from sim.sensors import SensorModel, SensorParams

PARAMS = ("u", "k1_0", "k2_0", "tau", "terminal_leak_multiplier", "acceleration_onset_fraction", "fatigue_exponent")
FEATURES = ("area_1hz", "area_4hz", "secant_stiffness_1hz", "decay_half_life_s", "decay_residual_0p3s")
P_HOLD_PA = 40e3
T_DECAY = np.linspace(0.0, 2.0, 2001)


def unit_from_theta(theta, base_fp: FatigueParams, base_sls: SLSParams):
    u, k1, k2, tau, leak, onset, expo = theta
    fp = replace(base_fp, terminal_leak_multiplier=leak, acceleration_onset_fraction=onset, fatigue_exponent=expo)
    return u, fp, replace(base_sls, k1=k1, k2=k2, tau=tau)


def raw_signals(theta, base_fp, base_sls, amp_frac=0.1):
    """Noise-free probe signals: two loops (V, P) and a pressure-decay trace P(t)."""
    u, fp, sls = unit_from_theta(theta, base_fp, base_sls)
    fs = fatigue_state(u * fp.rupture_cycles, 0.0, fp)
    dsls = degraded_sls(sls, fs)
    l1 = pv_loop(1.0, amp_frac * dsls.V0, dsls)
    l4 = pv_loop(4.0, amp_frac * dsls.V0, dsls)
    decay = simulate_pressure_decay(T_DECAY, P_HOLD_PA, dsls, NetworkParams().R_l / fs.leak_multiplier)
    return (l1["V"], l1["P"]), (l4["V"], l4["P"]), decay["P"]


def features_from_signals(loop1, loop4, p_decay):
    (V1, P1), (V4, P4) = loop1, loop4
    secant = (P1.max() - P1.min()) / (V1.max() - V1.min())
    half = operational_half_life(T_DECAY, p_decay, P_HOLD_PA)
    i03 = int(np.argmin(np.abs(T_DECAY - 0.3)))
    return np.array([loop_area(V1, P1), loop_area(V4, P4), secant, half, p_decay[i03] / P_HOLD_PA])


def features(theta, base_fp, base_sls, amp_frac=0.1):
    return features_from_signals(*raw_signals(theta, base_fp, base_sls, amp_frac))


def measured_features(theta, base_fp, base_sls, seed, noise_scale=1.0, amp_frac=0.1):
    """One noisy realisation: sensor noise/quantisation on every pressure and volume signal."""
    sp = SensorParams(pressure_sigma_pa=50.0 * noise_scale, pressure_lsb_pa=10.0,
                      volume_sigma_m3=1.0e-9 * noise_scale)
    (V1, P1), (V4, P4), pd = raw_signals(theta, base_fp, base_sls, amp_frac)
    m1 = SensorModel(sp, seed).measure(pressure=P1, volume=V1)
    m4 = SensorModel(sp, seed + 1).measure(pressure=P4, volume=V4)
    md = SensorModel(sp, seed + 2).measure(pressure=pd)
    pdm = np.clip(md["pressure"], 1e-9, None)               # half-life needs positive finite pressures
    return features_from_signals((m1["volume"], m1["pressure"]), (m4["volume"], m4["pressure"]), pdm)


def noise_covariance(theta, base_fp, base_sls, seed, n_rep=24, noise_scale=1.0, amp_frac=0.1):
    reps = np.array([measured_features(theta, base_fp, base_sls, seed + 10 * r, noise_scale, amp_frac)
                     for r in range(n_rep)])
    return np.cov(reps, rowvar=False, ddof=1)


def jacobian(theta, base_fp, base_sls, amp_frac=0.1, rel_step=1e-3):
    """Central-difference sensitivities (5 x 7): d y/d u for column 0, d y/d ln(theta_j) for the nuisance
    columns, so every column is comparably scaled and rank tests are meaningful."""
    theta = np.asarray(theta, float)
    cols = []
    for j in range(theta.size):
        h = rel_step * (abs(theta[j]) if j else 1.0)                 # u gets an absolute step
        tp, tm = theta.copy(), theta.copy()
        tp[j] += h; tm[j] -= h
        d = (features(tp, base_fp, base_sls, amp_frac) - features(tm, base_fp, base_sls, amp_frac)) / (2 * h)
        cols.append(d if j == 0 else d * theta[j])
    return np.column_stack(cols)


def fim(J, sigma):
    return J.T @ np.linalg.solve(sigma, J)


def active_columns(J, sigma, rtol=1e-9):
    """Parameters the whitened features actually respond to at this operating point. A zero column is an
    *irrelevant* parameter here (it cannot confound u), not an unidentifiable nuisance."""
    L = np.linalg.cholesky(np.linalg.inv(sigma))
    norms = np.linalg.norm(L.T @ J, axis=0)
    return norms > rtol * norms.max()


def crlb_u(F, rtol=1e-10):
    """(sigma_u, rank): Cramér–Rao bound on u (column 0) with every other column unknown; inf if singular."""
    rank = int(np.linalg.matrix_rank(F, tol=rtol * np.linalg.norm(F, 2)))
    if rank < F.shape[0]:
        return float("inf"), rank
    return float(np.sqrt(np.linalg.inv(F)[0, 0])), rank


def bound_u(J, sigma):
    """CRLB on u over the active parameter set. Returns (sigma_u, rank, n_active, u_active)."""
    act = active_columns(J, sigma)
    if not act[0]:
        return float("inf"), 0, int(act.sum()), False
    s, rank = crlb_u(fim(J[:, act], sigma))
    return s, rank, int(act.sum()), True


def whitened_angles_deg(J, sigma):
    """Angle between d y/d u and each nuisance sensitivity in the Sigma^-1/2 metric."""
    L = np.linalg.cholesky(np.linalg.inv(sigma))
    W = L.T @ J
    a = W[:, 0]
    out = []
    for j in range(1, J.shape[1]):
        b = W[:, j]
        den = np.linalg.norm(a) * np.linalg.norm(b)
        if den == 0.0:
            out.append(None)                                          # no sensitivity: nothing to alias
            continue
        c = abs(a @ b) / den
        out.append(float(np.degrees(np.arccos(np.clip(c, 0.0, 1.0)))))
    return out
