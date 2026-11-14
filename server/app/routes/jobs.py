from pathlib import Path

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse

from app.workers.job_store import job_store

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("/{job_id}")
def get_job_status(job_id: str):
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found or its temporary output files have expired.",
        )
    return job.to_public_dict()


@router.post("/{job_id}/cancel")
def cancel_job(job_id: str):
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")

    cancelled = job_store.cancel(job_id)
    if not cancelled:
        raise HTTPException(
            status_code=400,
            detail=f"Job cannot be cancelled (current status: {job.status.value}).",
        )
    return {"cancelled": True, "job_id": job_id, "status": "cancelled"}


@router.get("/{job_id}/download/{file_index}")
def download_result(job_id: str, file_index: int, response: Response):
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found or its temporary output files have expired.",
        )
    if file_index < 0 or file_index >= len(job.result_files):
        raise HTTPException(status_code=404, detail="Requested file index not found.")

    result = job.result_files[file_index]
    file_path = Path(result.path)
    if not file_path.exists():
        raise HTTPException(
            status_code=410,
            detail="Output file is no longer available on this server.",
        )

    # Privacy & download headers
    headers = {
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Access-Control-Expose-Headers": "Content-Disposition",
    }

    # NOTE: Repeated downloads do NOT extend retention. Hard deadline from completion.
    return FileResponse(
        path=file_path,
        filename=result.name,
        media_type=result.media_type,
        content_disposition_type="attachment",
        headers=headers,
    )
