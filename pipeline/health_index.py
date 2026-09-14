"""Causal baseline normalization and transparent health-index comparators."""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class BaselineModel:
    names: tuple[str, ...]
    mean: np.ndarray
    scale: np.ndarray
    directions: np.ndarray
    noise_free: bool


@dataclass(frozen=True)
class PCAModel:
    mean: np.ndarray
    component: np.ndarray


def fit_baseline(values, names, directions, noise_free=False) -> BaselineModel:
    values = np.asarray(values, dtype=float)
    directions = np.asarray(directions, dtype=float)
    names = tuple(names)
    if values.ndim != 2 or values.shape[0] < 1 or values.shape[1] != len(names):
        raise ValueError("baseline must be a 2D matrix matching names")
    if directions.shape != (values.shape[1],) or np.any(~np.isin(directions, [-1, 1])):
        raise ValueError("directions must contain one +1/-1 value per feature")
    if not np.all(np.isfinite(values)):
        raise ValueError("baseline values must be finite")
    mean = values.mean(axis=0)
    if noise_free:
        scale = np.abs(mean)
        if np.any(scale == 0):
            raise ValueError("noise-free fractional normalization requires nonzero baselines")
    else:
        if values.shape[0] < 2:
            raise ValueError("noisy baseline fitting requires at least two repeats")
        scale = values.std(axis=0, ddof=1)
        if np.any(scale <= np.finfo(float).eps * np.maximum(np.abs(mean), 1.0)):
            raise ValueError("noisy baseline has zero variance; do not manufacture a sigma floor")
    return BaselineModel(names, mean.copy(), scale.copy(), directions.copy(), bool(noise_free))


def transform_features(values, model: BaselineModel):
    values = np.asarray(values, dtype=float)
    if values.ndim == 1:
        values = values[None, :]
    if values.ndim != 2 or values.shape[1] != len(model.names):
        raise ValueError("feature matrix does not match fitted baseline")
    if not np.all(np.isfinite(values)):
        raise ValueError("feature values must be finite")
    return (values - model.mean) / model.scale * model.directions


def fused_hi(transformed):
    transformed = np.asarray(transformed, dtype=float)
    if transformed.ndim != 2 or transformed.shape[1] == 0:
        raise ValueError("transformed features must be a nonempty 2D matrix")
    return transformed.mean(axis=1)


def fit_baseline_pca(vectors) -> PCAModel:
    vectors = np.asarray(vectors, dtype=float)
    if vectors.ndim != 2 or vectors.shape[0] < 2 or vectors.shape[1] < 2:
        raise ValueError("PCA baseline must contain at least two vectors and dimensions")
    if not np.all(np.isfinite(vectors)):
        raise ValueError("PCA baseline must be finite")
    mean = vectors.mean(axis=0)
    _, _, vt = np.linalg.svd(vectors - mean, full_matrices=False)
    component = vt[0].copy()
    largest = int(np.argmax(np.abs(component)))
    if component[largest] < 0:
        component *= -1
    return PCAModel(mean.copy(), component)


def pca_scores(vectors, model: PCAModel):
    vectors = np.asarray(vectors, dtype=float)
    if vectors.ndim == 1:
        vectors = vectors[None, :]
    if vectors.ndim != 2 or vectors.shape[1] != model.mean.size:
        raise ValueError("PCA vectors do not match fitted baseline shape")
    return (vectors - model.mean) @ model.component
