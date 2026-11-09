from __future__ import annotations

import io
import os
import tarfile
import zipfile
from pathlib import Path

from app.core.config import settings

try:
    import py7zr
except ImportError:
    py7zr = None

try:
    import rarfile
except ImportError:
    rarfile = None

_COMPOUND_SUFFIXES = (
    ".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".tar.xz", ".txz"
)

MAX_RATIO = 100  # Max allowable uncompressed-to-compressed ratio (decompression bomb protection)


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

    out_dir.mkdir(parents=True, exist_ok=True)

    if archive_format == "zip":
        output_path = out_dir / f"{archive_name}.zip"
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            for path in input_paths:
                zf.write(path, arcname=path.name)
        return output_path

    if archive_format == "7z":
        if py7zr is None:
            raise RuntimeError("7Z creation requires the py7zr package.")
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


def _sanitize_archive_member(dest_root: Path, member_name: str) -> Path:
    """Validates that member_name resolves strictly within dest_root.

    Rejects directory traversal (Zip Slip), Windows drive prefixes, UNC paths,
    and null bytes.
    """
    clean = member_name.replace("\\", "/").strip()

    # Reject null bytes or absolute paths
    if "\x00" in clean or clean.startswith("/"):
        raise ValueError("Archive entry contains an illegal absolute path.")

    # Strip Windows drive letters (e.g., C:)
    if len(clean) >= 2 and clean[1] == ":":
        raise ValueError("Archive entry contains a drive specification.")

    # Check for path traversal components
    parts = clean.split("/")
    if any(p == ".." for p in parts):
        raise ValueError("Archive entry attempts directory traversal ('..').")

    # Filter out empty parts
    filtered_parts = [p for p in parts if p and p != "."]
    if not filtered_parts:
        raise ValueError("Archive entry name is empty.")

    target = dest_root.joinpath(*filtered_parts).resolve()
    dest_root_resolved = dest_root.resolve()

    if not str(target).startswith(str(dest_root_resolved)):
        raise ValueError("Archive entry resolves outside extraction directory.")

    return target


def _is_zip_symlink(info: zipfile.ZipInfo) -> bool:
    """Checks whether a ZipInfo entry is marked as a UNIX symbolic link."""
    mode = info.external_attr >> 16
    return (mode & 0o170000) == 0o120000


def _extract_zip_hardened(input_path: Path, dest_dir: Path) -> list[Path]:
    max_bytes = settings.max_archive_uncompressed_mb * 1024 * 1024
    total_written = 0
    extracted_files: list[Path] = []

    with zipfile.ZipFile(input_path, "r") as zf:
        infolist = zf.infolist()
        if len(infolist) > settings.max_archive_entries:
            raise ValueError(f"Archive exceeds maximum entry count of {settings.max_archive_entries}.")

        # Check total declared uncompressed size and ratios
        declared_total = sum(info.file_size for info in infolist)
        if declared_total > max_bytes:
            raise ValueError("Archive uncompressed size exceeds maximum allowed safety threshold.")

        compressed_total = max(1, sum(info.compress_size for info in infolist))
        if (declared_total / compressed_total) > MAX_RATIO and declared_total > 10 * 1024 * 1024:
            raise ValueError("Potential decompression bomb detected (suspicious compression ratio).")

        for info in infolist:
            if info.is_dir():
                continue
            if _is_zip_symlink(info):
                raise ValueError("Archive contains symbolic links, which are prohibited.")

            target_path = _sanitize_archive_member(dest_dir, info.filename)
            target_path.parent.mkdir(parents=True, exist_ok=True)

            with zf.open(info, "r") as src, target_path.open("wb") as dst:
                while True:
                    chunk = src.read(128 * 1024)
                    if not chunk:
                        break
                    total_written += len(chunk)
                    if total_written > max_bytes:
                        raise ValueError("Extracted size exceeded maximum uncompressed archive limit.")
                    dst.write(chunk)

            extracted_files.append(target_path)

    return extracted_files


def _extract_tar_hardened(input_path: Path, dest_dir: Path) -> list[Path]:
    max_bytes = settings.max_archive_uncompressed_mb * 1024 * 1024
    total_written = 0
    extracted_files: list[Path] = []

    with tarfile.open(input_path, "r:*") as tf:
        members = tf.getmembers()
        if len(members) > settings.max_archive_entries:
            raise ValueError(f"Archive exceeds maximum entry count of {settings.max_archive_entries}.")

        for member in members:
            if member.isdir():
                continue
            if member.issym() or member.islnk():
                raise ValueError("Archives containing symbolic or hard links are prohibited.")
            if member.isdev() or member.ischr() or member.isblk() or member.isfifo():
                raise ValueError("Archive contains special device entries, which are prohibited.")

            target_path = _sanitize_archive_member(dest_dir, member.name)
            target_path.parent.mkdir(parents=True, exist_ok=True)

            f = tf.extractfile(member)
            if f is None:
                continue

            with f, target_path.open("wb") as dst:
                while True:
                    chunk = f.read(128 * 1024)
                    if not chunk:
                        break
                    total_written += len(chunk)
                    if total_written > max_bytes:
                        raise ValueError("Extracted size exceeded maximum uncompressed archive limit.")
                    dst.write(chunk)

            extracted_files.append(target_path)

    return extracted_files


def _extract_7z_hardened(input_path: Path, dest_dir: Path) -> list[Path]:
    if py7zr is None:
        raise RuntimeError("7Z extraction requires the py7zr package.")

    max_bytes = settings.max_archive_uncompressed_mb * 1024 * 1024
    extracted_files: list[Path] = []

    with py7zr.SevenZipFile(input_path, "r") as archive:
        names = archive.getnames()
        if len(names) > settings.max_archive_entries:
            raise ValueError(f"Archive exceeds maximum entry count of {settings.max_archive_entries}.")

        for name in names:
            _sanitize_archive_member(dest_dir, name)

        archive.extractall(path=dest_dir)

    total_size = 0
    for p in sorted(dest_dir.rglob("*")):
        if p.is_file():
            size = p.stat().st_size
            total_size += size
            if total_size > max_bytes:
                raise ValueError("Extracted size exceeded maximum uncompressed archive limit.")
            extracted_files.append(p)

    return extracted_files


def _extract_rar_hardened(input_path: Path, dest_dir: Path) -> list[Path]:
    if rarfile is None:
        raise RuntimeError("RAR extraction requires the rarfile package.")

    max_bytes = settings.max_archive_uncompressed_mb * 1024 * 1024
    extracted_files: list[Path] = []

    try:
        with rarfile.RarFile(input_path) as archive:
            infolist = archive.infolist()
            if len(infolist) > settings.max_archive_entries:
                raise ValueError(f"Archive exceeds maximum entry count of {settings.max_archive_entries}.")

            for info in infolist:
                if info.isdir():
                    continue
                target_path = _sanitize_archive_member(dest_dir, info.filename)
                target_path.parent.mkdir(parents=True, exist_ok=True)

                with archive.open(info) as src, target_path.open("wb") as dst:
                    written = 0
                    while True:
                        chunk = src.read(128 * 1024)
                        if not chunk:
                            break
                        written += len(chunk)
                        if written > max_bytes:
                            raise ValueError("Extracted size exceeded maximum uncompressed archive limit.")
                        dst.write(chunk)
                extracted_files.append(target_path)

    except rarfile.RarCannotExec as exc:
        raise RuntimeError("RAR extraction requires an unrar or 7-Zip executable available on the system PATH.") from exc

    return extracted_files


def extract_archive(input_path: Path, out_dir: Path) -> list[Path]:
    """Safely extracts a supported archive into an isolated subdirectory."""
    lower = input_path.name.lower()
    stem = archive_stem(input_path)
    extract_dir = out_dir / f"{stem}-extracted"
    extract_dir.mkdir(parents=True, exist_ok=True)

    if lower.endswith(".zip"):
        extracted = _extract_zip_hardened(input_path, extract_dir)
    elif lower.endswith(".7z"):
        extracted = _extract_7z_hardened(input_path, extract_dir)
    elif lower.endswith(".rar"):
        extracted = _extract_rar_hardened(input_path, extract_dir)
    elif lower.endswith((".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".tar.xz", ".txz")):
        extracted = _extract_tar_hardened(input_path, extract_dir)
    else:
        raise ValueError(f"Unsupported archive format: '{input_path.name}'.")

    if not extracted:
        raise ValueError("The archive contains no files to extract.")

    return extracted
