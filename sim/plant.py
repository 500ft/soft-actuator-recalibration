"""
Phase A — Forward plant with viscoelastic (Standard-Linear-Solid) chamber walls.

This grows the Gate 0 lumped-RC core into a *time-domain* simulator that produces
realistic, rate-dependent pressure-volume (P-V) hysteresis loops, and reduces to the
Gate 0 linear cross-talk model in the quasi-static limit.

Chamber wall model — Standard Linear Solid (Zener), in the pressure-volume analog
---------------------------------------------------------------------------------
A spring k1 in parallel with a Maxwell arm (spring k2 + dashpot, relaxation time tau):

    x      = V - V0                         (volume strain about the rest volume)
    P      = k1*x + k2*(x - x_d)            (algebraic: wall pressure from state)
    dx_d/dt = (x - x_d)/tau                 (internal dashpot strain relaxes)

Limits:  quasi-static (slow)  -> x_d -> x   -> P = k1*x        (relaxed/soft modulus)
         fast                 -> x_d lags   -> P = (k1+k2)*x   (instantaneous/stiff)

Frequency response (x = A sin(wt)):  the complex stiffness is
    K(w) = k1 + k2 * (j w tau)/(1 + j w tau),   compliance  Chat(w) = 1/K(w).
The energy dissipated per cycle has the closed form
    E_loss(w) = pi * k2 * A^2 * (w tau)/(1 + (w tau)^2),
which peaks at  w*tau = 1, i.e.  f_peak = 1/(2 pi tau).  This analytical area is used
as a ground-truth check on the numerical loop area.

Pneumatic network (same topology as Gate 0)
-------------------------------------------
    regulated supply --R_s--> manifold (C_m) --R_v_i--> chamber_i --R_l_i--> atm
Volumetric flow Q = g*dP (g = 1/R). Chamber volume changes with net flow:
    dV_i/dt = g_v_i (P_m - P_i) - g_l_i P_i
Manifold node:
    C_m dP_m/dt = g_s (P_s - P_m) - sum_i g_v_i (P_m - P_i)
with P_i the SLS wall pressure (function of V_i, x_d_i).

Two drive modes:
  * volumetric drive  -> impose V_i(t) (the Gate-1 syringe/stepper method); integrate only
    the dashpot states; read P. Cleanest way to acquire a P-V loop.
  * pneumatic drive   -> modulate valve conductances; integrate the full network. Used for
    cross-talk / dynamics and the Gate-0 consistency check.
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from scipy.integrate import solve_ivp


# --------------------------------------------------------------------------- #
@dataclass
class SLSParams:
    """Standard-Linear-Solid chamber-wall parameters (P-V analog)."""
    k1: float = 2.0e10     # relaxed stiffness [Pa/m^3]  -> relaxed compliance 1/k1 = 5e-11
    k2: float = 2.0e10     # Maxwell-arm stiffness [Pa/m^3]
    tau: float = 0.10      # viscoelastic relaxation time [s] -> loss peak at 1/(2*pi*tau) ~ 1.6 Hz
    V0: float = 5.0e-6     # rest volume [m^3] (5 mL)

    @property
    def C_relaxed(self) -> float:
        return 1.0 / self.k1

    @property
    def C_instant(self) -> float:
        return 1.0 / (self.k1 + self.k2)

    @property
    def f_loss_peak(self) -> float:
        return 1.0 / (2 * np.pi * self.tau)


@dataclass
class NetworkParams:
    """Shared-manifold pneumatic network (Gate-0 compatible)."""
    n_chambers: int = 3
    P_s: float = 80_000.0   # regulated supply, gauge [Pa]
    R_s: float = 2.0e8      # supply resistance [Pa*s/m^3]
    R_v: float = 8.0e8      # nominal valve resistance [Pa*s/m^3]
    R_l: float = 8.0e9      # chamber bleed/leak [Pa*s/m^3]
    C_m: float = 5.0e-12    # manifold node compliance [m^3/Pa]


# --------------------------------------------------------------------------- #
# SLS constitutive relation
# --------------------------------------------------------------------------- #
def sls_pressure(V, x_d, sls: SLSParams):
    """Algebraic wall pressure from chamber volume V and dashpot strain x_d."""
    x = np.asarray(V) - sls.V0
    return sls.k1 * x + sls.k2 * (x - np.asarray(x_d))


def sls_complex_compliance(omega, sls: SLSParams):
    """Frequency-domain chamber compliance Chat(w) = 1/K(w) (complex)."""
    K = sls.k1 + sls.k2 * (1j * omega * sls.tau) / (1 + 1j * omega * sls.tau)
    return 1.0 / K


def sls_loss_energy_analytic(amplitude, omega, sls: SLSParams):
    """Closed-form dissipation per cycle for x = A sin(wt): pi k2 A^2 (wt)/(1+(wt)^2)."""
    wt = omega * sls.tau
    return np.pi * sls.k2 * amplitude**2 * wt / (1 + wt**2)


# --------------------------------------------------------------------------- #
# Drive mode 1: volumetric (impose V(t), read P) -- the P-V loop generator
# --------------------------------------------------------------------------- #
def simulate_volumetric(t, V_func, sls: SLSParams):
    """Impose chamber volume V_func(t) (scalar, single chamber); integrate the dashpot
    state and return P(t), V(t).

    Returns dict with keys: t, V, P, x_d.
    """
    x_d0 = V_func(t[0]) - sls.V0  # start relaxed (x_d = x) -> no startup transient

    def rhs(tt, y):
        x = V_func(tt) - sls.V0
        x_d = y[0]
        return [(x - x_d) / sls.tau]

    sol = solve_ivp(rhs, (t[0], t[-1]), [x_d0], t_eval=t, method="RK45",
                    rtol=1e-8, atol=1e-12, max_step=(t[-1] - t[0]) / 200)
    V = V_func(t)
    P = sls_pressure(V, sol.y[0], sls)
    return {"t": t, "V": V, "P": P, "x_d": sol.y[0]}


def simulate_pressure_decay(t, P_initial, sls: SLSParams, R_l, P_atm=0.0):
    """Simulate a closed-inlet pressure-hold test with leakage to atmosphere.

    This is the explicit leak observable. It is intentionally separate from
    :func:`simulate_volumetric`, whose imposed volume makes ``R_l`` unobservable.
    The chamber starts fully relaxed at ``P_initial`` and then loses volume through
    ``Q_l = (P-P_atm)/R_l`` while the SLS internal state also relaxes.
    """
    t = np.asarray(t, dtype=float)
    if t.ndim != 1 or t.size < 2 or not np.all(np.isfinite(t)):
        raise ValueError("t must be a finite one-dimensional array with at least two points")
    if np.any(np.diff(t) <= 0):
        raise ValueError("t must be strictly increasing")
    if not np.isfinite(P_initial) or not np.isfinite(P_atm) or P_initial <= P_atm:
        raise ValueError("P_initial must be finite and greater than P_atm")
    if not np.isfinite(R_l) or R_l <= 0:
        raise ValueError("R_l must be finite and > 0")

    x0 = P_initial / sls.k1
    V_initial = sls.V0 + x0

    def rhs(_tt, y):
        V, x_d = y
        P = float(sls_pressure(V, x_d, sls))
        dV = -(P - P_atm) / R_l
        dx_d = ((V - sls.V0) - x_d) / sls.tau
        return [dV, dx_d]

    duration = t[-1] - t[0]
    sol = solve_ivp(
        rhs,
        (t[0], t[-1]),
        [V_initial, x0],
        t_eval=t,
        method="RK45",
        rtol=1e-9,
        atol=1e-13,
        max_step=duration / 1000,
    )
    if not sol.success:
        raise RuntimeError(f"pressure-decay integration failed: {sol.message}")
    V, x_d = sol.y
    P = sls_pressure(V, x_d, sls)
    return {"t": t, "V": V, "P": P, "x_d": x_d}


def first_crossing(xs, ys, threshold):
    """Linearly interpolated first ``x`` where ``y`` reaches ``threshold`` (rising); None if never."""
    xs = np.asarray(xs, float)
    ys = np.asarray(ys, float)
    if xs.shape != ys.shape or xs.ndim != 1 or xs.size < 2:
        raise ValueError("xs and ys must be matching 1-D arrays with >= 2 points")
    if ys[0] >= threshold:
        return float(xs[0])
    for i in range(1, ys.size):
        y0, y1 = ys[i - 1], ys[i]
        if y1 >= threshold:
            x0, x1 = xs[i - 1], xs[i]
            if y1 == y0:
                return float(x1)
            frac = (threshold - y0) / (y1 - y0)
            return float(x0 + frac * (x1 - x0))
    return None


def operational_half_life(t, P, P_initial):
    """Return first interpolated time where pressure reaches ``P_initial/2``.

    Returns ``nan`` when the supplied trace never reaches the threshold. This is an
    operational metric; an SLS decay generally contains more than one time scale.
    """
    t = np.asarray(t, dtype=float)
    P = np.asarray(P, dtype=float)
    if t.ndim != 1 or P.ndim != 1 or t.size != P.size or t.size < 2:
        raise ValueError("t and P must be equal-length one-dimensional arrays")
    if not np.all(np.isfinite(t)) or not np.all(np.isfinite(P)) or np.any(np.diff(t) <= 0):
        raise ValueError("t and P must be finite and t strictly increasing")
    if not np.isfinite(P_initial) or P_initial <= 0:
        raise ValueError("P_initial must be finite and > 0")

    x = first_crossing(t, -P, -(P_initial / 2.0))     # falling crossing = rising crossing of -P
    return float("nan") if x is None else x


def pv_loop(frequency, amplitude, sls: SLSParams, n_periods=8, n_per_period=400):
    """Drive V = V0 + A sin(2*pi*f*t) and return the STEADY P-V loop (last period) plus
    its numerically integrated area. Discards startup transient.
    """
    omega = 2 * np.pi * frequency
    T = 1.0 / frequency
    t = np.linspace(0, n_periods * T, n_periods * n_per_period + 1)
    V_func = lambda tt: sls.V0 + amplitude * np.sin(omega * tt)
    out = simulate_volumetric(t, V_func, sls)
    # last full period
    last = slice(-(n_per_period + 1), None)
    Vl, Pl = out["V"][last], out["P"][last]
    area = loop_area(Vl, Pl)
    return {"V": Vl, "P": Pl, "area": area, "frequency": frequency}


def loop_area(V, P):
    """Enclosed area of a closed P-V loop via the shoelace formula (= energy/cycle)."""
    V = np.asarray(V); P = np.asarray(P)
    return abs(0.5 * np.sum(V * np.roll(P, -1) - np.roll(V, -1) * P))


# --------------------------------------------------------------------------- #
# Drive mode 2: pneumatic network (full state) -- for cross-talk / dynamics
# --------------------------------------------------------------------------- #
def steady_state(topology, gv0, k1, V0, gl, gs, P_s):
    """Closed-form operating point for a constant nominal valve conductance ``gv0`` (per chamber).

    At steady state x_d = x, so P_i = k1 (V_i - V0); chamber gv(P_m - P_i) - gl P_i = 0 and
    manifold gs(P_s - P_m) = sum gv (P_m - P_i). Returns ``(V, x_d, P_m state)``.
    """
    a = gv0 / (gv0 + gl)                       # P_i = a * P_m
    if topology == "shared":
        P_m = gs * P_s / (gs + np.sum(gv0 * (1 - a)))
        Pm_state = np.array([P_m])
    elif topology == "isolated":
        P_m = gs * P_s / (gs + gv0 * (1 - a))
        Pm_state = P_m
    else:
        raise ValueError("topology must be 'shared' or 'isolated'")
    V = V0 + a * P_m / k1
    return V, V - V0, Pm_state


def linear_network_crosstalk(omega, net: NetworkParams, sls: SLSParams, compliance_override=None):
    """Small-signal cross-talk |H_neighbor,driven|/|H_driven,driven| of the pneumatic
    network, using the SLS complex compliance Chat(w) (or a fixed override, to reproduce
    the Gate-0 constant-compliance model). This is the bridge back to Gate 0.
    """
    n = net.n_chambers
    gv = np.full(n, 1.0 / net.R_v); gl = np.full(n, 1.0 / net.R_l); gs = 1.0 / net.R_s
    Chat = (sls_complex_compliance(omega, sls) if compliance_override is None
            else complex(compliance_override))
    Vi0, _, Pm0 = steady_state("shared", gv, sls.k1, sls.V0, gl, gs, net.P_s)
    Pm0 = Pm0[0]
    Pi0 = sls.k1 * (Vi0 - sls.V0)

    # state = [P_1..P_n, P_m]; chamber capacitance is the (complex) Chat, manifold C_m.
    # j w Chat P_i = gv(P_m - P_i) - gl P_i  + input ;  j w C_m P_m = gs(-P_m) - sum gv(P_m - P_i)
    A = np.zeros((n + 1, n + 1), dtype=complex)
    for i in range(n):
        A[i, i] = -(gv[i] + gl[i]) / Chat
        A[i, n] = gv[i] / Chat
    A[n, n] = -(gs + gv.sum()) / net.C_m
    for j in range(n):
        A[n, j] = gv[j] / net.C_m
    B = np.zeros((n + 1, n), dtype=complex)
    for k in range(n):
        drop = Pm0 - Pi0[k]
        B[k, k] = drop / Chat
        B[n, k] = -drop / net.C_m
    Cout = np.zeros((n, n + 1)); Cout[range(n), range(n)] = 1.0
    H = Cout @ np.linalg.solve(1j * omega * np.eye(n + 1) - A, B)
    return float(abs(H[1, 0]) / abs(H[0, 0]))       # neighbor 1 driven by chamber 0
