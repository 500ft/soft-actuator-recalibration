"""Shared publication figure style for the Phase E/F study figures.

Usage:
    from scripts import figstyle
    figstyle.apply()
    ...
    figstyle.save(plt.gcf(), os.path.join(DATA, "study2_fig1_drift"))   # -> .png (300dpi) + .pdf

Colorblind-safe palette (Wong, Nature Methods 2011).
"""

from __future__ import annotations

PALETTE = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#000000"]


def apply():
    import matplotlib as mpl

    mpl.rcParams.update({
        "figure.dpi": 120,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.titleweight": "bold",
        "axes.labelsize": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.30,
        "grid.linewidth": 0.6,
        "lines.linewidth": 2.0,
        "lines.markersize": 6,
        "legend.frameon": False,
        "legend.fontsize": 9,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "figure.figsize": (5.2, 3.4),
        "axes.prop_cycle": mpl.cycler(color=PALETTE),
    })


def setup(style: bool = True):
    """Headless pyplot (with the publication style unless ``style=False``), or None if matplotlib is unavailable."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:  # pragma: no cover
        return None
    if style:
        apply()
    return plt


def save(fig, path_stem: str):
    """Write ``path_stem.png`` (300 dpi raster) and ``path_stem.pdf`` (vector)."""
    fig.savefig(f"{path_stem}.png")
    fig.savefig(f"{path_stem}.pdf")
