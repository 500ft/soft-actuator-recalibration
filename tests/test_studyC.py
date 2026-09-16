"""Study C estimator plumbing on hand-built data."""
import numpy as np

from scripts.run_studyC import choose_lambda, ridge_fit, ridge_predict, rmse


def test_ridge_recovers_a_linear_target_and_loo_picks_the_smallest_lambda():
    rng = np.random.default_rng(0)
    units = []
    for _ in range(6):
        X = rng.standard_normal((8, 3))
        y = X @ np.array([1.0, -2.0, 0.5]) + 3.0
        units.append([{"x": x, "u": float(t)} for x, t in zip(X, y)])
    X, y = np.vstack([r["x"] for u in units for r in u]), np.array([r["u"] for u in units for r in u])
    m = ridge_fit(X, y, 0.01)
    assert rmse(ridge_predict(m, X), y) < 0.05
    lam, scores = choose_lambda(units)
    assert lam == 0.01 and scores[0.01] < scores[1.0]
