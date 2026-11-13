import io
import json
from pathlib import Path
import cv2
import fitz
import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.services.scanner.capture_validation import (
    CaptureValidationError,
    validate_capture_file,
)
from app.services.scanner.dewarp import dewarp_page_image
from app.services.scanner.document_detection import detect_document_bounds
from app.services.scanner.enhancement import (
    EnhancementConfig,
    OutputFilterMode,
    enhance_scanned_image,
)
from app.services.scanner.geometry import (
    calculate_target_dimensions,
    order_quad_points,
    warp_perspective_crop,
)
from app.services.scanner.ocr import run_scanner_ocr
from app.services.scanner.pipeline import PageScanRequest, scan_pipeline
from app.services.scanner.presets import (
    PresetSettings,
    ScannerPreset,
    preset_store,
)
from app.services.scanner.quality_assessment import assess_image_quality
from app.services.scanner.searchable_pdf import create_searchable_pdf


@pytest.fixture
def test_client():
    return TestClient(app)


def test_capture_validation(tmp_path: Path):
    # Empty file
    empty = tmp_path / "empty.jpg"
    empty.write_bytes(b"")
    with pytest.raises(CaptureValidationError):
        validate_capture_file(empty)

    # Valid image
    img = Image.new("RGB", (300, 400), "white")
    valid_path = tmp_path / "doc.jpg"
    img.save(valid_path, format="JPEG")
    w, h, fmt = validate_capture_file(valid_path)
    assert w == 300
    assert h == 400
    assert fmt.lower() in ("jpg", "jpeg")


def test_quality_assessment():
    # Sharp image with high-frequency edges
    sharp_img = np.zeros((400, 400, 3), dtype=np.uint8)
    for i in range(10, 390, 15):
        cv2.line(sharp_img, (i, 10), (i, 390), (255, 255, 255), 2)
    sharp_eval = assess_image_quality(sharp_img)
    assert sharp_eval.is_sharp is True
    assert sharp_eval.sharpness_score > 0.3

    # Blurry image
    blurry_img = cv2.GaussianBlur(sharp_img, (45, 45), 0)
    blurry_eval = assess_image_quality(blurry_img)
    assert blurry_eval.sharpness_score < sharp_eval.sharpness_score


def test_geometry_and_perspective_warp():
    # Synthetic tilted quad
    pts = np.array([[50, 60], [350, 40], [370, 450], [40, 420]], dtype=np.float32)
    ordered = order_quad_points(pts)
    assert ordered[0][0] <= ordered[1][0]
    assert ordered[3][0] <= ordered[2][0]

    w, h = calculate_target_dimensions(ordered)
    assert w >= 300
    assert h >= 380

    test_img = np.ones((500, 500, 3), dtype=np.uint8) * 128
    cv2.putText(test_img, "KIWI TEST", (100, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    warped, matrix = warp_perspective_crop(test_img, ordered)
    assert warped.shape[0] == h
    assert warped.shape[1] == w
    assert matrix.shape == (3, 3)


def test_document_detection_synthetic():
    # Black background with white document page
    bg = np.zeros((600, 800, 3), dtype=np.uint8)
    # Draw white quad representing a sheet of paper
    pts = np.array([[100, 80], [700, 100], [680, 520], [120, 500]], dtype=np.int32)
    cv2.fillPoly(bg, [pts], (240, 240, 240))
    cv2.putText(bg, "Statement of Account", (200, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 20, 20), 2)

    bounds = detect_document_bounds(bg)
    assert bounds.detected_auto is True
    assert len(bounds.corners) == 4
    assert bounds.confidence >= 0.6


def test_dewarp_cylindrical():
    img = np.ones((400, 400, 3), dtype=np.uint8) * 200
    cv2.putText(img, "Curved Textbook Page", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    dewarped, applied = dewarp_page_image(img, force_dewarp=True, strength=0.5)
    assert dewarped.shape == img.shape
    assert applied is True


def test_image_enhancement_presets():
    img = np.ones((300, 300, 3), dtype=np.uint8) * 180
    # Add fake blue stamp
    cv2.circle(img, (150, 150), 40, (220, 40, 30), -1)  # BGR blue
    cv2.putText(img, "APPROVED", (120, 155), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Document mode
    cfg_doc = EnhancementConfig(filter_mode=OutputFilterMode.COLOR, whites=30.0, blacks=20.0, preserve_color_stamps=True)
    enhanced_doc = enhance_scanned_image(img, cfg_doc)
    assert enhanced_doc.shape == img.shape

    # Receipt mode (BW)
    cfg_receipt = EnhancementConfig(filter_mode=OutputFilterMode.BW, preserve_color_stamps=False)
    enhanced_receipt = enhance_scanned_image(img, cfg_receipt)
    assert enhanced_receipt.shape == img.shape


def test_preset_store_protection():
    builtins = preset_store.list_all()
    assert any(p.id == "auto" for p in builtins)
    assert any(p.id == "document" for p in builtins)
    assert any(p.id == "receipt" for p in builtins)

    # Protected against deletion
    with pytest.raises(ValueError):
        preset_store.delete_custom("auto")

    # Protected against overwriting
    with pytest.raises(ValueError):
        preset_store.save_custom(builtins[0])


def test_searchable_pdf_generation(tmp_path: Path):
    # Create image with text
    img = np.ones((400, 600, 3), dtype=np.uint8) * 255
    cv2.putText(img, "Kiwi Searchable OCR Test", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)

    ocr_res = run_scanner_ocr(img)

    out_pdf = tmp_path / "result.pdf"
    create_searchable_pdf([(img, ocr_res)], out_pdf)
    assert out_pdf.exists()
    assert out_pdf.stat().st_size > 0

    doc = fitz.open(out_pdf)
    assert len(doc) == 1
    doc.close()


def test_scan_pipeline_end_to_end(tmp_path: Path):
    # Save a test image
    img = np.ones((500, 500, 3), dtype=np.uint8) * 255
    cv2.putText(img, "Invoice No 1042", (60, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (10, 10, 10), 2)
    cv2.putText(img, "Total: $145.00", (60, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (10, 10, 10), 2)

    img_path = tmp_path / "page1.png"
    cv2.imwrite(str(img_path), img)

    out_dir = tmp_path / "pipeline_out"
    result = scan_pipeline.process(
        pages=[PageScanRequest(image_path=img_path)],
        out_dir=out_dir,
        preset_id="receipt",
        output_format="pdf_searchable",
    )
    assert result.page_count == 1
    assert len(result.output_files) == 1
    assert result.output_files[0].exists()
    assert result.output_files[0].suffix == ".pdf"


def test_scanner_api_routes(test_client, tmp_path: Path):
    # 1. Test /api/v1/scanner/presets
    res = test_client.get("/api/v1/scanner/presets")
    assert res.status_code == 200
    presets = res.json()
    assert len(presets) >= 6

    # 2. Test /api/v1/scanner/detect
    img = Image.new("RGB", (400, 400), "white")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    detect_res = test_client.post(
        "/api/v1/scanner/detect",
        files={"file": ("page.jpg", buf, "image/jpeg")},
    )
    assert detect_res.status_code == 200
    data = detect_res.json()
    assert data["width"] == 400
    assert data["height"] == 400
    assert len(data["corners"]) == 4
    assert "quality" in data

