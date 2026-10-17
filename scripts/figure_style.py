"""Shared figure rules: a data-only canvas with the words in a caption.

Plots call ``apply()`` before drawing and ``save()`` to write every format;
``save()`` refuses to write unless ``audit()`` finds nothing touching and no
glyph is missing from the font. Only presentation lives here; no plotted value
is computed in this module.

- The canvas carries data, axes, tick labels, axis labels, panel letters and
  one framed legend. Titles, definitions, outcomes and notes live in the
  caption file written next to the image and in the docs under it.
- Condition is carried by marker shape and line style, state by fill.
  Colour is used only for a field with a colourbar, so nothing else depends on it.
- Type is Computer Modern (matplotlib's bundled ``cmr10``), the family of the
  Latin Modern used by LaTeX-built figures in the sibling repositories. cmr10
  has no underscore, minus or Greek glyphs; write those in mathtext.

Adapted from the owner-approved rule set in
https://github.com/500ft/evidence-sufficiency-benchmark/pull/26.
Figures not yet rebuilt to these rules still use ``scripts/figstyle.py``.
"""
from pathlib import Path
import re
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.text import Text  # noqa: E402

INK = "black"
# Fill carries state: filled for the passing, recorded or primary case, hollow otherwise.
FILL = {True: INK, False: "white"}
REFERENCE = {"color": INK, "lw": 0.8, "ls": (0, (4, 3))}
MARKER = {"ms": 5, "mew": 0.9, "color": INK, "ls": "none"}
LETTERS = "abcdefghij"
# cmr10 maps these to other glyphs (an underscore prints as a dot accent) without a warning.
WRONG_GLYPHS = set('_<>|{}\\"')

# Three type sizes by role: axis labels and legend, panel letters, tick labels.
LABEL_SIZE, LETTER_SIZE, TICK_SIZE = 9, 9, 7
DPI = 600
# Widths in inches: 183 mm two-column, 89 mm one-column (the repository's existing convention).
FULL, SINGLE = 7.2, 3.5


def apply() -> None:
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["cmr10"],
        "mathtext.fontset": "cm",
        # cmr10 has no Unicode minus; mathtext tick labels carry a proper one.
        "axes.formatter.use_mathtext": True,
        "axes.unicode_minus": False,
        "font.size": LABEL_SIZE,
        "axes.labelsize": LABEL_SIZE,
        "legend.fontsize": LABEL_SIZE,
        "xtick.labelsize": TICK_SIZE,
        "ytick.labelsize": TICK_SIZE,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.8,
        "axes.edgecolor": INK,
        "axes.grid": False,
        "lines.linewidth": 1.0,
        "legend.frameon": True,
        "legend.fancybox": False,
        "legend.edgecolor": INK,
        "legend.framealpha": 1.0,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.dpi": DPI,
        "image.cmap": "cividis",
        "pdf.fonttype": 42,
        # Editable SVG text and stable element ids, so reruns give the same bytes.
        "svg.fonttype": "none",
        "svg.hashsalt": "soft-actuator-figures",
    })


def letter(ax, i: int, x: float = 0.0, y: float = 1.04) -> None:
    """Panel letter "(a)", "(b)", ... above the top-left corner of ``ax``."""
    ax.text(x, y, f"({LETTERS[i]})", transform=ax.transAxes, ha="left", va="bottom", size=LETTER_SIZE)


def audit(fig) -> list[tuple[str, str]]:
    """Pairs of printed things whose boxes touch. Empty means the canvas is clean.

    Every drawn text (tick labels inside the view, axis labels, panel letters,
    legend entries) is checked against every other drawn text, against the
    data drawn in each axes (lines, bars, bands) and against each legend frame.
    Data is not checked against data. Texts inside a legend are not checked
    against their own frame. A glyph missing from the font, or one cmr10
    prints wrongly outside mathtext, raises.
    """
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fig.canvas.draw()
    missing = [str(w.message) for w in caught if "missing from font" in str(w.message)]
    if missing:
        raise ValueError(f"glyphs missing from the font: {missing}")
    wrong = [t.get_text() for t in fig.findobj(Text) if t.get_visible()
             and WRONG_GLYPHS & set(re.sub(r"\$[^$]*\$", "", t.get_text()))]
    if wrong:
        raise ValueError(f"cmr10 prints these with the wrong glyph; use mathtext: {wrong}")
    renderer = fig.canvas.get_renderer()
    legends = list(fig.legends) + [ax.get_legend() for ax in fig.axes if ax.get_legend()]
    owner = {id(child): legend for legend in legends for child in legend.findobj()}
    tick_labels, drawn = set(), []
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            low, high = sorted(axis.get_view_interval())
            slack = 1e-9 * (high - low)
            for tick in axis.get_major_ticks() + axis.get_minor_ticks():
                for label in (tick.label1, tick.label2):
                    tick_labels.add(id(label))
                    if label.get_visible() and label.get_text().strip() and low - slack <= tick.get_loc() <= high + slack:
                        drawn.append(label)
    drawn += [t for t in fig.findobj(Text)
              if id(t) not in tick_labels and t.get_visible() and t.get_text().strip()]
    texts = [(f"text {t.get_text()!r}", t.get_window_extent(renderer).padded(1), owner.get(id(t))) for t in drawn]
    others = [(f"data in {ax.get_ylabel() or 'axes'}", artist.get_window_extent(renderer), None)
              for ax in fig.axes if ax.get_label() != "<colorbar>"
              for artist in list(ax.lines) + list(ax.patches) + list(ax.collections)]
    others += [("legend frame", legend.get_window_extent(renderer), legend) for legend in legends]
    hits = []
    for i, (name_a, box_a, legend_a) in enumerate(texts):
        for name_b, box_b, legend_b in texts[i + 1:] + others:
            if legend_a is not None and legend_a is legend_b:
                continue
            if box_a.overlaps(box_b):
                hits.append((name_a, name_b))
    return hits


def save(fig, stem, formats=("png", "pdf"), caption: str | None = None) -> None:
    """Write ``stem.<ext>`` for each format with no timestamps; refuse a touching canvas.

    With ``caption``, also write ``stem.caption.md``.
    """
    hits = audit(fig)
    if hits:
        raise ValueError(f"printed items touch: {hits}")
    stem = Path(stem)
    meta = {"pdf": {"CreationDate": None}, "svg": {"Date": None}}
    for ext in formats:
        path = stem.with_suffix(f".{ext}")
        fig.savefig(path, dpi=DPI, metadata=meta.get(ext, {}))
        if ext == "svg":
            # Matplotlib path lines carry trailing spaces; normalize the text export.
            path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")
    if caption is not None:
        stem.with_suffix(".caption.md").write_text(caption + "\n")
