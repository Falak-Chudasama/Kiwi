from __future__ import annotations

import io
from pathlib import Path
from typing import Tuple

from PIL import Image

# Register HEIC if available
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass

SUPPORTED_SCAN_EXTENSIONS = {
    "jpg", "jpeg", "png", "webp", "tiff", "tif", "bmp", "heic", "heif", "pdf"
}

MIN_DIMENSION_PX = 100
MAX_DIMENSION_PX = 16000
MAX_PIXELS = 100_000_000  # 100 MP limit against decompression bombs


class CaptureValidationError(ValueError):
    """Raised when an uploaded scan file fails validation."""
    pass


def validate_capture_file(path: Path) -> Tuple[int, int, str]:
    """Validates an uploaded capture image file.
    
    Returns (width, height, format_name).
    Raises CaptureValidationError on failure.
    """
    if not path.exists():
        raise CaptureValidationError("File does not exist.")

    size = path.stat().st_size
    if size == 0:
        raise CaptureValidationError("File is empty (0 bytes).")

    ext = path.suffix.lower().lstrip(".")
    if ext not in SUPPORTED_SCAN_EXTENSIONS:
        raise CaptureValidationError(
            f"Unsupported file format '.{ext}'. Supported formats: {', '.join(sorted(SUPPORTED_SCAN_EXTENSIONS))}."
        )

    if ext == "pdf":
        import fitz
        try:
            doc = fitz.open(path)
            page_count = len(doc)
            if page_count == 0:
                doc.close()
                raise CaptureValidationError("PDF contains no pages.")
            first_page = doc[0]
            w, h = int(first_page.rect.width), int(first_page.rect.height)
            doc.close()
            return w, h, "pdf"
        except Exception as exc:
            raise CaptureValidationError(f"Invalid PDF file: {exc}")

    try:
        with Image.open(path) as img:
            w, h = img.size
            fmt = (img.format or ext).lower()

            if w < MIN_DIMENSION_PX or h < MIN_DIMENSION_PX:
                raise CaptureValidationError(
                    f"Image resolution {w}x{h} is too low for document scanning (minimum {MIN_DIMENSION_PX}x{MIN_DIMENSION_PX})."
                )

            if w > MAX_DIMENSION_PX or h > MAX_DIMENSION_PX or (w * h) > MAX_PIXELS:
                raise CaptureValidationError(
                    f"Image resolution {w}x{h} exceeds maximum safe limits."
                )

            return w, h, fmt
    except Exception as exc:
        if isinstance(exc, CaptureValidationError):
            raise
        raise CaptureValidationError(f"Cannot decode image file: {exc}")

