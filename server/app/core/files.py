import os
import shutil
import subprocess
import tempfile
import uuid
import glob
from pathlib import Path


PROJECT_MARKER = ".kiwi-workspace"


def new_job_workspace() -> Path:
    root = Path(tempfile.mkdtemp(prefix="kiwi-"))
    (root / "input").mkdir()
    (root / "output").mkdir()
    (root / PROJECT_MARKER).touch()
    return root


def input_dir(workspace: Path) -> Path:
    path = workspace / "input"
    path.mkdir(parents=True, exist_ok=True)
    return path


def output_dir(workspace: Path) -> Path:
    path = workspace / "output"
    path.mkdir(parents=True, exist_ok=True)
    return path


def run_command(args: list[str], timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        capture_output=True,
        timeout=timeout,
        check=True,
        text=True,
    )


def cleanup_dir(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)


def safe_filename(name: str, fallback: str = "file") -> str:
    cleaned = Path(name).name.replace("\x00", "")
    return cleaned or fallback


def unique_output_name(directory: Path, filename: str) -> Path:
    candidate = directory / safe_filename(filename)
    if not candidate.exists():
        return candidate
    stem, suffix = candidate.stem, candidate.suffix
    return directory / f"{stem}-{uuid.uuid4().hex[:8]}{suffix}"


def command_path(configured: str, candidates: list[str] | None = None) -> str | None:
    """Resolve a configured executable plus common Windows installation locations."""
    from shutil import which

    found = which(configured)
    if found:
        return found
    for candidate in candidates or []:
        matches = glob.glob(candidate) if any(ch in candidate for ch in "*?[") else [candidate]
        for match in matches:
            found = which(match)
            if found:
                return found
            if os.path.exists(match):
                return match
    return None


def cleanup_stale_workspaces(max_age_seconds: int) -> None:
    import time
    temp_root = Path(tempfile.gettempdir())
    cutoff = time.time() - max_age_seconds
    for candidate in temp_root.glob("kiwi-*"):
        marker = candidate / PROJECT_MARKER
        try:
            if marker.exists() and candidate.stat().st_mtime < cutoff:
                cleanup_dir(candidate)
        except OSError:
            continue


def zip_files(files: list[Path], out_path: Path, base_dir: Path | None = None) -> Path:
    """Create a ZIP bundle from result files without creating persistent storage."""
    import zipfile

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            arcname = path.relative_to(base_dir) if base_dir else path.name
            archive.write(path, arcname=str(arcname).replace(os.sep, "/"))
    return out_path
