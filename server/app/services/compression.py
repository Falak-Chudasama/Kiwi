from __future__ import annotations

import shutil
from enum import Enum
from pathlib import Path

import fitz
from PIL import Image

from app.core.config import settings
from app.core.files import command_path, run_command


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
    CompressionLevel.MEDIUM: 0.92,
    CompressionLevel.HIGH: 0.78,
    CompressionLevel.EXTREME: 0.62,
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


def _oxipng_optimize_in_place(png_path: Path, level: CompressionLevel) -> None:
    """Run a final lossless pass with oxipng on top of Pillow's encode.

    oxipng re-derives the optimal PNG filter/deflate strategy per scanline
    and typically shaves another 5-20% off Pillow's already-optimized
    output at zero quality cost. It's a Rust binary shipped as prebuilt
    wheels, so this never requires a compiler on the user's machine. If the
    package isn't installed, compression still works via Pillow alone.
    """
    try:
        import oxipng
    except ImportError:
        return
    effort_by_level = {
        CompressionLevel.LOW: 2,
        CompressionLevel.MEDIUM: 3,
        CompressionLevel.HIGH: 4,
        CompressionLevel.EXTREME: 6,
    }
    try:
        oxipng.optimize(str(png_path), level=effort_by_level.get(level, 3))
    except Exception:
        # Never let a best-effort optimization pass break compression.
        pass


def _never_larger(original: Path, candidate: Path) -> Path:
    if candidate.exists() and candidate.stat().st_size < original.stat().st_size:
        return candidate
    candidate.unlink(missing_ok=True)
    fallback = candidate
    shutil.copy2(original, fallback)
    return fallback


def compress_image(input_path: Path, out_dir: Path, level: CompressionLevel) -> Path:
    ext = input_path.suffix.lower().lstrip(".")
    output_path = out_dir / f"{input_path.stem}_compressed.{ext}"
    image = Image.open(input_path)
    try:
        scale = IMAGE_SCALE_BY_LEVEL[level]
        if scale < 1.0:
            image = image.resize(
                (
                    max(1, round(image.width * scale)),
                    max(1, round(image.height * scale)),
                ),
                Image.Resampling.LANCZOS,
            )

        quality = IMAGE_QUALITY_BY_LEVEL[level]
        try:
            if ext in ("jpg", "jpeg"):
                image.convert("RGB").save(
                    output_path, format="JPEG", quality=quality, optimize=True, progressive=True
                )
            elif ext == "png":
                rgba = image.convert("RGBA")
                if level in (CompressionLevel.HIGH, CompressionLevel.EXTREME):
                    colors = 192 if level == CompressionLevel.HIGH else 128
                    # RGBA images can only be quantized with FASTOCTREE (2) or
                    # libimagequant (3) in Pillow; MEDIANCUT/MAXCOVERAGE only work
                    # on non-alpha images and raise ValueError on RGBA input.
                    if rgba.getchannel("A").getextrema() == (255, 255):
                        # Fully opaque: drop alpha so MEDIANCUT (better quality) applies.
                        rgba = rgba.convert("RGB").quantize(colors=colors, method=Image.Quantize.MEDIANCUT).convert("RGBA")
                    else:
                        rgba = rgba.quantize(colors=colors, method=Image.Quantize.FASTOCTREE)
                rgba.save(output_path, format="PNG", optimize=True, compress_level=9)
                _oxipng_optimize_in_place(output_path, level)
            elif ext == "webp":
                image.save(output_path, format="WEBP", quality=quality, method=6)
            elif ext in ("tiff", "tif"):
                image.save(output_path, format="TIFF", compression="tiff_adobe_deflate")
            else:
                image.convert("RGB").save(output_path, quality=quality)
        except (ValueError, OSError):
            # Any format-specific quirk (unsupported quantize mode, missing
            # codec, exotic color mode, etc.) falls back to a safe re-encode
            # so compression never hard-fails a supported image format.
            output_path.unlink(missing_ok=True)
            image.convert("RGB").save(output_path)
    finally:
        image.close()
    return _never_larger(input_path, output_path)


def _compress_pdf_via_rasterize(input_path: Path, out_dir: Path, level: CompressionLevel) -> Path:
    output_path = out_dir / f"{input_path.stem}_compressed.pdf"
    dpi = PDF_DPI_BY_LEVEL[level]
    source = fitz.open(input_path)
    result = fitz.open()
    matrix = fitz.Matrix(dpi / 72, dpi / 72)
    try:
        for page in source:
            pixmap = page.get_pixmap(matrix=matrix, colorspace=fitz.csRGB, alpha=False)
            img_bytes = pixmap.tobytes("jpeg", jpg_quality=IMAGE_QUALITY_BY_LEVEL[level])
            new_page = result.new_page(width=page.rect.width, height=page.rect.height)
            new_page.insert_image(new_page.rect, stream=img_bytes)
        result.save(output_path, garbage=4, deflate=True, clean=True)
    finally:
        result.close()
        source.close()
    return _never_larger(input_path, output_path)


def compress_pdf(input_path: Path, out_dir: Path, level: CompressionLevel) -> Path:
    output_path = out_dir / f"{input_path.stem}_compressed.pdf"
    gs = command_path(
        settings.ghostscript_bin,
        [
            r"C:\Program Files\gs\*\bin\gswin64c.exe",
            r"C:\Program Files (x86)\gs\*\bin\gswin32c.exe",
            "gs",
        ],
    )
    if gs:
        args = [
            gs,
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            f"-dPDFSETTINGS={GHOSTSCRIPT_PRESET_BY_LEVEL[level]}",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            f"-sOutputFile={output_path}",
            str(input_path),
        ]
        try:
            run_command(args, timeout=240)
            return _never_larger(input_path, output_path)
        except Exception:
            pass
    return _compress_pdf_via_rasterize(input_path, out_dir, level)


def compress_office_document(input_path: Path, out_dir: Path, level: CompressionLevel) -> Path:
    """
    Repack ZIP-based Office containers. This keeps the original file type.
    Never return a larger file.
    """
    import zipfile

    output_path = out_dir / f"{input_path.stem}_compressed{input_path.suffix}"
    try:
        with zipfile.ZipFile(input_path, "r") as source, zipfile.ZipFile(
            output_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as destination:
            for item in source.infolist():
                destination.writestr(
                    item.filename,
                    source.read(item.filename),
                    compress_type=zipfile.ZIP_DEFLATED,
                    compresslevel=9,
                )
        return _never_larger(input_path, output_path)
    except Exception:
        output_path.unlink(missing_ok=True)
        fallback = out_dir / f"{input_path.stem}_compressed{input_path.suffix}"
        shutil.copy2(input_path, fallback)
        return fallback


def compress_file(input_path: Path, out_dir: Path, level: CompressionLevel) -> Path:
    ext = input_path.suffix.lower().lstrip(".")
    if ext == "pdf":
        return compress_pdf(input_path, out_dir, level)
    if ext in ("jpg", "jpeg", "png", "webp", "tiff", "tif"):
        return compress_image(input_path, out_dir, level)
    if ext in ("docx", "pptx", "xlsx", "odt", "ods", "odp"):
        return compress_office_document(input_path, out_dir, level)
    raise ValueError(f"Compression is not supported for .{ext} files.")
