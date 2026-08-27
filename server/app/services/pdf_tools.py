from pathlib import Path

import fitz
import pikepdf
from PIL import Image


def merge_pdfs(input_paths: list[Path], out_dir: Path) -> Path:
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
        for idx, (start, end) in enumerate(page_ranges, start=1):
            chunk = pikepdf.Pdf.new()
            chunk.pages.extend(src.pages[start - 1:end])
            chunk_path = out_dir / f"{input_path.stem}_part{idx}.pdf"
            chunk.save(chunk_path)
            outputs.append(chunk_path)
    return outputs


def rotate_pdf(input_path: Path, out_dir: Path, degrees: int) -> Path:
    output_path = out_dir / f"{input_path.stem}_rotated.pdf"
    with pikepdf.open(input_path) as pdf:
        for page in pdf.pages:
            page.rotate(degrees, relative=True)
        pdf.save(output_path)
    return output_path


def reorder_pdf(input_path: Path, out_dir: Path, new_order: list[int]) -> Path:
    output_path = out_dir / f"{input_path.stem}_reordered.pdf"
    with pikepdf.open(input_path) as src:
        result = pikepdf.Pdf.new()
        for index in new_order:
            result.pages.append(src.pages[index])
        result.save(output_path)
    return output_path


def protect_pdf(input_path: Path, out_dir: Path, password: str) -> Path:
    output_path = out_dir / f"{input_path.stem}_protected.pdf"
    with pikepdf.open(input_path) as pdf:
        pdf.save(
            output_path,
            encryption=pikepdf.Encryption(owner=password, user=password, R=6),
        )
    return output_path


def unlock_pdf(input_path: Path, out_dir: Path, password: str) -> Path:
    output_path = out_dir / f"{input_path.stem}_unlocked.pdf"
    with pikepdf.open(input_path, password=password) as pdf:
        pdf.save(output_path)
    return output_path


def pdf_to_images(input_path: Path, out_dir: Path, image_format: str, dpi: int = 150) -> list[Path]:
    outputs: list[Path] = []
    doc = fitz.open(input_path)
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    for page_index in range(len(doc)):
        page = doc.load_page(page_index)
        pixmap = page.get_pixmap(matrix=matrix)
        page_path = out_dir / f"{input_path.stem}_page{page_index + 1}.{image_format}"
        pixmap.pil_save(page_path)
        outputs.append(page_path)
    doc.close()
    return outputs


def images_to_pdf(input_paths: list[Path], out_dir: Path) -> Path:
    output_path = out_dir / "combined.pdf"
    images = [Image.open(p).convert("RGB") for p in input_paths]
    first, rest = images[0], images[1:]
    first.save(output_path, save_all=True, append_images=rest)
    return output_path


def watermark_pdf(input_path: Path, out_dir: Path, text: str) -> Path:
    output_path = out_dir / f"{input_path.stem}_watermarked.pdf"
    doc = fitz.open(input_path)
    for page in doc:
        rect = page.rect
        page.insert_text(
            fitz.Point(rect.width / 4, rect.height / 2),
            text,
            fontsize=40,
            color=(0.6, 0.6, 0.6),
            rotate=45,
            overlay=True,
        )
    doc.save(output_path)
    doc.close()
    return output_path


def ocr_pdf(input_path: Path, out_dir: Path, language: str = "eng") -> Path:
    import ocrmypdf

    output_path = out_dir / f"{input_path.stem}_ocr.pdf"
    ocrmypdf.ocr(input_path, output_path, language=language, skip_text=True)
    return output_path
