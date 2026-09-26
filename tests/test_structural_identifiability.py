"""Brun collinearity index and profile-likelihood classification, on analytic cases."""
import numpy as np
import pytest

from pipeline.identifiability import (COLLINEARITY_POOR, collinearity_index, normalised_sensitivities,
                                      profile_verdict)


def _profile(us, ds):
    return [{"u": u, "delta_nll": d, "nll": d} for u, d in zip(us, ds)]


# --- Brun's collinearity index -------------------------------------------------------------------

def test_orthogonal_sensitivities_give_gamma_one():
    J = np.array([[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]])
    assert collinearity_index(J, np.eye(3), [0, 1]) == pytest.approx(1.0)


def test_perfectly_collinear_columns_give_infinite_gamma():
    J = np.array([[1.0, 2.0], [2.0, 4.0], [3.0, 6.0]])      # column 1 = 2 x column 0
    assert collinearity_index(J, np.eye(3), [0, 1]) == float("inf")


def test_gamma_rises_as_two_sensitivities_align():
    prev = 0.0
    for angle in (np.pi / 2, np.pi / 4, np.pi / 12, np.pi / 60):
        J = np.array([[1.0, np.cos(angle)], [0.0, np.sin(angle)], [0.0, 0.0]])
        g = collinearity_index(J, np.eye(3), [0, 1])
        assert g > prev, "gamma must increase as the directions align"
        prev = g
    assert prev > COLLINEARITY_POOR, "near-parallel sensitivities must exceed the poor-identifiability flag"


def test_a_parameter_with_no_sensitivity_makes_the_subset_undefined():
    J = np.array([[1.0, 0.0], [2.0, 0.0], [3.0, 0.0]])       # second parameter does nothing
    assert collinearity_index(J, np.eye(3), [0, 1]) == float("inf")
    # ...but the subset containing only the responsive parameter is fine
    assert collinearity_index(J, np.eye(3), [0]) == pytest.approx(1.0)


def test_index_scores_subsets_not_just_pairs():
    """Three parameters, pairwise near-orthogonal but jointly dependent (c = a + b)."""
    J = np.array([[1.0, 0.0, 1.0], [0.0, 1.0, 1.0], [0.0, 0.0, 0.0]])
    pairwise = max(collinearity_index(J, np.eye(3), s) for s in ([0, 1], [0, 2], [1, 2]))
    triple = collinearity_index(J, np.eye(3), [0, 1, 2])
    # an exactly singular subset lands on a huge finite number rather than inf, because the smallest
    # eigenvalue is ~1e-17 rather than exactly zero; either way it is orders above the poor flag
    assert triple > 1e6 and pairwise < 10 * COLLINEARITY_POOR
    # this is exactly why a subset index is needed: no pair reveals the dependency


def test_normalisation_makes_the_index_scale_free():
    J = np.array([[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]])
    scaled = J * np.array([1.0, 1e6])                        # one parameter in different units
    assert collinearity_index(J, np.eye(3), [0, 1]) == pytest.approx(
        collinearity_index(scaled, np.eye(3), [0, 1]))
    S, norms = normalised_sensitivities(J, np.eye(3))
    assert np.allclose(np.linalg.norm(S, axis=0), 1.0) and norms[0] > 0


def test_whitening_uses_the_noise_covariance():
    J = np.array([[1.0, 1.0], [1.0, -1.0]])
    tight = collinearity_index(J, np.diag([1.0, 1e-6]), [0, 1])   # second feature far more precise
    even = collinearity_index(J, np.eye(2), [0, 1])
    assert not np.isclose(tight, even), "the covariance must change the answer"


# --- profile-likelihood classification -------------------------------------------------------------

def test_a_profile_flat_everywhere_over_the_whole_domain_is_structural():
    """Flat AND exhaustive. Without the domain the same numbers are only domain-limited."""
    prof = _profile(np.linspace(0.1, 0.9, 9), np.zeros(9))
    v, flat = profile_verdict(prof, domain=(0.1, 0.9))
    assert v == "structural" and flat == 1.0
    assert profile_verdict(prof)[0] == "domain-limited", "an undeclared domain cannot license 'structural'"


def test_a_profile_rising_on_both_sides_is_identifiable():
    d = np.array([9.0, 4.0, 1.0, 0.0, 1.0, 4.0, 9.0])
    v, flat = profile_verdict(_profile(np.linspace(0.2, 0.8, 7), d))
    assert v == "identifiable" and flat < 1.0


def test_a_profile_rising_on_one_side_only_is_practical():
    d = np.array([0.0, 0.0, 0.0, 0.2, 1.0, 4.0, 9.0])        # flat to the left, rises to the right
    prof = _profile(np.linspace(0.2, 0.8, 7), d)
    # the flat side runs down to the physical floor, so there is nothing left to search
    assert profile_verdict(prof, domain=(0.2, 1.0))[0] == "practical"
    # the same profile on a grid that stopped short of the floor is merely untested there
    assert profile_verdict(prof, domain=(0.02, 1.0))[0] == "domain-limited"


def test_the_threshold_is_the_chi_square_cut_and_is_respected():
    d = np.array([1.5, 0.0, 1.5])                            # below 1.92 on both sides
    dom = {"domain": (0.3, 0.7)}
    assert profile_verdict(_profile([0.3, 0.5, 0.7], d), **dom)[0] == "structural"
    assert profile_verdict(_profile([0.3, 0.5, 0.7], d), threshold=1.0, **dom)[0] == "identifiable"


def test_flat_fraction_reports_how_much_of_the_grid_is_unconstrained():
    d = np.array([0.0, 0.0, 0.0, 0.0, 5.0])
    v, flat = profile_verdict(_profile(np.linspace(0.1, 0.9, 5), d), domain=(0.1, 0.9))
    assert v == "practical" and flat == pytest.approx(0.8)


# --- B1 vs B2 design, open bounds, convergence gating (2026-09-24 repair) --------------------------

def _prof(us, ds, converged=True):
    return [{"u": u, "delta_nll": d, "nll": d, "converged": converged} for u, d in zip(us, ds)]


def test_b2_consumes_ten_observations_and_b1_five():
    from pipeline.identifiability import neg_log_likelihood
    from scripts.run_studyB import theta_of
    from sim.fatigue import FatigueParams
    from sim.plant import SLSParams
    unit = type("U", (), {"fatigue": FatigueParams(), "sls": SLSParams()})()
    th = theta_of(unit, 0.9)
    # B1: five features
    assert np.isfinite(neg_log_likelihood(th, np.zeros(5), np.eye(5), unit.fatigue, unit.sls))
    with pytest.raises(ValueError, match="B2 .* needs 10"):
        neg_log_likelihood(th, np.zeros(5), np.eye(5), unit.fatigue, unit.sls, 0.1, u_base=0.05)
    # B2: ten
    assert np.isfinite(neg_log_likelihood(th, np.zeros(10), np.eye(10), unit.fatigue, unit.sls,
                                          0.1, u_base=0.05))
    with pytest.raises(ValueError, match="B1 .* needs 5"):
        neg_log_likelihood(th, np.zeros(10), np.eye(10), unit.fatigue, unit.sls)


def test_perturbing_the_baseline_changes_the_b2_likelihood():
    """If the baseline term were ignored, u_base could not matter. It must."""
    from pipeline.identifiability import neg_log_likelihood
    from scripts.run_studyB import theta_of
    from sim.fatigue import FatigueParams
    from sim.plant import SLSParams
    unit = type("U", (), {"fatigue": FatigueParams(), "sls": SLSParams()})()
    th = theta_of(unit, 0.9)
    y, si = np.zeros(10), np.eye(10)
    a = neg_log_likelihood(th, y, si, unit.fatigue, unit.sls, 0.1, u_base=0.05)
    b = neg_log_likelihood(th, y, si, unit.fatigue, unit.sls, 0.1, u_base=0.40)
    assert a != b, "the baseline observation must enter the likelihood"


def test_an_unconverged_point_makes_the_verdict_unresolved():
    from pipeline.identifiability import profile_verdict as pv
    d = [9.0, 1.0, 0.0, 1.0, 9.0]
    assert pv(_prof(np.linspace(0.2, 0.8, 5), d))[0] == "identifiable"
    bad = _prof(np.linspace(0.2, 0.8, 5), d)
    bad[1]["converged"] = False
    assert pv(bad)[0] == "unresolved", "a solver failure must not be read as a shape"
    assert pv(bad, require_converged=False)[0] == "identifiable"


def test_a_profile_that_never_crosses_on_one_side_is_domain_limited_not_practical():
    from pipeline.identifiability import profile_verdict as pv
    d = [9.0, 4.0, 0.0, 0.0, 0.0]          # rises left, flat to the grid edge on the right
    assert pv(_prof(np.linspace(0.5, 0.9, 5), d))[0] == "domain-limited"


def test_an_open_bound_is_never_reported_as_a_half_width():
    from pipeline.identifiability import profile_interval
    d = [9.0, 4.0, 0.0, 0.0, 0.0]
    iv = profile_interval(_prof([0.5, 0.6, 0.7, 0.8, 0.9], d))
    assert iv["upper_open"] is True and iv["upper"] is None
    assert iv["lower_open"] is False and iv["lower"] == 0.6
    assert iv["grid_max"] == 0.9
    closed = profile_interval(_prof([0.5, 0.6, 0.7, 0.8, 0.9], [9.0, 4.0, 0.0, 4.0, 9.0]))
    assert closed["lower"] == 0.6 and closed["upper"] == 0.8
    assert not closed["lower_open"] and not closed["upper_open"]


def test_a_weakly_identifiable_toy_profile_is_not_called_structural():
    """Acceptance criterion: staying below the threshold on a short grid is not a structural claim."""
    from pipeline.identifiability import profile_verdict as pv
    shallow = _prof(np.linspace(0.45, 0.55, 5), [0.4, 0.1, 0.0, 0.1, 0.4])   # flat, but barely sampled
    assert pv(shallow, domain=(0.02, 0.98))[0] == "domain-limited", (
        "a flat profile on a narrow grid is an untested region, not a structural direction")
    # widening the grid on the same model finds the curvature that was always there
    wide = _prof(np.linspace(0.02, 0.98, 9), [12.0, 9.0, 2.5, 0.4, 0.0, 0.4, 2.5, 9.0, 12.0])
    assert pv(wide, domain=(0.02, 0.98))[0] == "identifiable"


# --- whitening without inverting an ill-conditioned covariance ------------------------------------

def test_whitening_reproduces_the_quadratic_form_and_leaves_identity_alone():
    from pipeline.identifiability import whiten
    rng = np.random.default_rng(0)
    A = rng.normal(size=(4, 4))
    S = A @ A.T + 4 * np.eye(4)                     # well conditioned, so the naive form is trustworthy
    r = rng.normal(size=4)
    z = whiten(S, r)
    assert z @ z == pytest.approx(r @ np.linalg.inv(S) @ r, rel=1e-10)
    assert np.allclose(whiten(np.eye(3), np.array([1.0, 2.0, 3.0])), [1.0, 2.0, 3.0])
    J = rng.normal(size=(4, 2))                      # the Jacobian form must agree column by column
    assert np.allclose(whiten(S, J), np.column_stack([whiten(S, J[:, k]) for k in range(2)]))


def test_whitening_survives_the_feature_scale_spread_that_breaks_a_direct_inverse():
    """The real covariance mixes 1e-2 loop areas with a 1e11 stiffness: cond(Sigma) ~ 1e26."""
    from pipeline.identifiability import whiten
    rng = np.random.default_rng(1)
    d = np.array([6e-6, 9e-6, 6e7, 9e-4, 1.5e-3])    # the measured standard deviations, in order
    A = rng.normal(size=(5, 5)) * 0.25
    corr = A @ A.T
    corr /= np.sqrt(np.outer(np.diag(corr), np.diag(corr)))
    S = corr * np.outer(d, d)
    assert np.linalg.cond(S) > 1e20, "this test is pointless unless Sigma really is that ill-conditioned"
    assert np.linalg.cond(corr) < 50, "the conditioning must be scale, which is what makes it fixable"
    r = d * rng.normal(size=5)                       # a residual of the same scale as the noise
    z = whiten(S, r)
    assert np.isfinite(z).all()
    # the whitened residual is O(1) per feature regardless of the raw units
    assert 1e-3 < np.linalg.norm(z) < 1e3
    # a constant (zero-variance) feature is refused rather than silently producing NaN
    bad = S.copy(); bad[2, :] = 0.0; bad[:, 2] = 0.0
    with pytest.raises(ValueError, match="non-positive"):
        whiten(bad, r)


def test_an_undefined_prediction_is_infeasible_rather_than_a_crash_or_a_silent_nan():
    """operational_half_life is nan at low leak, so the feature vector is undefined on part of the box."""
    from pipeline.identifiability import neg_log_likelihood, features
    from scripts.run_studyB import theta_of
    from scripts.run_studyB_structural import bounds_for
    from sim.fatigue import FatigueParams
    from sim.plant import SLSParams
    unit = type("U", (), {"fatigue": FatigueParams(), "sls": SLSParams()})()
    th = theta_of(unit, 0.90)
    lo = [b[0] for b in bounds_for(th)]
    bad = th.copy()
    bad[1:] = [lo[1], lo[2], lo[3], lo[4], lo[5], lo[6]]   # the soft, fast, leak-free corner of the box
    assert not np.all(np.isfinite(features(bad, unit.fatigue, unit.sls, 0.1))), (
        "this test needs a genuinely undefined point; the feature definitions must have changed")
    v = neg_log_likelihood(bad, np.zeros(5), np.eye(5), unit.fatigue, unit.sls)
    assert v == float("inf"), "an undefined prediction must be infinitely bad, not nan and not a number"
    good = neg_log_likelihood(th, np.zeros(5), np.eye(5), unit.fatigue, unit.sls)
    assert np.isfinite(good)


# --- strict JSON, subset status, bound-flagged intervals (2026-09-25 closeout) ---------------------

def test_json_safe_makes_the_output_rfc8259_valid():
    """json.dump emits bare Infinity/NaN, which strict parsers reject. default= never fires for floats."""
    import json
    from pipeline.identifiability import json_safe
    raw = {"a": float("inf"), "b": [float("nan"), 1.5], "c": {"d": np.float64("-inf")},
           "e": np.int64(3), "f": np.bool_(True)}
    with pytest.raises(ValueError):
        json.dumps(raw, allow_nan=False)                 # the bug this guards against
    safe = json_safe(raw)
    text = json.dumps(safe, allow_nan=False)             # must not raise
    assert "Infinity" not in text and "NaN" not in text
    # and a strict reader round-trips it
    back = json.loads(text, parse_constant=lambda c: pytest.fail(f"non-standard token {c}"))
    assert back == {"a": None, "b": [None, 1.5], "c": {"d": None}, "e": 3, "f": True}


def test_the_committed_study_b_artifact_parses_strictly():
    import json, pathlib
    p = pathlib.Path("data/sim/studyB/studyB_structural.json")
    if not p.exists():                                   # pragma: no cover
        pytest.skip("artifact not generated in this checkout")
    raw = p.read_text()
    assert "Infinity" not in raw and "NaN" not in raw, "evidence must be readable outside Python"
    json.loads(raw, parse_constant=lambda c: pytest.fail(f"non-standard token {c}"))


def test_a_singular_subset_reports_its_status_instead_of_a_magnitude():
    """all_seven moved 6.5e7 -> 8.3e7 under a numerically BETTER whitening: it is float64 noise."""
    from pipeline.identifiability import collinearity_report
    J = np.array([[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]])
    assert collinearity_report(J, np.eye(3), [0, 1])[:2] == (1.0, "finite")
    # a member with no sensitivity is irrelevant here, not confounded
    inert = np.array([[1.0, 0.0], [2.0, 0.0], [3.0, 0.0]])
    v, st, who = collinearity_report(inert, np.eye(3), [0, 1], ("u", "dead"))
    assert v is None and st == "undefined_inert_parameter" and who == ["dead"]
    # an exactly dependent subset yields no number at all, rather than a huge one
    dep = np.array([[1.0, 0.0, 1.0], [0.0, 1.0, 1.0], [0.0, 0.0, 0.0]])
    v, st, _ = collinearity_report(dep, np.eye(3), [0, 1, 2])
    assert v is None and st == "numerically_singular"


def test_the_interval_flags_a_crossing_that_sits_on_a_nuisance_bound():
    """A crossing where the nuisance fit is pinned may be the box talking, not the data."""
    from pipeline.identifiability import profile_interval
    prof = [{"u": u, "nll": n, "delta_nll": n, "at_bound": ab} for u, n, ab in
            [(0.5, 9.0, [False]), (0.6, 4.0, [False]), (0.7, 0.0, [False]),
             (0.8, 0.0, [False]), (0.9, 5.0, [True])]]
    iv = profile_interval(prof)
    assert iv["lower"] == 0.6 and iv["upper"] == 0.9
    assert iv["lower_at_nuisance_bound"] is False
    assert iv["upper_at_nuisance_bound"] is True, "a pinned crossing must be visible in the record"


def test_the_plateau_spread_exposes_an_interval_the_profile_never_resolves_within():
    """A spread far below the threshold means the interval is ignorance, not precision."""
    from pipeline.identifiability import profile_interval
    flat = [{"u": u, "nll": n, "delta_nll": n, "at_bound": []} for u, n in
            [(0.5, 9.0), (0.7, 0.0), (0.8, 5e-10), (0.9, 3e-10), (0.98, 9.0)]]
    assert profile_interval(flat)["plateau_nll_spread"] < 1e-8
    real = [{"u": u, "nll": n, "delta_nll": n, "at_bound": []} for u, n in
            [(0.5, 9.0), (0.7, 0.0), (0.8, 0.9), (0.9, 1.5), (0.98, 9.0)]]
    assert profile_interval(real)["plateau_nll_spread"] > 1.0


def test_a_bound_pinned_or_bound_movable_crossing_cannot_yield_a_resolution():
    """The closeout finding: the post-onset upper crossing vanished when the nuisance box was widened.

    Guards the rule, not the number: a half-width may only be quoted from an interval whose terminations
    are the data's, so a pinned termination, a crossing that moves with the box, or a plateau far below
    the threshold each disqualify it. This is the third bounding artefact in the same region, after a
    rank test and a grid edge.
    """
    from pipeline.identifiability import profile_interval
    CUT = 1.92
    def disqualified(iv, sens):
        spread = iv.get("plateau_nll_spread")
        return bool(iv["lower_open"] or iv["upper_open"]
                    or iv.get("lower_at_nuisance_bound") or iv.get("upper_at_nuisance_bound")
                    or (sens and sens.get("crossing_moved"))
                    or (spread is not None and spread < 0.1 * CUT))

    pinned = profile_interval([{"u": u, "nll": n, "delta_nll": n, "at_bound": ab} for u, n, ab in
                               [(0.5, 9.0, [True]), (0.7, 0.0, [False]), (0.9, 9.0, [True])]])
    assert disqualified(pinned, None), "a crossing sitting on a bound must block a half-width"

    clean = [{"u": u, "nll": n, "delta_nll": n, "at_bound": [False]} for u, n in
             [(0.5, 9.0), (0.6, 0.9), (0.7, 0.0), (0.8, 0.9), (0.9, 9.0)]]
    iv = profile_interval(clean)
    assert not disqualified(iv, {"crossing_moved": False}), "a clean, curved interval must be usable"
    assert disqualified(iv, {"crossing_moved": True}), "a crossing that moves with the box must block it"

    flat = profile_interval([{"u": u, "nll": n, "delta_nll": n, "at_bound": [False]} for u, n in
                             [(0.5, 9.0), (0.7, 0.0), (0.8, 4e-10), (0.9, 6e-10), (0.98, 9.0)]])
    assert disqualified(flat, None), "a plateau nine orders below the cut is ignorance, not precision"
