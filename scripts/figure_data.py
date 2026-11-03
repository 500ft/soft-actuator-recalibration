"""Write the plotted series and captions that the MATLAB renderer reads.

The committed images are drawn by ``figures/matlab/render_figures.m``. Python
keeps every computation: it writes the result JSON, and for figures whose
curves are not stored there, a small CSV of exactly the plotted values under
``<study>/figdata/``. No value is rounded here. Writing these files never
touches a result JSON.
"""
import csv
from pathlib import Path


def write_csv(path, header, rows) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        for row in rows:
            w.writerow([repr(float(v)) if isinstance(v, float) else v for v in row])
    return path


def write_caption(stem, text: str) -> Path:
    path = Path(str(stem) + ".caption.md")
    path.write_text(text.strip() + "\n")
    return path
