from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.workers.job_store import job_store

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("/{job_id}")
def get_job_status(job_id: str):
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found or its temporary files have expired.")
    return job.to_public_dict()


@router.get("/{job_id}/download/{file_index}")
def download_result(job_id: str, file_index: int):
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found or its temporary files have expired.")
    if file_index < 0 or file_index >= len(job.result_files):
        raise HTTPException(status_code=404, detail="File not found.")

    result = job.result_files[file_index]
    file_path = Path(result.path)
    if not file_path.exists():
        raise HTTPException(status_code=410, detail="File is no longer available.")

    job_store.touch(job_id)
    return FileResponse(path=file_path, filename=result.name, media_type=result.media_type)
