from enum import Enum
from pathlib import Path

import fitz
from PIL import Image

from app.core.config import settings
from app.core.files import run_command


class CompressionLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


IMAGE_QUALITY_BY_LEVEL = {
    CompressionLevel.LOW: 85,
    CompressionLevel.MEDIUM: 70,
    CompressionLevel.HIGH: 50,
    CompressionLevel.EXTREME: 30,
}

IMAGE_SCALE_BY_LEVEL = {
    CompressionLevel.LOW: 1.0,
    CompressionLevel.MEDIUM: 1.0,
    CompressionLevel.HIGH: 0.85,
    CompressionLevel.EXTREME: 0.65,
}

PDF_DPI_BY_LEVEL = {
    CompressionLevel.LOW: 150,
    CompressionLevel.MEDIUM: 120,
    CompressionLevel.HIGH: 96,
    CompressionLevel.EXTREME: 72,
}

GHOSTSCRIPT_PRESET_BY_LEVEL = {
    CompressionLevel.LOW: "/printer",
    CompressionLevel.MEDIUM: "/ebook",
    CompressionLevel.HIGH: "/ebook",
    CompressionLevel.EXTREME: "/screen",
}


def compress_image(input_path: Path, out_dir: Path, level: CompressionLevel) -> Path:
    ext = input_path.suffix.lower().lstrip(".")
    output_path = out_dir / input_path.name

    image = Image.open(input_path)
    scale = IMAGE_SCALE_BY_LEVEL[level]
    if scale < 1.0:
        new_size = (int(image.width * scale), int(image.height * scale))
        image = image.resize(new_size, Image.LANCZOS)

    quality = IMAGE_QUALITY_BY_LEVEL[level]

    if ext in ("jpg", "jpeg"):
        if image.mode != "RGB":
            image = image.convert("RGB")
        image.save(output_path, format="JPEG", quality=quality, optimize=True)
    elif ext == "png":
        image.save(output_path, format="PNG", optimize=True, compress_level=9)
    elif ext == "webp":
        image.save(output_path, format="WEBP", quality=quality)
    elif ext in ("tiff", "tif"):
        image.save(output_path, format="TIFF", compression="tiff_deflate")
    else:
        image.save(output_path, quality=quality)

    return output_path


def compress_pdf(input_path: Path, out_dir: Path, level: CompressionLevel) -> Path:
    output_path = out_dir / f"{input_path.stem}_compressed.pdf"
    preset = GHOSTSCRIPT_PRESET_BY_LEVEL[level]
    args = [
        "gs",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS={preset}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output_path}",
        str(input_path),
    ]
    try:
        run_command(args, timeout=240)
    except Exception:
        return _compress_pdf_via_rasterize(input_path, out_dir, level)
    return output_path


def _compress_pdf_via_rasterize(input_path: Path, out_dir: Path, level: CompressionLevel) -> Path:
    output_path = out_dir / f"{input_path.stem}_compressed.pdf"
    dpi = PDF_DPI_BY_LEVEL[level]
    quality = IMAGE_QUALITY_BY_LEVEL[level]
    source = fitz.open(input_path)
    result = fitz.open()
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)

    for page in source:
        pixmap = page.get_pixmap(matrix=matrix)
        img_bytes = pixmap.pil_tobytes(format="JPEG", optimize=True)
        new_page = result.new_page(width=page.rect.width, height=page.rect.height)
        new_page.insert_image(new_page.rect, stream=img_bytes)

    result.save(output_path, garbage=4, deflate=True)
    result.close()
    source.close()
    return output_path


def compress_office_document(input_path: Path, out_dir: Path, level: CompressionLevel) -> Path:
    ext = input_path.suffix.lower().lstrip(".")
    pdf_path = out_dir / f"{input_path.stem}.pdf"
    args = [
        settings.soffice_bin,
        "--headless",
        "--norestore",
        "--convert-to",
        "pdf",
        "--outdir",
        str(out_dir),
        str(input_path),
    ]
    run_command(args, timeout=240)
    return compress_pdf(pdf_path, out_dir, level)


def compress_file(input_path: Path, out_dir: Path, level: CompressionLevel) -> Path:
    ext = input_path.suffix.lower().lstrip(".")
    if ext == "pdf":
        return compress_pdf(input_path, out_dir, level)
    if ext in ("jpg", "jpeg", "png", "webp", "tiff", "tif"):
        return compress_image(input_path, out_dir, level)
    if ext in ("docx", "pptx", "xlsx"):
        return compress_office_document(input_path, out_dir, level)
    raise ValueError(f"Compression is not supported for .{ext} files.")
