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
        "imagemagick": _command_available(
            "magick",
            [r"C:\Program Files\ImageMagick-*\magick.exe"],
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
        "py7zr": _module_available("py7zr"),
        "rarfile": _module_available("rarfile"),
    }


def _module_available(name: str) -> bool:
    import importlib.util

    return importlib.util.find_spec(name) is not None


def _document_conversion_support(source_ext: str, target_ext: str, tools: dict[str, bool]) -> tuple[bool, str | None]:
    s = source_ext.lower()
    t = target_ext.lower()

    if s == t:
        return False, "Same format"

    if s in ARCHIVE_INPUT_EXTENSIONS:
        if t in ARCHIVE_OUTPUT_EXTENSIONS:
            if s == "rar":
                return False, "RAR repackaging needs an extraction backend such as UnRAR or 7-Zip"
            if s == "7z" and not tools["py7zr"]:
                return False, "Requires py7zr to read 7Z archives"
            if t == "7z" and not tools["py7zr"]:
                return False, "Requires py7zr to write 7Z archives"
            return True, None
        return False, "Archives are package containers, not document/media formats"

    if s == "pdf":
        if t in {"docx", "pptx", "txt", "html", "md", "epub", "tex", "rst", "org"}:
            if t in {"md", "epub", "tex", "rst", "org"} and not tools["pandoc"]:
                return False, "Requires Pandoc"
            return True, None
        if t in RENDER_IMAGE_TARGETS or t in {"doc", "odt", "rtf", "ppt", "odp"}:
            return True, None if t in RENDER_IMAGE_TARGETS or tools["libreoffice"] else "Requires LibreOffice"
        if t in {"xlsx", "xls", "ods", "csv"}:
            return True, None
        return False, "No meaningful PDF representation for this target"

    if s in IMAGE_EXTENSIONS:
        if t in RENDER_IMAGE_TARGETS or t == "pdf":
            return True, None
        if t in {"docx", "doc", "odt", "rtf", "pptx", "ppt", "odp", "html", "htm"}:
            if t in {"docx", "pptx", "html", "htm"}:
                return True, None
            return tools["libreoffice"], "Requires LibreOffice"
        if t in {"txt", "md"}:
            return tools["tesseract"], "Requires Tesseract for OCR"
        return False, "Image data has no reliable representation in this format"

    if s in AUDIO_EXTENSIONS or s in VIDEO_EXTENSIONS:
        if t in AUDIO_EXTENSIONS or t in VIDEO_EXTENSIONS:
            return tools["ffmpeg"], "Requires FFmpeg media transcoder"
        if t in MEDIA_IMAGE_TARGETS:
            return tools["ffmpeg"], "Requires FFmpeg frame/waveform rendering"
        if t == "pdf":
            return tools["ffmpeg"], "Requires FFmpeg waveform/frame rendering"
        return False, "Media requires a semantic conversion, not a normal format transcode"

    if s in TEXT_DOCUMENTS:
        if t in RENDER_IMAGE_TARGETS or t == "pdf" or t in {"docx", "odt", "rtf", "epub", "pptx"}:
            if t in RENDER_IMAGE_TARGETS:
                return True, None
            if t == "pdf":
                return tools["pandoc"] or tools["libreoffice"], "Requires Pandoc or LibreOffice"
            return tools["pandoc"] or tools["libreoffice"], "Requires Pandoc or LibreOffice"
        if t in {"doc", "ppt", "odp", "xlsx", "xls", "ods", "csv"}:
            return tools["libreoffice"] or tools["pandoc"], "Requires LibreOffice (or Pandoc for supported text documents)"
        return False, "Use a document, image, or spreadsheet representation for text data"

    if s in WORD_DOCUMENTS:
        if t in RENDER_IMAGE_TARGETS or t == "pdf":
            return tools["libreoffice"], "Requires LibreOffice"
        if t in {"txt", "md", "html", "htm", "doc", "docx", "odt", "rtf", "epub", "tex", "rst", "org", "pptx"}:
            return tools["pandoc"] or tools["libreoffice"], "Requires Pandoc or LibreOffice"

    if s in SPREADSHEETS:
        if t in SPREADSHEETS | {"pdf", "html", "txt"}:
            return tools["libreoffice"], "Requires LibreOffice"
        if t in RENDER_IMAGE_TARGETS:
            return tools["libreoffice"], "Requires LibreOffice"
        return False, "Spreadsheet data has no reliable representation in this target"

    if s in PRESENTATIONS:
        if t in PRESENTATIONS | {"pdf", "html", "txt"}:
            return tools["libreoffice"] or tools["pandoc"], "Requires LibreOffice or Pandoc"
        if t in RENDER_IMAGE_TARGETS:
            return tools["libreoffice"], "Requires LibreOffice"
        return False, "Presentation content has no reliable representation in this target"

    if s in PANDOC_INPUTS and t in PANDOC_OUTPUTS:
        return tools["pandoc"], "Requires Pandoc"

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
