"""R2 acceptance tests: the frozen Study C2 contract, before any C2 run exists.

These encode the preregistration's rules so the design cannot drift during R3 implementation.
"""
import numpy as np
import pytest

from pipeline.schedules import (ARMS, BASELINE_CYCLE, C2_NAMESPACE, LEGACY_NAMESPACE, SCHEDULES,
                                arm_columns, below_median_subset, fixed_cycle_probes,
                                interpretation_label, materially_reduced, onset_anchored_probes,
                                passes_c_rule, probe_seed, probes_for)
from scripts.run_studyC import PROBE_START, PROBE_STEP, probes as studyC_probes
from pipeline.dispersion import SEED, sample_units


# --- the reference schedule must reproduce Study C exactly ---------------------------------------

def test_reference_schedule_matches_the_committed_study_c_schedule():
    for rupture in (1416.0, 2471.0, 3625.6, 4775.0):
        unit = type("U", (), {"fatigue": type("F", (), {"rupture_cycles": rupture})()})()
        assert np.array_equal(probes_for("reference", rupture, 0.7), studyC_probes(unit)[0])


def test_reference_seed_namespace_is_study_c_s_so_the_reference_arm_reproduces():
    expected = int(np.random.SeedSequence([SEED, LEGACY_NAMESPACE, 3, 5]).generate_state(1)[0])
    assert probe_seed("reference", 3, 5) == expected
    # every other schedule lives in a separate namespace and cannot collide with it
    assert probe_seed("dense", 3, 5) != expected
    assert probe_seed("dense", 3, 5) != probe_seed("sparse", 3, 5)


def test_schedule_ordinals_are_stable_under_insertion():
    """A new schedule must not renumber an existing one's seeds."""
    before = probe_seed("sparse", 1, 1)
    SCHEDULES["zzz_probe_only"] = {"kind": "fixed", "start": 100.0, "step": 250.0, "feasible": True}
    try:
        assert probe_seed("sparse", 1, 1) == before
    finally:
        del SCHEDULES["zzz_probe_only"]


# --- schedule mechanics ---------------------------------------------------------------------------

@pytest.mark.parametrize("schedule_id", sorted(SCHEDULES))
@pytest.mark.parametrize("rupture", [986.0, 1416.0, 3671.0, 4775.0])
def test_no_schedule_probes_at_or_after_rupture(schedule_id, rupture):
    c = probes_for(schedule_id, rupture, 0.7)
    assert c.size >= 1 and np.all(c < rupture)


@pytest.mark.parametrize("schedule_id", sorted(SCHEDULES))
def test_every_schedule_has_the_baseline_exactly_once(schedule_id):
    c = probes_for(schedule_id, 3671.0, 0.67)
    assert np.count_nonzero(c == BASELINE_CYCLE) == 1
    assert c[0] == BASELINE_CYCLE
    assert np.unique(c).size == c.size, "duplicate probe cycles"


def test_a_follow_up_start_on_the_baseline_is_de_duplicated_not_doubled():
    c = fixed_cycle_probes(1000.0, start=100.0, step=250.0)
    assert np.array_equal(c, np.array([100.0, 350.0, 600.0, 850.0]))


def test_late_start_keeps_the_baseline_and_drops_only_early_follow_ups():
    ref = probes_for("reference", 3000.0, 0.7)
    late = probes_for("late_start", 3000.0, 0.7)
    assert late[0] == BASELINE_CYCLE == ref[0]
    assert late.size < ref.size
    assert set(late[1:]).issubset(set(np.arange(500.0, 3000.0, 250.0)))


def test_dense_and_sparse_bracket_the_reference_probe_count():
    n = {s: probes_for(s, 3671.0, 0.67).size for s in ("dense", "reference", "sparse")}
    assert n["sparse"] < n["reference"] < n["dense"]


# --- the oracle isolates placement, not probe count -----------------------------------------------

@pytest.mark.parametrize("rupture,onset", [(1416.0, 0.78), (2471.0, 0.72), (4775.0, 0.74)])
def test_oracle_matches_the_reference_probe_count_so_only_placement_differs(rupture, onset):
    ref = probes_for("reference", rupture, onset)
    oracle = probes_for("onset_anchored_oracle", rupture, onset)
    assert oracle.size == ref.size, "oracle must not also change the number of probes"


def test_oracle_puts_every_non_baseline_probe_at_or_after_onset():
    rupture, onset = 1416.0, 0.78
    c = probes_for("onset_anchored_oracle", rupture, onset)
    assert np.all(c[1:] >= onset * rupture)
    ref = probes_for("reference", rupture, onset)
    n_post_ref = int((ref >= onset * rupture).sum())
    assert int((c >= onset * rupture).sum()) > n_post_ref, "oracle should improve post-onset coverage"


def test_oracle_degenerates_safely_for_a_single_probe_unit():
    assert np.array_equal(onset_anchored_probes(200.0, 0.7, 1), np.array([BASELINE_CYCLE]))


def test_only_the_oracle_is_marked_infeasible():
    assert SCHEDULES["onset_anchored_oracle"]["feasible"] is False
    assert all(SCHEDULES[s]["feasible"] for s in SCHEDULES if s != "onset_anchored_oracle")


# --- input arms -------------------------------------------------------------------------------------

def test_arms_select_the_declared_columns_and_life_is_never_an_input():
    assert arm_columns("full") == list(range(11))
    assert arm_columns("pressure_only") == list(range(10)) and 10 not in arm_columns("pressure_only")
    assert arm_columns("clock_only") == [10]
    with pytest.raises(ValueError):
        arm_columns("normalised_life")


def test_pressure_only_arm_actually_removes_the_clock_column():
    x = np.arange(11.0)
    assert 10.0 not in x[arm_columns("pressure_only")]
    assert list(x[arm_columns("clock_only")]) == [10.0]


# --- the pre-specifiable subset (replaces "the currently worst units") -----------------------------

def test_below_median_subset_is_defined_by_rupture_life_not_by_error():
    rupture = {0: 4165.0, 7: 1416.0, 12: 2205.0, 29: 4775.0}
    assert below_median_subset(rupture, 3625.6) == [7, 12]
    # a unit exactly at the median is not "below" it
    assert below_median_subset({1: 3625.6}, 3625.6) == []


def test_material_reduction_is_a_fixed_numeric_rule():
    assert materially_reduced(0.1627, 0.1127) is True       # exactly 0.05 counts
    assert materially_reduced(0.1627, 0.1128) is False
    assert materially_reduced(0.1627, 0.05, threshold=0.2) is False


# --- the unchanged Study C rule ----------------------------------------------------------------------

def test_c_rule_is_unchanged_and_rejects_the_committed_study_c_counts():
    assert passes_c_rule(6, 7) is False        # the committed Study C result stays C-FAIL
    assert passes_c_rule(8, 8) is True
    assert passes_c_rule(8, 7) is False and passes_c_rule(7, 8) is False
    with pytest.raises(ValueError):
        passes_c_rule(11, 8)


# --- interpretation labels, fixed before the grid exists ---------------------------------------------

def _label(**over):
    base = dict(pressure_only_feasible_pass=False, clock_only_indistinguishable_from_full=False,
                full_feasible_pass=False, full_oracle_pass=False,
                oracle_failures_all_below_median=False)
    return interpretation_label(**{**base, **over})


def test_every_interpretation_branch_is_reachable_and_ordered():
    assert _label(pressure_only_feasible_pass=True) == "signal-sufficient-without-clock"
    assert _label(clock_only_indistinguishable_from_full=True) == "clock-dominated"
    assert _label(full_feasible_pass=True) == "schedule-limited"
    assert _label(full_oracle_pass=True) == "mixed-timing-feasibility"
    assert _label(oracle_failures_all_below_median=True) == "clock-prior-limited"
    assert _label() == "signal-limited"


def test_pressure_only_success_outranks_every_other_reading():
    assert _label(pressure_only_feasible_pass=True, clock_only_indistinguishable_from_full=True,
                  full_feasible_pass=True) == "signal-sufficient-without-clock"


def test_a_feasible_pass_outranks_the_oracle_so_the_oracle_never_becomes_the_recommendation():
    assert _label(full_feasible_pass=True, full_oracle_pass=True) == "schedule-limited"


# --- the arms are exercisable on real units before R3 exists -------------------------------------------

def test_schedules_are_well_formed_on_the_real_dispersed_cohort():
    for i, unit in enumerate(sample_units(30, SEED)):
        rc, onset = unit.fatigue.rupture_cycles, unit.fatigue.acceleration_onset_fraction
        for s in SCHEDULES:
            c = probes_for(s, rc, onset)
            assert c.size >= 1 and c[0] == BASELINE_CYCLE and np.all(c < rc)
            assert len({probe_seed(s, i, k) for k in range(c.size)}) == c.size, "seed collision"
