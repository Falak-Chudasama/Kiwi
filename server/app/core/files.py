import glob
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Sequence

PROJECT_MARKER = ".kiwi-workspace"

# Windows reserved device names
_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}


def safe_filename(name: str, fallback: str = "file") -> str:
    """Sanitize arbitrary user-supplied filenames for Windows and POSIX.

    Strips directory traversal, illegal characters, null bytes, and Windows reserved names.
    """
    if not name:
        return fallback

    # Normalize separators and extract purely the basename
    cleaned = name.replace("\\", "/").split("/")[-1].replace("\x00", "").strip()

    # Strip control chars and characters forbidden on Windows/POSIX (<>:"/\|?*)
    cleaned = re.sub(r'[\x00-\x1f\x7f<>:"/\\|?*]', "", cleaned).strip()

    # Prevent hidden files or relative path traversal like "." or ".."
    cleaned = cleaned.lstrip(". ")

    # Truncate overly long filenames
    if len(cleaned) > 200:
        stem, ext = os.path.splitext(cleaned)
        cleaned = stem[: 200 - len(ext)] + ext

    # Check for reserved names
    stem = os.path.splitext(cleaned)[0].upper()
    if stem in _RESERVED_NAMES:
        cleaned = f"safe_{cleaned}"

    return cleaned or fallback


def unique_output_name(directory: Path, filename: str) -> Path:
    """Generates a collision-safe destination path inside directory."""
    clean = safe_filename(filename)
    candidate = directory / clean
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix
    return directory / f"{stem}-{uuid.uuid4().hex[:8]}{suffix}"


def new_job_workspace() -> Path:
    """Creates an isolated temporary directory for a single job."""
    root = Path(tempfile.mkdtemp(prefix="kiwi-"))
    (root / "input").mkdir(parents=True, exist_ok=True)
    (root / "output").mkdir(parents=True, exist_ok=True)
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


def cleanup_dir(path: Path | None) -> None:
    """Safely and recursively deletes a directory if it exists."""
    if path and path.exists():
        shutil.rmtree(path, ignore_errors=True)


def terminate_process_tree(pid: int) -> None:
    """Safely terminates a process and all its child processes."""
    try:
        import psutil
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            try:
                child.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        parent.kill()
    except Exception:
        # Fallback for Windows if psutil fails
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True, check=False)


def run_command(args: list[str], timeout: int = 300, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    """Executes an external command safely without shell=True, capturing output.

    Terminates the full process tree on timeout.
    """
    proc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=False,
        env=env or os.environ.copy(),
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        retcode = proc.poll()
        if retcode != 0:
            raise subprocess.CalledProcessError(retcode, args, output=stdout, stderr=stderr)
        return subprocess.CompletedProcess(args, retcode, stdout, stderr)
    except subprocess.TimeoutExpired:
        terminate_process_tree(proc.pid)
        proc.communicate()  # Clean up zombie/pipes
        raise


def command_path(configured: str, candidates: Sequence[str] | None = None) -> str | None:
    """Resolve a configured executable name or check candidate file paths."""
    found = shutil.which(configured)
    if found:
        return found

    for candidate in candidates or []:
        # Expand environment variables like %LOCALAPPDATA%
        expanded = os.path.expandvars(candidate)
        matches = glob.glob(expanded) if any(ch in expanded for ch in "*?[") else [expanded]
        for match in matches:
            found = shutil.which(match)
            if found:
                return found
            if os.path.exists(match):
                return match
    return None


def cleanup_stale_workspaces(max_age_seconds: int) -> None:
    """Scans system temp directory for orphaned kiwi workspaces and cleans them."""
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
    """Creates a ZIP archive from result files."""
    import zipfile
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            arcname = path.relative_to(base_dir) if base_dir else path.name
            archive.write(path, arcname=str(arcname).replace(os.sep, "/"))
    return out_path
