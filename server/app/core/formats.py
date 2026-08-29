from __future__ import annotations

from typing import Any


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
    "zip", "7z", "tar", "tar.gz", "tgz", "tar.bz2", "tbz2", "tar.xz", "txz", "rar"
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
    "pptx": "pptx",
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

# Formats that markitdown (or, for PDF specifically, pymupdf4llm) can turn
# into real structured Markdown -- headings, tables, lists -- rather than a
# flat text dump. This is the "x -> md" side of document conversion.
MARKDOWN_SOURCE_EXTENSIONS = {
    "pdf", "docx", "doc", "odt", "rtf", "pptx", "ppt", "odp",
    "xlsx", "xls", "ods", "csv", "html", "htm", "epub",
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
    from app.core.files import command_path

    return bool(command_path(name, candidates or []))


def tool_state() -> dict[str, bool]:
    return {
        "libreoffice": _command_available(
            "soffice",
            [
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            ],
        ),
        "pandoc": _command_available(
            "pandoc",
            [r"C:\Program Files\Pandoc\pandoc.exe"],
        ),
        "ffmpeg": _command_available(
            "ffmpeg",
            [
                r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
                r"C:\ffmpeg\bin\ffmpeg.exe",
            ],
        ),
        "tesseract": _command_available(
            "tesseract",
            [r"C:\Program Files\Tesseract-OCR\tesseract.exe"],
        ),
        "ghostscript": _command_available(
            "gswin64c",
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
    }


def _module_available(name: str) -> bool:
    import importlib.util

    return importlib.util.find_spec(name) is not None


# Metadata for the engine-status panel: what each engine unlocks and how to
# install it on each OS. Ordered by how much conversion coverage each one
# unlocks so the status panel can show the highest-impact gaps first.
ENGINE_INFO: list[dict[str, Any]] = [
    {
        "key": "libreoffice",
        "name": "LibreOffice",
        "unlocks": "Word/Excel/PowerPoint/OpenDocument conversion, legacy formats, PDF export",
        "install": {
            "windows": "winget install TheDocumentFoundation.LibreOffice",
            "macos": "brew install --cask libreoffice",
            "linux": "sudo apt install libreoffice",
        },
    },
    {
        "key": "pandoc",
        "name": "Pandoc",
        "unlocks": "Markdown, HTML, EPUB, LaTeX, RST, Org, and other markup/document conversion",
        "install": {
            "windows": "winget install --id JohnMacFarlane.Pandoc",
            "macos": "brew install pandoc",
            "linux": "sudo apt install pandoc",
        },
    },
    {
        "key": "ffmpeg",
        "name": "FFmpeg",
        "unlocks": "Audio and video transcoding, frame/waveform image export",
        "install": {
            "windows": "winget install Gyan.FFmpeg",
            "macos": "brew install ffmpeg",
            "linux": "sudo apt install ffmpeg",
        },
    },
    {
        "key": "ghostscript",
        "name": "Ghostscript",
        "unlocks": "High-quality PDF compression (falls back to slower page rasterization without it)",
        "install": {
            "windows": "winget install ArtifexSoftware.GhostScript",
            "macos": "brew install ghostscript",
            "linux": "sudo apt install ghostscript",
        },
    },
    {
        "key": "tesseract",
        "name": "Tesseract OCR",
        "unlocks": "Text extraction from scanned images and image-to-text/markdown",
        "install": {
            "windows": "winget install UB-Mannheim.TesseractOCR",
            "macos": "brew install tesseract",
            "linux": "sudo apt install tesseract-ocr",
        },
    },
    {
        "key": "py7zr",
        "name": "py7zr (Python package)",
        "unlocks": "Reading and writing .7z archives",
        "install": {
            "windows": "pip install py7zr",
            "macos": "pip install py7zr",
            "linux": "pip install py7zr",
        },
    },
    {
        "key": "rarfile",
        "name": "rarfile (Python package)",
        "unlocks": "Extracting .rar archives (also needs unrar or 7-Zip on PATH)",
        "install": {
            "windows": "pip install rarfile  (and: winget install RARLab.WinRAR)",
            "macos": "pip install rarfile  (and: brew install rar)",
            "linux": "pip install rarfile  (and: sudo apt install unrar)",
        },
    },
    {
        "key": "pdf2docx",
        "name": "pdf2docx (Python package)",
        "unlocks": "High-fidelity PDF to DOCX conversion with real tables, paragraphs, and layout",
        "install": {
            "windows": "pip install pdf2docx",
            "macos": "pip install pdf2docx",
            "linux": "pip install pdf2docx",
        },
    },
    {
        "key": "pymupdf4llm",
        "name": "PyMuPDF4LLM (Python package)",
        "unlocks": "Structured PDF to Markdown conversion (headings, tables, lists)",
        "install": {
            "windows": "pip install pymupdf4llm",
            "macos": "pip install pymupdf4llm",
            "linux": "pip install pymupdf4llm",
        },
    },
    {
        "key": "markitdown",
        "name": "MarkItDown (Python package)",
        "unlocks": "Word/PowerPoint/Excel/HTML/image to Markdown conversion",
        "install": {
            "windows": "pip install \"markitdown[all]\"",
            "macos": "pip install \"markitdown[all]\"",
            "linux": "pip install \"markitdown[all]\"",
        },
    },
    {
        "key": "oxipng",
        "name": "oxipng (Python package)",
        "unlocks": "Best-in-class lossless PNG compression",
        "install": {
            "windows": "pip install pyoxipng",
            "macos": "pip install pyoxipng",
            "linux": "pip install pyoxipng",
        },
    },
]


def engine_status() -> list[dict[str, Any]]:
    tools = tool_state()
    return [
        {**info, "installed": tools.get(info["key"], False)}
        for info in ENGINE_INFO
    ]


def _document_conversion_support(source_ext: str, target_ext: str, tools: dict[str, bool]) -> tuple[bool, str | None]:
    """Report whether convert_any(source_ext -> target_ext) will actually succeed.

    This mirrors app.services.universal.convert_any branch-for-branch so the
    UI never advertises a conversion that the engine can't really perform
    (and never hides one that it can). Each check here corresponds to the
    exact branch convert_any takes, and to the exact tool that branch calls.
    """
    s = source_ext.lower()
    t = target_ext.lower()

    if s == t:
        return False, "Same format"

    # Archives: repackaging only, mirrors _archive_convert.
    if s in ARCHIVE_INPUT_EXTENSIONS:
        if t in ARCHIVE_OUTPUT_EXTENSIONS:
            if s == "rar" and not tools["rarfile"]:
                return False, "RAR repackaging needs the rarfile module plus an UnRAR/7-Zip backend"
            if s == "7z" and not tools["py7zr"]:
                return False, "Requires py7zr to read 7Z archives"
            if t == "7z" and not tools["py7zr"]:
                return False, "Requires py7zr to write 7Z archives"
            return True, None
        return False, "Archives are package containers, not document/media formats"

    # PDF source: mirrors the "PDF paths" block in convert_any.
    if s == "pdf":
        if t == "txt" or t == "html":
            return True, None
        if t == "docx" or t == "pptx":
            return True, None
        if t in RENDER_IMAGE_TARGETS:
            return True, None
        if t in {"csv", "xlsx", "xls", "ods"}:
            return True, None
        if t in {"doc", "odt", "rtf"}:
            # Goes through an intermediate docx, then LibreOffice for legacy formats.
            if t == "doc" or t == "odt" or t == "rtf":
                return tools["libreoffice"], "Requires LibreOffice"
        if t in {"ppt", "odp"}:
            return tools["libreoffice"], "Requires LibreOffice"
        if t == "md":
            return tools["pymupdf4llm"], "Requires PyMuPDF4LLM"
        if t in {"epub", "tex", "rst", "org"}:
            return tools["pymupdf4llm"] and tools["pandoc"], "Requires PyMuPDF4LLM and Pandoc"
        return False, "No meaningful PDF representation for this target"

    # Images: mirrors "if source_ext in IMAGE_EXTENSIONS".
    if s in IMAGE_EXTENSIONS:
        if t in IMAGE_EXTENSIONS:
            return True, None
        # Everything else routes through _image_to_document.
        if t == "pdf":
            return True, None
        if t in {"docx", "doc", "odt", "rtf"}:
            if t == "docx":
                return True, None
            return tools["libreoffice"], "Requires LibreOffice to save as ." + t
        if t in {"pptx", "ppt", "odp"}:
            if t == "pptx":
                return True, None
            return tools["libreoffice"], "Requires LibreOffice to save as ." + t
        if t in {"txt", "md"}:
            return tools["tesseract"], "Requires Tesseract for OCR"
        if t in {"html", "htm"}:
            return True, None
        return False, "Image data has no reliable representation in this format"

    # Archive repackaging when both ends are archive containers is handled
    # above; a non-archive source never reaches an archive target here.

    # Audio/video: mirrors the ffmpeg block.
    if s in AUDIO_EXTENSIONS or s in VIDEO_EXTENSIONS:
        if t in MEDIA_IMAGE_TARGETS:
            return tools["ffmpeg"], "Requires FFmpeg frame/waveform rendering"
        if t == "pdf":
            return tools["ffmpeg"], "Requires FFmpeg waveform/frame rendering"
        if t in AUDIO_EXTENSIONS or t in VIDEO_EXTENSIONS:
            return tools["ffmpeg"], "Requires FFmpeg media transcoder"
        return False, "Media requires a semantic conversion, not a normal format transcode"

    # Text documents: mirrors the TEXT_DOCUMENTS block, checked before the
    # generic Pandoc bridge (source_ext in TEXT_DOCUMENTS short-circuits it).
    if s in TEXT_DOCUMENTS:
        if t in RENDER_IMAGE_TARGETS:
            return True, None
        if t in {"csv", "xlsx", "xls", "ods"}:
            return True, None
        if t in PANDOC_OUTPUTS:
            return tools["pandoc"], "Requires Pandoc"
        if t == "pdf":
            return tools["pandoc"] or tools["libreoffice"], "Requires Pandoc or LibreOffice"
        if t in {"doc", "ppt", "odp", "xls"}:
            return tools["libreoffice"], "Requires LibreOffice"
        return False, "Use a document, image, or spreadsheet representation for text data"

    # Word-processor documents (doc/docx/odt/rtf): these are not in
    # TEXT_DOCUMENTS, so convert_any falls through to the Pandoc bridge and,
    # failing that, the LibreOffice catch-all.
    if s in WORD_DOCUMENTS:
        if t == "md" and s in MARKDOWN_SOURCE_EXTENSIONS:
            return tools["markitdown"], "Requires MarkItDown"
        if t in PANDOC_OUTPUTS and s in PANDOC_INPUTS:
            return tools["pandoc"], "Requires Pandoc"
        if t in {"pdf", "doc", "docx", "odt", "rtf", "txt", "html", "htm", "xlsx", "xls", "ods", "csv", "ppt", "pptx", "odp"}:
            return tools["libreoffice"], "Requires LibreOffice"
        if t in RENDER_IMAGE_TARGETS:
            return tools["libreoffice"], "Requires LibreOffice"
        return False, "No installed converter can perform this conversion"

    # Spreadsheets: convert_any has no dedicated branch, so these fall
    # through to the LibreOffice catch-all (or image rendering).
    if s in SPREADSHEETS:
        if t == "md" and s in MARKDOWN_SOURCE_EXTENSIONS:
            return tools["markitdown"], "Requires MarkItDown"
        if t in {"pdf", "doc", "docx", "odt", "rtf", "txt", "html", "htm", "xlsx", "xls", "ods", "csv", "ppt", "pptx", "odp"}:
            return tools["libreoffice"], "Requires LibreOffice"
        if t in RENDER_IMAGE_TARGETS:
            return tools["libreoffice"], "Requires LibreOffice"
        return False, "Spreadsheet data has no reliable representation in this target"

    # Presentations: same fallthrough as spreadsheets, but pptx can also use Pandoc.
    if s in PRESENTATIONS:
        if t == "md" and s in MARKDOWN_SOURCE_EXTENSIONS:
            return tools["markitdown"], "Requires MarkItDown"
        if s in PANDOC_INPUTS and t in PANDOC_OUTPUTS:
            return tools["pandoc"], "Requires Pandoc"
        if t in {"pdf", "doc", "docx", "odt", "rtf", "txt", "html", "htm", "xlsx", "xls", "ods", "csv", "ppt", "pptx", "odp"}:
            return tools["libreoffice"], "Requires LibreOffice"
        if t in RENDER_IMAGE_TARGETS:
            return tools["libreoffice"], "Requires LibreOffice"
        return False, "Presentation content has no reliable representation in this target"

    # Native Pandoc markup bridge for anything else Pandoc understands.
    if s in PANDOC_INPUTS and t in PANDOC_OUTPUTS:
        return tools["pandoc"], "Requires Pandoc"

    # Final LibreOffice catch-all, matching convert_any's last resort.
    if t in {"pdf", "doc", "docx", "odt", "rtf", "txt", "html", "htm", "xlsx", "xls", "ods", "csv", "ppt", "pptx", "odp"}:
        return tools["libreoffice"], "Requires LibreOffice"
    if t in RENDER_IMAGE_TARGETS:
        return tools["libreoffice"], "Requires LibreOffice"

    return False, "No installed converter can perform this conversion"


def universal_target_options(source_ext: str) -> list[dict[str, Any]]:
    tools = tool_state()
    result: list[dict[str, Any]] = []
    for ext in all_target_extensions():
        supported, reason = _document_conversion_support(source_ext, ext, tools)
        result.append({
            "ext": ext,
            "category": category_of(ext),
            "supported": supported,
            "ready": supported,
            "reason": reason,
        })
    return result


def valid_document_targets(source_ext: str) -> list[str]:
    return [item["ext"] for item in universal_target_options(source_ext) if item["supported"]]


def document_target_options(source_ext: str) -> list[dict[str, Any]]:
    return universal_target_options(source_ext)


def image_target_options(source_ext: str) -> list[dict[str, Any]]:
    return universal_target_options(source_ext)


def valid_image_targets(source_ext: str) -> list[str]:
    return [item["ext"] for item in image_target_options(source_ext) if item["supported"] and item["ext"] in IMAGE_EXTENSIONS]
