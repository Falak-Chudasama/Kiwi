from __future__ import annotations

import io
import shutil
import zipfile
from enum import Enum
from pathlib import Path

import fitz
import pikepdf
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
ZIP_DEFLATE_LEVEL_BY_LEVEL = {
    CompressionLevel.LOW: 5,
    CompressionLevel.MEDIUM: 7,
    CompressionLevel.HIGH: 9,
    CompressionLevel.EXTREME: 9,
}
GHOSTSCRIPT_PRESET_BY_LEVEL = {
    CompressionLevel.LOW: "/printer",
    CompressionLevel.MEDIUM: "/ebook",
    CompressionLevel.HIGH: "/ebook",
    CompressionLevel.EXTREME: "/screen",
}


def _oxipng_optimize_in_place(png_path: Path, level: CompressionLevel) -> None:
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
        pass


def _never_larger(original: Path, candidate: Path) -> Path:
    """Ensures Kiwi never returns an output file larger than the input."""
    if candidate.exists() and candidate.stat().st_size < original.stat().st_size:
        return candidate
    candidate.unlink(missing_ok=True)
    shutil.copy2(original, candidate)
    return candidate


def compress_image(input_path: Path, out_dir: Path, level: CompressionLevel) -> Path:
    ext = input_path.suffix.lower().lstrip(".")
    out_dir.mkdir(parents=True, exist_ok=True)
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
                    if rgba.getchannel("A").getextrema() == (255, 255):
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
            output_path.unlink(missing_ok=True)
            image.convert("RGB").save(output_path)
    finally:
        image.close()

    return _never_larger(input_path, output_path)


def compress_pdf(input_path: Path, out_dir: Path, level: CompressionLevel) -> Path:
    """Non-destructive PDF compression.

    Tries Ghostscript vector/font optimization first.
    If Ghostscript is unavailable, performs non-destructive pikepdf/PyMuPDF
    stream compression and object deduplication.
    Never silently rasterizes pages to destroy text/vectors/forms/accessibility.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / f"{input_path.stem}_compressed.pdf"

    # 1. Try Ghostscript if available
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
            if output_path.exists() and output_path.stat().st_size > 0:
                return _never_larger(input_path, output_path)
        except Exception:
            output_path.unlink(missing_ok=True)

    # 2. Non-destructive stream and resource optimization via pikepdf
    try:
        with pikepdf.open(input_path) as pdf:
            pdf.remove_unreferenced_resources()
            pdf.save(
                output_path,
                compress_streams=True,
                object_stream_mode=pikepdf.ObjectStreamMode.generate,
            )
        if output_path.exists() and output_path.stat().st_size > 0:
            return _never_larger(input_path, output_path)
    except Exception:
        output_path.unlink(missing_ok=True)

    # 3. Non-destructive PyMuPDF clean/deflate pass
    try:
        doc = fitz.open(input_path)
        try:
            doc.save(output_path, garbage=4, deflate=True, clean=True)
            return _never_larger(input_path, output_path)
        finally:
            doc.close()
    except Exception:
        output_path.unlink(missing_ok=True)
        shutil.copy2(input_path, output_path)
        return output_path


def _optimize_inner_media(data: bytes, filename: str, level: CompressionLevel) -> bytes:
    """Best-effort optimization of embedded images inside an Office document."""
    lower = filename.lower()
    if not (lower.endswith(".jpg") or lower.endswith(".jpeg") or lower.endswith(".png")):
        return data

    try:
        img = Image.open(io.BytesIO(data))
        quality = 75 if level == CompressionLevel.HIGH else 60
        out_buf = io.BytesIO()
        if lower.endswith((".jpg", ".jpeg")):
            img.convert("RGB").save(out_buf, format="JPEG", quality=quality, optimize=True)
        elif lower.endswith(".png"):
            img.save(out_buf, format="PNG", optimize=True, compress_level=9)
        compressed_bytes = out_buf.getvalue()
        if len(compressed_bytes) < len(data):
            return compressed_bytes
    except Exception:
        pass
    return data


def compress_office_document(input_path: Path, out_dir: Path, level: CompressionLevel) -> Path:
    """Repack ZIP-based Office containers with the requested compression strength,
    optionally optimizing embedded media on HIGH/EXTREME settings.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / f"{input_path.stem}_compressed{input_path.suffix}"
    compress_level = ZIP_DEFLATE_LEVEL_BY_LEVEL.get(level, 9)

    try:
        with zipfile.ZipFile(input_path, "r") as source, zipfile.ZipFile(
            output_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=compress_level
        ) as destination:
            for item in source.infolist():
                data = source.read(item.filename)
                # Optimize embedded media files on high/extreme levels
                if level in (CompressionLevel.HIGH, CompressionLevel.EXTREME) and (
                    "/media/" in item.filename or "\\media\\" in item.filename
                ):
                    data = _optimize_inner_media(data, item.filename, level)

                destination.writestr(
                    item.filename,
                    data,
                    compress_type=zipfile.ZIP_DEFLATED,
                    compresslevel=compress_level,
                )
        return _never_larger(input_path, output_path)
    except Exception:
        output_path.unlink(missing_ok=True)
        shutil.copy2(input_path, output_path)
        return output_path


def compress_file(input_path: Path, out_dir: Path, level: CompressionLevel) -> Path:
    ext = input_path.suffix.lower().lstrip(".")
    if ext == "pdf":
        return compress_pdf(input_path, out_dir, level)
    if ext in ("jpg", "jpeg", "png", "webp", "tiff", "tif"):
        return compress_image(input_path, out_dir, level)
    if ext in ("docx", "pptx", "xlsx", "odt", "ods", "odp"):
        return compress_office_document(input_path, out_dir, level)
    raise ValueError(f"Compression is not supported for .{ext} files.")
