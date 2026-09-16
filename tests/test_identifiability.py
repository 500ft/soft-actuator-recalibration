"""Study B information tools on analytic cases."""
import numpy as np

from pipeline.identifiability import bound_u, crlb_u, fim, whitened_angles_deg


def test_fim_matches_linear_gaussian_analytic_value():
    J = np.array([[2.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    sigma = np.diag([1.0, 4.0, 0.25])
    F = fim(J, sigma)
    expected = J.T @ np.diag(1 / np.diag(sigma)) @ J
    assert np.allclose(F, expected)
    s, rank = crlb_u(F)
    assert rank == 2 and np.isclose(s, np.sqrt(np.linalg.inv(expected)[0, 0]))


def test_singular_information_is_reported_not_inverted():
    J = np.array([[1.0, 2.0], [2.0, 4.0], [3.0, 6.0]])          # columns proportional
    s, rank = crlb_u(fim(J, np.eye(3)))
    assert rank == 1 and s == float("inf")


def test_whitened_angle_of_orthogonal_pair_is_ninety_degrees():
    J = np.array([[1.0, 0.0], [0.0, 1.0]])
    assert np.isclose(whitened_angles_deg(J, np.eye(2))[0], 90.0)
    J2 = np.array([[1.0, 1.0], [0.0, 0.0]])
    assert np.isclose(whitened_angles_deg(J2 + 1e-12 * np.eye(2), np.eye(2))[0], 0.0, atol=1e-4)


def test_irrelevant_parameter_does_not_block_the_bound():
    J = np.array([[1.0, 0.0, 0.5], [0.5, 0.0, 1.0], [0.2, 0.0, 0.1]])   # middle parameter has no effect
    s, rank, n_active, u_active = bound_u(J, np.eye(3))
    assert u_active and n_active == 2 and rank == 2 and np.isfinite(s)
