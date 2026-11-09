import json

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.files import cleanup_dir, input_dir, new_job_workspace
from app.core.uploads import save_uploads
from app.models.job import Job, JobKind
from app.services.pdf_tools import SUPPORTED_PDF_IMAGE_FORMATS
from app.workers.queue import task_queue

router = APIRouter(prefix="/api/pdf", tags=["pdf"])


def _submit(kind: JobKind, workspace, input_paths: list[str], extra: dict) -> dict:
    job = Job(kind=kind, workspace=workspace, payload={"input_paths": input_paths, **extra})
    try:
        task_queue.submit(job)
        return {"job_id": job.id}
    except Exception:
        cleanup_dir(workspace)
        raise


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
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="Select at least two PDF files to merge.")
    workspace, saved = await _workspace_files(files)
    return _submit(JobKind.PDF_MERGE, workspace, [str(p) for p in saved], {})


@router.post("/split")
async def split(file: UploadFile = File(...), ranges: str = Form(...)):
    # Validate parameter BEFORE creating workspace to prevent orphaned directories
    try:
        parsed_ranges = json.loads(ranges)
        if not isinstance(parsed_ranges, list) or not parsed_ranges:
            raise ValueError()
        for r in parsed_ranges:
            if not isinstance(r, (list, tuple)) or len(r) != 2:
                raise ValueError()
            start, end = int(r[0]), int(r[1])
            if start < 1 or end < start:
                raise ValueError()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid page ranges. Expected format: [[1, 3], [5, 7]].",
        )

    workspace, saved = await _workspace_files([file])
    return _submit(JobKind.PDF_SPLIT, workspace, [str(saved[0])], {"ranges": parsed_ranges})


@router.post("/to-images")
async def to_images(
    file: UploadFile = File(...),
    image_format: str = Form("png"),
    dpi: int = Form(150),
):
    fmt = image_format.lower().lstrip(".")
    if fmt not in SUPPORTED_PDF_IMAGE_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image format '{fmt}'. Choose from: {', '.join(sorted(SUPPORTED_PDF_IMAGE_FORMATS))}.",
        )
    safe_dpi = max(50, min(300, int(dpi)))

    workspace, saved = await _workspace_files([file])
    return _submit(JobKind.PDF_TO_IMAGES, workspace, [str(saved[0])], {"image_format": fmt, "dpi": safe_dpi})


@router.post("/from-images")
async def from_images(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="Select at least one image to assemble into PDF.")
    workspace, saved = await _workspace_files(files)
    return _submit(JobKind.IMAGES_TO_PDF, workspace, [str(p) for p in saved], {})


@router.post("/rotate")
async def rotate(file: UploadFile = File(...), degrees: int = Form(...)):
    if degrees not in {90, 180, 270, -90, -180, -270}:
        raise HTTPException(status_code=400, detail="Rotation angle must be 90, 180, or 270 degrees.")
    workspace, saved = await _workspace_files([file])
    return _submit(JobKind.PDF_ROTATE, workspace, [str(saved[0])], {"degrees": degrees})


@router.post("/reorder")
async def reorder(file: UploadFile = File(...), order: str = Form(...)):
    # Validate parameter BEFORE creating workspace
    try:
        parsed_order = json.loads(order)
        if not isinstance(parsed_order, list) or not parsed_order:
            raise ValueError()
        parsed_order = [int(x) for x in parsed_order]
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid page order. Expected a JSON list of 0-based page indices, e.g. [2, 0, 1].",
        )

    workspace, saved = await _workspace_files([file])
    return _submit(JobKind.PDF_REORDER, workspace, [str(saved[0])], {"order": parsed_order})


@router.post("/protect")
async def protect(file: UploadFile = File(...), password: str = Form(...)):
    if not password or not password.strip():
        raise HTTPException(status_code=400, detail="Password cannot be empty.")
    workspace, saved = await _workspace_files([file])
    return _submit(JobKind.PDF_PROTECT, workspace, [str(saved[0])], {"password": password})


@router.post("/unlock")
async def unlock(file: UploadFile = File(...), password: str = Form(...)):
    if not password:
        raise HTTPException(status_code=400, detail="Password cannot be empty.")
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
    cleaned_text = text.strip()
    if not cleaned_text:
        raise HTTPException(status_code=400, detail="Watermark text cannot be empty.")

    # Validate color BEFORE workspace creation
    try:
        if color.strip().startswith("["):
            parsed = json.loads(color)
        else:
            parsed = [int(part.strip()) for part in color.split(",")]
        rgb = tuple(int(value) for value in parsed)
        if len(rgb) != 3 or any(not 0 <= value <= 255 for value in rgb):
            raise ValueError()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Watermark color must contain three RGB values between 0 and 255 (e.g. '120,120,120').",
        )

    workspace, saved = await _workspace_files([file])
    return _submit(
        JobKind.PDF_WATERMARK,
        workspace,
        [str(saved[0])],
        {
            "text": cleaned_text,
            "fontsize": max(8, min(180, int(fontsize))),
            "opacity": max(0.05, min(1.0, float(opacity))),
            "angle": int(angle),
            "position": position,
            "color": list(rgb),
        },
    )


@router.post("/ocr")
async def ocr(file: UploadFile = File(...), language: str = Form("eng")):
    lang = language.strip() or "eng"
    workspace, saved = await _workspace_files([file])
    return _submit(JobKind.PDF_OCR, workspace, [str(saved[0])], {"language": lang})
