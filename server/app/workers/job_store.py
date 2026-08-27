import threading
import time

from app.core.config import settings
from app.models.job import Job, JobStatus


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def add(self, job: Job) -> None:
        with self._lock:
            self._jobs[job.id] = job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update(
        self,
        job_id: str,
        status: JobStatus | None = None,
        progress: int | None = None,
        error: str | None = None,
        result_files: list[str] | None = None,
    ) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            if status is not None:
                job.status = status
            if progress is not None:
                job.progress = progress
            if error is not None:
                job.error = error
            if result_files is not None:
                job.result_files = result_files
            job.touch()

    def purge_expired(self) -> None:
        cutoff = time.time() - settings.job_ttl_seconds
        with self._lock:
            expired = [jid for jid, j in self._jobs.items() if j.updated_at < cutoff]
            for jid in expired:
                del self._jobs[jid]


job_store = JobStore()
