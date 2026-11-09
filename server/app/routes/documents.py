from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.files import cleanup_dir, input_dir, new_job_workspace
from app.core.formats import extension_of, resolve_strategy, universal_target_options
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

    # Validate strategy BEFORE creating workspace to prevent orphaned directories
    outcome = resolve_strategy(source_ext, target_ext)
    if not outcome.supported:
        raise HTTPException(
            status_code=400,
            detail=outcome.reason or f"Conversion from .{source_ext} to .{target_ext} is not supported.",
        )
    if not outcome.ready:
        raise HTTPException(
            status_code=400,
            detail=outcome.reason or f"Conversion requires an optional engine ({outcome.required_engine}) that is not detected on this machine.",
        )

    workspace = new_job_workspace()
    try:
        saved = await save_uploads([file], input_dir(workspace))
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
    except Exception:
        cleanup_dir(workspace)
        raise
