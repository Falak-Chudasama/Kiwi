import logging
import queue
import threading
from pathlib import Path
from typing import Callable

from fastapi import HTTPException

from app.core.config import settings
from app.core.files import cleanup_dir, output_dir
from app.models.job import Job, JobKind, JobStatus, ResultFile
from app.workers.job_store import job_store

logger = logging.getLogger("kiwi.worker")
TaskHandler = Callable[[Job], list[str]]


class QueueFullError(Exception):
    """Raised when the task queue has reached its maximum capacity."""


class TaskQueue:
    def __init__(self) -> None:
        self._queue: queue.Queue[Job] = queue.Queue(maxsize=settings.max_queue_size)
        self._handlers: dict[str, TaskHandler] = {}
        self._threads: list[threading.Thread] = []
        self._shutdown_event = threading.Event()
        # Per-engine concurrency guard for LibreOffice to avoid profile/instance lock contention
        self.libreoffice_lock = threading.Lock()

    def register(self, kind: str, handler: TaskHandler) -> None:
        self._handlers[kind] = handler

    def submit(self, job: Job) -> None:
        """Admits a job into the queue with back-pressure.

        Raises HTTPException(429) if capacity is exhausted.
        """
        try:
            self._queue.put_nowait(job)
            job_store.add(job)
        except queue.Full:
            cleanup_dir(job.workspace)
            raise HTTPException(
                status_code=429,
                detail=f"Kiwi processing queue is at maximum capacity ({settings.max_queue_size} pending jobs). Please try again shortly.",
            )

    def start(self) -> None:
        if self._threads:
            return
        for i in range(settings.worker_count):
            thread = threading.Thread(target=self._worker_loop, name=f"kiwi-worker-{i}", daemon=True)
            thread.start()
            self._threads.append(thread)

    def _worker_loop(self) -> None:
        while not self._shutdown_event.is_set():
            try:
                job = self._queue.get(timeout=1.0)
            except queue.Empty:
                continue

            try:
                self._run_job(job)
            finally:
                self._queue.task_done()

    @staticmethod
    def _media_type(path: Path) -> str:
        suffix = path.suffix.lower()
        return {
            ".pdf": "application/pdf",
            ".zip": "application/zip",
            ".7z": "application/x-7z-compressed",
            ".tar": "application/x-tar",
            ".json": "application/json",
            ".txt": "text/plain",
            ".csv": "text/csv",
            ".html": "text/html",
            ".htm": "text/html",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".avif": "image/avif",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".bmp": "image/bmp",
            ".tiff": "image/tiff",
            ".tif": "image/tiff",
            ".ico": "image/x-icon",
            ".heic": "image/heic",
            ".heif": "image/heif",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".odt": "application/vnd.oasis.opendocument.text",
            ".rtf": "application/rtf",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".odp": "application/vnd.oasis.opendocument.presentation",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".ods": "application/vnd.oasis.opendocument.spreadsheet",
            ".doc": "application/msword",
            ".ppt": "application/vnd.ms-powerpoint",
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".flac": "audio/flac",
            ".ogg": "audio/ogg",
            ".m4a": "audio/mp4",
            ".mp4": "video/mp4",
            ".webm": "video/webm",
            ".mkv": "video/x-matroska",
        }.get(suffix, "application/octet-stream")

    def _result_files(self, paths: list[str]) -> list[ResultFile]:
        results: list[ResultFile] = []
        for raw_path in paths:
            path = Path(raw_path)
            if path.exists() and path.is_file():
                results.append(
                    ResultFile(
                        str(path),
                        path.name,
                        path.stat().st_size,
                        self._media_type(path),
                    )
                )
        return results

    def _cleanup_inputs(self, job: Job) -> None:
        """Strict privacy: immediately deletes original input files upon job completion or failure."""
        cleanup_dir(job.workspace / "input")

    def _run_job(self, job: Job) -> None:
        if job.cancel_requested or job.status == JobStatus.CANCELLED:
            self._cleanup_inputs(job)
            cleanup_dir(job.workspace)
            return

        handler = self._handlers.get(job.kind.value)
        if handler is None:
            job_store.update(job.id, status=JobStatus.FAILED, error="Unsupported operation.")
            self._cleanup_inputs(job)
            cleanup_dir(job.workspace)
            return

        job_store.update(job.id, status=JobStatus.PROCESSING, progress=10)
        try:
            if job.cancel_requested:
                job_store.update(job.id, status=JobStatus.CANCELLED, error="Job cancelled.")
                self._cleanup_inputs(job)
                cleanup_dir(job.workspace)
                return

            result_paths = handler(job)

            if job.cancel_requested:
                job_store.update(job.id, status=JobStatus.CANCELLED, error="Job cancelled.")
                self._cleanup_inputs(job)
                cleanup_dir(job.workspace)
                return

            job_store.update(job.id, status=JobStatus.FINALIZING, progress=90)
            results = self._result_files(result_paths)
            if not results:
                raise RuntimeError("The conversion engine finished without producing valid output files.")

            # Validate each output file: existence, nonzero size
            for r in results:
                p = Path(r.path)
                if not p.exists() or p.stat().st_size == 0:
                    raise RuntimeError(f"Output file '{r.name}' is empty or invalid.")

            # Input files are purged immediately
            self._cleanup_inputs(job)
            job_store.update(job.id, status=JobStatus.DONE, progress=100, result_files=results)

        except Exception as exc:
            logger.exception("Job %s failed: %s", job.id, exc)
            self._cleanup_inputs(job)
            cleanup_dir(job.workspace)
            error_msg = self._clean_error(exc)
            job_store.update(job.id, status=JobStatus.FAILED, error=error_msg)

    @staticmethod
    def _clean_error(exc: Exception) -> str:
        from app.core.errors import KiwiConversionError

        if isinstance(exc, KiwiConversionError):
            return exc.safe_message

        import subprocess as _subprocess

        if isinstance(exc, _subprocess.CalledProcessError):
            return f"The conversion process exited with an error (code {exc.returncode})."
        if isinstance(exc, _subprocess.TimeoutExpired):
            return "The conversion exceeded the maximum time limit and was stopped."
        if isinstance(exc, (OSError, FileNotFoundError)):
            return "A file system error occurred during processing."

        message = str(exc).strip()
        # Ensure no sensitive path leaks in message
        from app.core.errors import sanitize_text
        return sanitize_text(message) or exc.__class__.__name__


task_queue = TaskQueue()
