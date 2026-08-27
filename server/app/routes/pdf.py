import json

from fastapi import APIRouter, File, Form, UploadFile

from app.core.uploads import save_uploads
from app.models.job import Job, JobKind
from app.workers.queue import task_queue

router = APIRouter(prefix="/api/pdf", tags=["pdf"])


def _submit(kind: JobKind, input_paths: list[str], extra: dict) -> dict:
    job = Job(kind=kind, payload={"input_paths": input_paths, **extra})
    task_queue.submit(job)
    return {"job_id": job.id}


@router.post("/merge")
async def merge(files: list[UploadFile] = File(...)):
    saved = await save_uploads(files)
    return _submit(JobKind.PDF_MERGE, [str(p) for p in saved], {})


@router.post("/split")
async def split(file: UploadFile = File(...), ranges: str = Form(...)):
    saved = await save_uploads([file])
    parsed_ranges = json.loads(ranges)
    return _submit(JobKind.PDF_SPLIT, [str(p) for p in saved], {"ranges": parsed_ranges})


@router.post("/to-images")
async def to_images(file: UploadFile = File(...), image_format: str = Form("png")):
    saved = await save_uploads([file])
    return _submit(JobKind.PDF_TO_IMAGES, [str(p) for p in saved], {"image_format": image_format})


@router.post("/from-images")
async def from_images(files: list[UploadFile] = File(...)):
    saved = await save_uploads(files)
    return _submit(JobKind.IMAGES_TO_PDF, [str(p) for p in saved], {})


@router.post("/rotate")
async def rotate(file: UploadFile = File(...), degrees: int = Form(...)):
    saved = await save_uploads([file])
    return _submit(JobKind.PDF_ROTATE, [str(p) for p in saved], {"degrees": degrees})


@router.post("/reorder")
async def reorder(file: UploadFile = File(...), order: str = Form(...)):
    saved = await save_uploads([file])
    parsed_order = json.loads(order)
    return _submit(JobKind.PDF_REORDER, [str(p) for p in saved], {"order": parsed_order})


@router.post("/protect")
async def protect(file: UploadFile = File(...), password: str = Form(...)):
    saved = await save_uploads([file])
    return _submit(JobKind.PDF_PROTECT, [str(p) for p in saved], {"password": password})


@router.post("/unlock")
async def unlock(file: UploadFile = File(...), password: str = Form(...)):
    saved = await save_uploads([file])
    return _submit(JobKind.PDF_UNLOCK, [str(p) for p in saved], {"password": password})


@router.post("/watermark")
async def watermark(file: UploadFile = File(...), text: str = Form(...)):
    saved = await save_uploads([file])
    return _submit(JobKind.PDF_WATERMARK, [str(p) for p in saved], {"text": text})


@router.post("/ocr")
async def ocr(file: UploadFile = File(...), language: str = Form("eng")):
    saved = await save_uploads([file])
    return _submit(JobKind.PDF_OCR, [str(p) for p in saved], {"language": language})
