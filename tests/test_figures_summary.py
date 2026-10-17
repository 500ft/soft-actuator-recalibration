"""The closed-study summary figures show only saved values; their words live in the captions."""
import csv
from pathlib import Path

import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")
from matplotlib.text import Text  # noqa: E402

from scripts import figure_style as style  # noqa: E402
from scripts import plot_result_summaries as plot  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/sim/summary"
DOCS = {"policy_comparison": ("README.md", "docs/results.md"),
        "trigger_timing": ("docs/results.md",), "cross_talk": ("docs/results.md",)}
squash = lambda s: " ".join(s.split())


@pytest.fixture(scope="module")
def built():
    audit, study3, study4 = plot.load()
    rows = plot.policies(audit, study3)
    figures = {"policy_comparison": plot.policy_figure(rows, audit),
               "trigger_timing": plot.lead_figure(study3),
               "cross_talk": plot.coupling_figure(study4)}
    captions = {"policy_comparison": plot.policy_caption(rows, audit, study3),
                "trigger_timing": plot.lead_caption(study3),
                "cross_talk": plot.coupling_caption(study4)}
    yield audit, study3, study4, figures, captions
    for fig in figures.values():
        matplotlib.pyplot.close(fig)


def markers(ax):
    return [line for line in ax.lines if len(line.get_xdata()) == 1]


def test_policy_markers_carry_csv_values_and_budget_state(built):
    audit, _, _, figures, _ = built
    with (OUT / "policy_comparison.csv").open() as f:
        rows = list(csv.DictReader(f))
    for ax, field in zip(figures["policy_comparison"].axes, ("mean_pose_rmse_mm", "recalibrations_per_actuator")):
        found = markers(ax)
        assert len(found) == len(rows)
        for y, (line, row) in enumerate(zip(found, rows)):
            assert (line.get_xdata()[0], line.get_ydata()[0]) == (float(row[field]), y)
            assert line.get_marker() == plot.POLICY_MARKERS[row["policy"]]
            assert line.get_markerfacecolor() == style.FILL[float(row["mean_pose_rmse_mm"]) <= audit["budget_mm"]]


def test_timing_markers_carry_csv_values(built):
    _, _, _, figures, _ = built
    with (OUT / "trigger_timing.csv").open() as f:
        rows = list(csv.DictReader(f))
    timing, lead = figures["trigger_timing"].axes
    pairs = markers(timing)
    assert [l.get_xdata()[0] for l in pairs[0::2]] == [float(r["budget_violation_life"]) for r in rows]
    assert [l.get_xdata()[0] for l in pairs[1::2]] == [float(r["trigger_life"]) for r in rows]
    leads = markers(lead)
    assert [l.get_xdata()[0] for l in leads] == [float(r["lead_life"]) for r in rows]
    assert [l.get_markerfacecolor() for l in leads] == [style.FILL[float(r["lead_life"]) >= 0] for r in rows]


def test_coupling_lines_carry_csv_values(built):
    _, _, study4, figures, _ = built
    with (OUT / "cross_talk.csv").open() as f:
        rows = list(csv.DictReader(f))
    ax = figures["cross_talk"].axes[0]
    curves = [line for line in ax.lines if len(line.get_xdata()) == len(rows)]
    for line, key in zip(curves, ("R_s_coupling_ratio", "C_m_coupling_ratio")):
        assert list(line.get_ydata()) == [float(r[key]) * 100 for r in rows]
    assert markers(ax)[0].get_ydata()[0] == study4["default_coupling"] * 100


@pytest.mark.parametrize("stem", DOCS)
def test_canvas_holds_only_axes_text_letters_and_legend(built, stem):
    fig = built[3][stem]
    printed = {t.get_text() for t in fig.findobj(Text) if t.get_visible() and t.get_text().strip()}
    allowed = {f"({c})" for c in style.LETTERS}
    allowed |= {ax.get_xlabel() for ax in fig.axes} | {ax.get_ylabel() for ax in fig.axes}
    allowed |= {t.get_text() for legend in fig.legends for t in legend.get_texts()}
    allowed |= {t.get_text() for ax in fig.axes for t in ax.get_xticklabels() + ax.get_yticklabels()}
    assert printed <= allowed, printed - allowed
    assert len(fig.legends) == 1 and not any(ax.get_legend() for ax in fig.axes)
    assert style.audit(fig) == []


@pytest.mark.parametrize("stem", DOCS)
def test_caption_matches_file_and_docs(built, stem):
    text = built[4][stem]
    assert text == (OUT / f"{stem}.caption.md").read_text().strip()
    for doc in DOCS[stem]:
        page = squash((ROOT / doc).read_text())
        assert squash(text) in page, doc
        assert f"data/sim/summary/{stem}.caption.md" in page, doc


def test_audit_refuses_a_wrong_glyph():
    style.apply()
    fig = matplotlib.pyplot.figure()
    fig.text(.1, .1, "R_s")
    with pytest.raises(ValueError, match="wrong glyph"):
        style.audit(fig)
    matplotlib.pyplot.close(fig)
