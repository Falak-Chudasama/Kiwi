import threading
import time
from pathlib import Path

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

            now = time.time()
            if status is not None:
                # Do not transition out of terminal states (cancelled/failed)
                if job.status in (JobStatus.CANCELLED, JobStatus.EXPIRED) and status not in (
                    JobStatus.CANCELLED,
                    JobStatus.EXPIRED,
                ):
                    return

                job.status = status
                if status == JobStatus.PROCESSING and job.started_at is None:
                    job.started_at = now
                elif status in (JobStatus.DONE, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.EXPIRED):
                    if job.completed_at is None:
                        job.completed_at = now
                    # Absolute hard deadline: expires strictly after job_ttl_seconds
                    job.expires_at = now + settings.job_ttl_seconds

            if progress is not None:
                job.progress = progress
            if error is not None:
                job.error = error
            if result_files is not None:
                job.result_files = result_files

    def cancel(self, job_id: str) -> bool:
        """Requests cancellation of a job. If queued or processing, marks cancelled and cleans workspace."""
        workspaces_to_clean: list[Path] = []
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return False

            if job.status in (JobStatus.DONE, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.EXPIRED):
                return False

            job.cancel_requested = True
            job.status = JobStatus.CANCELLED
            job.error = "Job cancelled by user."
            now = time.time()
            job.completed_at = now
            job.expires_at = now + 60  # Keep record briefly for client acknowledgement
            workspaces_to_clean.append(job.workspace)

        for ws in workspaces_to_clean:
            cleanup_dir(ws)
        return True

    def _cleanup_loop(self) -> None:
        while True:
            time.sleep(settings.cleanup_interval_seconds)
            self.purge_expired()

    def purge_expired(self) -> None:
        now = time.time()
        workspaces_to_clean: list[Path] = []

        with self._lock:
            for jid, job in list(self._jobs.items()):
                # 1. Enforce hard TTL deadline on terminal jobs
                if job.status in (JobStatus.DONE, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.EXPIRED):
                    if job.expires_at is not None and now >= job.expires_at:
                        workspaces_to_clean.append(job.workspace)
                        del self._jobs[jid]
                    continue

                # 2. Enforce maximum queue age for pending jobs
                if job.status == JobStatus.QUEUED:
                    if (now - job.created_at) > settings.max_queue_wait_seconds:
                        job.status = JobStatus.EXPIRED
                        job.error = "Job expired waiting in queue."
                        job.completed_at = now
                        job.expires_at = now + 60
                        workspaces_to_clean.append(job.workspace)
                    continue

                # 3. Enforce maximum execution duration for running jobs
                if job.status in (JobStatus.PROCESSING, JobStatus.FINALIZING):
                    started = job.started_at or job.created_at
                    if (now - started) > settings.max_job_duration_seconds:
                        job.status = JobStatus.FAILED
                        job.error = "Job exceeded maximum allowed execution duration."
                        job.completed_at = now
                        job.expires_at = now + 60
                        job.cancel_requested = True
                        workspaces_to_clean.append(job.workspace)

        for ws in workspaces_to_clean:
            cleanup_dir(ws)


job_store = JobStore()
