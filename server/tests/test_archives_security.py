import io
import zipfile
import tarfile
import pytest
from pathlib import Path

from app.services.archives import (
    create_archive,
    extract_archive,
    _sanitize_archive_member,
)

def test_zip_slip_traversal_blocked(tmp_path: Path):
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    # Direct test of member sanitization
    with pytest.raises(ValueError, match="directory traversal"):
        _sanitize_archive_member(dest_dir, "../../evil.sh")

    with pytest.raises(ValueError, match="illegal absolute path"):
        _sanitize_archive_member(dest_dir, "/etc/passwd")

    with pytest.raises(ValueError, match="drive specification"):
        _sanitize_archive_member(dest_dir, "C:\\Windows\\cmd.exe")

def test_zip_bomb_detection(tmp_path: Path):
    archive_path = tmp_path / "bomb.zip"
    dest_dir = tmp_path / "out"

    # Create a zip containing a highly compressed file with extreme ratio
    zeros = b"\x00" * (15 * 1024 * 1024)  # 15 MB of zeros
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("zero.dat", zeros)

    # Decompression bomb ratio check triggers
    with pytest.raises(ValueError, match="decompression bomb"):
        extract_archive(archive_path, dest_dir)

def test_archive_create_and_extract_zip(tmp_path: Path):
    f1 = tmp_path / "doc1.txt"
    f1.write_text("Kiwi archive content 1", encoding="utf-8")
    f2 = tmp_path / "doc2.txt"
    f2.write_text("Kiwi archive content 2", encoding="utf-8")

    out_dir = tmp_path / "archives"
    zip_path = create_archive([f1, f2], out_dir, "zip", name="testbundle")
    assert zip_path.exists()
    assert zip_path.suffix == ".zip"

    # Extract
    extract_dir = tmp_path / "extracted"
    results = extract_archive(zip_path, extract_dir)
    assert len(results) == 2
    names = {r.name for r in results}
    assert "doc1.txt" in names
    assert "doc2.txt" in names

def test_archive_tar_symlink_rejection(tmp_path: Path):
    tar_path = tmp_path / "links.tar"
    dest_dir = tmp_path / "out_tar"

    # Create a tar with a symbolic link
    with tarfile.open(tar_path, "w") as tf:
        info = tarfile.TarInfo(name="symlink")
        info.type = tarfile.SYMTYPE
        info.linkname = "/etc/passwd"
        tf.addfile(info)

    with pytest.raises(ValueError, match="symbolic or hard links"):
        extract_archive(tar_path, dest_dir)

