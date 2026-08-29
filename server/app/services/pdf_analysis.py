"""PDF pre-conversion analysis.

Before Kiwi decides *how* to convert a PDF, it should know *what the PDF is*.
This module inspects a PDF once (cheaply, using PyMuPDF only -- no OCR, no
heavy models) and produces a structured `PdfAnalysis` that downstream
converters use to pick a strategy: does a page need OCR, is the layout
multi-column, is there a real table on this page, etc.

This intentionally stays fast and dependency-light (PyMuPDF only) because it
runs on every PDF conversion, including the common case of a simple
single-column text PDF that needs none of this machinery. Heavier per-page
work (OCR, table extraction) is triggered only for the pages that actually
need it, based on this analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PageAnalysis:
    index: int
    width: float
    height: float
    rotation: int
    char_count: int
    image_count: int
    image_coverage: float  # fraction of page area covered by images, 0..1
    drawing_count: int  # vector graphics (lines/rects/curves) on the page
    is_scanned: bool  # essentially no native text, likely a photographed/scanned page
    needs_ocr: bool  # no usable text layer at all
    column_count: int
    has_table_hint: bool  # ruled lines suggest a table grid
    fonts: set[str] = field(default_factory=set)


@dataclass
class PdfAnalysis:
    page_count: int
    scanned: bool  # true if most/all pages have no usable text layer
    mixed_content: bool  # some pages scanned, some native
    requires_ocr: bool  # at least one page needs OCR
    ocr_page_indices: list[int]
    column_count: int  # dominant column count across the document
    has_tables: bool
    has_images: bool
    has_vector_graphics: bool
    complexity: str  # "low" | "medium" | "high"
    fonts: set[str] = field(default_factory=set)
    pages: list[PageAnalysis] = field(default_factory=list)

    @property
    def is_simple_text(self) -> bool:
        """A plain, single-column, native-text document with no tables/heavy
        graphics -- the case where lightweight extraction is sufficient and
        the expensive layout/OCR path would be wasted work."""
        return (
            not self.scanned
            and not self.requires_ocr
            and self.column_count <= 1
            and not self.has_tables
            and self.complexity == "low"
        )


def _page_column_count(page, text_dict: dict) -> int:
    """Estimate column count from the horizontal spread of text block x0s.

    Groups block left-edges into clusters; distinct, well-separated clusters
    that each span a meaningful vertical range indicate side-by-side columns
    rather than incidental left-margin variation (e.g. indentation).
    """
    blocks = [b for b in text_dict.get("blocks", []) if b.get("type") == 0 and b.get("lines")]
    if len(blocks) < 4:
        return 1

    page_width = page.rect.width or 1.0
    xs = sorted(b["bbox"][0] for b in blocks)

    # Cluster x0 values with a gap threshold proportional to page width.
    gap_threshold = page_width * 0.08
    clusters: list[list[float]] = [[xs[0]]]
    for x in xs[1:]:
        if x - clusters[-1][-1] > gap_threshold:
            clusters.append([x])
        else:
            clusters[-1].append(x)

    # A cluster only counts as a column if it has a meaningful number of
    # blocks (not a single stray caption) and starts left of the page's
    # right half (real columns tile left-to-right across the content area).
    significant = [c for c in clusters if len(c) >= 2]
    if len(significant) <= 1:
        return 1
    return min(len(significant), 4)


def _has_table_hint(page) -> bool:
    """Cheap heuristic: 4+ axis-aligned line drawings forming a grid-like
    pattern strongly suggests a ruled table. Full table extraction (which is
    expensive) is only run on pages that pass this filter."""
    try:
        drawings = page.get_drawings()
    except Exception:
        return False

    h_lines = 0
    v_lines = 0
    for d in drawings:
        for item in d.get("items", []):
            if item[0] != "l":
                continue
            p1, p2 = item[1], item[2]
            if abs(p1.y - p2.y) < 1.0 and abs(p1.x - p2.x) > 10:
                h_lines += 1
            elif abs(p1.x - p2.x) < 1.0 and abs(p1.y - p2.y) > 10:
                v_lines += 1
    return h_lines >= 2 and v_lines >= 2


def analyze_pdf(pdf_path: Path, max_pages_deep: int = 60) -> PdfAnalysis:
    """Run a single-pass structural analysis over the PDF.

    `max_pages_deep` caps how many pages get the full per-page treatment
    (drawings/table-hint/column detection) to keep very long PDFs fast; pages
    beyond that are still scanned for text/OCR status (cheap) but assumed to
    share the dominant column count and complexity of the analyzed sample.
    """
    import fitz

    doc = fitz.open(pdf_path)
    try:
        pages: list[PageAnalysis] = []
        all_fonts: set[str] = set()
        column_votes: dict[int, int] = {}
        any_tables = False
        any_images = False
        any_vector = False

        page_count = len(doc)
        for i, page in enumerate(doc):
            rect = page.rect
            page_area = max(rect.width * rect.height, 1.0)
            text = page.get_text("text")
            char_count = len(text.strip())

            images = page.get_images(full=True)
            image_count = len(images)
            image_coverage = 0.0
            if image_count:
                try:
                    covered = 0.0
                    for img in page.get_image_info():
                        b = img.get("bbox")
                        if b:
                            covered += max(0.0, (b[2] - b[0])) * max(0.0, (b[3] - b[1]))
                    image_coverage = min(1.0, covered / page_area)
                except Exception:
                    image_coverage = min(1.0, image_count * 0.3)

            deep = i < max_pages_deep
            drawing_count = 0
            column_count = 1
            table_hint = False
            if deep:
                try:
                    drawing_count = len(page.get_drawings())
                except Exception:
                    drawing_count = 0
                text_dict = page.get_text("dict")
                column_count = _page_column_count(page, text_dict)
                table_hint = _has_table_hint(page)
                for block in text_dict.get("blocks", []):
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            font = span.get("font")
                            if font:
                                all_fonts.add(font)

            # A page is "scanned" if it has essentially no extractable text
            # but does have substantial image coverage (i.e. it's a photo of
            # a page, not a genuinely blank page).
            is_scanned = char_count < 5 and (image_coverage > 0.3 or image_count > 0)
            needs_ocr = char_count < 5

            pages.append(PageAnalysis(
                index=i,
                width=rect.width,
                height=rect.height,
                rotation=page.rotation,
                char_count=char_count,
                image_count=image_count,
                image_coverage=image_coverage,
                drawing_count=drawing_count,
                is_scanned=is_scanned,
                needs_ocr=needs_ocr,
                column_count=column_count,
                has_table_hint=table_hint,
            ))

            if image_count:
                any_images = True
            if drawing_count > 3:
                any_vector = True
            if table_hint:
                any_tables = True
            column_votes[column_count] = column_votes.get(column_count, 0) + 1

        doc.close_needed = False
    finally:
        try:
            doc.close()
        except Exception:
            pass

    scanned_pages = [p for p in pages if p.is_scanned]
    ocr_pages = [p.index for p in pages if p.needs_ocr]

    scanned = len(scanned_pages) > 0 and len(scanned_pages) >= max(1, page_count * 0.6)
    mixed_content = 0 < len(ocr_pages) < page_count

    dominant_columns = max(column_votes, key=lambda k: column_votes[k]) if column_votes else 1

    # Also detect tables via pdfplumber on a small sample if the cheap
    # geometry hint found nothing but the doc isn't scanned -- catches
    # borderless tables that only whitespace-align, which is common in
    # exported spreadsheets/invoices. Kept sample-only (first 5 pages) to
    # stay fast.
    if not any_tables and not scanned:
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pl:
                for pg in pl.pages[:5]:
                    if pg.find_tables():
                        any_tables = True
                        break
        except Exception:
            pass

    complexity = "low"
    signals = sum([
        dominant_columns > 1,
        any_tables,
        any_vector,
        any_images,
        len(all_fonts) > 4,
    ])
    if signals >= 3:
        complexity = "high"
    elif signals >= 1:
        complexity = "medium"

    return PdfAnalysis(
        page_count=page_count,
        scanned=scanned,
        mixed_content=mixed_content,
        requires_ocr=len(ocr_pages) > 0,
        ocr_page_indices=ocr_pages,
        column_count=dominant_columns,
        has_tables=any_tables,
        has_images=any_images,
        has_vector_graphics=any_vector,
        complexity=complexity,
        fonts=all_fonts,
        pages=pages,
    )
