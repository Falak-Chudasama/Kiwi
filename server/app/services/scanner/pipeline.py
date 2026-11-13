from __future__ import annotations

import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import cv2
import fitz
import numpy as np

from app.services.scanner.capture_validation import validate_capture_file
from app.services.scanner.dewarp import dewarp_page_image
from app.services.scanner.document_detection import detect_document_bounds
from app.services.scanner.enhancement import EnhancementConfig, enhance_scanned_image
from app.services.scanner.geometry import warp_perspective_crop
from app.services.scanner.ocr import OcrResult, run_scanner_ocr
from app.services.scanner.presets import PresetSettings, preset_store
from app.services.scanner.quality_assessment import QualityAssessment, assess_image_quality
from app.services.scanner.searchable_pdf import create_searchable_pdf


@dataclass
class PageScanRequest:
    image_path: Path
    crop_corners: Optional[List[List[float]]] = None  # 4 points: [[x, y], ...]
    rotation: int = 0  # 0, 90, 180, 270


@dataclass
class ScanResult:
    output_files: List[Path]
    page_count: int
    quality_assessments: List[QualityAssessment]
    full_text: str
    mean_confidence: float


def _rotate_image(img: np.ndarray, angle: int) -> np.ndarray:
    if angle % 360 == 90:
        return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    elif angle % 360 == 180:
        return cv2.rotate(img, cv2.ROTATE_180)
    elif angle % 360 == 270:
        return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return img


class ScanPipeline:
    """End-to-end scanner pipeline orchestrator."""

    def process(
        self,
        pages: List[PageScanRequest],
        out_dir: Path,
        preset_id: str = "auto",
        custom_settings: Optional[PresetSettings] = None,
        output_format: str = "pdf_searchable",
        progress_cb: Optional[Callable[[str, int], None]] = None,
    ) -> ScanResult:
        out_dir.mkdir(parents=True, exist_ok=True)
        if not pages:
            raise ValueError("No pages provided for scanning.")

        # 1. Resolve preset & settings
        preset = preset_store.get(preset_id)
        settings = custom_settings or (preset.settings if preset else PresetSettings())

        enhancement_cfg = EnhancementConfig(
            filter_mode=settings.filter_mode,
            brightness=settings.brightness,
            contrast=settings.contrast,
            exposure=settings.exposure,
            shadows=settings.shadows,
            highlights=settings.highlights,
            whites=settings.whites,
            blacks=settings.blacks,
            gamma=settings.gamma,
            sharpen=settings.sharpen,
            denoise=settings.denoise,
            remove_shadows=settings.remove_shadows,
            preserve_color_stamps=settings.preserve_color_stamps,
        )

        if progress_cb:
            progress_cb("Analysing", 15)

        processed_pages: List[Tuple[np.ndarray, Optional[OcrResult]]] = []
        quality_reports: List[QualityAssessment] = []
        page_texts: List[str] = []
        all_confidences: List[float] = []

        total_pages = len(pages)

        # Process each page sequentially for strict memory bounding
        for idx, req in enumerate(pages):
            step_base = 20 + int((idx / total_pages) * 60)

            # Validate input
            validate_capture_file(req.image_path)

            # Handle PDF inputs by rendering the first page to image
            if req.image_path.suffix.lower() == ".pdf":
                doc = fitz.open(req.image_path)
                first_page = doc[0]
                pix = first_page.get_pixmap(dpi=150)
                img_data = pix.tobytes("png")
                doc.close()
                raw_bgr = cv2.imdecode(np.frombuffer(img_data, np.uint8), cv2.IMREAD_COLOR)
            else:
                raw_bgr = cv2.imread(str(req.image_path), cv2.IMREAD_COLOR)

            if raw_bgr is None:
                raise ValueError(f"Could not read image from {req.image_path.name}")

            # Apply manual user rotation if specified
            if req.rotation:
                raw_bgr = _rotate_image(raw_bgr, req.rotation)

            # Assess capture quality
            quality = assess_image_quality(raw_bgr)
            quality_reports.append(quality)

            if progress_cb:
                progress_cb(f"Correcting geometry (page {idx + 1}/{total_pages})", step_base + 10)

            # Determine crop corners
            if req.crop_corners and len(req.crop_corners) == 4:
                corners = req.crop_corners
            else:
                bounds = detect_document_bounds(raw_bgr)
                corners = bounds.corners

            # Geometric perspective rectification
            warped, _ = warp_perspective_crop(raw_bgr, corners)

            # Optional dewarping (e.g. for Book preset)
            if settings.dewarp_enabled:
                warped, _ = dewarp_page_image(warped, force_dewarp=True)

            if progress_cb:
                progress_cb(f"Enhancing image (page {idx + 1}/{total_pages})", step_base + 20)

            # High-fidelity non-destructive enhancement
            enhanced = enhance_scanned_image(warped, enhancement_cfg)

            # Optical Character Recognition
            ocr_res = None
            if settings.ocr_enabled and output_format in ("pdf_searchable", "txt"):
                if progress_cb:
                    progress_cb(f"Running OCR (page {idx + 1}/{total_pages})", step_base + 30)
                ocr_res = run_scanner_ocr(enhanced, language=settings.ocr_language)
                if ocr_res.full_text:
                    page_texts.append(ocr_res.full_text)
                    all_confidences.append(ocr_res.mean_confidence)

            processed_pages.append((enhanced, ocr_res))

        if progress_cb:
            progress_cb("Generating output files", 90)

        output_files: List[Path] = []
        combined_text = "\n\n--- Page Break ---\n\n".join(page_texts)

        # Export according to output_format
        if output_format == "pdf_searchable":
            pdf_path = out_dir / "scanned_document.pdf"
            create_searchable_pdf(processed_pages, pdf_path)
            output_files.append(pdf_path)

        elif output_format == "pdf_image":
            # Image-only PDF with no invisible text layer
            pdf_path = out_dir / "scanned_document_images.pdf"
            image_only_pages = [(img, None) for img, _ in processed_pages]
            create_searchable_pdf(image_only_pages, pdf_path)
            output_files.append(pdf_path)

        elif output_format == "images_zip":
            zip_path = out_dir / "scanned_pages.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for idx, (img, _) in enumerate(processed_pages, start=1):
                    _, buf = cv2.imencode(".png", img)
                    zf.writestr(f"page_{idx:03d}.png", buf.tobytes())
            output_files.append(zip_path)

        elif output_format == "txt":
            txt_path = out_dir / "scanned_text.txt"
            txt_path.write_text(combined_text, encoding="utf-8")
            output_files.append(txt_path)

        else:
            # Default to searchable PDF
            pdf_path = out_dir / "scanned_document.pdf"
            create_searchable_pdf(processed_pages, pdf_path)
            output_files.append(pdf_path)

        mean_confidence = (sum(all_confidences) / max(1, len(all_confidences))) if all_confidences else 0.0

        if progress_cb:
            progress_cb("Completed", 100)

        return ScanResult(
            output_files=output_files,
            page_count=len(processed_pages),
            quality_assessments=quality_reports,
            full_text=combined_text,
            mean_confidence=mean_confidence,
        )


scan_pipeline = ScanPipeline()

