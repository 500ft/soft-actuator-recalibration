"""The Study C and dispersion-audit figures show only stored values; their words live in the captions."""
import json
from pathlib import Path

import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")
from matplotlib.text import Text  # noqa: E402

from scripts import analyze_studyC_failure as failure  # noqa: E402
from scripts import figure_style as style  # noqa: E402
from scripts import run_dispersion_audit as dispersion  # noqa: E402
from scripts import run_studyC as transfer  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FAMILY = {
    "transfer": (transfer, "data/sim/studyC/studyC_results.json"),
    "failure": (failure, "data/sim/studyC/studyC_failure_analysis.json"),
    "dispersion": (dispersion, "data/sim/dispersion_audit/dispersion_audit.json"),
}


@pytest.fixture(scope="module")
def built():
    out = {}
    for name, (module, source) in FAMILY.items():
        results = json.loads((ROOT / source).read_text())
        out[name] = (module, results, module.figure(results))
    yield out
    for _, _, fig in out.values():
        matplotlib.pyplot.close(fig)


def markers(ax):
    return [line for line in ax.lines if len(line.get_xdata()) == 1]


def test_transfer_markers_carry_stored_errors(built):
    _, results, fig = built["transfer"]
    points = markers(fig.axes[0])
    expected = []
    for i, h in enumerate(results["heldout"]):
        expected += [(i + transfer.DODGE, h["rmse_clock"], "s"), (i - transfer.DODGE, h["rmse"], "o")]
    assert [(p.get_xdata()[0], p.get_ydata()[0], p.get_marker()) for p in points] == expected
    for p in points:
        assert p.get_markerfacecolor() == style.FILL[bool(p.get_ydata()[0] <= transfer.PASS_RMSE)]
    assert [t.get_text() for t in fig.axes[0].get_xticklabels()] == [str(i) for i in results["test_units"]]


def test_failure_markers_carry_stored_units(built):
    _, results, fig = built["failure"]
    for ax, key in zip(fig.axes, ("n_post_onset", "rupture_deviation_from_training_median")):
        got = [(p.get_xdata()[0], p.get_ydata()[0], p.get_markerfacecolor()) for p in markers(ax)]
        assert got == [(r[key], r["rmse"], style.FILL[r["within_target"]]) for r in results["per_unit"]]


def test_dispersion_markers_carry_stored_sweep(built):
    _, results, fig = built["dispersion"]
    sweep = results["B_transfer_sensitivity"]["results"]
    panels = dict(zip("ab", fig.axes))
    for panel in "ab":
        series = [s for s in dispersion.SERIES if s[0] == panel]
        got = [(p.get_xdata()[0], p.get_ydata()[0], p.get_marker()) for p in markers(panels[panel])]
        assert got == [(x["rupture_cv"], x[key], m) for _, key, m, _, _ in series for x in sweep]
    published = {line.get_xdata()[0] for line in panels["a"].lines if line.get_linewidth() == 0.35}
    assert published == set(results["B_transfer_sensitivity"]["measured_reference_values"].values())


@pytest.mark.parametrize("name", FAMILY)
def test_canvas_holds_only_axes_text_panel_letters_and_legend(built, name):
    _, _, fig = built[name]
    printed = {t.get_text() for t in fig.findobj(Text) if t.get_visible() and t.get_text().strip()}
    allowed = {f"({c})" for c in style.LETTERS}
    allowed |= {ax.get_xlabel() for ax in fig.axes} | {ax.get_ylabel() for ax in fig.axes}
    allowed |= {t.get_text() for legend in fig.legends for t in legend.get_texts()}
    allowed |= {t.get_text() for ax in fig.axes for t in ax.get_xticklabels() + ax.get_yticklabels()}
    assert printed <= allowed, printed - allowed
    assert len(fig.legends) == 1 and not any(ax.get_legend() for ax in fig.axes)
    assert not any(ax.get_title() for ax in fig.axes)


@pytest.mark.parametrize("name", FAMILY)
def test_nothing_printed_touches_anything(built, name):
    assert style.audit(built[name][2]) == []


@pytest.mark.parametrize("name", FAMILY)
def test_caption_matches_committed_file(built, name):
    module, results, _ = built[name]
    text = module.caption(results)
    assert text == (ROOT / (module.STEM + ".caption.md")).read_text().strip()
    if "verdict" in results:
        assert results["verdict"] in text


def test_wrong_cmr10_glyph_is_refused():
    fig = matplotlib.pyplot.figure()
    fig.text(0.1, 0.1, "R_s")
    with pytest.raises(ValueError, match="mathtext"):
        style.audit(fig)
    matplotlib.pyplot.close(fig)
