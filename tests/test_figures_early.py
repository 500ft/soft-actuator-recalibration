"""The rebuilt Gate 0 and Phase B figures show only saved values; their words live in the captions."""
import json
from pathlib import Path

import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.text import Text  # noqa: E402

from scripts import figure_style as style  # noqa: E402
from scripts import gate0_lumped_rc as gate0  # noqa: E402
from scripts import phaseB_fatigue_demo as phaseB  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
GATE0 = json.loads((ROOT / "data/gate0/gate0_results.json").read_text())
PHASEB = json.loads((ROOT / "data/sim/phaseB/phaseB_results.json").read_text())
squash = lambda s: " ".join(s.split())

CASES = {
    "data/gate0/fig_crosstalk_vs_compliance": (gate0.compliance_figure, gate0.compliance_caption, GATE0),
    "data/sim/phaseB/fig_rest_recovery": (phaseB.recovery_figure, phaseB.recovery_caption, PHASEB),
    "data/sim/phaseB/fig_leak_sensitivity": (phaseB.leak_figure, phaseB.leak_caption, PHASEB),
}


@pytest.fixture(scope="module")
def figures():
    with plt.rc_context():
        style.apply()
        built = {stem: figure(data) for stem, (figure, _, data) in CASES.items()}
        yield built
    for fig in built.values():
        plt.close(fig)


def test_plotted_values_equal_the_saved_result(figures):
    (line,) = figures["data/gate0/fig_crosstalk_vs_compliance"].axes[0].lines
    hm = GATE0["headline_metric"]
    assert list(line.get_xdata()) == hm["fatigue_levels"]
    assert list(line.get_ydata()) == [v * 100 for v in hm["crosstalk_vs_fatigue"]]

    ax = figures["data/sim/phaseB/fig_rest_recovery"].axes[0]
    rec = PHASEB["recovery"]
    (total,) = ax.lines
    assert list(total.get_xdata()) == [r["rest_hours"] for r in rec]
    assert list(total.get_ydata()) == [r["mullins_permanent"] * 100 + r["mullins_recoverable"] * 100 for r in rec]
    assert phaseB.recovery_cycles(PHASEB) == 2000

    (line,) = figures["data/sim/phaseB/fig_leak_sensitivity"].axes[0].lines
    rows = PHASEB["sensitivity"]["terminal_leak_multipliers"]
    assert list(line.get_xdata()) == [r["terminal_multiplier"] for r in rows]
    assert list(line.get_ydata()) == [r["rupture_half_life_s"] * 1e3 for r in rows]


def test_canvas_holds_only_axes_text_and_legend(figures):
    for stem, fig in figures.items():
        printed = {t.get_text() for t in fig.findobj(Text) if t.get_visible() and t.get_text().strip()}
        allowed = {ax.get_xlabel() for ax in fig.axes} | {ax.get_ylabel() for ax in fig.axes}
        allowed |= {t.get_text() for legend in fig.legends for t in legend.get_texts()}
        allowed |= {t.get_text() for ax in fig.axes for t in ax.get_xticklabels() + ax.get_yticklabels()}
        assert printed <= allowed, (stem, printed - allowed)
        assert len(fig.legends) + sum(ax.get_legend() is not None for ax in fig.axes) <= 1, stem


def test_nothing_printed_touches_anything(figures):
    for stem, fig in figures.items():
        assert style.audit(fig) == [], stem


def test_captions_match_files_and_docs():
    for stem, (_, caption, data) in CASES.items():
        assert caption(data) == (ROOT / f"{stem}.caption.md").read_text().strip(), stem
    gate0_text = gate0.compliance_caption(GATE0)
    assert "from 11.8 % to 23.4 %" in gate0_text
    assert squash(gate0_text) in squash((ROOT / "docs/Gate0_Coupling_Simulation.md").read_text())
    assert "10× gives 14.4 ms; 20× gives 7.0 ms; 40× gives 3.5 ms" in phaseB.leak_caption(PHASEB)
