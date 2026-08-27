import threading
import time

from app.core.config import settings
from app.core.files import cleanup_dir
from app.models.job import Job, JobStatus, ResultFile


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True,
            name="kiwi-cleanup",
        )
        self._cleanup_thread.start()

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
        result_files: list[ResultFile] | None = None,
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

    def touch(self, job_id: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.touch()

    def _cleanup_loop(self) -> None:
        while True:
            time.sleep(settings.cleanup_interval_seconds)
            self.purge_expired()

    def purge_expired(self) -> None:
        cutoff = time.time() - settings.job_ttl_seconds
        expired: list[Job] = []
        with self._lock:
            for jid, job in list(self._jobs.items()):
                # Never delete an active job merely because its processing
                # happens to take longer than the output retention period.
                if job.status in {JobStatus.QUEUED, JobStatus.PROCESSING}:
                    continue
                if job.updated_at < cutoff:
                    expired.append(job)
                    del self._jobs[jid]
        for job in expired:
            cleanup_dir(job.workspace)


job_store = JobStore()
