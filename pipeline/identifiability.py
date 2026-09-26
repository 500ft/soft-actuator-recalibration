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
    # Take the sensor model's own defaults rather than restating them. They were hard-coded here as
    # 50.0 / 10.0 / 1.0e-9, so editing SensorParams would silently have left this copy behind.
    # Quantisation is a property of the instrument and is NOT scaled by noise_scale.
    d = SensorParams()
    sp = SensorParams(pressure_sigma_pa=d.pressure_sigma_pa * noise_scale,
                      pressure_lsb_pa=d.pressure_lsb_pa,
                      volume_sigma_m3=d.volume_sigma_m3 * noise_scale)
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


def whiten(sigma, x):
    """Map residuals or Jacobian rows into the Sigma^-1/2 metric, without ever forming Sigma^-1.

    The feature vector mixes loop areas near 1e-2 with a secant stiffness near 1e11, so the standard
    deviations span about thirteen orders of magnitude and ``cond(Sigma)`` reaches ~1e26 -- far past
    what float64 can invert meaningfully. Almost all of that is *scale*: writing ``Sigma = D R D`` with
    ``D = diag(sd)`` leaves a correlation matrix whose condition number is under 5. So divide by the
    standard deviations first, then apply the Cholesky factor of the correlation matrix. The result is
    algebraically identical to ``chol(inv(Sigma)).T @ x`` and numerically stable, whereas inverting
    Sigma directly returns noise in the low-order bits and made the likelihood emit NaN.

    ``x`` may be a residual vector or a (n_features, n_params) Jacobian; returns the whitened array,
    for which ``||whiten(S, r)||**2 == r @ inv(S) @ r``.
    """
    from scipy.linalg import solve_triangular
    sigma = np.asarray(sigma, float)
    x = np.asarray(x, float)
    d = np.sqrt(np.diag(sigma))
    if np.any(~np.isfinite(d)) or np.any(d <= 0.0):
        raise ValueError("the noise covariance has a non-positive or non-finite diagonal entry, so no "
                         "feature scale can be formed; check noise_covariance for a constant feature")
    corr = sigma / np.outer(d, d)
    chol = np.linalg.cholesky(corr)
    scaled = x / d if x.ndim == 1 else x / d[:, None]
    return solve_triangular(chol, scaled, lower=True)


def fim(J, sigma):
    W = whiten(sigma, J)
    return W.T @ W


def active_columns(J, sigma, rtol=1e-9):
    """Parameters the whitened features actually respond to at this operating point. A zero column is an
    *irrelevant* parameter here (it cannot confound u), not an unidentifiable nuisance."""
    norms = np.linalg.norm(whiten(sigma, J), axis=0)
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
    W = whiten(sigma, J)
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


# --- structural vs practical identifiability (2026-09-23) -----------------------------------------
# Study B reports the life coordinate as "structurally" aliased after onset on the evidence of a
# rank-deficient FIM. Wieland et al. 2021 argue a Fisher-based analysis is insensitive to practical
# non-identifiability, and Chis et al. 2016 that sloppiness is not the same thing. These two tools are
# the standard way to separate the cases: Brun's collinearity index scores a parameter *subset*, and a
# profile likelihood distinguishes a structurally flat direction from one that is merely poorly
# constrained at this noise level. See literature/01-identifiability-observability.md.

COLLINEARITY_POOR = 10.0          # Brun et al. 2001: gamma above ~10-20 flags a poorly identifiable subset
INFEASIBLE_PENALTY = 1e15         # stand-in objective where a predicted feature is undefined


def normalised_sensitivities(J, sigma):
    """Whitened sensitivity matrix with every column scaled to unit length.

    Brun's index is defined on unit-length columns so that it measures *direction* overlap rather than
    relative magnitude: a parameter the data barely responds to is not thereby collinear with another.
    """
    W = whiten(sigma, J)
    norms = np.linalg.norm(W, axis=0)
    keep = norms > 0
    out = np.zeros_like(W)
    out[:, keep] = W[:, keep] / norms[keep]
    return out, norms


def collinearity_index(J, sigma, subset):
    """Brun's gamma_K for a parameter subset: 1 / sqrt(smallest eigenvalue of S~^T S~).

    gamma = 1 means orthogonal sensitivities; gamma -> infinity means the subset's effects on the
    observables are linearly dependent, i.e. a change in one can be compensated by the others.
    Returns infinity for a subset containing a parameter with no sensitivity at all.
    """
    S, norms = normalised_sensitivities(J, sigma)
    idx = list(subset)
    if np.any(norms[idx] == 0):
        return float("inf")
    lam = np.linalg.eigvalsh(S[:, idx].T @ S[:, idx]).min()
    return float("inf") if lam <= 0 else float(1.0 / np.sqrt(lam))


def collinearity_report(J, sigma, subset, params=None):
    """``(value, status)`` for a subset, where ``value`` is ``None`` unless the index is meaningful.

    Brun's index is ``1/sqrt(lambda_min)``, so as ``lambda_min`` approaches machine precision the value
    stops carrying information and starts reporting rounding. The ``all_seven`` subset is exactly that
    case: it moved from 6.5e7 to 8.3e7 under a numerically *better* whitening, which is the signature of
    a quantity at the float64 noise floor. Reporting it as a number invites a comparison that means
    nothing, so a singular subset reports its status instead.

    Statuses: ``"finite"`` (value usable), ``"undefined_inert_parameter"`` (a member has no sensitivity
    here, so it cannot be confounded with anything -- irrelevant, not aliased), ``"numerically_singular"``
    (``lambda_min`` is at or below the rank tolerance; the direction is dependent to the limit of what
    float64 can see, and no magnitude may be quoted).
    """
    S, norms = normalised_sensitivities(J, sigma)
    idx = list(subset)
    if np.any(norms[idx] == 0):
        inert = [(params[i] if params else i) for i in idx if norms[i] == 0]
        return None, "undefined_inert_parameter", inert
    M = S[:, idx].T @ S[:, idx]
    lam = float(np.linalg.eigvalsh(M).min())
    # the standard rank tolerance: below it, lambda_min is indistinguishable from zero in float64
    if lam <= len(idx) * np.finfo(float).eps * max(1.0, float(np.linalg.norm(M, 2))):
        return None, "numerically_singular", []
    return float(1.0 / np.sqrt(lam)), "finite", []


def json_safe(obj):
    """Recursively replace non-finite floats with ``None`` so the result is RFC 8259 JSON.

    ``json.dump`` emits bare ``Infinity`` and ``NaN`` by default. Both are Python extensions that strict
    parsers reject, which would make the committed evidence unreadable to anything but Python. Passing
    ``default=`` does not help: it is only consulted for types json cannot serialise, and float is not
    one of them. The reason for each missing value is carried in a sibling ``*_status`` field, never in
    a sentinel magnitude.
    """
    if isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [json_safe(v) for v in obj]
    if isinstance(obj, float) and not np.isfinite(obj):
        return None
    if isinstance(obj, np.floating):
        return None if not np.isfinite(obj) else float(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj


def neg_log_likelihood(theta, y_obs, sigma, base_fp, base_sls, amp_frac=0.1, u_base=None):
    """Gaussian negative log-likelihood of an observation under the feature model.

    ``u_base=None`` is the **B1** design: one snapshot, five features.
    A float is the **B2** design: the young baseline at ``u_base`` stacked with the snapshot, ten
    features, with the nuisance parameters *shared* between the two observations because they come
    from the same unit. Only the life coordinate differs between them.
    """
    theta = np.asarray(theta, float)
    pred = features(theta, base_fp, base_sls, amp_frac)
    if u_base is not None:
        th_b = theta.copy()
        th_b[0] = float(u_base)
        pred = np.concatenate([features(th_b, base_fp, base_sls, amp_frac), pred])
    if not np.all(np.isfinite(pred)):
        # operational_half_life is nan whenever the decay never halves inside the 2 s window, which is
        # much of the admissible box at low leak. The feature is genuinely undefined there, so the point
        # is infeasible rather than merely a bad fit; callers turn this into a finite search penalty.
        return float("inf")
    y = np.asarray(y_obs, float)
    if y.size != pred.size or np.asarray(sigma).shape[0] != pred.size:
        raise ValueError(f"design mismatch: the model predicts {pred.size} features but the observation "
                         f"has {y.size} and the covariance is {np.asarray(sigma).shape[0]}"
                         f"x{np.asarray(sigma).shape[0]}. "
                         f"B1 (u_base=None) needs 5; B2 (u_base set) needs 10.")
    r = y - pred
    z = whiten(sigma, r)
    return float(0.5 * z @ z)


def profile_likelihood_u(u_grid, theta_true, y_obs, sigma, base_fp, base_sls, free_idx,
                         bounds, amp_frac=0.1, maxiter=200, u_base=None, n_starts=2):
    """Profile the negative log-likelihood over ``u``, re-optimising the free nuisance parameters.

    At each fixed u the nuisance parameters are re-fitted, so the resulting curve is the likelihood's
    true shape along u rather than a quadratic approximation to it. Raue et al. 2009: a profile flat in
    both directions indicates *structural* non-identifiability; one that rises on one side only
    indicates a *practical* limit set by the data.

    Two details decide whether the curve is the model's shape or the optimiser's:

    - **Strictly positive parameters are fitted in log space.** The stiffnesses here settle near 1e10
      while tau is near 1e-1, so on raw variables L-BFGS-B is searching across eleven orders of
      magnitude and stalls; the profile then looks flat because the *solver* gave up, not because the
      likelihood is. Log-scaling makes the step size meaningful in every coordinate.
    - **Each point is warm-started from its neighbour** (continuation). Adjacent points on the grid have
      nearly the same optimum, so the previous solution is the best start available, and it keeps the
      curve smooth instead of letting independent fits jump between local minima.

    ``converged`` is recorded per point and is what stops a solver failure being read as a flat
    direction; see ``profile_verdict``.
    """
    from scipy.optimize import minimize
    theta_true = np.asarray(theta_true, float)
    free = list(free_idx)
    lo_hi = [bounds[i] for i in free]
    lo_arr = np.array([b[0] for b in lo_hi], float)
    hi_arr = np.array([b[1] for b in lo_hi], float)
    # fit strictly positive parameters in log space; leave any that can reach zero or below alone
    logscale = [b[0] > 0.0 for b in lo_hi]
    def to_opt(x):
        return np.array([np.log(v) if lg else v for v, lg in zip(x, logscale)], float)
    def from_opt(z):
        return np.array([np.exp(v) if lg else v for v, lg in zip(z, logscale)], float)
    opt_bounds = [(np.log(lo), np.log(hi)) if lg else (lo, hi)
                  for (lo, hi), lg in zip(lo_hi, logscale)]

    fixed_starts = [theta_true[free].copy()]
    for k in range(1, n_starts):
        frac = 0.5 if k % 2 else 1.6
        fixed_starts.append(np.clip(theta_true[free] * frac, lo_arr, hi_arr))

    out = []
    previous = None                       # the neighbouring point's solution, for continuation
    for u in u_grid:
        infeasible = [0]

        def obj(z):
            th = theta_true.copy()
            th[0] = u
            th[free] = from_opt(z)
            v = neg_log_likelihood(th, y_obs, sigma, base_fp, base_sls, amp_frac, u_base)
            if not np.isfinite(v):
                # L-BFGS-B cannot take a gradient through inf, so an infeasible point becomes a large
                # finite wall it can back away from. Landing on the wall is recorded, never scored.
                infeasible[0] += 1
                return INFEASIBLE_PENALTY
            return v

        starts = list(fixed_starts)
        if previous is not None:
            starts.insert(0, previous)    # try the warm start first
        best_res = None
        for x0 in starts:
            z0 = np.clip(to_opt(np.clip(x0, lo_arr, hi_arr)),
                         [b[0] for b in opt_bounds], [b[1] for b in opt_bounds])
            r = minimize(obj, z0, method="L-BFGS-B", bounds=opt_bounds, options={"maxiter": maxiter})
            if best_res is None or r.fun < best_res.fun:
                best_res = r
        x_hat = from_opt(best_res.x)
        on_penalty = bool(best_res.fun >= INFEASIBLE_PENALTY)
        # a fit that ended on the penalty wall has not found a feasible optimum, whatever the solver
        # says, and must not be carried into the next point as a warm start
        converged = bool(best_res.success) and not on_penalty
        if not on_penalty:
            previous = x_hat
        tol = 1e-9 * np.maximum(1.0, np.abs([lo_arr, hi_arr]))
        at_bound = [bool(abs(v - lo_arr[j]) <= tol[0][j] or abs(v - hi_arr[j]) <= tol[1][j])
                    for j, v in enumerate(x_hat)]
        out.append({"u": float(u), "nll": float(best_res.fun), "converged": converged,
                    "ended_on_infeasible_penalty": on_penalty,
                    "n_infeasible_evaluations": int(infeasible[0]),
                    "n_iterations": int(best_res.nit), "solver_message": str(best_res.message),
                    "fitted_nuisance": [float(v) for v in x_hat], "at_bound": at_bound})
    return merge_profiles(out)


def merge_profiles(*profiles):
    """Combine profile segments onto one grid and re-reference delta_nll to the joint minimum."""
    merged = {}
    for prof in profiles:
        for q in prof:
            merged[round(float(q["u"]), 12)] = q         # a later segment supersedes an earlier point
    out = [merged[k] for k in sorted(merged)]
    best = min(q["nll"] for q in out)
    for q in out:
        q["delta_nll"] = q["nll"] - best
    return out


def crossing_brackets(profile, threshold=1.92):
    """The (below, above) u pair straddling the threshold on each side of the minimum.

    Returns ``{"lower": (u_in, u_out) or None, "upper": ...}``. ``None`` means the profile never crosses
    on that side, so there is no crossing to refine and the interval is open there.
    """
    d = np.array([q["delta_nll"] for q in profile], float)
    u = np.array([q["u"] for q in profile], float)
    order = np.argsort(u)
    d, u = d[order], u[order]
    i = int(np.argmin(d))
    out = {"lower": None, "upper": None}
    left = np.where(d[:i] > threshold)[0]
    if left.size:
        j = int(left[-1])                                 # last point above the cut, walking rightwards
        out["lower"] = (float(u[j + 1]), float(u[j]))
    right = np.where(d[i + 1:] > threshold)[0]
    if right.size:
        j = i + 1 + int(right[0])
        out["upper"] = (float(u[j - 1]), float(u[j]))
    return out


def profile_interval(profile, threshold=1.92):
    """Confidence interval read off a profile, with open ends reported honestly.

    Returns ``{"lower", "upper", "lower_open", "upper_open", "grid_min", "grid_max"}``. A bound is
    **open** when the profile never crosses the threshold on that side within the grid: the interval
    extends past the tested domain and no half-width may be quoted from it. Turning a grid edge into a
    confidence bound is the specific error this function exists to prevent.
    """
    ordered = sorted(profile, key=lambda q: q["u"])
    d = np.array([q["delta_nll"] for q in ordered], float)
    u = np.array([q["u"] for q in ordered], float)
    at_bound = [bool(any(q.get("at_bound", []))) for q in ordered]
    i = int(np.argmin(d))
    left = np.where(d[:i] > threshold)[0]
    right = np.where(d[i + 1:] > threshold)[0]
    lower_open, upper_open = left.size == 0, right.size == 0
    li = None if lower_open else int(left[-1])
    ri = None if upper_open else int(i + 1 + right[0])
    # A crossing where the nuisance fit is pinned to its box may be the box talking, not the data: the
    # optimiser simply ran out of freedom to compensate. Flagging it is what stops such a crossing being
    # read as a measured precision.
    return {
        "lower": None if li is None else float(u[li]),
        "upper": None if ri is None else float(u[ri]),
        "lower_open": bool(lower_open), "upper_open": bool(upper_open),
        "lower_at_nuisance_bound": None if li is None else at_bound[li],
        "upper_at_nuisance_bound": None if ri is None else at_bound[ri],
        "grid_min": float(u.min()), "grid_max": float(u.max()),
        "u_at_minimum": float(u[i]),
        "plateau_nll_spread": _plateau_spread(ordered, threshold),
    }


def _plateau_spread(ordered, threshold):
    """Total nll variation across the points inside the threshold: how flat the "interval" really is.

    A spread orders of magnitude below the threshold means the interval is a plateau the profile never
    resolves within, so its width is a bound on ignorance rather than a precision.
    """
    inside = [q["nll"] for q in ordered if q["delta_nll"] <= threshold]
    return None if len(inside) < 2 else float(max(inside) - min(inside))


def profile_verdict(profile, threshold=1.92, require_converged=True, domain=None, atol=1e-9):
    """Classify a profile. ``threshold`` 1.92 is the 95% chi-square(1) cut on delta(-log L).

    **The cut is a diagnostic scale here, not a calibrated confidence interval.** 1.92 is an asymptotic
    likelihood-ratio approximation, and this problem violates several of its comforts: a nonlinear feature
    map, bounded nuisance parameters, infeasible regions where a feature is undefined, an estimated and
    strongly correlated covariance, and near-zero information across the post-onset plateau. Whether it
    achieves nominal coverage here is untested (PV-CRIT-09). If a coverage study finds it does not, the
    threshold must NOT be tuned to make it nominal. Provenance: docs/PARAMETER_PROVENANCE.md.

    ``domain`` is the ``(lo, hi)`` physical range of the profiled parameter. It is what separates a
    profile that stopped because the *parameter* ran out from one that stopped because the *grid* did,
    and without it the two are indistinguishable -- so when it is ``None`` every un-crossed side is
    reported as ``domain-limited`` and neither ``practical`` nor ``structural`` can be returned.
    Declaring a domain is therefore a claim: "the grid reached the edge of what is physically possible."

    Returns (verdict, flat_fraction). Verdicts:

    - ``"unresolved"`` -- an optimisation failed, so the profile is not trustworthy. Checked first,
      because a solver failure can look exactly like a flat direction.
    - ``"identifiable"`` -- the profile rises through the threshold on **both** sides of the minimum.
    - ``"practical"`` -- it rises on one side, and the flat side reaches the declared physical bound.
      There is no more domain to search, so this is practical non-identifiability in the sense of
      Raue et al. 2009.
    - ``"structural"`` -- flat on both sides across the full declared domain. Still only a *candidate*
      for a structural direction; a noiseless symmetry analysis is what actually establishes one.
    - ``"domain-limited"`` -- it failed to cross on a side that stopped short of the physical bound
      (or no domain was declared). The interval is open there. This is an untested region, **not**
      evidence of a flat direction, and the remedy is a wider grid. Distinguishing this from
      ``practical`` is the point of the function.
    """
    if require_converged and not all(p.get("converged", True) for p in profile):
        return "unresolved", float("nan")
    d = np.array([p["delta_nll"] for p in profile], float)
    u = np.array([p["u"] for p in profile], float)
    order = np.argsort(u)
    d, u = d[order], u[order]
    flat = float(np.mean(d <= threshold))
    i = int(np.argmin(d))
    rises_left = bool(np.any(d[:i] > threshold)) if i > 0 else False
    rises_right = bool(np.any(d[i + 1:] > threshold)) if i < len(d) - 1 else False
    if rises_left and rises_right:
        return "identifiable", flat
    # every un-crossed side must be shown to have run to the edge of the physical domain
    lo, hi = (None, None) if domain is None else (float(domain[0]), float(domain[1]))
    def _exhausted(edge, bound):
        return bound is not None and abs(edge - bound) <= atol
    left_done = rises_left or _exhausted(float(u[0]), lo)
    right_done = rises_right or _exhausted(float(u[-1]), hi)
    if not (left_done and right_done):
        return "domain-limited", flat
    return ("structural" if not rises_left and not rises_right else "practical"), flat