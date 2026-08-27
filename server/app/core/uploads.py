from pathlib import Path

from fastapi import UploadFile

from app.core.files import upload_dir


async def save_upload(file: UploadFile, dest_dir: Path) -> Path:
    dest_path = dest_dir / file.filename
    contents = await file.read()
    dest_path.write_bytes(contents)
    return dest_path


async def save_uploads(files: list[UploadFile]) -> list[Path]:
    dest_dir = upload_dir()
    saved: list[Path] = []
    for file in files:
        saved.append(await save_upload(file, dest_dir))
    return saved
