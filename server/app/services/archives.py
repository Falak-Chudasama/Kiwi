import shutil
import tarfile
import zipfile
from pathlib import Path

import py7zr


def create_archive(input_paths: list[Path], out_dir: Path, archive_format: str, name: str = "archive") -> Path:
    if archive_format == "zip":
        output_path = out_dir / f"{name}.zip"
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in input_paths:
                zf.write(path, arcname=path.name)
        return output_path

    if archive_format == "7z":
        output_path = out_dir / f"{name}.7z"
        with py7zr.SevenZipFile(output_path, "w") as archive:
            for path in input_paths:
                archive.write(path, arcname=path.name)
        return output_path

    if archive_format == "tar":
        output_path = out_dir / f"{name}.tar"
        with tarfile.open(output_path, "w") as tf:
            for path in input_paths:
                tf.add(path, arcname=path.name)
        return output_path

    raise ValueError(f"Unsupported archive format: {archive_format}")


def extract_archive(input_path: Path, out_dir: Path) -> list[Path]:
    ext = input_path.suffix.lower().lstrip(".")
    extract_dir = out_dir / f"{input_path.stem}_extracted"
    extract_dir.mkdir(parents=True, exist_ok=True)

    if ext == "zip":
        with zipfile.ZipFile(input_path) as zf:
            zf.extractall(extract_dir)
    elif ext == "7z":
        with py7zr.SevenZipFile(input_path, "r") as archive:
            archive.extractall(path=extract_dir)
    elif ext in ("tar", "gz", "bz2", "xz"):
        with tarfile.open(input_path) as tf:
            tf.extractall(extract_dir)
    else:
        raise ValueError(f"Unsupported archive format: .{ext}")

    extracted = [p for p in extract_dir.rglob("*") if p.is_file()]

    zip_path = out_dir / f"{extract_dir.name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in extracted:
            zf.write(file_path, arcname=file_path.relative_to(extract_dir))

    return [zip_path]
