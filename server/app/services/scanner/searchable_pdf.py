from __future__ import annotations

import io
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import fitz
import numpy as np
from PIL import Image

from app.services.scanner.ocr import OcrResult, OcrWord


def create_searchable_pdf(
    pages: List[Tuple[np.ndarray, Optional[OcrResult]]],
    output_pdf_path: Path,
    dpi: int = 150,
) -> Path:
    """Generates a high-fidelity PDF from enhanced page images.
    
    If an OcrResult is provided for a page, burns in an invisible text layer (render_mode=3)
    aligned with the image coordinates, making the PDF fully searchable, selectable, and copyable.
    """
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()

    try:
        for image_bgr, ocr_res in pages:
            img_h, img_w = image_bgr.shape[:2]

            # 72 points per inch
            pts_w = (img_w / float(dpi)) * 72.0
            pts_h = (img_h / float(dpi)) * 72.0
            scale_x = pts_w / float(img_w)
            scale_y = pts_h / float(img_h)

            page = doc.new_page(width=pts_w, height=pts_h)

            # Encode image to JPEG / PNG in-memory
            # Encode high-quality JPEG for documents
            is_success, buffer = cv2.imencode(".jpg", image_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
            if not is_success:
                continue

            page.insert_image(page.rect, stream=buffer.tobytes())

            # Add invisible text layer if OCR text is available
            if ocr_res and ocr_res.words:
                for word in ocr_res.words:
                    if not word.text.strip():
                        continue

                    # Map coordinates from image pixel space to PDF points
                    wx0 = word.x0 * scale_x
                    wy0 = word.y0 * scale_y
                    wy1 = word.y1 * scale_y
                    box_h = max(2.0, wy1 - wy0)
                    font_size = max(5.0, box_h * 0.85)

                    try:
                        # Baseline placement: wy1 - font_size * 0.15
                        page.insert_text(
                            (wx0, wy1 - font_size * 0.15),
                            word.text,
                            fontsize=font_size,
                            render_mode=3,  # invisible
                        )
                    except Exception:
                        pass

        doc.save(str(output_pdf_path))
        return output_pdf_path
    finally:
        doc.close()

