"""R1 failure-map logic on hand-built records (no simulation, no fitting)."""
import json

import numpy as np
import pytest

from scripts.analyze_studyC_failure import (SOURCE, aggregate_by_label, coverage, coverage_label,
                                            partial_pearson, pearson, probe_cycles, sha256)


def _row(label, rmse, clock, pre=0.1, post=0.1):
    return {"coverage_label": label, "rmse": rmse, "rmse_clock": clock,
            "within_target": rmse <= 0.10, "beats_clock": rmse < clock,
            "rmse_pre_onset": pre, "rmse_post_onset": post}


def test_probe_schedule_stops_before_rupture_and_starts_at_the_baseline():
    c = probe_cycles(1416.0)
    assert c[0] == 100.0 and c[-1] < 1416.0
    assert np.allclose(np.diff(c), 250.0)


def test_pre_post_onset_counts_are_exact_at_the_boundary():
    # rupture 1000 -> probes at 100, 350, 600, 850. Onset at exactly 600 counts as post-onset.
    cov = coverage(1000.0, 0.6)
    assert cov["n_probes"] == 4 and cov["n_post_onset"] == 2 and cov["n_pre_onset"] == 2
    assert cov["first_post_onset_cycles"] == 600.0
    assert cov["onset_to_first_post_onset_cycles"] == 0.0
    # nudging the onset just above a probe cycle moves that probe to the pre-onset side
    assert coverage(1000.0, 0.6001)["n_post_onset"] == 1


def test_no_post_onset_unit_reports_nulls_and_the_right_label():
    cov = coverage(1000.0, 0.99)          # onset at 990, last probe 850
    assert cov["n_post_onset"] == 0 and cov["coverage_label"] == "no_post_onset"
    assert cov["first_post_onset_cycles"] is None
    assert cov["first_post_onset_life"] is None
    assert cov["onset_to_first_post_onset_cycles"] is None


def test_coverage_label_thresholds_are_deterministic():
    assert coverage_label(0) == "no_post_onset"
    assert coverage_label(1) == coverage_label(2) == "sparse_post_onset"
    assert coverage_label(3) == coverage_label(99) == "adequate_post_onset"


def test_beating_the_clock_is_not_counted_as_a_target_pass():
    rows = [_row("adequate_post_onset", 0.15, 0.40)]      # beats a bad clock, misses 0.10
    agg = aggregate_by_label(rows)["adequate_post_onset"]
    assert agg["n_beats_clock"] == 1 and agg["n_within_target"] == 0


def test_aggregate_keeps_units_with_a_missing_segment():
    rows = [_row("sparse_post_onset", 0.2, 0.3, post=None),
            _row("adequate_post_onset", 0.05, 0.2, pre=None)]
    agg = aggregate_by_label(rows)
    assert agg["sparse_post_onset"]["n_units"] == 1
    assert agg["sparse_post_onset"]["n_missing_post_onset_segment"] == 1
    assert agg["adequate_post_onset"]["n_missing_pre_onset_segment"] == 1
    assert sum(v["n_units"] for v in agg.values()) == 2


def test_empty_label_reports_none_rather_than_a_fabricated_zero():
    agg = aggregate_by_label([_row("adequate_post_onset", 0.05, 0.2)])
    assert agg["no_post_onset"]["n_units"] == 0 and agg["no_post_onset"]["mean_rmse"] is None


def test_partial_correlation_removes_a_common_driver():
    c = np.arange(10.0)
    a, b = 2 * c, -3 * c                                   # both driven entirely by c
    assert pearson(a, b) == pytest.approx(-1.0)            # perfectly correlated before control
    # with nothing left after removing c, the partial correlation is undefined, not zero
    assert partial_pearson(a, b, c) is None
    assert pearson(a, [0.0] * 10) is None                  # undefined, not a crash


def test_partial_correlation_keeps_an_association_that_is_not_the_common_driver():
    rng = np.random.default_rng(0)
    c = rng.normal(size=200)
    extra = rng.normal(size=200)
    a = c + extra                                          # shares c, plus its own signal
    b = c + extra                                          # same extra signal -> survives control
    assert partial_pearson(a, b, c) == pytest.approx(1.0, abs=1e-6)
    d = c + rng.normal(size=200)                           # shares only c
    assert abs(partial_pearson(a, d, c)) < 0.2


def test_source_hash_matches_the_committed_result_the_analysis_declares():
    """The script aborts on mismatch; this pins the hash the committed analysis was built from."""
    recorded = json.load(open("data/sim/studyC/studyC_failure_analysis.json"))
    assert recorded["source_sha256"] == sha256(SOURCE)
    assert recorded["post_hoc_descriptive"] is True
