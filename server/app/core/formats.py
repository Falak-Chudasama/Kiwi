from __future__ import annotations

import functools
import shutil
from dataclasses import dataclass
from typing import Any

from app.core.config import settings
from app.core.files import command_path


# --- Format Categories & Extensions ---

DOCUMENT_OUTPUT_EXTENSIONS = [
    "pdf", "docx", "doc", "odt", "rtf", "txt", "md", "html", "htm", "epub",
    "tex", "rst", "org", "xml", "pptx", "ppt", "odp", "xlsx", "xls", "ods", "csv",
]

IMAGE_EXTENSIONS = [
    "jpg", "jpeg", "png", "webp", "avif", "gif", "bmp", "tiff", "tif",
    "ico", "heic", "heif", "svg",
]

AUDIO_EXTENSIONS = [
    "mp3", "wav", "flac", "ogg", "opus", "m4a", "aac", "wma",
]

VIDEO_EXTENSIONS = [
    "mp4", "mkv", "webm", "avi", "mov", "m4v", "mpeg", "mpg", "3gp",
]

ARCHIVE_INPUT_EXTENSIONS = [
    "zip", "7z", "tar", "tar.gz", "tgz", "tar.bz2", "tbz2", "tar.xz", "txz", "rar",
]
ARCHIVE_OUTPUT_EXTENSIONS = ["zip", "7z", "tar"]

MEDIA_IMAGE_TARGETS = {"jpg", "jpeg", "png", "webp", "gif", "bmp"}
RENDER_IMAGE_TARGETS = MEDIA_IMAGE_TARGETS | {"tiff", "tif", "ico", "heic", "heif"}

COMPRESSIBLE_EXTENSIONS = {
    "pdf", "jpg", "jpeg", "png", "webp", "tiff", "tif",
    "docx", "pptx", "xlsx", "odt", "ods", "odp",
}

WORD_DOCUMENTS = {"doc", "docx", "odt", "rtf"}
TEXT_DOCUMENTS = {
    "txt", "md", "markdown", "html", "htm", "tex", "rst", "org", "xml",
    "json", "yaml", "yml", "toml", "ini", "cfg", "conf", "log", "sql",
    "py", "js", "jsx", "ts", "tsx", "css", "scss", "sass", "java", "c", "h",
    "cpp", "hpp", "cs", "go", "rs", "php", "rb", "sh", "bat", "ps1", "vue", "svelte",
}
SPREADSHEETS = {"xlsx", "xls", "ods", "csv"}
PRESENTATIONS = {"ppt", "pptx", "odp"}

PANDOC_INPUTS = {
    "txt": "plain",
    "md": "markdown",
    "markdown": "markdown",
    "html": "html",
    "htm": "html",
    "tex": "latex",
    "rst": "rst",
    "org": "org",
    "xml": "docbook",
    "docx": "docx",
    "odt": "odt",
    "rtf": "rtf",
    "epub": "epub",
}

PANDOC_OUTPUTS = {
    "txt": "plain",
    "md": "markdown",
    "html": "html5",
    "htm": "html5",
    "tex": "latex",
    "rst": "rst",
    "org": "org",
    "docx": "docx",
    "odt": "odt",
    "rtf": "rtf",
    "epub": "epub",
    "pptx": "pptx",
}

MARKDOWN_SOURCE_EXTENSIONS = {
    "pdf", "docx", "doc", "odt", "rtf", "pptx", "ppt", "odp",
    "xlsx", "xls", "ods", "csv", "html", "htm", "epub",
}

_OFFICE_TARGET_EXTS = {
    "pdf", "doc", "docx", "odt", "rtf", "txt", "html", "htm",
    "xlsx", "xls", "ods", "csv", "ppt", "pptx", "odp",
}

_OFFICE_SEMANTIC_BRIDGES = {
    ("pptx", "docx"),
    ("docx", "pptx"),
    ("xlsx", "docx"),
    ("xls", "docx"),
    ("ods", "docx"),
    ("csv", "docx"),
    ("xlsx", "doc"),
    ("xls", "doc"),
    ("ods", "doc"),
    ("csv", "doc"),
    ("xlsx", "odt"),
    ("xls", "odt"),
    ("ods", "odt"),
    ("csv", "odt"),
    ("xlsx", "rtf"),
    ("xls", "rtf"),
    ("ods", "rtf"),
    ("csv", "rtf"),
}


def extension_of(filename: str) -> str:
    lower = filename.lower()
    for compound in (".tar.gz", ".tar.bz2", ".tar.xz"):
        if lower.endswith(compound):
            return compound[1:]
    return lower.rsplit(".", 1)[-1] if "." in lower else ""


def category_of(ext: str) -> str:
    ext = ext.lower().lstrip(".")
    if ext == "pdf":
        return "pdf"
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in WORD_DOCUMENTS:
        return "document"
    if ext in SPREADSHEETS:
        return "spreadsheet"
    if ext in PRESENTATIONS:
        return "presentation"
    if ext in TEXT_DOCUMENTS:
        return "text"
    if ext in AUDIO_EXTENSIONS:
        return "audio"
    if ext in VIDEO_EXTENSIONS:
        return "video"
    if ext in ARCHIVE_INPUT_EXTENSIONS or ext in ARCHIVE_OUTPUT_EXTENSIONS:
        return "archive"
    return "generic"


def all_target_extensions() -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for ext in (
        DOCUMENT_OUTPUT_EXTENSIONS
        + IMAGE_EXTENSIONS
        + AUDIO_EXTENSIONS
        + VIDEO_EXTENSIONS
        + ARCHIVE_OUTPUT_EXTENSIONS
    ):
        if ext not in seen:
            seen.add(ext)
            result.append(ext)
    return result


def _command_available(name: str, candidates: list[str] | None = None) -> bool:
    return bool(command_path(name, candidates or []))


def _module_available(name: str) -> bool:
    import importlib.util
    return importlib.util.find_spec(name) is not None


@functools.lru_cache(maxsize=1)
def tool_state() -> dict[str, bool]:
    """Probes runtime availability of external tools and optional packages."""
    return {
        "libreoffice": _command_available(
            settings.soffice_bin,
            [
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
                r"%LOCALAPPDATA%\Programs\LibreOffice\program\soffice.exe",
            ],
        ),
        "pandoc": _command_available(
            settings.pandoc_bin,
            [
                r"C:\Program Files\Pandoc\pandoc.exe",
                r"%LOCALAPPDATA%\Pandoc\pandoc.exe",
            ],
        ),
        "ffmpeg": _command_available(
            settings.ffmpeg_bin,
            [
                r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
                r"C:\ffmpeg\bin\ffmpeg.exe",
            ],
        ),
        "tesseract": _command_available(
            settings.tesseract_bin,
            [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            ],
        ),
        "ghostscript": _command_available(
            settings.ghostscript_bin,
            [
                r"C:\Program Files\gs\*\bin\gswin64c.exe",
                r"C:\Program Files (x86)\gs\*\bin\gswin32c.exe",
                "gs",
            ],
        ),
        "py7zr": _module_available("py7zr"),
        "rarfile": _module_available("rarfile"),
        "pdf2docx": _module_available("pdf2docx"),
        "pymupdf4llm": _module_available("pymupdf4llm"),
        "markitdown": _module_available("markitdown"),
        "oxipng": _module_available("oxipng"),
        "docxcompose": _module_available("docxcompose"),
    }


ENGINE_INFO: list[dict[str, Any]] = [
    {
        "key": "libreoffice",
        "name": "LibreOffice",
        "unlocks": "Word, Excel, PowerPoint, OpenDocument conversions and legacy office formats",
        "install": {
            "windows": "winget install TheDocumentFoundation.LibreOffice",
            "macos": "brew install --cask libreoffice",
            "linux": "sudo apt install libreoffice",
        },
    },
    {
        "key": "pandoc",
        "name": "Pandoc",
        "unlocks": "Markdown, HTML, EPUB, LaTeX, RST, Org markup conversions",
        "install": {
            "windows": "winget install --id JohnMacFarlane.Pandoc",
            "macos": "brew install pandoc",
            "linux": "sudo apt install pandoc",
        },
    },
    {
        "key": "ffmpeg",
        "name": "FFmpeg",
        "unlocks": "Audio/video transcoding, waveform generation, and video frame extraction",
        "install": {
            "windows": "winget install Gyan.FFmpeg",
            "macos": "brew install ffmpeg",
            "linux": "sudo apt install ffmpeg",
        },
    },
    {
        "key": "ghostscript",
        "name": "Ghostscript",
        "unlocks": "High-fidelity vector and font PDF compression",
        "install": {
            "windows": "winget install ArtifexSoftware.GhostScript",
            "macos": "brew install ghostscript",
            "linux": "sudo apt install ghostscript",
        },
    },
    {
        "key": "tesseract",
        "name": "Tesseract OCR",
        "unlocks": "Text extraction from scanned images and image-to-text OCR",
        "install": {
            "windows": "winget install UB-Mannheim.TesseractOCR",
            "macos": "brew install tesseract",
            "linux": "sudo apt install tesseract-ocr",
        },
    },
    {
        "key": "py7zr",
        "name": "py7zr (Python package)",
        "unlocks": "Reading and writing 7Z archives",
        "install": {
            "windows": "pip install py7zr",
            "macos": "pip install py7zr",
            "linux": "pip install py7zr",
        },
    },
    {
        "key": "rarfile",
        "name": "rarfile (Python package)",
        "unlocks": "Extracting RAR archives (requires unrar/7-Zip)",
        "install": {
            "windows": "pip install rarfile",
            "macos": "pip install rarfile",
            "linux": "pip install rarfile",
        },
    },
]


def engine_status() -> list[dict[str, Any]]:
    tools = tool_state()
    return [{**info, "installed": tools.get(info["key"], False)} for info in ENGINE_INFO]


# --- Authoritative Strategy Registry ---

@dataclass
class StrategyOutcome:
    supported: bool
    ready: bool
    status: str  # ready, requires_engine, degraded_or_lossy, content_dependent, unsupported
    strategy: str | None = None
    required_engine: str | None = None
    reason: str | None = None
    fidelity: str | None = None


def resolve_strategy(source_ext: str, target_ext: str, tools: dict[str, bool] | None = None) -> StrategyOutcome:
    """Authoritative strategy resolver for any (source_ext, target_ext) pair."""
    s = source_ext.lower().lstrip(".")
    t = target_ext.lower().lstrip(".")

    if s == t:
        return StrategyOutcome(
            supported=False,
            ready=False,
            status="unsupported",
            reason="Source and target formats are identical.",
        )

    t_state = tools if tools is not None else tool_state()

    # 1. Archives repackaging
    if s in ARCHIVE_INPUT_EXTENSIONS:
        if t in ARCHIVE_OUTPUT_EXTENSIONS:
            if s == "rar" and not t_state["rarfile"]:
                return StrategyOutcome(
                    supported=True,
                    ready=False,
                    status="requires_engine",
                    required_engine="rarfile",
                    strategy="archive_repack",
                    reason="Requires rarfile and unrar/7-Zip backend to extract RAR",
                )
            if s == "7z" and not t_state["py7zr"]:
                return StrategyOutcome(
                    supported=True,
                    ready=False,
                    status="requires_engine",
                    required_engine="py7zr",
                    strategy="archive_repack",
                    reason="Requires py7zr to read 7Z archives",
                )
            if t == "7z" and not t_state["py7zr"]:
                return StrategyOutcome(
                    supported=True,
                    ready=False,
                    status="requires_engine",
                    required_engine="py7zr",
                    strategy="archive_repack",
                    reason="Requires py7zr to write 7Z archives",
                )
            return StrategyOutcome(
                supported=True,
                ready=True,
                status="ready",
                strategy="archive_repack",
                fidelity="high",
            )
        return StrategyOutcome(
            supported=False,
            ready=False,
            status="unsupported",
            reason="Archives are container packages, not document or media files.",
        )

    # 2. PDF sources
    if s == "pdf":
        if t in {"txt", "html"}:
            return StrategyOutcome(
                supported=True,
                ready=True,
                status="ready",
                strategy="text_extraction",
                fidelity="high",
            )
        if t == "docx":
            ready = t_state["pdf2docx"]
            return StrategyOutcome(
                supported=True,
                ready=ready,
                status="ready" if ready else "requires_engine",
                required_engine="pdf2docx" if not ready else None,
                strategy="pdf2docx_layout",
                fidelity="high",
            )
        if t == "pptx":
            return StrategyOutcome(
                supported=True,
                ready=True,
                status="ready",
                strategy="slide_generation",
                fidelity="high",
            )
        if t in RENDER_IMAGE_TARGETS:
            return StrategyOutcome(
                supported=True,
                ready=True,
                status="ready",
                strategy="pdf_raster_render",
                fidelity="high",
            )
        if t in {"csv", "xlsx", "xls", "ods"}:
            ready = True
            if t in {"xls", "ods"} and not t_state["libreoffice"]:
                ready = False
            return StrategyOutcome(
                supported=True,
                ready=ready,
                status="content_dependent" if ready else "requires_engine",
                required_engine="libreoffice" if not ready else None,
                strategy="table_extraction",
                reason="Table extraction requires the PDF to contain structured tabular data.",
                fidelity="content_dependent",
            )
        if t in {"doc", "odt", "rtf", "ppt", "odp"}:
            ready = t_state["libreoffice"]
            return StrategyOutcome(
                supported=True,
                ready=ready,
                status="ready" if ready else "requires_engine",
                required_engine="libreoffice" if not ready else None,
                strategy="intermediate_office_conversion",
                reason="Requires LibreOffice for legacy format export" if not ready else None,
            )
        if t == "md":
            ready = t_state["pymupdf4llm"]
            return StrategyOutcome(
                supported=True,
                ready=ready,
                status="ready" if ready else "requires_engine",
                required_engine="pymupdf4llm" if not ready else None,
                strategy="structured_markdown_export",
            )
        if t in {"epub", "tex", "rst", "org"}:
            ready = t_state["pymupdf4llm"] and t_state["pandoc"]
            return StrategyOutcome(
                supported=True,
                ready=ready,
                status="ready" if ready else "requires_engine",
                required_engine="pandoc" if not ready else None,
                strategy="markdown_pandoc_pipeline",
            )
        return StrategyOutcome(
            supported=False,
            ready=False,
            status="unsupported",
            reason="No direct PDF converter exists for this target format.",
        )

    # 3. Image sources
    if s in IMAGE_EXTENSIONS:
        if t in IMAGE_EXTENSIONS:
            if t == "svg":
                return StrategyOutcome(
                    supported=True,
                    ready=True,
                    status="degraded_or_lossy",
                    strategy="raster_embed_svg",
                    reason="Embeds raster image into SVG container; does not vectorize shapes.",
                    fidelity="embedded_raster",
                )
            return StrategyOutcome(
                supported=True,
                ready=True,
                status="ready",
                strategy="pillow_reencode",
                fidelity="high",
            )
        if t == "pdf":
            return StrategyOutcome(
                supported=True,
                ready=True,
                status="ready",
                strategy="image_to_pdf",
                fidelity="high",
            )
        if t in {"docx", "pptx"}:
            return StrategyOutcome(
                supported=True,
                ready=True,
                status="ready",
                strategy="document_image_embed",
                fidelity="high",
            )
        if t in {"doc", "odt", "rtf", "ppt", "odp"}:
            ready = t_state["libreoffice"]
            return StrategyOutcome(
                supported=True,
                ready=ready,
                status="ready" if ready else "requires_engine",
                required_engine="libreoffice" if not ready else None,
                strategy="office_image_document",
            )
        if t in {"txt", "md"}:
            ready = t_state["tesseract"]
            return StrategyOutcome(
                supported=True,
                ready=ready,
                status="ready" if ready else "requires_engine",
                required_engine="tesseract" if not ready else None,
                strategy="tesseract_ocr",
                reason="Requires Tesseract OCR for text recognition from image" if not ready else None,
            )
        if t in {"html", "htm"}:
            return StrategyOutcome(
                supported=True,
                ready=True,
                status="ready",
                strategy="html_image_embed",
            )
        return StrategyOutcome(
            supported=False,
            ready=False,
            status="unsupported",
            reason="Image pixels cannot be converted into this format.",
        )

    # 4. Audio & Video sources
    if s in AUDIO_EXTENSIONS or s in VIDEO_EXTENSIONS:
        ready = t_state["ffmpeg"]
        if t in MEDIA_IMAGE_TARGETS:
            return StrategyOutcome(
                supported=True,
                ready=ready,
                status="ready" if ready else "requires_engine",
                required_engine="ffmpeg" if not ready else None,
                strategy="ffmpeg_waveform_or_frame",
                reason="Requires FFmpeg for media rendering" if not ready else None,
            )
        if t == "pdf":
            return StrategyOutcome(
                supported=True,
                ready=ready,
                status="ready" if ready else "requires_engine",
                required_engine="ffmpeg" if not ready else None,
                strategy="ffmpeg_image_to_pdf",
            )
        if t in AUDIO_EXTENSIONS or t in VIDEO_EXTENSIONS:
            is_black_video = s in AUDIO_EXTENSIONS and t in VIDEO_EXTENSIONS
            return StrategyOutcome(
                supported=True,
                ready=ready,
                status="degraded_or_lossy" if is_black_video else ("ready" if ready else "requires_engine"),
                required_engine="ffmpeg" if not ready else None,
                strategy="ffmpeg_transcode",
                reason="Audio-to-video renders a black video stream with audio." if is_black_video else None,
            )
        return StrategyOutcome(
            supported=False,
            ready=False,
            status="unsupported",
            reason="Media streams require an audio or video target format.",
        )

    # 5. Text & Code sources
    if s in TEXT_DOCUMENTS:
        if t in RENDER_IMAGE_TARGETS:
            return StrategyOutcome(
                supported=True,
                ready=True,
                status="ready",
                strategy="text_raster_render",
            )
        if t in {"csv", "xlsx", "xls", "ods"}:
            ready = True
            if t in {"xls", "ods"} and not t_state["libreoffice"]:
                ready = False
            return StrategyOutcome(
                supported=True,
                ready=ready,
                status="content_dependent" if ready else "requires_engine",
                required_engine="libreoffice" if not ready else None,
                strategy="text_to_spreadsheet",
                reason="Parses Markdown or whitespace-delimited columns into tabular rows.",
            )
        if t in PANDOC_OUTPUTS:
            ready = t_state["pandoc"]
            return StrategyOutcome(
                supported=True,
                ready=ready,
                status="ready" if ready else "requires_engine",
                required_engine="pandoc" if not ready else None,
                strategy="pandoc_text_markup",
            )
        if t == "pdf":
            ready = t_state["pandoc"] and t_state["libreoffice"]
            return StrategyOutcome(
                supported=True,
                ready=ready,
                status="ready" if ready else "requires_engine",
                required_engine="pandoc or libreoffice" if not ready else None,
                strategy="pandoc_pdf_pipeline",
            )
        if t in {"doc", "ppt", "odp", "xls"}:
            ready = t_state["libreoffice"]
            return StrategyOutcome(
                supported=True,
                ready=ready,
                status="ready" if ready else "requires_engine",
                required_engine="libreoffice" if not ready else None,
                strategy="office_text_bridge",
            )
        return StrategyOutcome(
            supported=False,
            ready=False,
            status="unsupported",
            reason="No text translation engine for this target format.",
        )

    # 6. Word documents (doc, docx, odt, rtf)
    if s in WORD_DOCUMENTS:
        if t == "md" and s in MARKDOWN_SOURCE_EXTENSIONS:
            ready = t_state["markitdown"]
            return StrategyOutcome(
                supported=True,
                ready=ready,
                status="ready" if ready else "requires_engine",
                required_engine="markitdown" if not ready else None,
                strategy="markitdown_structural_export",
            )
        if (s, t) in _OFFICE_SEMANTIC_BRIDGES:
            ready = True
            if (s in {"xls", "ods"} or t in {"doc", "odt", "rtf"}) and not t_state["libreoffice"]:
                ready = False
            return StrategyOutcome(
                supported=True,
                ready=ready,
                status="ready" if ready else "requires_engine",
                required_engine="libreoffice" if not ready else None,
                strategy="kiwi_semantic_bridge",
                fidelity="high",
            )
        if s in PANDOC_INPUTS and t in PANDOC_OUTPUTS:
            ready = t_state["pandoc"]
            return StrategyOutcome(
                supported=True,
                ready=ready,
                status="ready" if ready else "requires_engine",
                required_engine="pandoc" if not ready else None,
                strategy="pandoc_doc_bridge",
            )
        if t in _OFFICE_TARGET_EXTS:
            ready = t_state["libreoffice"]
            return StrategyOutcome(
                supported=True,
                ready=ready,
                status="ready" if ready else "requires_engine",
                required_engine="libreoffice" if not ready else None,
                strategy="libreoffice_conversion",
            )
        if t in RENDER_IMAGE_TARGETS:
            ready = t_state["libreoffice"]
            return StrategyOutcome(
                supported=True,
                ready=ready,
                status="ready" if ready else "requires_engine",
                required_engine="libreoffice" if not ready else None,
                strategy="office_render_images",
            )
        return StrategyOutcome(
            supported=False,
            ready=False,
            status="unsupported",
            reason="Word processor documents cannot be converted to this target format.",
        )

    # 7. Spreadsheets & Presentations
    if s in SPREADSHEETS or s in PRESENTATIONS:
        if t == "md" and s in MARKDOWN_SOURCE_EXTENSIONS:
            ready = t_state["markitdown"]
            return StrategyOutcome(
                supported=True,
                ready=ready,
                status="ready" if ready else "requires_engine",
                required_engine="markitdown" if not ready else None,
                strategy="markitdown_structural_export",
            )
        if (s, t) in _OFFICE_SEMANTIC_BRIDGES:
            ready = True
            if (s in {"xls", "ods"} or t in {"doc", "odt", "rtf"}) and not t_state["libreoffice"]:
                ready = False
            return StrategyOutcome(
                supported=True,
                ready=ready,
                status="ready" if ready else "requires_engine",
                required_engine="libreoffice" if not ready else None,
                strategy="kiwi_semantic_bridge",
                fidelity="high",
            )
        if s in PANDOC_INPUTS and t in PANDOC_OUTPUTS:
            ready = t_state["pandoc"]
            return StrategyOutcome(
                supported=True,
                ready=ready,
                status="ready" if ready else "requires_engine",
                required_engine="pandoc" if not ready else None,
                strategy="pandoc_presentation_bridge",
            )
        if t in _OFFICE_TARGET_EXTS:
            ready = t_state["libreoffice"]
            return StrategyOutcome(
                supported=True,
                ready=ready,
                status="ready" if ready else "requires_engine",
                required_engine="libreoffice" if not ready else None,
                strategy="libreoffice_conversion",
            )
        if t in RENDER_IMAGE_TARGETS:
            ready = t_state["libreoffice"]
            return StrategyOutcome(
                supported=True,
                ready=ready,
                status="ready" if ready else "requires_engine",
                required_engine="libreoffice" if not ready else None,
                strategy="office_render_images",
            )
        return StrategyOutcome(
            supported=False,
            ready=False,
            status="unsupported",
            reason="Spreadsheet/presentation content cannot be converted to this target format.",
        )

    # 8. Catch-all LibreOffice
    if t in _OFFICE_TARGET_EXTS:
        ready = t_state["libreoffice"]
        return StrategyOutcome(
            supported=True,
            ready=ready,
            status="ready" if ready else "requires_engine",
            required_engine="libreoffice" if not ready else None,
            strategy="libreoffice_fallback",
        )

    return StrategyOutcome(
        supported=False,
        ready=False,
        status="unsupported",
        reason=f"No viable conversion strategy exists from .{s} to .{t}.",
    )


def universal_target_options(source_ext: str) -> list[dict[str, Any]]:
    """Returns all potential target formats for a given source extension, with status and readiness."""
    tools = tool_state()
    result: list[dict[str, Any]] = []
    for ext in all_target_extensions():
        outcome = resolve_strategy(source_ext, ext, tools)
        result.append({
            "ext": ext,
            "category": category_of(ext),
            "supported": outcome.supported,
            "ready": outcome.ready,
            "status": outcome.status,
            "reason": outcome.reason,
            "strategy": outcome.strategy,
            "fidelity": outcome.fidelity,
        })
    return result


def valid_document_targets(source_ext: str) -> list[str]:
    return [item["ext"] for item in universal_target_options(source_ext) if item["supported"] and item["ready"]]


def document_target_options(source_ext: str) -> list[dict[str, Any]]:
    return universal_target_options(source_ext)


def image_target_options(source_ext: str) -> list[dict[str, Any]]:
    return universal_target_options(source_ext)


def valid_image_targets(source_ext: str) -> list[str]:
    return [
        item["ext"]
        for item in image_target_options(source_ext)
        if item["supported"] and item["ready"] and item["ext"] in IMAGE_EXTENSIONS
    ]
