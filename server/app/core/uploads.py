from pathlib import Path

from fastapi import UploadFile

from app.core.files import safe_filename, unique_output_name


async def save_upload(file: UploadFile, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    filename = safe_filename(file.filename or "upload")
    dest_path = unique_output_name(dest_dir, filename)
    with dest_path.open("wb") as target:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            target.write(chunk)
    await file.close()
    return dest_path


async def save_uploads(files: list[UploadFile], dest_dir: Path) -> list[Path]:
    return [await save_upload(file, dest_dir) for file in files]
