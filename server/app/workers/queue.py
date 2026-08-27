import logging
import queue
import threading
from typing import Callable

from app.core.config import settings
from app.models.job import Job, JobStatus
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
        for i in range(settings.worker_count):
            t = threading.Thread(target=self._worker_loop, name=f"kiwi-worker-{i}", daemon=True)
            t.start()
            self._threads.append(t)

    def _worker_loop(self) -> None:
        while True:
            job = self._queue.get()
            self._run_job(job)
            self._queue.task_done()

    def _run_job(self, job: Job) -> None:
        handler = self._handlers.get(job.kind.value)
        if handler is None:
            job_store.update(job.id, status=JobStatus.FAILED, error="Unsupported operation.")
            return

        job_store.update(job.id, status=JobStatus.PROCESSING, progress=5)
        try:
            result_files = handler(job)
            job_store.update(
                job.id,
                status=JobStatus.DONE,
                progress=100,
                result_files=result_files,
            )
        except Exception as exc:
            logger.exception("Job %s failed", job.id)
            job_store.update(job.id, status=JobStatus.FAILED, error=str(exc))


task_queue = TaskQueue()
