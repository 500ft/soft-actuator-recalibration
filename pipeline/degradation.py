"""Causal alarms and degradation-model fitting for Phase C."""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from scipy.optimize import least_squares
from scipy.special import expit


@dataclass(frozen=True)
class AlarmResult:
    alarm_index: int | None
    status: str
    statistic: float


@dataclass(frozen=True)
class CusumCalibration:
    threshold: float
    target_false_alarm_rate: float
    sustained_false_alarm_rate: float


@dataclass(frozen=True)
class DegradationFit:
    model: str
    parameters: tuple[float, ...]
    predicted: np.ndarray
    onset: float
    rss: float
    aicc: float
    status: str
    form_matched_ceiling: bool = False


def sustained_sigma_alarm(values, baseline_mean, baseline_std, sigma=3.0, consecutive=2):
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or values.size == 0 or not np.all(np.isfinite(values)):
        raise ValueError("values must be a nonempty finite one-dimensional array")
    if not np.isfinite(baseline_std) or baseline_std <= 0:
        return AlarmResult(None, "undefined_zero_baseline_sigma", float("nan"))
    threshold = baseline_mean + sigma * baseline_std
    run = 0
    for i, value in enumerate(values):
        run = run + 1 if value > threshold else 0
        if run >= consecutive:
            return AlarmResult(i, "alarm", float(value))
    return AlarmResult(None, "no_alarm", float(values[-1]))


def _cusum_max(values, reference):
    score = 0.0
    maximum = 0.0
    for value in values:
        score = max(0.0, score + float(value) - reference)
        maximum = max(maximum, score)
    return maximum


def cusum_alarm(values, reference, threshold):
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or values.size == 0 or not np.all(np.isfinite(values)):
        raise ValueError("values must be a nonempty finite one-dimensional array")
    if not np.isfinite(reference) or reference < 0 or not np.isfinite(threshold) or threshold <= 0:
        raise ValueError("reference must be nonnegative and threshold positive")
    score = 0.0
    for i, value in enumerate(values):
        score = max(0.0, score + float(value) - reference)
        if score > threshold:
            return AlarmResult(i, "alarm", score)
    return AlarmResult(None, "no_alarm", score)


def false_alarm_rate(trajectories, detector):
    trajectories = np.asarray(trajectories, dtype=float)
    if trajectories.ndim != 2 or trajectories.shape[0] == 0:
        raise ValueError("trajectories must be a nonempty 2D matrix")
    alarms = sum(detector(row).status == "alarm" for row in trajectories)
    return alarms / trajectories.shape[0]


def calibrate_cusum_to_sustained(null_trajectories, reference=0.5):
    """Match CUSUM family-wise FA to sustained-3σ on independent null paths."""
    paths = np.asarray(null_trajectories, dtype=float)
    if paths.ndim != 2 or paths.shape[0] < 10 or not np.all(np.isfinite(paths)):
        raise ValueError("null_trajectories must be a finite 2D matrix with >= 10 paths")
    sustained_fa = false_alarm_rate(
        paths, lambda row: sustained_sigma_alarm(row, baseline_mean=0, baseline_std=1)
    )
    resolution = 1.0 / (paths.shape[0] + 1)
    target = max(sustained_fa, resolution)
    maxima = np.array([_cusum_max(row, reference) for row in paths])
    threshold = float(np.quantile(maxima, 1.0 - target, method="higher"))
    if threshold <= 0:
        threshold = float(np.nextafter(0.0, 1.0))
    return CusumCalibration(threshold, target, sustained_fa)


def corrected_aic(n, k, rss):
    """Small-sample corrected AIC with an explicit global sample guard."""
    if n <= k + 1:
        return float("inf"), "undefined_insufficient_samples"
    if not np.isfinite(rss) or rss < 0:
        raise ValueError("rss must be finite and nonnegative")
    rss = max(float(rss), np.finfo(float).tiny)
    value = n * np.log(rss / n) + 2 * k + 2 * k * (k + 1) / (n - k - 1)
    return float(value), "ok"


def _fit_inputs(u, y):
    u = np.asarray(u, dtype=float)
    y = np.asarray(y, dtype=float)
    if u.ndim != 1 or y.ndim != 1 or u.size != y.size or u.size < 3:
        raise ValueError("u and y must be equal-length one-dimensional arrays")
    if not np.all(np.isfinite(u)) or not np.all(np.isfinite(y)) or np.any(np.diff(u) <= 0):
        raise ValueError("u and y must be finite and u strictly increasing")
    return u, y


def _undefined_fit(model, n, k, status):
    return DegradationFit(
        model, tuple(), np.full(n, np.nan), float("nan"), float("nan"),
        float("inf"), status, model == "segmented_quadratic"
    )


def fit_linear(u, y):
    u, y = _fit_inputs(u, y)
    design = np.column_stack([np.ones_like(u), u])
    beta, *_ = np.linalg.lstsq(design, y, rcond=None)
    predicted = design @ beta
    rss = float(np.sum((y - predicted) ** 2))
    score, status = corrected_aic(u.size, 2, rss)
    return DegradationFit("linear", tuple(beta), predicted, float("nan"), rss, score, status)


def fit_segmented_quadratic(u, y, onset_bounds=(0.30, 0.90), min_side=3):
    u, y = _fit_inputs(u, y)
    if u.size <= 5:
        return _undefined_fit("segmented_quadratic", u.size, 4,
                              "undefined_insufficient_breakpoint_support")
    candidates = np.linspace(onset_bounds[0], onset_bounds[1], 241)
    best = None
    for onset in candidates:
        if np.count_nonzero(u < onset) < min_side or np.count_nonzero(u > onset) < min_side:
            continue
        hinge = np.maximum(0.0, u - onset) ** 2
        design = np.column_stack([np.ones_like(u), u, hinge])
        beta, *_ = np.linalg.lstsq(design, y, rcond=None)
        predicted = design @ beta
        rss = float(np.sum((y - predicted) ** 2))
        if best is None or rss < best[0]:
            best = (rss, onset, beta, predicted)
    if best is None:
        return _undefined_fit("segmented_quadratic", u.size, 4,
                              "undefined_insufficient_breakpoint_support")
    rss, onset, beta, predicted = best
    score, status = corrected_aic(u.size, 4, rss)
    return DegradationFit(
        "segmented_quadratic", tuple(beta) + (float(onset),), predicted,
        float(onset), rss, score, status, True
    )


def fit_logistic(u, y):
    u, y = _fit_inputs(u, y)
    if u.size <= 5:
        return _undefined_fit("logistic", u.size, 4, "undefined_insufficient_samples")

    def model(p):
        return p[0] + p[1] * expit(p[2] * (u - p[3]))

    span = max(float(np.ptp(y)), np.finfo(float).eps)
    initial = np.array([float(y.min()), span, 10.0, 0.70])
    fit = least_squares(
        lambda p: model(p) - y,
        initial,
        bounds=([-np.inf, 0.0, 0.1, 0.05], [np.inf, np.inf, 200.0, 0.95]),
        max_nfev=20_000,
    )
    if not fit.success:
        return _undefined_fit("logistic", u.size, 4, "fit_failed")
    predicted = model(fit.x)
    rss = float(np.sum((y - predicted) ** 2))
    score, status = corrected_aic(u.size, 4, rss)
    return DegradationFit(
        "logistic", tuple(fit.x), predicted, float(fit.x[3]), rss, score, status
    )


def fit_double_logistic(u, y):
    u, y = _fit_inputs(u, y)
    if u.size <= 8:  # k=7 requires n > k+1
        return _undefined_fit("double_logistic", u.size, 7,
                              "undefined_insufficient_samples")

    def model(p):
        return (
            p[0]
            + p[1] * expit(p[2] * (u - p[3]))
            + p[4] * expit(p[5] * (u - p[6]))
        )

    span = max(float(np.ptp(y)), np.finfo(float).eps)
    initial = np.array([float(y.min()), 0.3 * span, 10.0, 0.35,
                        0.7 * span, 10.0, 0.75])
    fit = least_squares(
        lambda p: model(p) - y,
        initial,
        bounds=(
            [-np.inf, 0, 0.1, 0.02, 0, 0.1, 0.05],
            [np.inf, np.inf, 200, 0.90, np.inf, 200, 0.98],
        ),
        max_nfev=40_000,
    )
    if not fit.success:
        return _undefined_fit("double_logistic", u.size, 7, "fit_failed")
    predicted = model(fit.x)
    rss = float(np.sum((y - predicted) ** 2))
    score, status = corrected_aic(u.size, 7, rss)
    onset = float(max(fit.x[3], fit.x[6]))
    return DegradationFit(
        "double_logistic", tuple(fit.x), predicted, onset, rss, score, status
    )


def predict_fit(fit: DegradationFit, u):
    """Evaluate a successful fitted model on new normalized-life points."""
    if fit.status != "ok":
        return np.full(np.asarray(u).shape, np.nan)
    u = np.asarray(u, dtype=float)
    p = fit.parameters
    if fit.model == "linear":
        return p[0] + p[1] * u
    if fit.model == "segmented_quadratic":
        onset = p[3]
        return p[0] + p[1] * u + p[2] * np.maximum(0.0, u - onset) ** 2
    if fit.model == "logistic":
        return p[0] + p[1] * expit(p[2] * (u - p[3]))
    if fit.model == "double_logistic":
        return p[0] + p[1] * expit(p[2] * (u - p[3])) + p[4] * expit(p[5] * (u - p[6]))
    raise ValueError(f"unknown fitted model: {fit.model}")


FITTERS = {
    "linear": fit_linear,
    "segmented_quadratic": fit_segmented_quadratic,
    "logistic": fit_logistic,
    "double_logistic": fit_double_logistic,
}


def fit_all_models(u, y):
    return {name: fit(u, y) for name, fit in FITTERS.items()}


def chronological_forecast(fitter, u, y, train_fraction=0.80, min_holdout=2):
    """Fit on the chronological prefix and score the final held-out observations."""
    u, y = _fit_inputs(u, y)
    holdout = max(min_holdout, int(np.ceil((1 - train_fraction) * u.size)))
    if u.size - holdout < 3:
        return float("nan"), "undefined_insufficient_training_samples"
    split = u.size - holdout
    fit = fitter(u[:split], y[:split])
    if fit.status != "ok":
        return float("nan"), fit.status
    predicted = predict_fit(fit, u[split:])
    return float(np.sqrt(np.mean((predicted - y[split:]) ** 2))), "ok"


def roc_auc(scores, labels):
    """ROC AUC via pairwise/rank interpretation; no sklearn dependency."""
    scores = np.asarray(scores, dtype=float)
    labels = np.asarray(labels, dtype=bool)
    if scores.ndim != 1 or labels.ndim != 1 or scores.size != labels.size:
        raise ValueError("scores and labels must be equal-length one-dimensional arrays")
    positive = scores[labels]
    negative = scores[~labels]
    if positive.size == 0 or negative.size == 0:
        return float("nan")
    comparisons = positive[:, None] - negative[None, :]
    return float((np.count_nonzero(comparisons > 0) + 0.5 * np.count_nonzero(comparisons == 0))
                 / comparisons.size)
