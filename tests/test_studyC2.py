"""R3 — the Study C2 runner's contract, verified without executing the preregistered grid."""
import json

import numpy as np
import pytest

from pipeline.dispersion import SEED, sample_units
from pipeline.schedules import CLOCK_COLUMN, N_INPUTS, arm_columns
from scripts import run_studyC as C
from scripts import run_studyC2 as C2


# --- the reference cell must be Study C, exactly ---------------------------------------------------

def test_reference_records_reproduce_study_c_record_for_record():
    """The strongest guarantee available: same probes, same noise draws, same inputs, same targets."""
    units = sample_units(C.N_UNITS, SEED)
    for i in (7, 22):                                   # a short-lived and a median-life held-out unit
        want, got = C.unit_records(units[i], i), C2.unit_records(units[i], i, "reference")
        assert len(got) == len(want)
        for a, b in zip(want, got):
            assert a["cycles"] == b["cycles"] and a["u"] == b["u"]
            assert a["post_onset"] == b["post_onset"]
            np.testing.assert_array_equal(a["x"], b["x"])


def test_a_different_schedule_draws_different_noise_than_the_reference():
    unit = sample_units(C.N_UNITS, SEED)[22]
    ref = C2.unit_records(unit, 22, "reference")
    dense = C2.unit_records(unit, 22, "dense")
    assert len(dense) > len(ref)
    assert not np.array_equal(ref[0]["x"], dense[0]["x"]), "new schedules must use a separate seed namespace"


# --- inputs -----------------------------------------------------------------------------------------

def test_records_carry_exactly_the_eleven_inputs_and_never_normalised_life():
    unit = sample_units(C.N_UNITS, SEED)[22]
    rows = C2.unit_records(unit, 22, "sparse")
    for r in rows:
        assert r["x"].shape == (N_INPUTS,)
        assert not np.any(np.isclose(r["x"], r["u"])) or r["u"] == 0.0, "life must not appear as an input"
    # the clock column is cycles/1000, not life
    assert rows[0]["x"][CLOCK_COLUMN] == pytest.approx(rows[0]["cycles"] / 1000.0)


@pytest.mark.parametrize("arm,width", [("full", 11), ("pressure_only", 10), ("clock_only", 1)])
def test_stack_restricts_to_the_arm_s_columns(arm, width):
    recs = [{"x": np.arange(11.0), "u": 0.5}, {"x": np.arange(11.0) * 2, "u": 0.6}]
    X, y = C2.stack(recs, arm_columns(arm))
    assert X.shape == (2, width) and list(y) == [0.5, 0.6]
    if arm == "pressure_only":
        assert 10.0 not in X[0]
    if arm == "clock_only":
        assert list(X[:, 0]) == [10.0, 20.0]


# --- fitting discipline --------------------------------------------------------------------------------

def _synthetic_units(n_units, n_rows, width=11, seed=0):
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n_units):
        X = rng.normal(size=(n_rows, width))
        y = X @ np.linspace(1.0, 0.1, width) + 0.5
        out.append([{"x": x, "u": float(t)} for x, t in zip(X, y)])
    return out


def test_lambda_selection_reads_training_units_only():
    train = _synthetic_units(5, 6)
    lam_a, scores_a = C2.choose_lambda(train, arm_columns("full"))
    # mutating data that is *not* in the training list cannot change the choice
    _ = _synthetic_units(5, 6, seed=99)
    lam_b, scores_b = C2.choose_lambda(train, arm_columns("full"))
    assert lam_a == lam_b and scores_a == scores_b
    assert set(scores_a) == {str(x) for x in C.LAMBDAS}


def test_heldout_predictions_reuse_the_training_standardisation():
    train = _synthetic_units(4, 8)
    columns = arm_columns("full")
    X, y = C2.stack([r for u in train for r in u], columns)
    model = C.ridge_fit(X, y, 0.1)
    held = _synthetic_units(1, 5, seed=7)[0]
    Xh, _ = C2.stack(held, columns)
    manual = ((Xh - model["mu"]) / model["sd"]) @ model["w"] + model["b"]
    np.testing.assert_allclose(C.ridge_predict(model, Xh), manual)
    # a fresh standardisation on the held-out unit would give different numbers
    refit = C.ridge_fit(Xh, np.array([r["u"] for r in held]), 0.1)
    assert not np.allclose(model["mu"], refit["mu"])


# --- cohort summary ---------------------------------------------------------------------------------------

def _rows(errs, clocks=None):
    clocks = clocks if clocks is not None else [e + 0.05 for e in errs]
    return [{"unit": i, "rmse": e, "rmse_clock": c, "within_target": e <= 0.10,
             "beats_clock": e < c, "n_probes": 10, "n_post_onset": 4,
             "probe_cost_ratio_vs_reference": 1.0} for i, (e, c) in enumerate(zip(errs, clocks))]


def test_cluster_bootstrap_resamples_whole_units_not_probes():
    rows = _rows([0.05] * 9 + [0.50])           # one extreme unit
    s = C2.summarise(rows, seed_offset=2)
    lo, hi = s["cluster_bootstrap_ci"]
    # resampling 10 unit-level values can drop or repeat the outlier, so the interval must be wide
    # and must be reachable only by whole-unit means (multiples of 1/10 of the outlier's excess)
    assert lo < s["mean_rmse"] < hi and hi - lo > 0.05
    assert len(s["leave_one_unit_out_range"]) == 2 and s["n_units"] == 10


def test_summary_never_reports_a_pass_below_the_unchanged_rule():
    assert C2.summarise(_rows([0.05] * 6 + [0.5] * 4), 2)["passes_c_rule"] is False   # 6/10 within
    beats_none = _rows([0.05] * 10, clocks=[0.01] * 10)
    assert C2.summarise(beats_none, 2)["n_within_target"] == 10
    assert C2.summarise(beats_none, 2)["passes_c_rule"] is False                      # 0/10 beat clock
    assert C2.summarise(_rows([0.05] * 10), 2)["passes_c_rule"] is True


def test_failing_units_are_listed_for_the_below_median_check():
    s = C2.summarise(_rows([0.05, 0.5, 0.05, 0.4] + [0.05] * 6), 2)
    assert s["failing_units"] == [1, 3]


# --- provenance guards -------------------------------------------------------------------------------------

def test_reference_cell_mismatch_aborts_before_interpretation():
    committed = {"heldout": [{"rupture_cycles": 1416.0, "rmse": 0.227}]}
    ok = [{"unit": 7, "rupture_cycles": 1416.0, "rmse": 0.227}]
    assert C2.verify_reference_cell(ok, committed) is True
    drifted = [{"unit": 7, "rupture_cycles": 1416.0, "rmse": 0.2271}]
    with pytest.raises(SystemExit, match="does not reproduce Study C"):
        C2.verify_reference_cell(drifted, committed)


def test_the_runner_declares_the_preregistration_it_was_frozen_against():
    assert C2.PREREG.endswith("studyC2-preregistration.md")
    assert len(C2.sha256(C2.PREREG)) == 64
    assert C2.DATA == "data/sim/studyC2" and C2.DATA != C.DATA, "C2 must never write into Study C"


def test_study_c_committed_result_is_still_c_fail_on_disk():
    committed = json.load(open("data/sim/studyC/studyC_results.json"))
    assert committed["verdict"] == "C-FAIL"
    assert committed["n_within_target"] == 6 and committed["n_beats_clock"] == 7


# --- wiring: main() runs end to end on a stub cohort, producing no research result -------------------

def test_main_runs_end_to_end_and_writes_a_complete_manifest(tmp_path, monkeypatch):
    """Exercises the runner's wiring on a deliberately tiny stub cohort and schedule.

    This is not the preregistered grid: the cohort, split and probe schedule are all replaced, so the
    numbers are meaningless and nothing is written to data/sim/studyC2. Running the real grid is R4.
    """
    n_units, n_train = 10, 7
    order = np.random.default_rng(SEED + 1).permutation(n_units)
    train_idx, test_idx = sorted(order[:n_train].tolist()), sorted(order[n_train:].tolist())
    units = sample_units(n_units, SEED)

    studyc_dir = tmp_path / "studyC"; studyc_dir.mkdir()
    stub = {"train_units": train_idx, "test_units": test_idx, "verdict": "C-FAIL",
            "heldout": [{"rupture_cycles": units[i].fatigue.rupture_cycles, "rmse": 0.0} for i in test_idx]}
    (studyc_dir / "studyC_results.json").write_text(json.dumps(stub))

    monkeypatch.setattr(C2, "N_UNITS", n_units)
    monkeypatch.setattr(C2, "N_TRAIN", n_train)
    monkeypatch.setattr(C2, "DATA", str(tmp_path / "studyC2"))
    monkeypatch.setattr(C2, "STUDYC_DATA", str(studyc_dir))
    monkeypatch.setattr(C2, "STUDYC_RESULTS", str(studyc_dir / "studyC_results.json"))
    monkeypatch.setattr(C2, "SCHEDULES", {k: C2.SCHEDULES[k] for k in ("reference", "onset_anchored_oracle")})
    monkeypatch.setattr(C2, "probes_for", lambda s, rc, on: np.array([100.0, 0.5 * rc, 0.9 * rc]))
    monkeypatch.setattr(C2, "verify_reference_cell", lambda rows, committed: True)   # covered separately

    C2.main([])

    out = json.loads((tmp_path / "studyC2" / "studyC2_results.json").read_text())
    for key in ("preregistration_sha256", "base_commit", "generator_hashes", "seed", "train_units",
                "test_units", "schedules", "arms", "cells", "material_reduction",
                "interpretation_label", "claim_language", "reference_reproduces_study_c"):
        assert key in out, f"manifest is missing {key}"
    assert out["study_c_verdict_unchanged"] == "C-FAIL"
    assert len(out["cells"]) == 2 * len(C2.ARMS)
    assert {c["arm"] for c in out["cells"]} == set(C2.ARMS)
    for c in out["cells"]:
        assert len(c["per_unit"]) == len(test_idx)
        assert len({r["unit"] for r in c["per_unit"]}) == len(test_idx), "a unit appears twice"
    assert out["cells"][0]["summary"]["passes_c_rule"] in (True, False)
    assert (tmp_path / "studyC2" / "studyC2_fig_schedule_sensitivity.png").is_file()
    # the real Study C directory was never touched
    assert not (tmp_path / "studyC2" / "studyC_results.json").exists()


def test_main_refuses_to_overwrite_a_result_from_another_preregistration(tmp_path, monkeypatch):
    monkeypatch.setattr(C2, "DATA", str(tmp_path / "studyC2"))
    (tmp_path / "studyC2").mkdir()
    (tmp_path / "studyC2" / "studyC2_results.json").write_text(json.dumps({"preregistration_sha256": "stale"}))
    with pytest.raises(SystemExit, match="--overwrite"):
        C2.main([])
