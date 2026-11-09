from __future__ import annotations

import base64
import io
import warnings
from pathlib import Path

from PIL import Image, ImageOps

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    pillow_heif.register_avif_opener()
except (ImportError, AttributeError):
    pass

# Decompression bomb safety: limit maximum decoded pixels to 100MP
Image.MAX_IMAGE_PIXELS = 100_000_000
warnings.filterwarnings("error", category=Image.DecompressionBombWarning)


def _oxipng_optimize(png_path: Path) -> None:
    """Best-effort lossless PNG re-optimization pass on top of Pillow's encode."""
    try:
        import oxipng
        oxipng.optimize(str(png_path), level=3)
    except Exception:
        pass


ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]

PILLOW_SAVE_FORMAT = {
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "png": "PNG",
    "webp": "WEBP",
    "avif": "AVIF",
    "gif": "GIF",
    "bmp": "BMP",
    "tiff": "TIFF",
    "tif": "TIFF",
    "ico": "ICO",
    "heic": "HEIF",
    "heif": "HEIF",
}

FLATTEN_BACKGROUND_FORMATS = {"jpg", "jpeg", "bmp"}


def probe_supported_image_formats() -> dict[str, bool]:
    """Dynamically probes runtime Pillow encoder capabilities for image formats."""
    results: dict[str, bool] = {}
    test_img = Image.new("RGB", (8, 8), color="white")
    for ext, fmt in PILLOW_SAVE_FORMAT.items():
        try:
            buf = io.BytesIO()
            test_img.save(buf, format=fmt)
            results[ext] = True
        except Exception:
            results[ext] = False
    results["svg"] = True  # CairoSVG / container support
    test_img.close()
    return results


def _load_source_image(input_path: Path) -> Image.Image:
    ext = input_path.suffix.lower().lstrip(".")
    if ext == "svg":
        import cairosvg
        png_bytes = cairosvg.svg2png(url=str(input_path))
        return Image.open(io.BytesIO(png_bytes))

    with warnings.catch_warnings():
        warnings.filterwarnings("error", category=Image.DecompressionBombWarning)
        try:
            img = Image.open(input_path)
            if (img.width * img.height) > Image.MAX_IMAGE_PIXELS:
                img.close()
                raise ValueError("Image exceeds maximum allowed dimensions/pixels (decompression bomb protection).")
            return img
        except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
            raise ValueError("Image exceeds maximum allowed dimensions/pixels (decompression bomb protection).") from exc


def _resize(image: Image.Image, width: int | None, height: int | None, fit_mode: str) -> Image.Image:
    if width is None and height is None:
        return image
    if width is not None and height is not None:
        if fit_mode == "exact":
            return image.resize((width, height), Image.Resampling.LANCZOS)
        # Contain: preserves aspect ratio within the given bounds
        return ImageOps.contain(image, (width, height), Image.Resampling.LANCZOS)
    if width is not None:
        new_height = max(1, round(image.height * width / image.width))
        return image.resize((width, new_height), Image.Resampling.LANCZOS)
    assert height is not None
    new_width = max(1, round(image.width * height / image.height))
    return image.resize((new_width, height), Image.Resampling.LANCZOS)


def _prepare_for_format(image: Image.Image, target_ext: str) -> Image.Image:
    if target_ext in FLATTEN_BACKGROUND_FORMATS and image.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        rgba = image.convert("RGBA")
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    if target_ext in {"jpg", "jpeg"} and image.mode != "RGB":
        return image.convert("RGB")
    return image


def convert_image(
    input_path: Path,
    target_ext: str,
    out_dir: Path,
    width: int | None = None,
    height: int | None = None,
    fit_mode: str = "contain",
) -> Path:
    target_ext = target_ext.lower().lstrip(".")
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / f"{input_path.stem}.{target_ext}"

    try:
        source = _load_source_image(input_path)
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValueError("Image exceeds maximum allowed dimensions/pixels (decompression bomb protection).") from exc

    try:
        resized = _resize(source, width, height, fit_mode)
        prepared = _prepare_for_format(resized, target_ext)
        save_format = PILLOW_SAVE_FORMAT.get(target_ext, target_ext.upper())

        save_kwargs: dict = {}
        if target_ext in ("jpg", "jpeg"):
            save_kwargs.update(quality=90, optimize=True, progressive=True)
        elif target_ext in ("webp", "avif"):
            save_kwargs.update(quality=90)
        elif target_ext == "png":
            save_kwargs.update(optimize=True, compress_level=9)
        elif target_ext in ("tiff", "tif"):
            save_kwargs.update(compression="tiff_deflate")
        elif target_ext == "gif":
            save_kwargs.update(optimize=True)

        if target_ext == "svg":
            # Transparently wrap raster in SVG container, noting raster containment
            rgba = prepared.convert("RGBA")
            buf = io.BytesIO()
            rgba.save(buf, format="PNG", optimize=True)
            encoded = base64.b64encode(buf.getvalue()).decode("ascii")
            output_path.write_text(
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{rgba.width}" height="{rgba.height}" viewBox="0 0 {rgba.width} {rgba.height}">'
                f'<!-- Embedded raster image in SVG container; not vectorized paths -->'
                f'<image href="data:image/png;base64,{encoded}" width="100%" height="100%" preserveAspectRatio="none"/></svg>',
                encoding="utf-8",
            )
        elif target_ext == "ico":
            sizes = [(s, s) for s in ICO_SIZES if s <= max(prepared.size)] or [(min(prepared.size), min(prepared.size))]
            prepared.save(output_path, format="ICO", sizes=sizes)
        else:
            prepared.save(output_path, format=save_format, **save_kwargs)

        if target_ext == "png":
            _oxipng_optimize(output_path)

        return output_path
    finally:
        source.close()
