"""Phase D dataset access shared by studies 2, 3 and the cluster-CI run."""

from __future__ import annotations

import json
import os

import numpy as np

from pipeline.correctors import rmse
from sim.kinematics import pcc_transform

DATA = "data/sim/phaseD"


def load():
    d = dict(np.load(os.path.join(DATA, "dataset.npz")))
    m = json.load(open(os.path.join(DATA, "manifest.json")))
    return d, m


def feats(d, i):
    """Shared-manifold pressure + ALL chamber valve commands (focal + neighbors)."""
    return np.concatenate([d["meas_manifold_pressure"][i][:, None], d["cmd_all"][i]], axis=-1)


def pose_rmse(model, d, ix, act):
    """Mean tip-position RMSE [m] over traces ``ix`` for one actuator's PCC geometry."""
    errs = []
    for i in ix:
        kp = np.clip(model.predict(feats(d, i)), 0.0, None)
        pred = np.array([pcc_transform(float(k), act["plane_azimuth_rad"], act["length_m"])[:3, 3]
                         for k in kp])
        errs.append(rmse(pred, d["true_position"][i]))
    return float(np.mean(errs))
