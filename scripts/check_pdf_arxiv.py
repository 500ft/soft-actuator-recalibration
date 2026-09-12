#!/usr/bin/env python3
"""arXiv PDF pre-flight gate for docs/preprint_v1.pdf.

arXiv requires PDF-only submissions to embed ALL fonts (standard and
non-standard) as outlines. Unembedded base-14 fonts (Helvetica/Courier/Times)
and Type3 bitmap fonts are standard auto-hold reasons. This gate fails on:

  * any font without an embedded FontFile / FontFile2 / FontFile3
    (checked RECURSIVELY, including XObject/Form resources — page-level
    /Font dicts alone miss fonts referenced by form XObjects);
  * any Type3 (bitmap) font, embedded or not;
  * an encrypted PDF, a zero-page PDF, or embedded JavaScript.

Run: python -m scripts.check_pdf_arxiv   (exits nonzero on any failure)
"""

from __future__ import annotations

import os
import sys

from pypdf import PdfReader
from pypdf.generic import IndirectObject

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(os.path.dirname(HERE), "docs", "preprint_v1.pdf")

BASE14 = {
    "Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique",
    "Courier", "Courier-Bold", "Courier-Oblique", "Courier-BoldOblique",
    "Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic",
    "Symbol", "ZapfDingbats",
}


def _resolve(obj):
    return obj.get_object() if isinstance(obj, IndirectObject) else obj


def _font_records(resources, seen, out):
    """Recursively collect (basefont, subtype, embedded) from a resource dict."""
    resources = _resolve(resources)
    if not resources:
        return
    fonts = _resolve(resources.get("/Font")) or {}
    for key in fonts:
        f = _resolve(fonts[key])
        ref = id(f)
        if ref in seen:
            continue
        seen.add(ref)
        subtype = str(f.get("/Subtype", ""))
        base = str(f.get("/BaseFont", f"<unnamed {key}>")).lstrip("/")
        desc = _resolve(f.get("/FontDescriptor"))
        # Type0 composite fonts keep the descriptor on their descendant font.
        if desc is None and "/DescendantFonts" in f:
            for d in _resolve(f["/DescendantFonts"]):
                desc = _resolve(_resolve(d).get("/FontDescriptor"))
                if desc is not None:
                    break
        embedded = bool(desc) and any(
            k in desc for k in ("/FontFile", "/FontFile2", "/FontFile3"))
        out.append((base, subtype, embedded))
    # Form XObjects carry their own resource dicts with their own fonts.
    xobjects = _resolve(resources.get("/XObject")) or {}
    for key in xobjects:
        x = _resolve(xobjects[key])
        if str(x.get("/Subtype", "")) == "/Form" and "/Resources" in x:
            _font_records(x["/Resources"], seen, out)


def main(pdf_path: str | None = None) -> int:
    """Gate `pdf_path` (default: the historical PDF); 0 on pass, 1 on failure.
    A candidate render is gated the same way: python -m scripts.check_pdf_arxiv build/x.pdf"""
    target = pdf_path or (sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else PDF)
    failures: list[str] = []
    reader = PdfReader(target)

    if reader.is_encrypted:
        failures.append("PDF is encrypted — arXiv rejects encrypted PDFs")
    if len(reader.pages) == 0:
        failures.append("PDF has zero pages")

    # Embedded JavaScript (document-level names tree or OpenAction).
    root = reader.trailer["/Root"]
    names = _resolve(root.get("/Names")) or {}
    if "/JavaScript" in names:
        failures.append("PDF carries embedded JavaScript (/Names /JavaScript)")
    open_action = _resolve(root.get("/OpenAction"))
    # LaTeX/hyperref commonly stores a page destination as an ArrayObject.
    # Only action dictionaries can carry an /S /JavaScript entry.
    if hasattr(open_action, "get") and str(open_action.get("/S", "")) == "/JavaScript":
        failures.append("PDF carries a JavaScript OpenAction")

    records: list[tuple[str, str, bool]] = []
    seen: set[int] = set()
    for page in reader.pages:
        if "/Resources" in page:
            _font_records(page["/Resources"], seen, records)

    if not records:
        failures.append("no fonts found — parser miss or empty document")

    print(f"{PDF}: {len(reader.pages)} pages, {len(records)} font records")
    for base, subtype, embedded in sorted(set(records)):
        # Subset prefixes look like 'AAAAAA+DejaVuSans'.
        bare = base.split("+", 1)[-1]
        status = "embedded" if embedded else "NOT EMBEDDED"
        print(f"  {base:<36} {subtype:<10} {status}")
        if subtype == "/Type3":
            failures.append(f"Type3 bitmap font present: {base} — arXiv requires outline fonts")
        if not embedded:
            tag = " (base-14)" if bare in BASE14 else ""
            failures.append(f"font not embedded: {base}{tag}")

    if failures:
        print("\nFAIL:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("\nOK: all fonts embedded as outlines; not encrypted; no JavaScript.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
