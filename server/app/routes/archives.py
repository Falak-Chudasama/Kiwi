from fastapi import APIRouter, File, Form, UploadFile

from app.core.uploads import save_uploads
from app.models.job import Job, JobKind
from app.workers.queue import task_queue

router = APIRouter(prefix="/api/archives", tags=["archives"])


@router.post("/create")
async def create(
    files: list[UploadFile] = File(...),
    archive_format: str = Form(...),
    name: str = Form("archive"),
):
    saved = await save_uploads(files)
    job = Job(
        kind=JobKind.ARCHIVE_CREATE,
        payload={
            "input_paths": [str(p) for p in saved],
            "archive_format": archive_format,
            "name": name,
        },
    )
    task_queue.submit(job)
    return {"job_id": job.id}


@router.post("/extract")
async def extract(file: UploadFile = File(...)):
    saved = await save_uploads([file])
    job = Job(
        kind=JobKind.ARCHIVE_EXTRACT,
        payload={"input_paths": [str(p) for p in saved]},
    )
    task_queue.submit(job)
    return {"job_id": job.id}
