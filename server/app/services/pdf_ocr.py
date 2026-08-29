"""Selective, per-page OCR for PDFs.

Kiwi should never blindly OCR a PDF that already has a healthy text layer --
that's slower and strictly worse than the embedded text. This module is
called only for the specific pages that `pdf_analysis.PdfAnalysis` flagged
as needing OCR (no usable text layer), so a mixed document with 8 native
pages and 2 scanned pages only pays the OCR cost for those 2 pages.

Uses Tesseract via pytesseract, which is already a Kiwi dependency and, on
Windows, ships with the same installer Kiwi already documents for the user.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class OcrWord:
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    confidence: float


@dataclass
class OcrPageResult:
    text: str
    words: list[OcrWord]
    mean_confidence: float


def ocr_available() -> bool:
    import shutil

    try:
        import pytesseract  # noqa: F401
    except ImportError:
        return False
    return shutil.which("tesseract") is not None


def ocr_page(page, dpi: int = 300) -> OcrPageResult:
    """Rasterize a single PyMuPDF page and OCR it, returning word-level boxes
    in PDF point space (not pixel space) so callers can place text at the
    same coordinates native PDF text would occupy.
    """
    import fitz
    import pytesseract
    from PIL import Image
    import io

    zoom = dpi / 72.0
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    image = Image.open(io.BytesIO(pix.tobytes("png")))

    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

    words: list[OcrWord] = []
    confidences: list[float] = []
    n = len(data.get("text", []))
    for i in range(n):
        text = data["text"][i].strip()
        if not text:
            continue
        try:
            conf = float(data["conf"][i])
        except (ValueError, TypeError):
            conf = -1.0
        if conf < 0:
            continue
        x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
        # Convert pixel coords back to PDF point space.
        words.append(OcrWord(
            text=text,
            x0=x / zoom,
            y0=y / zoom,
            x1=(x + w) / zoom,
            y1=(y + h) / zoom,
            confidence=conf,
        ))
        confidences.append(conf)

    full_text = " ".join(w.text for w in words)
    mean_conf = sum(confidences) / len(confidences) if confidences else 0.0
    return OcrPageResult(text=full_text, words=words, mean_confidence=mean_conf)


def ocr_lines(page, dpi: int = 300) -> list[list[OcrWord]]:
    """Like `ocr_page` but groups words into lines (by OCR line/block/par
    numbering) so callers can reconstruct paragraph-like text rather than a
    flat bag of words. Returns a list of lines, each a list of words in
    reading order.
    """
    import fitz
    import pytesseract
    from PIL import Image
    import io

    zoom = dpi / 72.0
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    image = Image.open(io.BytesIO(pix.tobytes("png")))
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

    lines: dict[tuple, list[OcrWord]] = {}
    n = len(data.get("text", []))
    for i in range(n):
        text = data["text"][i].strip()
        if not text:
            continue
        try:
            conf = float(data["conf"][i])
        except (ValueError, TypeError):
            conf = -1.0
        if conf < 0:
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
        word = OcrWord(
            text=text,
            x0=x / zoom, y0=y / zoom, x1=(x + w) / zoom, y1=(y + h) / zoom,
            confidence=conf,
        )
        lines.setdefault(key, []).append(word)

    ordered_keys = sorted(lines.keys())
    return [sorted(lines[k], key=lambda w: w.x0) for k in ordered_keys]
