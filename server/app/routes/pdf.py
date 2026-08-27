import json

from fastapi import APIRouter, File, Form, UploadFile

from app.core.files import cleanup_dir, input_dir, new_job_workspace
from app.core.uploads import save_uploads
from app.models.job import Job, JobKind
from app.workers.queue import task_queue

router = APIRouter(prefix="/api/pdf", tags=["pdf"])


def _submit(kind: JobKind, workspace, input_paths: list[str], extra: dict) -> dict:
    job = Job(kind=kind, workspace=workspace, payload={"input_paths": input_paths, **extra})
    task_queue.submit(job)
    return {"job_id": job.id}


async def _workspace_files(files: list[UploadFile]):
    workspace = new_job_workspace()
    try:
        saved = await save_uploads(files, input_dir(workspace))
        return workspace, saved
    except Exception:
        cleanup_dir(workspace)
        raise


@router.post("/merge")
async def merge(files: list[UploadFile] = File(...)):
    workspace, saved = await _workspace_files(files)
    return _submit(JobKind.PDF_MERGE, workspace, [str(p) for p in saved], {})


@router.post("/split")
async def split(file: UploadFile = File(...), ranges: str = Form(...)):
    workspace, saved = await _workspace_files([file])
    parsed_ranges = json.loads(ranges)
    return _submit(JobKind.PDF_SPLIT, workspace, [str(saved[0])], {"ranges": parsed_ranges})


@router.post("/to-images")
async def to_images(file: UploadFile = File(...), image_format: str = Form("png"), dpi: int = Form(150)):
    workspace, saved = await _workspace_files([file])
    return _submit(JobKind.PDF_TO_IMAGES, workspace, [str(saved[0])], {"image_format": image_format, "dpi": dpi})


@router.post("/from-images")
async def from_images(files: list[UploadFile] = File(...)):
    workspace, saved = await _workspace_files(files)
    return _submit(JobKind.IMAGES_TO_PDF, workspace, [str(p) for p in saved], {})


@router.post("/rotate")
async def rotate(file: UploadFile = File(...), degrees: int = Form(...)):
    workspace, saved = await _workspace_files([file])
    return _submit(JobKind.PDF_ROTATE, workspace, [str(saved[0])], {"degrees": degrees})


@router.post("/reorder")
async def reorder(file: UploadFile = File(...), order: str = Form(...)):
    workspace, saved = await _workspace_files([file])
    return _submit(JobKind.PDF_REORDER, workspace, [str(saved[0])], {"order": json.loads(order)})


@router.post("/protect")
async def protect(file: UploadFile = File(...), password: str = Form(...)):
    workspace, saved = await _workspace_files([file])
    return _submit(JobKind.PDF_PROTECT, workspace, [str(saved[0])], {"password": password})


@router.post("/unlock")
async def unlock(file: UploadFile = File(...), password: str = Form(...)):
    workspace, saved = await _workspace_files([file])
    return _submit(JobKind.PDF_UNLOCK, workspace, [str(saved[0])], {"password": password})


@router.post("/watermark")
async def watermark(
    file: UploadFile = File(...),
    text: str = Form(...),
    fontsize: int = Form(40),
    opacity: float = Form(0.25),
    angle: int = Form(35),
    position: str = Form("center"),
    color: str = Form("120,120,120"),
):
    workspace, saved = await _workspace_files([file])
    try:
        if color.strip().startswith("["):
            parsed = json.loads(color)
        else:
            parsed = [int(part.strip()) for part in color.split(",")]
        rgb = tuple(int(value) for value in parsed)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("Watermark color must be a valid RGB value.") from exc
    if len(rgb) != 3 or any(not 0 <= value <= 255 for value in rgb):
        raise ValueError("Watermark color must contain three RGB values between 0 and 255.")
    return _submit(
        JobKind.PDF_WATERMARK,
        workspace,
        [str(saved[0])],
        {
            "text": text,
            "fontsize": max(8, min(180, fontsize)),
            "opacity": max(0.05, min(1.0, opacity)),
            "angle": angle,
            "position": position,
            "color": list(rgb),
        },
    )


@router.post("/ocr")
async def ocr(file: UploadFile = File(...), language: str = Form("eng")):
    workspace, saved = await _workspace_files([file])
    return _submit(JobKind.PDF_OCR, workspace, [str(saved[0])], {"language": language})
