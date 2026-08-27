import logging
import queue
import threading
from pathlib import Path
from typing import Callable

from app.core.config import settings
from app.core.files import cleanup_dir, output_dir
from app.models.job import Job, JobKind, JobStatus, ResultFile
from app.workers.job_store import job_store

logger = logging.getLogger("kiwi.worker")
TaskHandler = Callable[[Job], list[str]]


class TaskQueue:
    def __init__(self) -> None:
        self._queue: queue.Queue[Job] = queue.Queue()
        self._handlers: dict[str, TaskHandler] = {}
        self._threads: list[threading.Thread] = []

    def register(self, kind: str, handler: TaskHandler) -> None:
        self._handlers[kind] = handler

    def submit(self, job: Job) -> None:
        job_store.add(job)
        self._queue.put(job)

    def start(self) -> None:
        if self._threads:
            return
        for i in range(settings.worker_count):
            thread = threading.Thread(target=self._worker_loop, name=f"kiwi-worker-{i}", daemon=True)
            thread.start()
            self._threads.append(thread)

    def _worker_loop(self) -> None:
        while True:
            job = self._queue.get()
            try:
                self._run_job(job)
            finally:
                self._queue.task_done()

    @staticmethod
    def _media_type(path: Path) -> str:
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
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".odt": "application/vnd.oasis.opendocument.text",
            ".rtf": "application/rtf",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".odp": "application/vnd.oasis.opendocument.presentation",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".ods": "application/vnd.oasis.opendocument.spreadsheet",
            ".doc": "application/msword",
            ".ppt": "application/vnd.ms-powerpoint",
        }.get(path.suffix.lower(), "application/octet-stream")

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

    def _package_multi_output(self, job: Job, paths: list[str]) -> list[str]:
        # Keep multi-file results as individual downloads. Bundling results into
        # another ZIP hides what the operation actually produced and makes
        # extraction especially confusing.
        return paths

    def _cleanup_inputs(self, job: Job) -> None:
        cleanup_dir(job.workspace / "input")

    def _run_job(self, job: Job) -> None:
        handler = self._handlers.get(job.kind.value)
        if handler is None:
            job_store.update(job.id, status=JobStatus.FAILED, error="Unsupported operation.")
            cleanup_dir(job.workspace)
            return

        job_store.update(job.id, status=JobStatus.PROCESSING, progress=5)
        try:
            result_paths = handler(job)
            result_paths = self._package_multi_output(job, result_paths)
            results = self._result_files(result_paths)
            if not results:
                raise RuntimeError("The operation completed without producing a downloadable result.")

            self._cleanup_inputs(job)
            job_store.update(job.id, status=JobStatus.DONE, progress=100, result_files=results)
        except Exception as exc:
            logger.exception("Job %s failed", job.id)
            self._cleanup_inputs(job)
            cleanup_dir(job.workspace)
            job_store.update(job.id, status=JobStatus.FAILED, error=self._clean_error(exc))

    @staticmethod
    def _clean_error(exc: Exception) -> str:
        message = str(exc).strip()
        return message or exc.__class__.__name__


task_queue = TaskQueue()
