DOCUMENT_INPUT_EXTENSIONS = {
    "docx", "doc", "odt", "rtf", "txt", "md", "markdown",
    "xlsx", "xls", "ods", "csv",
    "pptx", "ppt", "odp",
    "html", "htm", "epub", "pdf",
}

DOCUMENT_OUTPUT_EXTENSIONS = {
    "pdf", "docx", "odt", "rtf", "txt", "md", "html", "epub",
    "xlsx", "ods", "csv", "pptx", "odp",
}

IMAGE_EXTENSIONS = {
    "jpg", "jpeg", "png", "webp", "avif", "gif", "bmp", "tiff", "tif",
    "ico", "heic", "heif", "svg",
}

ARCHIVE_INPUT_EXTENSIONS = {"zip", "7z", "tar", "gz", "bz2", "xz", "rar"}
ARCHIVE_OUTPUT_EXTENSIONS = {"zip", "7z", "tar"}

COMPRESSIBLE_EXTENSIONS = {
    "pdf", "jpg", "jpeg", "png", "webp", "tiff", "tif",
    "docx", "pptx", "xlsx",
}

MARKUP_EXTENSIONS = {"md", "markdown", "html", "htm", "epub", "rtf", "txt", "odt"}

OFFICE_LAYOUT_EXTENSIONS = {
    "docx", "doc", "xlsx", "xls", "pptx", "ppt", "odp", "ods", "pdf",
}


def extension_of(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def is_markup_conversion(source_ext: str, target_ext: str) -> bool:
    return source_ext in MARKUP_EXTENSIONS and target_ext in (
        MARKUP_EXTENSIONS | {"pdf"}
    )


def valid_document_targets(source_ext: str) -> list[str]:
    targets = DOCUMENT_OUTPUT_EXTENSIONS - {source_ext}
    return sorted(targets)


def valid_image_targets(source_ext: str) -> list[str]:
    targets = IMAGE_EXTENSIONS - {source_ext}
    return sorted(targets)
