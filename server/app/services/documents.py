import subprocess
from pathlib import Path

from app.core.config import settings
from app.core.files import run_command
from app.core.formats import MARKUP_EXTENSIONS, extension_of

PANDOC_FORMAT_MAP = {
    "md": "markdown",
    "markdown": "markdown",
    "html": "html",
    "htm": "html",
    "rtf": "rtf",
    "odt": "odt",
    "epub": "epub",
    "docx": "docx",
    "txt": "plain",
}

LIBREOFFICE_FILTER_MAP = {
    "pdf": "pdf",
    "docx": "docx",
    "odt": "odt",
    "rtf": "rtf",
    "txt": "txt",
    "html": "html",
    "xlsx": "xlsx",
    "ods": "ods",
    "csv": "csv",
    "pptx": "pptx",
    "odp": "odp",
}


def _should_use_pandoc(source_ext: str, target_ext: str) -> bool:
    pandoc_capable = set(PANDOC_FORMAT_MAP) | {"pdf"}
    return source_ext in MARKUP_EXTENSIONS and target_ext in pandoc_capable


def convert_with_pandoc(input_path: Path, target_ext: str, out_dir: Path) -> Path:
    output_path = out_dir / f"{input_path.stem}.{target_ext}"
    to_format = PANDOC_FORMAT_MAP.get(target_ext, target_ext)
    args = ["pandoc", str(input_path), "-o", str(output_path)]
    if target_ext != "pdf":
        args += ["-t", to_format]
    run_command(args, timeout=180)
    return output_path


def convert_with_libreoffice(input_path: Path, target_ext: str, out_dir: Path) -> Path:
    filter_name = LIBREOFFICE_FILTER_MAP.get(target_ext, target_ext)
    args = [
        settings.soffice_bin,
        "--headless",
        "--norestore",
        "--convert-to",
        filter_name,
        "--outdir",
        str(out_dir),
        str(input_path),
    ]
    run_command(args, timeout=240)
    produced = out_dir / f"{input_path.stem}.{target_ext}"
    if not produced.exists():
        matches = list(out_dir.glob(f"{input_path.stem}.*"))
        if matches:
            return matches[0]
        raise RuntimeError("Document conversion did not produce an output file.")
    return produced


def convert_document(input_path: Path, target_ext: str, out_dir: Path) -> Path:
    source_ext = extension_of(input_path.name)
    target_ext = target_ext.lower()

    if _should_use_pandoc(source_ext, target_ext):
        try:
            return convert_with_pandoc(input_path, target_ext, out_dir)
        except subprocess.CalledProcessError:
            pass

    return convert_with_libreoffice(input_path, target_ext, out_dir)
