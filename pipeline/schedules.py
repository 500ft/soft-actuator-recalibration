"""Study C2 — probe schedules, input arms and interpretation rules, frozen by the C2 preregistration.

These are the parts of the C2 design that must not drift during implementation, so they live here as
pure, tested functions rather than as prose. The runner (R3) consumes them; it does not redefine them.
Design: docs/specs/observability-program/studyC2-preregistration.md
"""

from __future__ import annotations

import numpy as np

# --- seeding -------------------------------------------------------------------------------------
# Study C drew its measurement noise from SeedSequence([SEED, 7, unit_index, probe_index]). The
# reference schedule must reuse that namespace so it reproduces the committed run exactly; every new
# schedule uses a separate namespace so its noise cannot collide with it.
LEGACY_NAMESPACE = 7
C2_NAMESPACE = 8

# --- input arms ----------------------------------------------------------------------------------
# Study C's 11 inputs: 5 current log-ratios, 5 previous-probe log-ratios, cycles/1000.
N_PRESSURE_NOW = 5
N_PRESSURE_LAG = 5
CLOCK_COLUMN = N_PRESSURE_NOW + N_PRESSURE_LAG
N_INPUTS = CLOCK_COLUMN + 1
ARMS = ("full", "pressure_only", "clock_only")

BASELINE_CYCLE = 100.0          # every condition normalises against the same young state
PASS_RMSE = 0.10                # unchanged from Study C; derived as "two Study A grid steps"
# Unchanged from Study C: >= 8/10 within target and >= 8/10 beating clock. This bar has NO PRECEDENT in
# the literature -- it is a defensible preregistered choice, not a field standard, and at ten units the
# 6-vs-8 distinction may sit inside sampling variance (literature/gaps.md items 2 and 8).
# Do not relax it to rescue a result; provenance: docs/PARAMETER_PROVENANCE.md
PASS_COUNT = 8
MATERIAL_REDUCTION_LIFE = 0.05  # on the pre-specified below-median subset

SCHEDULES = {
    "reference": {"kind": "fixed", "start": 100.0, "step": 250.0, "feasible": True},
    "dense": {"kind": "fixed", "start": 100.0, "step": 125.0, "feasible": True},
    "sparse": {"kind": "fixed", "start": 100.0, "step": 500.0, "feasible": True},
    "late_start": {"kind": "fixed", "start": 500.0, "step": 250.0, "feasible": True},
    # Places the same number of probes as the reference schedule, but spanning the unit's true onset.
    # Uses generator truth, so it is a mechanistic diagnostic upper bound, never a deployable policy.
    "onset_anchored_oracle": {"kind": "oracle", "feasible": False},
}


def arm_columns(arm):
    """Column indices of Study C's 11-input vector that this arm keeps."""
    if arm == "full":
        return list(range(N_INPUTS))
    if arm == "pressure_only":
        return list(range(CLOCK_COLUMN))
    if arm == "clock_only":
        return [CLOCK_COLUMN]
    raise ValueError(f"unknown arm {arm!r}; expected one of {ARMS}")


def fixed_cycle_probes(rupture_cycles, start, step):
    """Baseline at BASELINE_CYCLE plus a fixed cadence, de-duplicated, all strictly before rupture."""
    if step <= 0:
        raise ValueError("step must be > 0")
    follow_up = np.arange(float(start), float(rupture_cycles), float(step))
    cycles = np.unique(np.concatenate([[BASELINE_CYCLE], follow_up]))
    return cycles[cycles < rupture_cycles]


def onset_anchored_probes(rupture_cycles, onset_fraction, n_probes):
    """Oracle: the baseline plus ``n_probes - 1`` probes spread from the true onset to just before
    rupture. Probe *count* is matched to the reference schedule so that only placement differs."""
    if n_probes < 1:
        raise ValueError("n_probes must be >= 1")
    if n_probes == 1:
        return np.array([BASELINE_CYCLE])
    onset_cycles = max(float(onset_fraction) * float(rupture_cycles), BASELINE_CYCLE)
    tail = np.linspace(onset_cycles, float(rupture_cycles), n_probes - 1, endpoint=False)
    cycles = np.unique(np.concatenate([[BASELINE_CYCLE], tail]))
    return cycles[cycles < rupture_cycles]


def probes_for(schedule_id, rupture_cycles, onset_fraction):
    """Probe cycles for one unit under one named schedule."""
    spec = SCHEDULES[schedule_id]
    if spec["kind"] == "fixed":
        return fixed_cycle_probes(rupture_cycles, spec["start"], spec["step"])
    reference_n = fixed_cycle_probes(rupture_cycles, SCHEDULES["reference"]["start"],
                                     SCHEDULES["reference"]["step"]).size
    return onset_anchored_probes(rupture_cycles, onset_fraction, reference_n)


def probe_seed(schedule_id, unit_index, probe_index):
    """Deterministic measurement seed. The reference schedule reuses Study C's namespace exactly."""
    if schedule_id == "reference":
        entropy = [LEGACY_NAMESPACE, int(unit_index), int(probe_index)]
    else:
        entropy = [C2_NAMESPACE, int(unit_index), _schedule_ordinal(schedule_id), int(probe_index)]
    from pipeline.dispersion import SEED
    return int(np.random.SeedSequence([SEED] + entropy).generate_state(1)[0])


def _schedule_ordinal(schedule_id):
    """Stable integer id, so adding a schedule later cannot renumber an existing one."""
    return sorted(SCHEDULES).index(schedule_id)


def below_median_subset(rupture_by_unit, training_median):
    """Units whose rupture life is below the training median.

    Pre-specifiable: known from the generator before any held-out error is computed. This replaces
    selecting "the currently worst units", which would choose an evaluation subset from outcomes.
    """
    return [u for u, rc in sorted(rupture_by_unit.items()) if rc < training_median]


def materially_reduced(reference_mean, candidate_mean, threshold=MATERIAL_REDUCTION_LIFE):
    """Descriptive rule fixed before the run: mean u-RMSE on the below-median subset falls by
    at least ``threshold`` life."""
    return bool(reference_mean - candidate_mean >= threshold)


def passes_c_rule(n_within_target, n_beats_clock, n_units=10):
    """Study C's unchanged rule. Never relaxed for C2."""
    if n_within_target > n_units or n_beats_clock > n_units:
        raise ValueError("counts cannot exceed the number of held-out units")
    return bool(n_within_target >= PASS_COUNT and n_beats_clock >= PASS_COUNT)


def interpretation_label(*, pressure_only_feasible_pass, clock_only_indistinguishable_from_full,
                         full_feasible_pass, full_oracle_pass, oracle_failures_all_below_median):
    """The predeclared reading of the C2 grid. Evaluated in this fixed order of precedence.

    Every input is a boolean computed from the unchanged Study C rule; none of them may be chosen
    after seeing the grid.
    """
    if pressure_only_feasible_pass:
        return "signal-sufficient-without-clock"
    if clock_only_indistinguishable_from_full:
        return "clock-dominated"
    if full_feasible_pass:
        return "schedule-limited"
    if full_oracle_pass:
        return "mixed-timing-feasibility"
    if oracle_failures_all_below_median:
        return "clock-prior-limited"
    return "signal-limited"
