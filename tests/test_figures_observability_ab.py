"""Study A ablation and Study B figures show only stored values; their words live in the captions."""
import json
from pathlib import Path

import numpy as np
import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")
from matplotlib.text import Text  # noqa: E402

from scripts import figure_style as style  # noqa: E402
from scripts import run_studyA, run_studyB, run_studyB_structural  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIGURES = {  # stem -> (result file, figure function, caption function)
    "data/sim/studyA/studyA_fig_ablation": ("data/sim/studyA/studyA_results.json",
                                            run_studyA.ablation_figure, run_studyA.ablation_caption),
    "data/sim/studyB/studyB_fig_identifiability_map": ("data/sim/studyB/studyB_results.json",
                                                       run_studyB.map_figure, run_studyB.map_caption),
    "data/sim/studyB/studyB_fig_structural": ("data/sim/studyB/studyB_structural.json",
                                              run_studyB_structural.structural_figure,
                                              run_studyB_structural.structural_caption),
}


@pytest.fixture(scope="module")
def built():
    out = {}
    for stem, (source, figure, caption) in FIGURES.items():
        result = json.loads((ROOT / source).read_text())
        out[stem] = (result, figure(result), caption(result))
    yield out
    for _, fig, _ in out.values():
        matplotlib.pyplot.close(fig)


def single_points(ax):
    return [(line.get_xdata()[0], line.get_ydata()[0], line.get_markerfacecolor())
            for line in ax.lines if len(line.get_xdata()) == 1]


def test_ablation_markers_carry_stored_spreads(built):
    result, fig, _ = built["data/sim/studyA/studyA_fig_ablation"]
    rows = run_studyA.ablation_rows(result)
    assert single_points(fig.axes[0]) == [(v, y, style.FILL[v > run_studyA.ZERO]) for y, (_, v) in enumerate(rows)]
    assert [t.get_text() for t in fig.axes[0].get_yticklabels()] == [run_studyA.ABLATION_NAMES[k] for k, _ in rows]


def test_identifiability_map_carries_stored_bounds(built):
    result, fig, _ = built["data/sim/studyB/studyB_fig_identifiability_map"]
    a, b = fig.axes[:2]
    u = np.array(result["u_grid"])
    drawn = [(line.get_xdata(), line.get_ydata(), line.get_markerfacecolor()) for line in a.lines[:-2]]
    expected = []
    for ys in run_studyB.design_curves(result).values():
        fin = np.isfinite(ys)
        if fin.any():
            expected.append((u[fin], ys[fin], style.FILL[True]))
        if (~fin).any():
            expected.append((u[~fin], np.full((~fin).sum(), run_studyB.TOP), style.FILL[False]))
    assert len(drawn) == len(expected)
    for (x, y, fill), (ex, ey, efill) in zip(drawn, expected):
        assert np.array_equal(x, ex) and np.array_equal(y, ey) and fill == efill
    grid = run_studyB.amplitude_grid(result)
    field = b.images[0].get_array()
    assert np.array_equal(field.mask, ~np.isfinite(grid))
    assert np.array_equal(field.data[np.isfinite(grid)], grid[np.isfinite(grid)])


def test_structural_figure_carries_stored_indices_and_profiles(built):
    result, fig, _ = built["data/sim/studyB/studyB_fig_structural"]
    a, b, c = fig.axes[:3]
    assert single_points(a) == [(v, y, style.INK if post else "none")
                                for y, v, post, _ in run_studyB_structural.collinearity_points(result)]
    for ax, u_true in zip((b, c), run_studyB_structural.PANEL_U):
        curves = [line for line in ax.lines if line.get_marker() in ("o", "s")]
        expected = run_studyB_structural.profile_curves(result, u_true)
        assert len(curves) == len(expected)
        for line, (us, ys, _) in zip(curves, expected.values()):
            assert list(line.get_xdata()) == us and list(line.get_ydata()) == ys


def test_canvas_holds_only_axes_text_panel_letters_and_legend(built):
    for stem, (_, fig, _) in built.items():
        printed = {t.get_text() for t in fig.findobj(Text) if t.get_visible() and t.get_text().strip()}
        allowed = {f"({c})" for c in style.LETTERS}
        allowed |= {ax.get_xlabel() for ax in fig.axes} | {ax.get_ylabel() for ax in fig.axes}
        legends = list(fig.legends) + [ax.get_legend() for ax in fig.axes if ax.get_legend()]
        assert len(legends) == 1, stem
        allowed |= {t.get_text() for legend in legends for t in legend.get_texts()}
        allowed |= {t.get_text() for ax in fig.axes for t in ax.get_xticklabels() + ax.get_yticklabels()}
        if stem.endswith("identifiability_map"):  # heatmap cell numbers, the one allowed exception
            grid = run_studyB.amplitude_grid(built[stem][0])
            allowed |= {f"{v * 100:.2g}" for v in grid[np.isfinite(grid)]} | {r"$\infty$"}
        assert printed <= allowed, (stem, printed - allowed)


def test_nothing_printed_touches_anything(built):
    for stem, (_, fig, _) in built.items():
        assert style.audit(fig) == [], stem


def test_captions_match_committed_files(built):
    for stem, (_, _, caption) in built.items():
        assert caption == (ROOT / f"{stem}.caption.md").read_text().strip(), stem
