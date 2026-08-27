import io
from pathlib import Path

from PIL import Image
import pillow_heif

pillow_heif.register_heif_opener()

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


def _load_source_image(input_path: Path) -> Image.Image:
    ext = input_path.suffix.lower().lstrip(".")
    if ext == "svg":
        import cairosvg

        png_bytes = cairosvg.svg2png(url=str(input_path))
        return Image.open(io.BytesIO(png_bytes))
    return Image.open(input_path)


def _prepare_for_format(image: Image.Image, target_ext: str) -> Image.Image:
    if target_ext in FLATTEN_BACKGROUND_FORMATS and image.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        rgba = image.convert("RGBA")
        background.paste(rgba, mask=rgba.split()[-1])
        return background
    if target_ext in ("jpg", "jpeg") and image.mode != "RGB":
        return image.convert("RGB")
    return image


def convert_image(input_path: Path, target_ext: str, out_dir: Path) -> Path:
    target_ext = target_ext.lower()
    source = _load_source_image(input_path)
    prepared = _prepare_for_format(source, target_ext)
    output_path = out_dir / f"{input_path.stem}.{target_ext}"
    save_format = PILLOW_SAVE_FORMAT.get(target_ext, target_ext.upper())

    if target_ext == "ico":
        sizes = [(s, s) for s in ICO_SIZES if s <= max(prepared.size)]
        if not sizes:
            sizes = [(min(prepared.size), min(prepared.size))]
        prepared.save(output_path, format="ICO", sizes=sizes)
        return output_path

    save_kwargs: dict = {}
    if target_ext in ("jpg", "jpeg", "webp", "avif"):
        save_kwargs["quality"] = 90
    if target_ext == "png":
        save_kwargs["optimize"] = True

    prepared.save(output_path, format=save_format, **save_kwargs)
    return output_path
