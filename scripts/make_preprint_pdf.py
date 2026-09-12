#!/usr/bin/env python3
"""Render docs/preprint_v1.md to a formatted PDF (reportlab).

Self-contained: no pandoc / LaTeX needed. Handles the markdown subset the preprint uses
(headings, paragraphs, **bold**/*italic*/`code`, bullet lists, pipe tables, --- rules,
![img](path) figures + italic captions) and embeds the figures. Unicode (Greek/math) is
supported by registering matplotlib's bundled DejaVuSans TTFs.

Run: python -m scripts.make_preprint_pdf --source docs/preprint_v1_4_candidate.md --output build/preprint_v1_4_candidate.pdf

Explicit paths only. The historical docs/preprint_v1.pdf is the archived v1.3 release whose
SHA-256 is pinned in docs/publication-readiness.json; this script REFUSES to write to it and
verifies its bytes are unchanged after every run. Each render writes a JSON manifest next to
the output recording source and output SHA-256, renderer identity and library versions, with
author_approval null -- a rendered PDF is not an approved PDF.
"""

from __future__ import annotations

import os
import re

import matplotlib
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as _rl_canvas
from reportlab.platypus import (HRFlowable, Image, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
HISTORICAL_MD = os.path.join(REPO, "docs", "preprint_v1.md")
HISTORICAL_PDF = os.path.join(REPO, "docs", "preprint_v1.pdf")
READINESS = os.path.join(REPO, "docs", "publication-readiness.json")
# Set per run by build(); module-level for the helpers that resolve figure paths.
MD = HISTORICAL_MD
OUT = None

# ── Unicode fonts (DejaVu ships with matplotlib) ────────────────────────────────
_FONTDIR = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
pdfmetrics.registerFont(TTFont("DejaVu", os.path.join(_FONTDIR, "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", os.path.join(_FONTDIR, "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Italic", os.path.join(_FONTDIR, "DejaVuSans-Oblique.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-BoldItalic", os.path.join(_FONTDIR, "DejaVuSans-BoldOblique.ttf")))
pdfmetrics.registerFontFamily("DejaVu", normal="DejaVu", bold="DejaVu-Bold",
                              italic="DejaVu-Italic", boldItalic="DejaVu-BoldItalic")
# Embedded monospace for code spans — the reportlab base-14 Courier is NOT
# embedded in the output, which violates arXiv's all-fonts-embedded requirement.
pdfmetrics.registerFont(TTFont("DejaVuMono", os.path.join(_FONTDIR, "DejaVuSansMono.ttf")))

class _EmbeddedFontCanvas(_rl_canvas.Canvas):
    """reportlab asserts its default Helvetica into every page's content stream
    (``BT /F1 12 Tf ... ET``) even when no Helvetica glyph is ever drawn, which
    drags the unembedded base-14 font into the page resources — an arXiv
    auto-hold trigger for PDF-only submissions. Pointing the initial graphics
    state at the embedded DejaVu face removes the reference entirely."""

    def __init__(self, *args, **kwargs):
        # The base font is referenced by every page's preamble ('BT %s 12 Tf')
        # and gets ALLOCATED in the document font dict the moment the canvas is
        # constructed — rebuilding the preamble later is too late. The canvas
        # exposes the initial font as a constructor argument, BUT doctemplate
        # passes initialFontName=None explicitly, so setdefault() is defeated;
        # a hard override of the None is required.
        if not kwargs.get("initialFontName"):
            kwargs["initialFontName"] = "DejaVu"
        super().__init__(*args, **kwargs)


BLUE = HexColor("#1a5276")
_B = getSampleStyleSheet()["Normal"]
_B.fontName = "DejaVu"     # kill the Helvetica default anywhere it could inherit through
TITLE = ParagraphStyle("title", parent=_B, fontName="DejaVu-Bold", fontSize=15, leading=19,
                       alignment=TA_CENTER, spaceAfter=8)
H1 = ParagraphStyle("h1", parent=_B, fontName="DejaVu-Bold", fontSize=12.5, leading=15,
                    spaceBefore=12, spaceAfter=4, textColor=BLUE)
H2 = ParagraphStyle("h2", parent=_B, fontName="DejaVu-Bold", fontSize=10.5, leading=13,
                    spaceBefore=7, spaceAfter=3)
BODY = ParagraphStyle("body", parent=_B, fontName="DejaVu", fontSize=9.3, leading=13,
                      alignment=TA_JUSTIFY, spaceAfter=5)
BULLET = ParagraphStyle("bullet", parent=BODY, leftIndent=16, firstLineIndent=-9, spaceAfter=2)
CAPTION = ParagraphStyle("caption", parent=_B, fontName="DejaVu-Italic", fontSize=8.3,
                         leading=11, alignment=TA_CENTER, textColor=colors.grey, spaceAfter=8)
CELL = ParagraphStyle("cell", parent=_B, fontName="DejaVu", fontSize=8.5, leading=11)
CELLH = ParagraphStyle("cellh", parent=CELL, fontName="DejaVu-Bold")


def inline(s: str) -> str:
    """Markdown inline -> reportlab mini-markup (escape, then bold/italic/code/links)."""
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    s = re.sub(r"!\[.*?\]\(.*?\)", "", s)                       # strip stray image md
    s = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1", s)                 # links -> text
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", s)
    s = re.sub(r"`(.+?)`", r'<font face="DejaVuMono" size="8">\1</font>', s)
    s = s.replace(r"\*", "*").replace(r"\[", "[").replace(r"\]", "]")
    return s


def make_table(rows):
    grid = []
    for r, cells in enumerate(rows):
        style = CELLH if r == 0 else CELL
        grid.append([Paragraph(inline(c), style) for c in cells])
    tbl = Table(grid, hAlign="CENTER", repeatRows=1)
    tbl.setStyle(TableStyle([
        # Table cells carry a cell-style font that _drawCell asserts via
        # canvas.setFont even for Paragraph content; the default is Helvetica,
        # which would allocate an unembedded base-14 font into the document.
        ("FONTNAME", (0, 0), (-1, -1), "DejaVu"),
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#d6eaf8")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, HexColor("#f2f3f4")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return tbl


def figure(relpath):
    path = os.path.normpath(os.path.join(os.path.dirname(MD), relpath))
    iw, ih = ImageReader(path).getSize()
    w = 4.3 * inch
    img = Image(path, width=w, height=w * ih / iw)
    img.hAlign = "CENTER"
    return img


class ProtectedOutputError(RuntimeError):
    """Raised when a render would overwrite the archived historical PDF."""


def _sha256(path):
    import hashlib
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _historical_pinned_sha():
    import json
    with open(READINESS, encoding="utf-8") as fh:
        return json.load(fh)["historical_pdf_sha256"]


def _same_file(a, b):
    """True if two paths name the same file, following symlinks and case-insensitive filesystems."""
    ra, rb = os.path.realpath(a), os.path.realpath(b)
    if ra == rb or os.path.normcase(ra) == os.path.normcase(rb):
        return True
    try:
        return os.path.samefile(ra, rb)
    except OSError:
        return False


def protected_paths():
    """Files a render must never write: the pinned archive, its readiness record, and every
    tracked source under docs/ that a render could take as --source."""
    fixed = [HISTORICAL_PDF, READINESS, HISTORICAL_MD]
    docs = os.path.join(REPO, "docs")
    extra = [os.path.join(docs, n) for n in os.listdir(docs) if n.endswith((".md", ".pdf", ".json", ".txt"))]
    return fixed + extra


def validate_destinations(source, output, manifest):
    """Every destination must be distinct from every protected file, from the source, and from each other."""
    for label, dest in (("--output", output), ("--manifest", manifest)):
        for prot in protected_paths():
            if _same_file(dest, prot):
                raise ProtectedOutputError(f"{label} {dest} is a protected file ({os.path.relpath(prot, REPO)}); choose another path")
        if _same_file(dest, source):
            raise ProtectedOutputError(f"{label} {dest} is the render source; choose another path")
    if _same_file(output, manifest):
        raise ProtectedOutputError("--output and --manifest resolve to the same file")


def build(source=None, output=None, manifest=None):
    """Render `source` markdown to `output` PDF and write `manifest` (JSON).

    Every destination (output AND manifest) is validated against the archive, the readiness
    record, every tracked docs/ file and the source itself, following symlinks, BEFORE any
    write; the archive and readiness record are hash-verified AFTER the last write.
    """
    global MD, OUT
    import datetime, json, platform
    import reportlab, pypdf
    MD = os.path.abspath(source or HISTORICAL_MD)
    if output is None:
        raise ProtectedOutputError("--output is required; this script never writes to a default path")
    OUT = os.path.abspath(output)
    if not OUT.lower().endswith(".pdf"):
        raise ProtectedOutputError(f"--output must be a .pdf path, got {output}")
    MANIFEST = os.path.abspath(manifest) if manifest else os.path.splitext(OUT)[0] + ".manifest.json"
    if not os.path.isfile(MD):
        raise FileNotFoundError(MD)
    validate_destinations(MD, OUT, MANIFEST)
    pinned = _historical_pinned_sha()
    before = _sha256(HISTORICAL_PDF)
    if before != pinned:
        raise ProtectedOutputError(f"historical PDF already differs from its pinned SHA-256 ({before[:12]} != {pinned[:12]}); refusing to render until that is resolved")
    readiness_before = _sha256(READINESS)
    source_before = _sha256(MD)
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(MANIFEST) or ".", exist_ok=True)
    lines = open(MD, encoding="utf-8").read().splitlines()
    story, para, tbl = [], [], []

    def flush_para():
        if para:
            story.append(Paragraph(inline(" ".join(para)), BODY))
            para.clear()

    def flush_tbl():
        if tbl:
            rows = [[c.strip() for c in row.strip().strip("|").split("|")] for row in tbl
                    if not re.match(r"^\|[\s:|-]+\|?\s*$", row)]
            story.append(make_table(rows)); story.append(Spacer(1, 6)); tbl.clear()

    for raw in lines:
        line = raw.rstrip()
        if line.startswith("|"):
            flush_para(); tbl.append(line); continue
        flush_tbl()
        if not line.strip():
            flush_para(); continue
        m_img = re.match(r"^!\[.*?\]\((.+?)\)\s*$", line)
        if m_img:
            flush_para(); story.append(Spacer(1, 4)); story.append(figure(m_img.group(1))); continue
        if line.startswith("### "):
            flush_para(); story.append(Paragraph(inline(line[4:]), H2)); continue
        if line.startswith("## "):
            flush_para(); story.append(Paragraph(inline(line[3:]), H1)); continue
        if line.startswith("# "):
            flush_para(); story.append(Paragraph(inline(line[2:]), TITLE)); continue
        if line.strip() == "---":
            flush_para(); story.append(HRFlowable(width="100%", thickness=0.5,
                                                  color=colors.lightgrey, spaceBefore=4, spaceAfter=6)); continue
        if re.match(r"^\*[^*].*[^*]\*$", line.strip()):           # whole-line italic = caption
            flush_para(); story.append(Paragraph(inline(line.strip()[1:-1]), CAPTION)); continue
        if line.lstrip().startswith(("- ", "> ")):
            flush_para(); story.append(Paragraph("•&nbsp;" + inline(line.lstrip()[2:]), BULLET)); continue
        para.append(line.strip())
    flush_para(); flush_tbl()

    SimpleDocTemplate(OUT, pagesize=LETTER, leftMargin=0.9*inch, rightMargin=0.9*inch,
                      topMargin=0.9*inch, bottomMargin=0.9*inch,
                      title="P-V Loop Shape as a Fatigue Health Indicator (preprint draft)"
                      ).build(story, canvasmaker=_EmbeddedFontCanvas)
    def _verify_protected(stage):
        if _sha256(HISTORICAL_PDF) != pinned:
            raise ProtectedOutputError(f"historical PDF bytes changed ({stage}); this is a bug, do not commit")
        if _sha256(READINESS) != readiness_before:
            raise ProtectedOutputError(f"publication-readiness.json changed ({stage}); this is a bug, do not commit")
        if _sha256(MD) != source_before:
            raise ProtectedOutputError(f"render source changed ({stage}); this is a bug, do not commit")
    _verify_protected("after PDF write")
    record = {
        "schema_version": 2,
        "rendered_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": os.path.relpath(MD, REPO), "source_sha256": source_before,
        "output": os.path.relpath(OUT, REPO), "output_sha256": _sha256(OUT),
        "manifest": os.path.relpath(MANIFEST, REPO),
        "renderer": "scripts/make_preprint_pdf.py",
        "versions": {"python": platform.python_version(), "reportlab": reportlab.Version,
                     "pypdf": pypdf.__version__, "matplotlib_fonts": matplotlib.__version__},
        "historical_pdf_sha256_verified_unchanged": pinned,
        "readiness_sha256_verified_unchanged": readiness_before,
        "author_approval": None,
        "note": "A rendered PDF is not an approved PDF. Publication readiness is governed by docs/publication-readiness.json, which this render does not modify.",
    }
    with open(MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2); fh.write("\n")
    _verify_protected("after manifest write")     # the LAST write, so the claim in the manifest is true
    print(f"PDF written: {OUT}")
    print(f"manifest:    {MANIFEST}")
    return record


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", default=HISTORICAL_MD, help="markdown to render (default: the historical docs/preprint_v1.md)")
    ap.add_argument("--output", required=True, help="PDF path to write; the archived docs/preprint_v1.pdf is refused")
    ap.add_argument("--manifest", default=None, help="manifest JSON path (default: <output>.manifest.json)")
    a = ap.parse_args(argv)
    try:
        build(a.source, a.output, a.manifest)
    except ProtectedOutputError as e:
        print(f"REFUSED: {e}"); return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
