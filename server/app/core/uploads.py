from pathlib import Path
from fastapi import HTTPException, UploadFile

from app.core.config import settings
from app.core.files import safe_filename, unique_output_name


CHUNK_SIZE = 128 * 1024  # 128 KB chunks


async def save_upload(
    file: UploadFile,
    dest_dir: Path,
    max_bytes: int | None = None,
    current_request_bytes: int = 0,
    max_request_bytes: int | None = None,
) -> tuple[Path, int]:
    """Streams an upload into dest_dir, strictly enforcing upload byte quotas.

    Returns (saved_path, bytes_written).
    Cleans up any partial file on error and ensures file handles are closed.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    limit_per_file = max_bytes if max_bytes is not None else (settings.max_upload_mb * 1024 * 1024)
    limit_request = max_request_bytes if max_request_bytes is not None else (settings.max_request_mb * 1024 * 1024)

    filename = safe_filename(file.filename or "upload")
    dest_path = unique_output_name(dest_dir, filename)

    bytes_written = 0
    try:
        with dest_path.open("wb") as target:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                chunk_len = len(chunk)
                bytes_written += chunk_len

                if bytes_written > limit_per_file:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File '{filename}' exceeds maximum allowed upload size of {settings.max_upload_mb} MB.",
                    )

                if (current_request_bytes + bytes_written) > limit_request:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Total request upload size exceeds maximum allowed limit of {settings.max_request_mb} MB.",
                    )

                target.write(chunk)
        return dest_path, bytes_written
    except Exception:
        if dest_path.exists():
            try:
                dest_path.unlink()
            except OSError:
                pass
        raise
    finally:
        await file.close()


async def save_uploads(files: list[UploadFile], dest_dir: Path) -> list[Path]:
    """Saves multiple uploaded files, strictly bounding file count, per-file size,
    and cumulative request size.
    """
    if len(files) > settings.max_file_count:
        raise HTTPException(
            status_code=400,
            detail=f"Too many files selected ({len(files)}). The maximum allowed is {settings.max_file_count}.",
        )

    saved_paths: list[Path] = []
    total_bytes = 0
    try:
        for file in files:
            path, written = await save_upload(
                file=file,
                dest_dir=dest_dir,
                current_request_bytes=total_bytes,
            )
            saved_paths.append(path)
            total_bytes += written
        return saved_paths
    except Exception:
        for p in saved_paths:
            try:
                if p.exists():
                    p.unlink()
            except OSError:
                pass
        raise
