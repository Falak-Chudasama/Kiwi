from __future__ import annotations

import mimetypes
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any

import pymupdf as fitz
from docx import Document
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from PIL import Image
from pydantic import BaseModel, Field
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


# ============================================================================
# Kiwi application setup
# ============================================================================

ROOT = Path(__file__).resolve().parent

WORK = ROOT / ".kiwi-work"
WORK.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Kiwi Local File Utility",
    docs_url="/api/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Uploaded-file registry
# ============================================================================

# Maps Kiwi's temporary file ID -> local file path
files: dict[str, Path] = {}


# ============================================================================
# Supported formats
# ============================================================================

IMAGE_EXTS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
    ".avif",
    ".gif",
}

PDF_EXTS = {
    ".pdf",
}

DOC_EXTS = {
    ".md",
    ".markdown",
    ".txt",
    ".docx",
    ".doc",
    ".odt",
    ".rtf",
    ".html",
    ".htm",
}

VIDEO_EXTS = {
    ".mp4",
    ".mkv",
    ".mov",
    ".avi",
    ".webm",
    ".m4v",
    ".mpeg",
    ".mpg",
}

AUDIO_EXTS = {
    ".mp3",
    ".wav",
    ".flac",
    ".aac",
    ".ogg",
    ".opus",
    ".m4a",
}


# ============================================================================
# Utility helpers
# ============================================================================

def tool(name: str) -> str | None:
    """
    Return the executable path if a local command is available.
    """
    return shutil.which(name)


def kind(path: Path) -> str:
    """
    Determine a broad file category.
    """

    ext = path.suffix.lower()

    if ext in IMAGE_EXTS:
        return "image"

    if ext in PDF_EXTS:
        return "pdf"

    if ext in VIDEO_EXTS:
        return "video"

    if ext in AUDIO_EXTS:
        return "audio"

    if ext in DOC_EXTS:
        return "document"

    return "file"


def mime(path: Path) -> str:
    """
    Guess MIME type from the filename.
    """

    return (
        mimetypes.guess_type(path.name)[0]
        or "application/octet-stream"
    )


def target_list(
    *pairs: tuple[str, str],
) -> list[dict[str, str]]:
    """
    Convert target tuples into the structure expected by the frontend.
    """

    return [
        {
            "id": target_id,
            "label": label,
        }
        for target_id, label in pairs
    ]


# ============================================================================
# Capability detection
# ============================================================================

def capabilities(
    path: Path,
) -> list[dict[str, Any]]:
    """
    Determine what Kiwi can do with a file.

    The frontend uses this instead of displaying a giant list
    of every possible operation.
    """

    file_kind = kind(path)
    ext = path.suffix.lower()

    output: list[dict[str, Any]] = []

    # ------------------------------------------------------------------------
    # Images
    # ------------------------------------------------------------------------

    if file_kind == "image":
        output.append(
            {
                "id": "convert_image",
                "label": "Convert",
                "description": "Choose another image format.",
                "targets": target_list(
                    ("jpg", "JPG"),
                    ("png", "PNG"),
                    ("webp", "WebP"),
                    ("tiff", "TIFF"),
                ),
            }
        )

        output.append(
            {
                "id": "compress_image",
                "label": "Compress",
                "description": "Reduce the image size.",
            }
        )

        output.append(
            {
                "id": "images_to_pdf",
                "label": "Image to PDF",
                "description": "Create a PDF from the selected image.",
            }
        )

    # ------------------------------------------------------------------------
    # PDFs
    # ------------------------------------------------------------------------

    elif file_kind == "pdf":
        output.append(
            {
                "id": "pdf_to_image",
                "label": "Convert to images",
                "description": "Render PDF pages as image files.",
                "targets": target_list(
                    ("png", "PNG"),
                    ("jpg", "JPG"),
                    ("webp", "WebP"),
                ),
            }
        )

        output.append(
            {
                "id": "extract_pdf_text",
                "label": "Extract text",
                "description": "Create a plain-text copy of the PDF.",
            }
        )

        output.append(
            {
                "id": "split_pdf",
                "label": "Split PDF",
                "description": "Create one PDF file per page.",
            }
        )

        # Important:
        # This is shown for PDFs so the frontend can expose the merge
        # operation when multiple PDFs are selected.
        output.append(
            {
                "id": "merge_pdf",
                "label": "Merge PDFs",
                "description": "Combine multiple PDFs into one PDF.",
            }
        )

    # ------------------------------------------------------------------------
    # Documents
    # ------------------------------------------------------------------------

    elif file_kind == "document":
        targets: list[tuple[str, str]] = []

        # Markdown -> DOCX/PDF/HTML via Pandoc
        if ext in {".md", ".markdown"} and tool("pandoc"):
            targets.extend(
                [
                    ("docx", "DOCX"),
                    ("pdf", "PDF"),
                    ("html", "HTML"),
                ]
            )

        # TXT -> PDF/DOCX can be done without external tools
        if ext == ".txt":
            targets.extend(
                [
                    ("pdf", "PDF"),
                    ("docx", "DOCX"),
                ]
            )

        # Office-style document -> PDF via LibreOffice
        if ext in {".docx", ".odt", ".rtf"} and (
            tool("libreoffice") or tool("soffice")
        ):
            targets.append(
                ("pdf", "PDF")
            )

        if targets:
            output.append(
                {
                    "id": "convert_document",
                    "label": "Convert",
                    "description": (
                        "Use the best local document engine available."
                    ),
                    "targets": target_list(*targets),
                }
            )

    # ------------------------------------------------------------------------
    # Audio / video
    # ------------------------------------------------------------------------

    elif file_kind in {"video", "audio"} and tool("ffmpeg"):
        if file_kind == "video":
            targets = target_list(
                ("mp4", "MP4"),
                ("webm", "WebM"),
                ("gif", "GIF"),
            )
        else:
            targets = target_list(
                ("mp3", "MP3"),
                ("wav", "WAV"),
                ("flac", "FLAC"),
                ("m4a", "M4A"),
            )

        output.append(
            {
                "id": "convert_media",
                "label": "Convert",
                "description": "Transcode locally with FFmpeg.",
                "targets": targets,
            }
        )

    return output


# ============================================================================
# Health check
# ============================================================================

@app.get("/api/health")
def health():
    """
    Simple local health check.
    """

    return {
        "ok": True,
        "offline": True,
        "engines": {
            "pandoc": bool(tool("pandoc")),
            "libreoffice": bool(
                tool("libreoffice") or tool("soffice")
            ),
            "ffmpeg": bool(tool("ffmpeg")),
        },
    }


# ============================================================================
# Upload + analyze
# ============================================================================

@app.post("/api/analyze")
async def analyze(
    uploaded_files: list[UploadFile] = File(..., alias="files"),
):
    """
    Accept uploaded files under the multipart field name "files".

    The frontend sends:
        form.append("files", file)

    The alias is therefore important.
    """

    result: list[dict[str, Any]] = []

    for upload in uploaded_files:
        file_id = uuid.uuid4().hex

        safe_name = Path(
            upload.filename or "file"
        ).name

        destination = (
            WORK / f"{file_id}_{safe_name}"
        )

        with destination.open("wb") as output_file:
            while True:
                chunk = await upload.read(1024 * 1024)

                if not chunk:
                    break

                output_file.write(chunk)

        files[file_id] = destination

        result.append(
            {
                "id": file_id,
                "name": safe_name,
                "size": destination.stat().st_size,
                "mime": mime(destination),
                "kind": kind(destination),
                "capabilities": capabilities(destination),
            }
        )

    return {
        "files": result,
    }


# ============================================================================
# Processing request model
# ============================================================================

class ProcessRequest(BaseModel):
    file_ids: list[str]
    operation: str
    target: str | None = None
    options: dict[str, Any] = Field(
        default_factory=dict
    )


# ============================================================================
# Uploaded-file validation
# ============================================================================

def require_ids(
    ids: list[str],
) -> list[Path]:
    """
    Resolve Kiwi file IDs to local filesystem paths.
    """

    if not ids:
        raise HTTPException(
            status_code=400,
            detail="No files supplied.",
        )

    resolved: list[Path] = []

    for file_id in ids:
        path = files.get(file_id)

        if path is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    "File session expired. "
                    "Please select the files again."
                ),
            )

        if not path.exists():
            raise HTTPException(
                status_code=404,
                detail=(
                    "One or more selected files "
                    "are no longer available."
                ),
            )

        resolved.append(path)

    return resolved


# ============================================================================
# Local command execution
# ============================================================================

def run_cmd(
    args: list[str],
    cwd: Path | None = None,
) -> None:
    """
    Run a local executable.

    No file is sent anywhere over the network.
    """

    try:
        subprocess.run(
            args,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            timeout=300,
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=400,
            detail=(
                "Required local engine is not installed: "
                f"{args[0]}"
            ),
        )

    except subprocess.CalledProcessError as exc:
        message = (
            exc.stderr[-1500:]
            if exc.stderr
            else "Local conversion engine failed."
        )

        raise HTTPException(
            status_code=400,
            detail=message,
        )

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=408,
            detail=(
                "Conversion took too long and was stopped."
            ),
        )


# ============================================================================
# PDF operations
# ============================================================================

def merge_pdfs(
    paths: list[Path],
) -> Path:
    """
    Merge PDFs using the modern pypdf API.

    PdfMerger is intentionally NOT used because newer pypdf versions
    no longer expose it.
    """

    if not paths:
        raise HTTPException(
            status_code=400,
            detail="No PDFs supplied.",
        )

    if not all(
        path.suffix.lower() == ".pdf"
        for path in paths
    ):
        raise HTTPException(
            status_code=400,
            detail="All selected files must be PDFs.",
        )

    output = (
        WORK / f"{uuid.uuid4().hex}_merged.pdf"
    )

    writer = PdfWriter()

    for path in paths:
        reader = PdfReader(str(path))

        for page in reader.pages:
            writer.add_page(page)

    with output.open("wb") as output_file:
        writer.write(output_file)

    return output


def pdf_to_images(
    paths: list[Path],
    target: str,
) -> Path:
    """
    Render PDF pages to images and return a ZIP.
    """

    if len(paths) != 1:
        raise HTTPException(
            status_code=400,
            detail=(
                "PDF to image conversion "
                "currently accepts one PDF."
            ),
        )

    source = paths[0]

    if source.suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="Input must be a PDF.",
        )

    if target not in {
        "png",
        "jpg",
        "webp",
    }:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported image target."
            ),
        )

    output_dir = (
        WORK / f"{uuid.uuid4().hex}_pages"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    document = fitz.open(str(source))

    try:
        for index, page in enumerate(document):
            pixmap = page.get_pixmap(
                matrix=fitz.Matrix(1.6, 1.6),
                alpha=False,
            )

            extension = (
                "jpg"
                if target == "jpg"
                else target
            )

            destination = (
                output_dir
                / f"page-{index + 1}.{extension}"
            )

            pixmap.save(
                str(destination)
            )

    finally:
        document.close()

    archive_base = (
        WORK / f"{uuid.uuid4().hex}_pages"
    )

    archive_path = Path(
        shutil.make_archive(
            str(archive_base),
            "zip",
            output_dir,
        )
    )

    shutil.rmtree(
        output_dir,
        ignore_errors=True,
    )

    return archive_path


def extract_pdf_text(
    path: Path,
) -> Path:
    """
    Extract text from a PDF.
    """

    document = fitz.open(str(path))

    try:
        text = "\n\n".join(
            page.get_text()
            for page in document
        )
    finally:
        document.close()

    output = (
        WORK
        / f"{path.stem}_extracted.txt"
    )

    output.write_text(
        text,
        encoding="utf-8",
    )

    return output


def split_pdf(
    path: Path,
) -> Path:
    """
    Split a PDF into one PDF per page and return a ZIP.
    """

    document = fitz.open(str(path))

    output_dir = (
        WORK / f"{uuid.uuid4().hex}_split"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        for index in range(len(document)):
            one_page = fitz.open()

            try:
                one_page.insert_pdf(
                    document,
                    from_page=index,
                    to_page=index,
                )

                destination = (
                    output_dir
                    / f"{path.stem}_page_{index + 1}.pdf"
                )

                one_page.save(
                    str(destination)
                )

            finally:
                one_page.close()

    finally:
        document.close()

    archive_base = (
        WORK / f"{uuid.uuid4().hex}_split"
    )

    archive_path = Path(
        shutil.make_archive(
            str(archive_base),
            "zip",
            output_dir,
        )
    )

    shutil.rmtree(
        output_dir,
        ignore_errors=True,
    )

    return archive_path


# ============================================================================
# Image operations
# ============================================================================

def image_convert(
    paths: list[Path],
    target: str,
    quality: str = "balanced",
) -> Path:
    """
    Convert one or more images.
    """

    if not paths:
        raise HTTPException(
            status_code=400,
            detail="No images supplied.",
        )

    output_dir = (
        WORK / f"{uuid.uuid4().hex}_images"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    quality_value = {
        "small": 65,
        "balanced": 82,
        "quality": 94,
    }.get(
        quality,
        82,
    )

    target = target.lower()

    if target == "jpg":
        actual_extension = "jpg"
        format_name = "JPEG"

    elif target == "png":
        actual_extension = "png"
        format_name = "PNG"

    elif target == "webp":
        actual_extension = "webp"
        format_name = "WEBP"

    elif target == "tiff":
        actual_extension = "tiff"
        format_name = "TIFF"

    else:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported image target: {target}"
            ),
        )

    for source in paths:
        with Image.open(source) as image:
            current = image

            if target == "jpg":
                if current.mode not in {
                    "RGB",
                    "L",
                }:
                    current = current.convert(
                        "RGB"
                    )

                save_options: dict[str, Any] = {
                    "quality": quality_value,
                    "optimize": True,
                }

            elif target == "webp":
                save_options = {
                    "quality": quality_value,
                    "optimize": True,
                }

            elif target == "png":
                save_options = {
                    "optimize": True,
                }

            else:
                save_options = {}

            destination = (
                output_dir
                / f"{source.stem}.{actual_extension}"
            )

            current.save(
                destination,
                format=format_name,
                **save_options,
            )

    # One input -> one output
    if len(paths) == 1:
        return next(
            output_dir.iterdir()
        )

    # Multiple inputs -> ZIP
    archive_base = (
        WORK / f"{uuid.uuid4().hex}_converted"
    )

    archive_path = Path(
        shutil.make_archive(
            str(archive_base),
            "zip",
            output_dir,
        )
    )

    shutil.rmtree(
        output_dir,
        ignore_errors=True,
    )

    return archive_path


def images_to_pdf(
    paths: list[Path],
) -> Path:
    """
    Combine one or more images into a single PDF.
    """

    if not paths:
        raise HTTPException(
            status_code=400,
            detail="No images supplied.",
        )

    converted: list[Image.Image] = []

    try:
        for path in paths:
            with Image.open(path) as image:
                converted.append(
                    image.convert("RGB")
                )

        output = (
            WORK
            / f"{uuid.uuid4().hex}_images.pdf"
        )

        converted[0].save(
            output,
            save_all=True,
            append_images=converted[1:],
        )

        return output

    finally:
        for image in converted:
            image.close()


# ============================================================================
# Text/document operations
# ============================================================================

def text_to_pdf(
    path: Path,
) -> Path:
    """
    Very simple TXT -> PDF conversion.
    """

    output = (
        WORK / f"{uuid.uuid4().hex}.pdf"
    )

    page_width, page_height = A4

    pdf = canvas.Canvas(
        str(output),
        pagesize=A4,
    )

    pdf.setFont(
        "Helvetica",
        10,
    )

    y = page_height - 48

    text = path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    for raw_line in text.splitlines():
        line = raw_line[:115]

        pdf.drawString(
            42,
            y,
            line,
        )

        y -= 14

        if y < 42:
            pdf.showPage()

            pdf.setFont(
                "Helvetica",
                10,
            )

            y = page_height - 48

    pdf.save()

    return output


def text_to_docx(
    path: Path,
) -> Path:
    """
    Simple TXT -> DOCX conversion.
    """

    output = (
        WORK / f"{uuid.uuid4().hex}.docx"
    )

    document = Document()

    text = path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    for line in text.splitlines():
        document.add_paragraph(line)

    document.save(output)

    return output


# ============================================================================
# Main processing endpoint
# ============================================================================

@app.post("/api/process")
def process(
    request: ProcessRequest,
):
    paths = require_ids(
        request.file_ids
    )

    operation = request.operation

    target = (
        request.target or ""
    ).lower()

    quality = str(
        request.options.get(
            "quality",
            "balanced",
        )
    )

    try:
        # --------------------------------------------------------------------
        # Merge PDFs
        # --------------------------------------------------------------------

        if operation == "merge_pdf":
            output = merge_pdfs(paths)

        # --------------------------------------------------------------------
        # Images -> PDF
        # --------------------------------------------------------------------

        elif operation == "images_to_pdf":
            if not all(
                kind(path) == "image"
                for path in paths
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "All selected files "
                        "must be images."
                    ),
                )

            output = images_to_pdf(paths)

        # --------------------------------------------------------------------
        # Image conversion
        # --------------------------------------------------------------------

        elif operation == "convert_image":
            if not all(
                kind(path) == "image"
                for path in paths
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "All selected files "
                        "must be images."
                    ),
                )

            output = image_convert(
                paths,
                target,
                quality,
            )

        # --------------------------------------------------------------------
        # Image compression
        # --------------------------------------------------------------------

        elif operation == "compress_image":
            if not all(
                kind(path) == "image"
                for path in paths
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "All selected files "
                        "must be images."
                    ),
                )

            original_extension = (
                paths[0]
                .suffix
                .lower()
                .lstrip(".")
            )

            if original_extension == "jpeg":
                original_extension = "jpg"

            if original_extension not in {
                "jpg",
                "png",
                "webp",
                "tiff",
            }:
                original_extension = "webp"

            output = image_convert(
                paths,
                original_extension,
                quality,
            )

        # --------------------------------------------------------------------
        # PDF -> images
        # --------------------------------------------------------------------

        elif operation == "pdf_to_image":
            output = pdf_to_images(
                paths,
                target,
            )

        # --------------------------------------------------------------------
        # PDF -> TXT
        # --------------------------------------------------------------------

        elif operation == "extract_pdf_text":
            if len(paths) != 1:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Text extraction currently "
                        "accepts one PDF."
                    ),
                )

            output = extract_pdf_text(
                paths[0]
            )

        # --------------------------------------------------------------------
        # Split PDF
        # --------------------------------------------------------------------

        elif operation == "split_pdf":
            if len(paths) != 1:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Split PDF currently "
                        "accepts one PDF."
                    ),
                )

            output = split_pdf(
                paths[0]
            )

        # --------------------------------------------------------------------
        # Documents
        # --------------------------------------------------------------------

        elif operation == "convert_document":
            if len(paths) != 1:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Document conversion "
                        "currently accepts one file."
                    ),
                )

            source = paths[0]
            source_extension = (
                source.suffix.lower()
            )

            # TXT -> PDF
            if (
                source_extension == ".txt"
                and target == "pdf"
            ):
                output = text_to_pdf(
                    source
                )

            # TXT -> DOCX
            elif (
                source_extension == ".txt"
                and target == "docx"
            ):
                output = text_to_docx(
                    source
                )

            # Pandoc conversion
            elif (
                target in {
                    "docx",
                    "pdf",
                    "html",
                }
                and tool("pandoc")
            ):
                pandoc = (
                    tool("pandoc")
                    or "pandoc"
                )

                output = (
                    WORK
                    / f"{uuid.uuid4().hex}.{target}"
                )

                run_cmd(
                    [
                        pandoc,
                        str(source),
                        "-o",
                        str(output),
                    ]
                )

            # LibreOffice -> PDF
            elif target == "pdf":
                libreoffice = (
                    tool("libreoffice")
                    or tool("soffice")
                )

                if not libreoffice:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "LibreOffice "
                            "is not installed."
                        ),
                    )

                output_dir = (
                    WORK
                    / f"{uuid.uuid4().hex}_office"
                )

                output_dir.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                run_cmd(
                    [
                        libreoffice,
                        "--headless",
                        "--convert-to",
                        "pdf",
                        "--outdir",
                        str(output_dir),
                        str(source),
                    ]
                )

                generated = list(
                    output_dir.glob("*.pdf")
                )

                if not generated:
                    raise HTTPException(
                        status_code=500,
                        detail=(
                            "LibreOffice did not "
                            "produce a PDF."
                        ),
                    )

                output = generated[0]

            else:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "This conversion requires "
                        "Pandoc or LibreOffice."
                    ),
                )

        # --------------------------------------------------------------------
        # Media
        # --------------------------------------------------------------------

        elif operation == "convert_media":
            if not tool("ffmpeg"):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "FFmpeg is not installed."
                    ),
                )

            if len(paths) != 1:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Media conversion "
                        "currently accepts one file."
                    ),
                )

            ffmpeg = (
                tool("ffmpeg")
                or "ffmpeg"
            )

            output = (
                WORK
                / f"{uuid.uuid4().hex}.{target}"
            )

            run_cmd(
                [
                    ffmpeg,
                    "-y",
                    "-i",
                    str(paths[0]),
                    str(output),
                ]
            )

        # --------------------------------------------------------------------
        # Unknown operation
        # --------------------------------------------------------------------

        else:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unsupported operation: "
                    f"{operation}"
                ),
            )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

    return {
        "id": uuid.uuid4().hex,
        "status": "done",
        "output_name": output.name,
        "download_url": (
            f"/api/download/{output.name}"
        ),
    }


# ============================================================================
# Download
# ============================================================================

@app.get("/api/download/{name}")
def download(
    name: str,
):
    """
    Download a locally generated Kiwi output.
    """

    safe_name = Path(name).name

    path = WORK / safe_name

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="Output expired.",
        )

    return FileResponse(
        path,
        filename=path.name,
        media_type=mime(path),
    )