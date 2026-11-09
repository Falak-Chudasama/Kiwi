import io
import pytest
from pathlib import Path
from fastapi import HTTPException, UploadFile
from app.core.uploads import save_upload, save_uploads
from app.core.config import settings

@pytest.mark.asyncio
async def test_save_upload_respects_file_size_limit(tmp_path: Path):
    # Set limit to 100 KB for this test
    content = b"x" * (120 * 1024)  # 120 KB
    file = UploadFile(filename="large.dat", file=io.BytesIO(content))

    with pytest.raises(HTTPException) as exc_info:
        await save_upload(file, tmp_path, max_bytes=100 * 1024)

    assert exc_info.value.status_code == 413
    # Check that partial file was cleaned up on disk
    assert len(list(tmp_path.iterdir())) == 0

@pytest.mark.asyncio
async def test_save_upload_success(tmp_path: Path):
    content = b"hello kiwi test"
    file = UploadFile(filename="test.txt", file=io.BytesIO(content))

    dest, written = await save_upload(file, tmp_path)
    assert dest.exists()
    assert dest.read_bytes() == content
    assert written == len(content)

@pytest.mark.asyncio
async def test_save_uploads_file_count_limit(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(settings, "max_file_count", 3)
    files = [
        UploadFile(filename=f"f{i}.txt", file=io.BytesIO(b"data"))
        for i in range(5)
    ]

    with pytest.raises(HTTPException) as exc_info:
        await save_uploads(files, tmp_path)

    assert exc_info.value.status_code == 400
    assert "Too many files" in exc_info.value.detail

