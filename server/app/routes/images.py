from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.files import cleanup_dir, input_dir, new_job_workspace
from app.core.formats import extension_of, image_target_options, valid_image_targets
from app.core.uploads import save_uploads
from app.models.job import Job, JobKind
from app.workers.queue import task_queue

router = APIRouter(prefix="/api/images", tags=["images"])


@router.get("/targets")
def get_targets(filename: str):
    ext = extension_of(filename)
    return {"source_ext": ext, "targets": image_target_options(ext)}


@router.post("/convert")
async def convert(
    files: list[UploadFile] = File(...),
    target_ext: str = Form(...),
    width: Optional[int] = Form(None),
    height: Optional[int] = Form(None),
    fit_mode: str = Form("contain"),
):
    if not files:
        raise HTTPException(status_code=400, detail="No image files supplied.")
    if width is not None and width <= 0:
        raise HTTPException(status_code=400, detail="Width must be greater than zero.")
    if height is not None and height <= 0:
        raise HTTPException(status_code=400, detail="Height must be greater than zero.")
    if fit_mode not in {"contain", "exact"}:
        raise HTTPException(status_code=400, detail="Unknown image sizing mode.")

    target_ext = target_ext.lower().lstrip(".")

    for file in files:
        source_ext = extension_of(file.filename or "")
        if target_ext not in valid_image_targets(source_ext):
            raise HTTPException(
                status_code=400,
                detail=f"Image conversion from .{source_ext} to .{target_ext} is not supported.",
            )

    workspace = new_job_workspace()
    try:
        saved = await save_uploads(files, input_dir(workspace))
    except Exception:
        cleanup_dir(workspace)
        raise

    job = Job(
        kind=JobKind.IMAGE_CONVERT,
        workspace=workspace,
        payload={
            "input_paths": [str(p) for p in saved],
            "target_ext": target_ext,
            "width": width,
            "height": height,
            "fit_mode": fit_mode,
        },
    )
    task_queue.submit(job)
    return {"job_id": job.id}
