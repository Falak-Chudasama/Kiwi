import time
from pathlib import Path
import pytest

from app.models.job import Job, JobKind, JobStatus
from app.workers.job_store import job_store
from app.workers.queue import task_queue
from app.core.config import settings
from fastapi import HTTPException

def test_queue_admission_control(tmp_path: Path):
    import queue
    # Simulate a full queue by setting maxsize=2 and filling it
    task_queue._queue = queue.Queue(maxsize=2)
    j1 = Job(kind=JobKind.PDF_MERGE, payload={}, workspace=tmp_path / "j1")
    j2 = Job(kind=JobKind.PDF_MERGE, payload={}, workspace=tmp_path / "j2")
    j3 = Job(kind=JobKind.PDF_MERGE, payload={}, workspace=tmp_path / "j3")

    task_queue._queue.put_nowait(j1)
    task_queue._queue.put_nowait(j2)

    # 3rd job exceeds capacity and raises 429
    with pytest.raises(HTTPException) as exc_info:
        task_queue.submit(j3)
    assert exc_info.value.status_code == 429
    assert "capacity" in exc_info.value.detail.lower()

def test_job_store_hard_ttl_deadline(tmp_path: Path):
    ws = tmp_path / "workspace_ttl"
    ws.mkdir()
    (ws / "output.txt").write_text("result")

    job = Job(kind=JobKind.DOCUMENT_CONVERT, payload={}, workspace=ws)
    job_store.add(job)

    # Finish job
    job_store.update(job.id, status=JobStatus.DONE)
    retrieved = job_store.get(job.id)
    assert retrieved is not None
    assert retrieved.completed_at is not None
    assert retrieved.expires_at is not None

    # Simulate clock advancing past expiry
    retrieved.expires_at = time.time() - 10
    job_store.purge_expired()

    # Must be gone from store and disk
    assert job_store.get(job.id) is None
    assert not ws.exists()

def test_job_cancellation(tmp_path: Path):
    ws = tmp_path / "workspace_cancel"
    ws.mkdir()
    job = Job(kind=JobKind.DOCUMENT_CONVERT, payload={}, workspace=ws)
    job_store.add(job)

    cancelled = job_store.cancel(job.id)
    assert cancelled is True

    retrieved = job_store.get(job.id)
    assert retrieved.status == JobStatus.CANCELLED
    assert retrieved.cancel_requested is True
    # Workspace cleaned immediately
    assert not ws.exists()
