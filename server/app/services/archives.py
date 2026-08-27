from __future__ import annotations

import os
import tarfile
import zipfile
from pathlib import Path

try:
    import py7zr
except ImportError:  # Optional until a 7Z operation is requested.
    py7zr = None

try:
    import rarfile
except ImportError:  # Optional until a RAR operation is requested.
    rarfile = None


_COMPOUND_SUFFIXES = (
    ".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".tar.xz", ".txz"
)


def archive_stem(path: Path) -> str:
    lower = path.name.lower()
    for suffix in _COMPOUND_SUFFIXES:
        if lower.endswith(suffix):
            return path.name[: -len(suffix)]
    return path.stem


def _archive_stem(paths: list[Path]) -> str:
    if not paths:
        return "archive"
    stems = [p.stem for p in paths]
    if len(stems) == 1:
        return stems[0] or "archive"
    common = os.path.commonprefix(stems).strip(" _-.\\")
    if len(common) >= 3:
        return f"{common}-bundle"
    return f"{stems[0] or 'archive'}-and-{len(stems) - 1}-more"


def create_archive(input_paths: list[Path], out_dir: Path, archive_format: str, name: str | None = None) -> Path:
    archive_format = archive_format.lower().lstrip(".")
    archive_name = (name or _archive_stem(input_paths)).strip() or _archive_stem(input_paths)
    safe_chars = "-_. ()"
    archive_name = "".join(c for c in archive_name if c.isalnum() or c in safe_chars).strip() or "archive"
    if archive_name.lower().endswith(f".{archive_format}"):
        archive_name = archive_name.rsplit(".", 1)[0]

    if archive_format == "zip":
        output_path = out_dir / f"{archive_name}.zip"
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            for path in input_paths:
                zf.write(path, arcname=path.name)
        return output_path

    if archive_format == "7z":
        if py7zr is None:
            raise RuntimeError("7Z support requires py7zr. Install Kiwi dependencies again.")
        output_path = out_dir / f"{archive_name}.7z"
        with py7zr.SevenZipFile(output_path, "w") as archive:
            for path in input_paths:
                archive.write(path, arcname=path.name)
        return output_path

    if archive_format == "tar":
        output_path = out_dir / f"{archive_name}.tar"
        with tarfile.open(output_path, "w") as tf:
            for path in input_paths:
                tf.add(path, arcname=path.name)
        return output_path

    raise ValueError(f"Unsupported archive format: {archive_format}")


def create_zip_bundle(input_paths: list[Path], output_path: Path, root_name: str | None = None) -> Path:
    root = Path(root_name) if root_name else None
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in input_paths:
            arcname = path.name if root is None else str(root / path.name)
            zf.write(path, arcname=arcname)
    return output_path


def _safe_member_path(base: Path, member_name: str) -> Path:
    clean = member_name.replace("\\", "/")
    target = (base / clean).resolve()
    base_resolved = base.resolve()
    if target != base_resolved and base_resolved not in target.parents:
        raise ValueError("Archive contains an unsafe path.")
    return target


def _extract_zip(input_path: Path, extract_dir: Path) -> None:
    with zipfile.ZipFile(input_path) as zf:
        for member in zf.infolist():
            _safe_member_path(extract_dir, member.filename)
        zf.extractall(extract_dir)


def _extract_tar(input_path: Path, extract_dir: Path) -> None:
    with tarfile.open(input_path, "r:*") as tf:
        for member in tf.getmembers():
            _safe_member_path(extract_dir, member.name)
            if member.issym() or member.islnk():
                raise ValueError("Archives containing symbolic or hard links are not supported.")
        tf.extractall(extract_dir)


def extract_archive(input_path: Path, out_dir: Path) -> list[Path]:
    lower = input_path.name.lower()
    stem = archive_stem(input_path)
    extract_dir = out_dir / f"{stem}-extracted"
    extract_dir.mkdir(parents=True, exist_ok=True)

    if lower.endswith(".zip"):
        _extract_zip(input_path, extract_dir)
    elif lower.endswith(".7z"):
        if py7zr is None:
            raise RuntimeError("7Z extraction requires py7zr. Install Kiwi dependencies again.")
        with py7zr.SevenZipFile(input_path, "r") as archive:
            for name in archive.getnames():
                _safe_member_path(extract_dir, name)
            archive.extractall(path=extract_dir)
    elif lower.endswith(".rar"):
        if rarfile is None:
            raise RuntimeError("RAR extraction requires rarfile plus an UnRAR/7-Zip backend.")
        try:
            with rarfile.RarFile(input_path) as archive:
                for name in archive.namelist():
                    _safe_member_path(extract_dir, name)
                archive.extractall(path=extract_dir)
        except rarfile.RarCannotExec as exc:
            raise RuntimeError("RAR extraction needs an unrar/7-Zip backend installed and available on PATH.") from exc
    elif lower.endswith((".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".tar.xz", ".txz")):
        _extract_tar(input_path, extract_dir)
    else:
        raise ValueError(f"Unsupported archive format: {input_path.name}")

    extracted = sorted(p for p in extract_dir.rglob("*") if p.is_file())
    if not extracted:
        raise ValueError("The archive contains no files to extract.")

    return extracted
