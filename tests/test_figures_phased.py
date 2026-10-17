"""The Phase D figures show only stored values, and their words live in the caption files.

Each figure is rebuilt from its committed result JSON; no study or dataset is run.
"""
import json
from pathlib import Path

import numpy as np
import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")
from matplotlib.text import Text  # noqa: E402

from scripts import figure_style as style  # noqa: E402
from scripts import run_study2, run_study3, run_study3_cluster_ci, run_study4  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/sim/phaseD"


def load(name):
    return json.loads((DATA / name).read_text())


S2, S3, CI, S4 = (load(n) for n in ("study2_results.json", "study3_results.json",
                                    "study3_cluster_ci_results.json", "study4_results.json"))
AUDIT = load("matched_clock_audit.json")
FIGURES = {  # stem: (figure, caption)
    run_study2.FIG1: (lambda: run_study2.drift_figure(S2), lambda: run_study2.drift_caption(S2)),
    run_study2.FIG2: (lambda: run_study2.corrector_figure(S2), lambda: run_study2.corrector_caption(S2)),
    run_study3.FIG4: (lambda: run_study3.tradeoff_figure(S3), lambda: run_study3.tradeoff_caption(S3, AUDIT)),
    run_study3_cluster_ci.FIG4B: (lambda: run_study3_cluster_ci.cluster_tradeoff_figure(CI),
                                  lambda: run_study3_cluster_ci.cluster_tradeoff_caption(CI)),
    run_study4.FIG: (lambda: run_study4.crosstalk_figure(S4), lambda: run_study4.crosstalk_caption(S4)),
}


@pytest.fixture(scope="module")
def figures():
    built = {stem: make() for stem, (make, _) in FIGURES.items()}
    yield built
    for fig in built.values():
        matplotlib.pyplot.close(fig)


def points(ax):
    """Single-point marker lines, in drawing order."""
    return [line for line in ax.lines if len(line.get_xdata()) == 1]


def test_drift_lines_carry_stored_errors(figures):
    expA = S2["experimentA_static_drift_over_life"]
    lines = figures[run_study2.FIG1].axes[0].lines
    assert [list(line.get_ydata()) for line in lines] == [expA["shared"], expA["isolated"]]
    assert all(list(line.get_xdata()) == expA["life_fractions"] for line in lines)


def test_corrector_bars_carry_stored_errors(figures):
    expB = S2["experimentB_static_vs_dynamic_young_to_old"]
    heights = [bar.get_height() for bar in figures[run_study2.FIG2].axes[0].patches]
    assert heights == [expB[t][k] for k in ("static_kappa_rmse", "dynamic_kappa_rmse")
                       for t in ("isolated", "shared")]


@pytest.mark.parametrize("stem, policies, budget", [
    (run_study3.FIG4, S3["policies_on_heldout"], S3["accuracy_budget_mm"]),
    (run_study3_cluster_ci.FIG4B, CI["policies_on_heldout_with_cluster_ci"], CI["provenance"]["accuracy_budget_mm"]),
])
def test_policy_markers_carry_stored_values_and_budget_state(figures, stem, policies, budget):
    markers = points(figures[stem].axes[0])
    assert len(markers) == len(run_study3.POLICIES)
    for line, (key, _, marker) in zip(markers, run_study3.POLICIES):
        p = policies[key]
        assert (line.get_xdata()[0], line.get_ydata()[0]) == (p["recal_per_actuator"], p["mean_pose_rmse_mm"])
        assert line.get_marker() == marker
        assert line.get_markerfacecolor() == style.FILL[p["mean_pose_rmse_mm"] <= budget]


def test_lead_frontier_carries_stored_leads(figures):
    frontier = CI["lead_frontier_with_cluster_ci"]
    ax = figures[run_study3_cluster_ci.FIG4B].axes[1]
    per = np.array([p["lead_per_actuator"] for p in frontier]).T
    curves = [list(line.get_ydata()) for line in ax.lines if len(line.get_xdata()) == len(frontier)]
    assert curves == [list(row) for row in per] + [[p["mean_lead_life"] for p in frontier]]
    for line, p in zip(points(ax), frontier):
        assert line.get_ydata()[0] == p["mean_lead_life"]
        assert line.get_markerfacecolor() == style.FILL[p["mean_lead_life"] > 0]


def test_crosstalk_curves_carry_stored_sweep(figures):
    ax = figures[run_study4.FIG].axes[0]
    curves = [line for line in ax.lines if len(line.get_xdata()) == len(S4["sweep_multiplier"])]
    for line, (key, *_) in zip(curves, run_study4.KNOBS):
        assert list(line.get_ydata()) == list(np.asarray(S4["coupling_vs_multiplier"][key]) * 100.0)
    (default,) = points(ax)
    assert default.get_ydata()[0] == S4["default_coupling"] * 100.0


@pytest.mark.parametrize("stem", FIGURES)
def test_canvas_holds_only_axes_text_panel_letters_and_legend(figures, stem):
    fig = figures[stem]
    printed = {t.get_text() for t in fig.findobj(Text) if t.get_visible() and t.get_text().strip()}
    allowed = {f"({c})" for c in style.LETTERS}
    allowed |= {ax.get_xlabel() for ax in fig.axes} | {ax.get_ylabel() for ax in fig.axes}
    allowed |= {t.get_text() for legend in fig.legends for t in legend.get_texts()}
    allowed |= {t.get_text() for ax in fig.axes for t in ax.get_xticklabels() + ax.get_yticklabels()}
    assert printed <= allowed, printed - allowed
    assert len(fig.legends) == 1 and not any(ax.get_legend() for ax in fig.axes)
    assert not any(ax.get_title() for ax in fig.axes)


@pytest.mark.parametrize("stem", FIGURES)
def test_nothing_printed_touches_anything(figures, stem):
    assert style.audit(figures[stem]) == []


@pytest.mark.parametrize("stem", FIGURES)
def test_caption_matches_committed_file(stem):
    assert FIGURES[stem][1]() == (DATA / f"{stem}.caption.md").read_text().strip()
