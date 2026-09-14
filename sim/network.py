"""Phase D — multi-chamber shared-manifold vs isolated-supply network dynamics.

Time-domain integrator that turns valve-conductance commands into realized per-chamber
pressures, with Standard-Linear-Solid chamber walls (``sim.plant``) and per-chamber fatigue
degradation. This is where the *dynamic* fatigue-coupled cross-talk lives:

  * **shared** manifold — all chambers draw from one supply node ``P_m``; driving one
    chamber's valve pulls the shared node and perturbs its neighbors -> cross-talk.
  * **isolated** supplies — each chamber has its own regulated node ``P_m_i``; the state
    blocks are decoupled and the off-diagonal coupling is exactly zero.

Per Gate 0 the coupling is *dynamic*: its DC gain is compliance-independent while its
actuation-band gain drifts with fatigue (the SLS complex compliance changes). Traces must
therefore excite the actuation band (~1-5 Hz); a static (DC) dataset cannot show the effect.

State layout
------------
shared:   ``[V_0..V_{n-1}, x_d_0..x_d_{n-1}, P_m]``                  (2n + 1)
isolated: ``[V_0..V_{n-1}, x_d_0..x_d_{n-1}, P_m_0..P_m_{n-1}]``     (3n, block-diagonal)
"""

from __future__ import annotations

import numpy as np
from scipy.integrate import solve_ivp

from sim.plant import NetworkParams, steady_state


def _sls_arrays(sls_list):
    k1 = np.array([s.k1 for s in sls_list], dtype=float)
    k2 = np.array([s.k2 for s in sls_list], dtype=float)
    tau = np.array([s.tau for s in sls_list], dtype=float)
    V0 = np.array([s.V0 for s in sls_list], dtype=float)
    return k1, k2, tau, V0


def _wall_pressure(V, x_d, k1, k2, V0):
    x = V - V0
    return k1 * x + k2 * (x - x_d)


def _conductances(n, net, leak_multiplier):
    gs = 1.0 / net.R_s
    gl = np.full(n, 1.0 / net.R_l)
    if leak_multiplier is not None:
        gl = gl * np.asarray(leak_multiplier, dtype=float)
    gv_nominal = np.full(n, 1.0 / net.R_v)
    return gs, gl, gv_nominal


def simulate_network(t, gv_func, topology, sls_list, net: NetworkParams, *, leak_multiplier=None):
    """Integrate the network and return realized per-chamber pressures.

    ``gv_func(tt) -> ndarray(n)`` gives the (time-varying) valve conductances; the operating
    point is taken at the nominal ``1/R_v`` so a zero-mean excitation starts near steady
    state. Returns ``{t, P (n,T), V (n,T), P_m}``.
    """
    t = np.asarray(t, dtype=float)
    if t.ndim != 1 or t.size < 2 or np.any(np.diff(t) <= 0):
        raise ValueError("t must be a strictly increasing 1-D array with >= 2 points")
    n = len(sls_list)
    k1, k2, tau, V0 = _sls_arrays(sls_list)
    gs, gl, gv_nominal = _conductances(n, net, leak_multiplier)
    Ps = net.P_s

    V_ss, x_d_ss, Pm_ss = steady_state(topology, gv_nominal, k1, V0, gl, gs, Ps)
    y0 = np.concatenate([V_ss, x_d_ss, Pm_ss])

    if topology == "shared":
        atol = np.concatenate([np.full(2 * n, 1e-14), [1e-3]])

        def rhs(tt, y):
            V = y[:n]; x_d = y[n:2 * n]; P_m = y[2 * n]
            gv = np.asarray(gv_func(tt), dtype=float)
            P_i = _wall_pressure(V, x_d, k1, k2, V0)
            dV = gv * (P_m - P_i) - gl * P_i
            dx = ((V - V0) - x_d) / tau
            dPm = (gs * (Ps - P_m) - np.sum(gv * (P_m - P_i))) / net.C_m
            return np.concatenate([dV, dx, [dPm]])
    else:
        atol = np.concatenate([np.full(2 * n, 1e-14), np.full(n, 1e-3)])

        def rhs(tt, y):
            V = y[:n]; x_d = y[n:2 * n]; P_m = y[2 * n:3 * n]
            gv = np.asarray(gv_func(tt), dtype=float)
            P_i = _wall_pressure(V, x_d, k1, k2, V0)
            dV = gv * (P_m - P_i) - gl * P_i
            dx = ((V - V0) - x_d) / tau
            dPm = (gs * (Ps - P_m) - gv * (P_m - P_i)) / net.C_m
            return np.concatenate([dV, dx, dPm])

    sol = solve_ivp(rhs, (t[0], t[-1]), y0, t_eval=t, method="BDF", rtol=1e-7, atol=atol)
    if not sol.success:
        raise RuntimeError(f"network integration failed: {sol.message}")
    V = sol.y[:n]; x_d = sol.y[n:2 * n]
    P = _wall_pressure(V, x_d, k1[:, None], k2[:, None], V0[:, None])
    P_m = sol.y[2 * n] if topology == "shared" else sol.y[2 * n:3 * n]
    return {"t": t, "P": P, "V": V, "P_m": P_m}


def probe_coupling(sls_list, net: NetworkParams, topology, *, leak_multiplier=None):
    """Chamber-0 sinusoidal probe (2 Hz, 10 % depth, 10 periods): |chamber-1 response| / |chamber-0 response|.

    Isolated supplies give ~0 (numerically, solver tolerance); a shared manifold gives a
    measurable ratio that drifts with fatigue at actuation-band frequencies.
    """
    _, _, gv0 = _conductances(len(sls_list), net, leak_multiplier)
    t = np.linspace(0.0, 10 * 0.5, 10 * 200 + 1)

    def gv(tt):
        out = gv0.copy()
        out[0] = gv0[0] * (1.0 + 0.1 * np.sin(2.0 * np.pi * 2.0 * tt))
        return out

    res = simulate_network(t, gv, topology, sls_list, net, leak_multiplier=leak_multiplier)

    def amp(x):
        seg = x[-400:]                     # last two periods
        return 0.5 * (seg.max() - seg.min())

    return amp(res["P"][1]) / max(amp(res["P"][0]), 1e-30)
