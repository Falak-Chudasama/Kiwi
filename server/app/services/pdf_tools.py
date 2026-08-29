from __future__ import annotations

import io
from pathlib import Path

import fitz
import pikepdf
from PIL import Image, ImageDraw, ImageFont

from app.core.config import settings
from app.core.files import command_path


def _oxipng_optimize(png_path: Path) -> None:
    """Best-effort lossless PNG re-optimization; skipped if oxipng isn't installed."""
    try:
        import oxipng
        oxipng.optimize(str(png_path), level=3)
    except Exception:
        pass


def merge_pdfs(input_paths: list[Path], out_dir: Path) -> Path:
    if len(input_paths) < 2:
        raise ValueError("Select at least two PDFs to merge.")
    output_path = out_dir / "merged.pdf"
    target = pikepdf.Pdf.new()
    for path in input_paths:
        with pikepdf.open(path) as src:
            target.pages.extend(src.pages)
    target.save(output_path)
    return output_path


def split_pdf(input_path: Path, out_dir: Path, page_ranges: list[tuple[int, int]]) -> list[Path]:
    outputs: list[Path] = []
    with pikepdf.open(input_path) as src:
        page_count = len(src.pages)
        for idx, (start, end) in enumerate(page_ranges, start=1):
            if start < 1 or end > page_count or start > end:
                raise ValueError(f"Invalid page range {start}-{end} for a {page_count}-page PDF.")
            chunk = pikepdf.Pdf.new()
            chunk.pages.extend(src.pages[start - 1:end])
            chunk_path = out_dir / f"{input_path.stem}_part{idx}.pdf"
            chunk.save(chunk_path)
            outputs.append(chunk_path)
    return outputs


def rotate_pdf(input_path: Path, out_dir: Path, degrees: int) -> Path:
    if degrees not in {90, 180, 270, -90, -180, -270}:
        raise ValueError("Rotation must be 90, 180, or 270 degrees.")
    output_path = out_dir / f"{input_path.stem}_rotated.pdf"
    with pikepdf.open(input_path) as pdf:
        for page in pdf.pages:
            page.rotate(degrees, relative=True)
        pdf.save(output_path)
    return output_path


def reorder_pdf(input_path: Path, out_dir: Path, new_order: list[int]) -> Path:
    output_path = out_dir / f"{input_path.stem}_reordered.pdf"
    with pikepdf.open(input_path) as src:
        if sorted(new_order) != list(range(len(src.pages))):
            raise ValueError("Page order must contain every page exactly once.")
        result = pikepdf.Pdf.new()
        for index in new_order:
            result.pages.append(src.pages[index])
        result.save(output_path)
    return output_path


def protect_pdf(input_path: Path, out_dir: Path, password: str) -> Path:
    if not password:
        raise ValueError("Password cannot be empty.")
    output_path = out_dir / f"{input_path.stem}_protected.pdf"
    with pikepdf.open(input_path) as pdf:
        pdf.save(output_path, encryption=pikepdf.Encryption(owner=password, user=password, R=6))
    return output_path


def unlock_pdf(input_path: Path, out_dir: Path, password: str) -> Path:
    if not password:
        raise ValueError("Password cannot be empty.")
    output_path = out_dir / f"{input_path.stem}_unlocked.pdf"
    with pikepdf.open(input_path, password=password) as pdf:
        pdf.save(output_path)
    return output_path


def pdf_to_images(input_path: Path, out_dir: Path, image_format: str, dpi: int = 150) -> list[Path]:
    if image_format not in {"png", "jpg", "jpeg", "webp"}:
        raise ValueError("PDF image output must be PNG, JPG, or WEBP.")

    outputs: list[Path] = []
    doc = fitz.open(input_path)
    try:
        matrix = fitz.Matrix(dpi / 72, dpi / 72)
        for page_index in range(len(doc)):
            page = doc.load_page(page_index)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            png = pixmap.tobytes("png")
            image = Image.open(io.BytesIO(png)).convert("RGB")
            page_path = out_dir / f"{input_path.stem}_page{page_index + 1}.{image_format}"
            if image_format in {"jpg", "jpeg"}:
                image.save(page_path, format="JPEG", quality=92, optimize=True)
            elif image_format == "webp":
                image.save(page_path, format="WEBP", quality=90, method=6)
            else:
                image.save(page_path, format="PNG", optimize=True)
                _oxipng_optimize(page_path)
            image.close()
            outputs.append(page_path)
    finally:
        doc.close()
    return outputs


def _open_any_image(path: Path) -> Image.Image:
    """Open an image for PDF assembly, including formats Pillow can't read directly."""
    ext = path.suffix.lower().lstrip(".")
    if ext == "svg":
        import cairosvg

        png_bytes = cairosvg.svg2png(url=str(path))
        return Image.open(io.BytesIO(png_bytes)).convert("RGB")
    if ext in {"heic", "heif"}:
        import pillow_heif

        pillow_heif.register_heif_opener()
    try:
        return Image.open(path).convert("RGB")
    except Exception as exc:
        raise ValueError(
            f"'{path.name}' could not be read as an image. It may be corrupted or in an unsupported format."
        ) from exc


def images_to_pdf(input_paths: list[Path], out_dir: Path) -> Path:
    if not input_paths:
        raise ValueError("Select at least one image.")
    output_path = out_dir / "combined.pdf"
    images = [_open_any_image(p) for p in input_paths]
    try:
        first, rest = images[0], images[1:]
        first.save(output_path, save_all=True, append_images=rest)
    finally:
        for image in images:
            image.close()
    return output_path


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        r"C:\Windows\Fonts\arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            try:
                return ImageFont.truetype(candidate, size=size)
            except OSError:
                pass
    return ImageFont.load_default()


def _watermark_image(
    text: str,
    fontsize: int,
    opacity: float,
    angle: int,
    color: tuple[int, int, int],
) -> tuple[bytes, tuple[int, int]]:
    font = _font(fontsize)
    bbox = font.getbbox(text)
    text_w = max(1, bbox[2] - bbox[0])
    text_h = max(1, bbox[3] - bbox[1])
    pad = max(20, fontsize // 2)
    layer = Image.new("RGBA", (text_w + pad * 2, text_h + pad * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    alpha = int(255 * max(0.05, min(1.0, opacity)))
    draw.text((pad, pad), text, font=font, fill=(*color, alpha))
    rotated = layer.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
    buf = io.BytesIO()
    rotated.save(buf, format="PNG")
    return buf.getvalue(), rotated.size


def watermark_pdf(
    input_path: Path,
    out_dir: Path,
    text: str,
    fontsize: int = 40,
    opacity: float = 0.25,
    angle: int = 35,
    position: str = "center",
    color: tuple[int, int, int] = (120, 120, 120),
) -> Path:
    text = text.strip()
    if not text:
        raise ValueError("Watermark text cannot be empty.")
    if not 8 <= fontsize <= 200:
        raise ValueError("Watermark font size must be between 8 and 200.")
    if not 0.0 <= opacity <= 1.0:
        raise ValueError("Watermark opacity must be between 0 and 1.")

    output_path = out_dir / f"{input_path.stem}_watermarked.pdf"
    png_bytes, (img_w, img_h) = _watermark_image(text, fontsize, opacity, angle, color)

    doc = fitz.open(input_path)
    try:
        for page in doc:
            rect = page.rect
            scale = min(rect.width * 0.75 / img_w, rect.height * 0.50 / img_h)
            scale = max(0.25, min(1.0, scale))
            width, height = img_w * scale, img_h * scale
            margin = 24
            if position == "top-left":
                x0, y0 = margin, margin
            elif position == "top-right":
                x0, y0 = rect.width - width - margin, margin
            elif position == "bottom-left":
                x0, y0 = margin, rect.height - height - margin
            elif position == "bottom-right":
                x0, y0 = rect.width - width - margin, rect.height - height - margin
            else:
                x0, y0 = (rect.width - width) / 2, (rect.height - height) / 2
            target = fitz.Rect(x0, y0, x0 + width, y0 + height)
            # Arbitrary angles are handled by rotating the PNG first.
            # This avoids PyMuPDF's restricted text-rotation enum.
            page.insert_image(target, stream=png_bytes, overlay=True)
        doc.save(output_path)
    finally:
        doc.close()
    return output_path


def ocr_pdf(input_path: Path, out_dir: Path, language: str = "eng") -> Path:
    import pytesseract
    from pytesseract import Output

    tesseract = command_path(
        settings.tesseract_bin,
        [r"C:\Program Files\Tesseract-OCR\tesseract.exe"],
    )
    if not tesseract:
        raise RuntimeError(
            "OCR needs Tesseract OCR installed and available on PATH. "
            "Install Tesseract, restart Kiwi, or set KIWI_TESSERACT_BIN."
        )

    pytesseract.pytesseract.tesseract_cmd = tesseract

    output_path = out_dir / f"{input_path.stem}_ocr.pdf"
    source = fitz.open(input_path)
    result = fitz.open()
    dpi = 170
    matrix = fitz.Matrix(dpi / 72, dpi / 72)

    try:
        for source_page in source:
            pixmap = source_page.get_pixmap(matrix=matrix, colorspace=fitz.csRGB, alpha=False)
            jpeg_bytes = pixmap.tobytes("jpeg", jpg_quality=78)
            image = Image.open(io.BytesIO(jpeg_bytes)).convert("RGB")
            page = result.new_page(width=source_page.rect.width, height=source_page.rect.height)
            page.insert_image(page.rect, stream=jpeg_bytes)

            try:
                data = pytesseract.image_to_data(
                    image,
                    lang=language,
                    config="--psm 3",
                    output_type=Output.DICT,
                )
            except pytesseract.TesseractError as exc:
                raise RuntimeError(
                    f"Tesseract could not run with language '{language}'. "
                    "Make sure that language data is installed."
                ) from exc

            scale = 72 / dpi
            for index, raw_text in enumerate(data["text"]):
                text = raw_text.strip()
                if not text:
                    continue
                try:
                    confidence = float(data["conf"][index])
                except (TypeError, ValueError):
                    confidence = -1
                if confidence < 20:
                    continue
                x = float(data["left"][index]) * scale
                y = float(data["top"][index]) * scale
                w = float(data["width"][index]) * scale
                h = float(data["height"][index]) * scale
                rect = fitz.Rect(x, y, x + max(w, 1), y + max(h * 1.35, 6))
                fontsize = max(4.0, min(40.0, h * 0.82))
                try:
                    page.insert_textbox(
                        rect,
                        text,
                        fontname="helv",
                        fontsize=fontsize,
                        color=(0, 0, 0),
                        render_mode=3,
                        overlay=True,
                    )
                except (ValueError, RuntimeError):
                    continue
            image.close()

        result.save(output_path, garbage=4, deflate=True, clean=True)
    finally:
        result.close()
        source.close()

    return output_path
