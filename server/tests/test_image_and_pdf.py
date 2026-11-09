import io
from pathlib import Path
import pytest
from PIL import Image

from app.services.images import convert_image, probe_supported_image_formats
from app.services.pdf_tools import pdf_to_images, SUPPORTED_PDF_IMAGE_FORMATS

def test_probe_supported_image_formats():
    capabilities = probe_supported_image_formats()
    assert capabilities.get("png") is True
    assert capabilities.get("jpg") is True
    assert capabilities.get("webp") is True
    assert capabilities.get("avif") is True  # Probes our registered avif opener

def test_image_convert_png_to_webp(tmp_path: Path):
    img = Image.new("RGB", (64, 64), color="red")
    src = tmp_path / "test.png"
    img.save(src, format="PNG")

    out_dir = tmp_path / "out"
    result = convert_image(src, "webp", out_dir)
    assert result.exists()
    assert result.suffix == ".webp"
    assert result.stat().st_size > 0

    with Image.open(result) as res_img:
        assert res_img.size == (64, 64)

def test_image_convert_aspect_ratio_preserve(tmp_path: Path):
    img = Image.new("RGB", (200, 100), color="blue")
    src = tmp_path / "test2.png"
    img.save(src, format="PNG")

    out_dir = tmp_path / "out_resize"
    # Provide width only: height should automatically scale proportionally to 50
    result = convert_image(src, "png", out_dir, width=100)
    assert result.exists()
    with Image.open(result) as res_img:
        assert res_img.size == (100, 50)

def test_image_decompression_bomb_rejection(tmp_path: Path):
    img = Image.new("RGB", (10, 10), color="white")
    src = tmp_path / "bomb.png"
    img.save(src, format="PNG")

    from PIL import Image as PILImage
    orig_limit = PILImage.MAX_IMAGE_PIXELS
    PILImage.MAX_IMAGE_PIXELS = 50  # Artificially low limit to test safety handler
    try:
        with pytest.raises(ValueError, match="decompression bomb"):
            convert_image(src, "jpg", tmp_path / "out_bomb")
    finally:
        PILImage.MAX_IMAGE_PIXELS = orig_limit

def test_pdf_to_images_supports_all_declared_formats(tmp_path: Path):
    import fitz
    doc = fitz.open()
    page = doc.new_page(width=100, height=100)
    page.draw_rect(fitz.Rect(10, 10, 90, 90), color=(1, 0, 0), fill=(0, 1, 0))
    pdf_path = tmp_path / "test.pdf"
    doc.save(pdf_path)
    doc.close()

    out_dir = tmp_path / "pdf_imgs"
    for fmt in ["png", "jpg", "webp", "tiff", "bmp"]:
        results = pdf_to_images(pdf_path, out_dir, fmt, dpi=72)
        assert len(results) == 1
        assert results[0].exists()
        assert results[0].suffix == f".{fmt}"
        assert results[0].stat().st_size > 0

