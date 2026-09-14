"""Phase D — fatigue-coupled piecewise-constant-curvature (PCC) kinematics.

Maps a realized chamber pressure together with the Phase-B fatigue state to a bending
curvature, and the curvature to the tip SE(3) pose of one constant-curvature soft segment.

The laws are deliberately transparent, deterministic, and analytically invertible so that
the noise-free pose is recoverable *exactly* — this is the Phase-D kinematics gate
(``tests/test_kinematics.py``). They are modelling choices for a synthetic study, not a
calibrated model of a physical actuator.

Pressure -> curvature
---------------------
A soft bending actuator curves more, per unit pressure, as its walls soften. We tie the
bending compliance to the Phase-B ``compliance_multiplier`` (>= 1, growing with life; see
``sim.fatigue``):

    kappa = kappa_gain * compliance_multiplier * max(P - P_threshold, 0)      [1/m]

so fatigue *amplifies* curvature at a fixed pressure — the curvature drift this study
tracks. The bending-plane azimuth ``phi`` is a fixed per-actuator property.

PCC forward map (Webster & Jones 2010 robot-independent convention)
-------------------------------------------------------------------
A backbone of arc length ``L`` leaves the base along +z. With bend angle
``theta = kappa * L``:

    p(kappa, phi, L) = (1/kappa) * [ (1 - cos theta) cos phi,
                                     (1 - cos theta) sin phi,
                                     sin theta ]                      (kappa > 0)
    R(kappa, phi, L) = Rz(phi) @ Ry(theta) @ Rz(-phi)

Limit kappa -> 0:  p -> [0, 0, L],  R -> I  (a straight segment).

Analytic ground-truth checks (used by the gate test):
  * kappa -> 0                       -> tip [0, 0, L], identity orientation
  * theta = kappa*L = pi/2, phi = 0  -> tip [1/kappa, 0, 1/kappa], tangent along +x
  * forward -> inverse round-trips (kappa, phi) to machine precision
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


@dataclass(frozen=True)
class PCCParams:
    """Per-actuator constant-curvature segment plus the pressure->curvature law."""

    length_m: float = 0.10              # backbone arc length L [m]
    kappa_gain: float = 2.0e-5          # curvature per (Pa * compliance) [1/(m*Pa)]
    plane_azimuth_rad: float = 0.0      # fixed bending-plane angle phi [rad]

    def __post_init__(self) -> None:
        if not math.isfinite(self.length_m) or self.length_m <= 0:
            raise ValueError("length_m must be finite and > 0")
        if not math.isfinite(self.kappa_gain) or self.kappa_gain <= 0:
            raise ValueError("kappa_gain must be finite and > 0")
        if not math.isfinite(self.plane_azimuth_rad):
            raise ValueError("plane_azimuth_rad must be finite")


def curvature_from_pressure(pressure_pa, compliance_multiplier, params: PCCParams):
    """kappa = kappa_gain * compliance_multiplier * max(P, 0). Vectorized."""
    p = np.asarray(pressure_pa, dtype=float)
    if not math.isfinite(compliance_multiplier) or compliance_multiplier <= 0:
        raise ValueError("compliance_multiplier must be finite and > 0")
    excess = np.clip(p, 0.0, None)
    return params.kappa_gain * float(compliance_multiplier) * excess


def _Rz(a: float) -> np.ndarray:
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def _Ry(a: float) -> np.ndarray:
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])


def pcc_transform(kappa: float, phi: float, length_m: float) -> np.ndarray:
    """Homogeneous 4x4 tip transform of a constant-curvature segment.

    ``kappa`` >= 0 [1/m], ``phi`` bending-plane azimuth [rad], ``length_m`` arc length [m].
    """
    if not math.isfinite(kappa) or kappa < 0:
        raise ValueError("kappa must be finite and >= 0")
    if not math.isfinite(length_m) or length_m <= 0:
        raise ValueError("length_m must be finite and > 0")
    theta = kappa * length_m
    T = np.eye(4)
    if kappa <= 0.0 or theta == 0.0:
        T[:3, 3] = [0.0, 0.0, length_m]
        return T
    r = 1.0 / kappa
    T[:3, 3] = r * np.array([(1 - math.cos(theta)) * math.cos(phi),
                             (1 - math.cos(theta)) * math.sin(phi),
                             math.sin(theta)])
    T[:3, :3] = _Rz(phi) @ _Ry(theta) @ _Rz(-phi)
    return T
