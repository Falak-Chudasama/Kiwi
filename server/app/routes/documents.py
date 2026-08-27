from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.files import cleanup_dir, input_dir, new_job_workspace
from app.core.formats import document_target_options, extension_of, universal_target_options
from app.core.uploads import save_uploads
from app.models.job import Job, JobKind
from app.workers.queue import task_queue

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("/targets")
def get_targets(filename: str):
    source_ext = extension_of(filename)
    return {
        "source_ext": source_ext,
        "targets": universal_target_options(source_ext),
    }


@router.post("/convert")
async def convert(
    file: UploadFile = File(...),
    target_ext: str = Form(...),
):
    source_ext = extension_of(file.filename or "")
    target_ext = target_ext.lower().lstrip(".")

    options = {item["ext"]: item for item in document_target_options(source_ext)}
    option = options.get(target_ext)
    if not option or not option["supported"]:
        raise HTTPException(
            status_code=400,
            detail=option["reason"] if option else f"Conversion from .{source_ext} to .{target_ext} is not supported.",
        )

    workspace = new_job_workspace()
    try:
        saved = await save_uploads([file], input_dir(workspace))
    except Exception:
        cleanup_dir(workspace)
        raise

    job = Job(
        kind=JobKind.DOCUMENT_CONVERT,
        workspace=workspace,
        payload={
            "input_paths": [str(p) for p in saved],
            "target_ext": target_ext,
        },
    )
    task_queue.submit(job)
    return {"job_id": job.id}
