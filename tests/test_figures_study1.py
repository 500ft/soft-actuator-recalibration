"""The Study 1 figures show only stored values from study1_results.json; their words live in the captions."""
import json
from pathlib import Path

import numpy as np
import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")
from matplotlib.text import Text  # noqa: E402

from scripts import figure_style as style  # noqa: E402
from scripts import run_study1 as study  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "data/sim/study1"
RESULT = json.loads((OUT / "study1_results.json").read_text())


@pytest.fixture(scope="module", params=list(study.FIGURES))
def built(request):
    style.apply()
    figure, caption = study.FIGURES[request.param]
    fig = figure(RESULT)
    yield request.param, fig, caption
    matplotlib.pyplot.close(fig)


def expected(stem):
    """Plotted values per axes, in drawing order, straight from the JSON."""
    if stem == "fig_hi_fusion_comparison":
        f = RESULT["fusion_comparison"]
        return [[f[key] for key, _, _ in study.FUSION]]
    if stem == "fig_recovery_validation":
        return [[[r["fits"][k]["tau_s"] / 3600 for r in RESULT["recovery"]] for k, _, _ in study.RECOVERY]]
    if stem == "fig_onset_generalization_gap":
        return [[[r["models"]["segmented_quadratic"]["median_absolute_onset_error"] for r in rows]]
                for rows in study._onset_series(RESULT).values()]
    if stem == "fig_metric_fixtures":
        return [[[v] for _, _, v, _ in study._fixture_rows(RESULT)]]
    rows = study._detection_rows(RESULT)
    return [[c["detection"][k]["median_alarm_cycle"] for k, _, _ in study.DETECTORS for c in rows]]


def test_marks_carry_stored_values(built):
    stem, fig, _ = built
    axes = [ax for ax in fig.axes]
    assert len(axes) == len(expected(stem))
    for ax, values in zip(axes, expected(stem)):
        if stem == "fig_detector_comparison":
            assert [p.get_height() for p in ax.patches] == values
            continue
        if stem == "fig_metric_fixtures":
            marks = [line for line in ax.lines if line.get_marker() == "o"]
            assert [list(m.get_xdata()) for m in marks] == values
            assert [m.get_markerfacecolor() for m in marks] == [style.FILL[ok] for *_, ok in study._fixture_rows(RESULT)]
            continue
        # The recovery reference line is drawn first and is not a data series.
        lines = ax.lines[1:] if stem == "fig_recovery_validation" else ax.lines
        assert [np.asarray(line.get_ydata()).tolist() for line in lines] == values


def test_canvas_holds_only_axes_text_panel_letters_and_legend(built):
    _, fig, _ = built
    printed = {t.get_text() for t in fig.findobj(Text) if t.get_visible() and t.get_text().strip()}
    allowed = {f"({c})" for c in style.LETTERS}
    allowed |= {fig.get_supxlabel(), fig.get_supylabel()}
    allowed |= {label for ax in fig.axes for label in (ax.get_xlabel(), ax.get_ylabel())}
    allowed |= {t.get_text() for legend in fig.legends for t in legend.get_texts()}
    allowed |= {t.get_text() for ax in fig.axes for t in ax.get_xticklabels() + ax.get_yticklabels()}
    assert printed <= allowed, printed - allowed
    assert len(fig.legends) == 1 and not any(ax.get_legend() for ax in fig.axes)
    assert not any(ax.get_title() for ax in fig.axes)


def test_nothing_printed_touches_anything(built):
    _, fig, _ = built
    assert style.audit(fig) == []


def test_caption_matches_committed_file(built):
    stem, _, caption = built
    assert caption(RESULT) == (OUT / f"{stem}.caption.md").read_text().strip()


def test_cmr10_underscore_is_refused():
    style.apply()
    fig = matplotlib.pyplot.figure()
    fig.text(0.1, 0.1, "R_s")
    with pytest.raises(ValueError, match="mathtext"):
        style.audit(fig)
    matplotlib.pyplot.close(fig)
