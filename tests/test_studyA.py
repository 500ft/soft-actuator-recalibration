"""Study A metric and verdict logic on hand-built cases."""
import numpy as np

from scripts.run_studyA import LIFE, spread_metrics, verdict


def test_spread_metrics_on_a_hand_built_case():
    rng = np.random.default_rng(0)
    units = np.array([1.0, 2.0, 3.0])[:, None, None]                   # three unit levels
    h = units + 0.01 * rng.standard_normal((3, 2, 50))                 # tiny within-unit noise
    m = spread_metrics(h)
    assert np.allclose(m["sd_between"], 1.0, atol=0.01)
    assert np.all(m["ratio"] > 50) and np.all(m["icc"] > 0.99)
    same = np.ones((3, 2, 50)) + 0.01 * rng.standard_normal((3, 2, 50))  # no between-unit signal
    assert np.median(spread_metrics(same)["icc"]) < 0.5


def test_verdict_rules():
    n = len(LIFE)
    good = (np.full(n, 5.0), np.full(n, 0.9))
    assert verdict(0.0, *good, 0.2) == "A-DEGENERATE"
    assert verdict(0.1, *good, 0.2) == "A-PASS"
    assert verdict(0.1, *good, 0.05) == "A-FAIL"
    assert verdict(0.1, np.full(n, 1.0), np.full(n, 0.9), 0.2) == "A-FAIL"
    assert verdict(0.1, *good, 0.05, amended=True) == "A-PASS"
    assert verdict(0.1, np.full(n, 1.0), np.full(n, 0.9), 0.2, amended=True) == "A-FAIL"

