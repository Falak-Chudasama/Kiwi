import shutil
import subprocess
import uuid
from pathlib import Path

from app.core.config import settings


def new_job_dir(root: Path) -> Path:
    job_dir = root / uuid.uuid4().hex
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir


def upload_dir() -> Path:
    return new_job_dir(settings.uploads_dir)


def output_dir() -> Path:
    return new_job_dir(settings.outputs_dir)


def run_command(args: list[str], timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        capture_output=True,
        timeout=timeout,
        check=True,
    )


def cleanup_dir(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)
