from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.files import cleanup_dir, input_dir, new_job_workspace
from app.core.formats import ARCHIVE_INPUT_EXTENSIONS, ARCHIVE_OUTPUT_EXTENSIONS, extension_of
from app.core.uploads import save_uploads
from app.models.job import Job, JobKind
from app.workers.queue import task_queue

router = APIRouter(prefix="/api/archives", tags=["archives"])


@router.post("/create")
async def create(
    files: list[UploadFile] = File(...),
    archive_format: str = Form(...),
    name: str = Form("bundle"),
):
    if not files:
        raise HTTPException(status_code=400, detail="Select at least one file to archive.")

    archive_format = archive_format.lower().lstrip(".")
    if archive_format not in ARCHIVE_OUTPUT_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported archive format: {archive_format}")

    workspace = new_job_workspace()
    try:
        saved = await save_uploads(files, input_dir(workspace))
    except Exception:
        cleanup_dir(workspace)
        raise

    job = Job(
        kind=JobKind.ARCHIVE_CREATE,
        workspace=workspace,
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
    filename = (file.filename or "").lower()
    if not any(filename.endswith(f".{ext}") for ext in ARCHIVE_INPUT_EXTENSIONS):
        raise HTTPException(status_code=400, detail="Unsupported archive format.")

    workspace = new_job_workspace()
    try:
        saved = await save_uploads([file], input_dir(workspace))
    except Exception:
        cleanup_dir(workspace)
        raise

    job = Job(
        kind=JobKind.ARCHIVE_EXTRACT,
        workspace=workspace,
        payload={"input_paths": [str(saved[0])]},
    )
    task_queue.submit(job)
    return {"job_id": job.id}
