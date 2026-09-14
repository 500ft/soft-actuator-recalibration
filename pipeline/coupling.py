"""Phase F — P-V health trajectories and recalibration policy primitives.

The Phase E finding is that pressure-only proprioception is dominated by the fatigue
*compliance-scale drift* (a young calibration's pose error grows ~100x over life). The Phase F
question is operational: when should you recalibrate? The thesis is that the **observable P-V
loop** (its hysteresis loop area / shape) is a health indicator of that drift, so a
P-V-health-triggered recalibration can hold accuracy near an always-on policy at a fraction of
the recalibration count.

This module provides the *observable* health signal (the P-V loop area from a volumetric
probe — Gate 1's acquisition method, not the ground-truth compliance multiplier), per-actuator
health-vs-life trajectories, a bootstrap correlation for the health-indicator claim, and the
recalibration-schedule policies. Threshold selection lives in ``scripts/run_study3.py`` and
uses training/validation actuators only.
"""

from __future__ import annotations

import numpy as np

from sim.fatigue import FatigueParams, degraded_sls, fatigue_state
from sim.plant import SLSParams, first_crossing, pv_loop


def pv_loop_area(sls: SLSParams):
    """Observable P-V hysteresis loop area from a volumetric probe (energy/cycle).

    Fixed sinusoidal volume drive (10 % of V0) at the loss-peak frequency; the enclosed P-V
    area grows with the fatigue loss modulus. This is the measurable loop-shape signal, not
    a ground-truth state.
    """
    return float(pv_loop(sls.f_loss_peak, 0.1 * sls.V0, sls)["area"])


def health_trajectory(base_sls: SLSParams, rupture_cycles, life_fractions):
    """P-V loop-area health signal at each normalized life fraction for one actuator."""
    fp = FatigueParams(rupture_cycles=float(rupture_cycles))
    return np.asarray([pv_loop_area(degraded_sls(base_sls, fatigue_state(lf * rupture_cycles, 0.0, fp)))
                       for lf in life_fractions], dtype=float)


def bootstrap_correlation(x, y, n_boot=1000, seed=0, ci=0.95):
    """Pearson r between ``x`` and ``y`` with a bootstrap confidence interval.

    Used to quantify the health-indicator claim: P-V health drift vs pose error over life.
    """
    x = np.asarray(x, float); y = np.asarray(y, float)
    if x.shape != y.shape or x.ndim != 1 or x.size < 3:
        raise ValueError("x and y must be matching 1-D arrays with >= 3 points")
    rng = np.random.default_rng(seed)
    point = float(np.corrcoef(x, y)[0, 1])
    n = x.size
    boot = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, n, n)
        xb, yb = x[idx], y[idx]
        if xb.std() < 1e-15 or yb.std() < 1e-15:
            boot[b] = 0.0
        else:
            boot[b] = np.corrcoef(xb, yb)[0, 1]
    lo = float(np.quantile(boot, (1 - ci) / 2))
    hi = float(np.quantile(boot, 1 - (1 - ci) / 2))
    return {"r": point, "ci_low": lo, "ci_high": hi}


def lead_time(health_norm, errors_fixed_cal, tau, budget_mm, life_fractions):
    """Trigger-vs-budget lead time from one young-calibrated trajectory.

    The trigger crossing is the first life fraction where normalized P-V loop
    area reaches ``1 + tau`` from the young calibration. The budget crossing is
    the first life fraction where the young/fixed-calibration pose error reaches
    ``budget_mm``. Crossings are linearly interpolated between observed life
    stages; missing or non-positive leads are returned with explicit statuses.
    """
    health_norm = np.asarray(health_norm, float)
    errors_fixed_cal = np.asarray(errors_fixed_cal, float)
    life_fractions = np.asarray(life_fractions, float)
    if health_norm.shape != errors_fixed_cal.shape or health_norm.shape != life_fractions.shape:
        raise ValueError("health, error, and life arrays must have matching shapes")
    trigger_life = first_crossing(life_fractions, health_norm, 1.0 + float(tau))
    budget_life = first_crossing(life_fractions, errors_fixed_cal, float(budget_mm))
    if trigger_life is None:
        return {"trigger_life": None, "budget_violation_life": budget_life,
                "lead_life": None, "status": "never_triggers"}
    if budget_life is None:
        return {"trigger_life": trigger_life, "budget_violation_life": None,
                "lead_life": None, "status": "never_violates"}
    lead = float(budget_life - trigger_life)
    status = "ok" if lead > 0.0 else "nonpositive_lead"
    return {"trigger_life": trigger_life, "budget_violation_life": budget_life,
            "lead_life": lead, "status": status}


def per_group_correlations(groups, x, y):
    """Pearson r per group with median/range summary over finite group values."""
    groups = np.asarray(groups)
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    if groups.shape != x.shape or x.shape != y.shape or x.ndim != 1:
        raise ValueError("groups, x, and y must be matching 1-D arrays")
    records = []
    for group in sorted(set(groups.tolist())):
        mask = groups == group
        xg, yg = x[mask], y[mask]
        if xg.size < 3 or xg.std() < 1e-15 or yg.std() < 1e-15:
            r = None
        else:
            r = float(np.corrcoef(xg, yg)[0, 1])
        records.append({"group": int(group), "r": r, "n": int(xg.size)})
    finite = [rec["r"] for rec in records if rec["r"] is not None and np.isfinite(rec["r"])]
    return {
        "values": records,
        "median": float(np.median(finite)) if finite else None,
        "min": float(np.min(finite)) if finite else None,
        "max": float(np.max(finite)) if finite else None,
    }


def recalibration_schedule(health, policy, tau=None):
    """Per-life-stage calibrate? flags for one actuator's health trajectory.

    ``policy`` in {"fixed", "always", "triggered"}. Stage 0 always calibrates. "triggered"
    recalibrates when the health drift since the last calibration exceeds ``tau``.
    Returns a boolean list (True = (re)calibrate at this stage).
    """
    health = np.asarray(health, float)
    n = health.size
    if n == 0:
        return []
    flags = [True] + [False] * (n - 1)        # always calibrate once at the start
    if policy == "fixed":
        return flags
    if policy == "always":
        return [True] * n
    if policy == "triggered":
        if tau is None:
            raise ValueError("triggered policy requires tau")
        last = health[0]
        for i in range(1, n):
            if abs(health[i] - last) > tau:
                flags[i] = True
                last = health[i]
        return flags
    raise ValueError(f"unknown policy {policy!r}")


def cycle_schedule(cycles, period):
    """Per-life-stage calibrate? flags for a sensing-free cycle-count (clock) policy.

    The obvious cheap competitor to the P-V trigger: recalibrate whenever the
    accumulated actuation-cycle count since the last calibration exceeds ``period``
    (absolute cycles — a real clock cannot know an actuator's rupture life, so the
    period is global, not per-actuator). Stage 0 always calibrates. Decisions are
    only available at observation stages, same as the trigger, so the comparison
    is like-for-like.
    """
    cycles = np.asarray(cycles, float)
    n = cycles.size
    if n == 0:
        return []
    flags = [True] + [False] * (n - 1)
    last = cycles[0]
    for i in range(1, n):
        if cycles[i] - last > period:
            flags[i] = True
            last = cycles[i]
    return flags


def apply_schedule(flags, errors_if_recalibrated, errors_if_stale):
    """Resolve realized per-stage error given a calibrate? schedule.

    ``errors_if_recalibrated[i]`` = error when calibrated AT stage i (fresh).
    ``errors_if_stale[i][j]`` = error at stage i using the calibration fitted at stage j (j<=i).
    Returns ``(realized_errors, n_recal)``.
    """
    realized = []
    last_cal = None
    for i, do_cal in enumerate(flags):
        if do_cal:
            last_cal = i
            realized.append(errors_if_recalibrated[i])
        else:
            realized.append(errors_if_stale[i][last_cal])
    return np.asarray(realized, float), int(sum(flags))
