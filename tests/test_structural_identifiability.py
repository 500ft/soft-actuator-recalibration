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

def test_a_profile_flat_everywhere_is_structural():
    v, flat = profile_verdict(_profile(np.linspace(0.1, 0.9, 9), np.zeros(9)))
    assert v == "structural" and flat == 1.0


def test_a_profile_rising_on_both_sides_is_identifiable():
    d = np.array([9.0, 4.0, 1.0, 0.0, 1.0, 4.0, 9.0])
    v, flat = profile_verdict(_profile(np.linspace(0.2, 0.8, 7), d))
    assert v == "identifiable" and flat < 1.0


def test_a_profile_rising_on_one_side_only_is_practical():
    d = np.array([0.0, 0.0, 0.0, 0.2, 1.0, 4.0, 9.0])        # flat to the left, rises to the right
    assert profile_verdict(_profile(np.linspace(0.2, 0.8, 7), d))[0] == "practical"


def test_the_threshold_is_the_chi_square_cut_and_is_respected():
    d = np.array([1.5, 0.0, 1.5])                            # below 1.92 on both sides
    assert profile_verdict(_profile([0.3, 0.5, 0.7], d))[0] == "structural"
    assert profile_verdict(_profile([0.3, 0.5, 0.7], d), threshold=1.0)[0] == "identifiable"


def test_flat_fraction_reports_how_much_of_the_grid_is_unconstrained():
    d = np.array([0.0, 0.0, 0.0, 0.0, 5.0])
    v, flat = profile_verdict(_profile(np.linspace(0.1, 0.9, 5), d))
    assert v == "practical" and flat == pytest.approx(0.8)
