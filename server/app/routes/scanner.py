from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import fitz
from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse
import numpy as np

from app.core.files import cleanup_dir, input_dir, new_job_workspace
from app.core.uploads import save_uploads
from app.models.job import Job, JobKind
from app.services.scanner.capture_validation import validate_capture_file
from app.services.scanner.document_detection import detect_document_bounds
from app.services.scanner.presets import ScannerPreset, preset_store
from app.services.scanner.quality_assessment import assess_image_quality
from app.workers.job_store import job_store
from app.workers.queue import task_queue

router = APIRouter(prefix="/api/v1/scanner", tags=["scanner"])


@router.post("/detect")
async def detect_document(file: UploadFile = File(...)):
    """Detects document boundary corners and assesses capture quality."""
    suffix = Path(file.filename or "upload.jpg").suffix.lower()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = Path(tmp.name)
        content = await file.read()
        tmp_path.write_bytes(content)

    try:
        validate_capture_file(tmp_path)
        if suffix == ".pdf":
            doc = fitz.open(tmp_path)
            first_page = doc[0]
            pix = first_page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("png")
            doc.close()
            bgr = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
        else:
            bgr = cv2.imread(str(tmp_path), cv2.IMREAD_COLOR)

        if bgr is None:
            raise HTTPException(status_code=400, detail="Cannot decode uploaded image.")

        h, w = bgr.shape[:2]
        quality = assess_image_quality(bgr)
        bounds = detect_document_bounds(bgr)

        return {
            "width": int(w),
            "height": int(h),
            "corners": [[float(c[0]), float(c[1])] for c in bounds.corners],
            "confidence": float(bounds.confidence),
            "detected_auto": bool(bounds.detected_auto),
            "aspect_ratio": float(bounds.aspect_ratio),
            "document_type_hint": str(bounds.document_type_hint),
            "quality": quality.to_dict(),
        }
    finally:
        tmp_path.unlink(missing_ok=True)


@router.get("/presets")
def list_presets():
    """Lists all available built-in and user custom presets."""
    return [p.model_dump() for p in preset_store.list_all()]


@router.get("/presets/{preset_id}")
def get_preset(preset_id: str):
    """Retrieves a single scanner preset by ID."""
    preset = preset_store.get(preset_id)
    if preset is None:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found.")
    return preset.model_dump()


@router.post("/presets")
def create_custom_preset(preset: ScannerPreset):
    """Saves a new custom user preset."""
    try:
        saved = preset_store.save_custom(preset)
        return saved.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/presets/{preset_id}")
def update_custom_preset(preset_id: str, preset: ScannerPreset):
    """Updates an existing custom preset."""
    if preset_id.lower().strip() != preset.id.lower().strip():
        raise HTTPException(status_code=400, detail="Preset ID in path does not match body.")
    try:
        saved = preset_store.save_custom(preset)
        return saved.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/presets/{preset_id}")
def delete_custom_preset(preset_id: str):
    """Deletes a custom user preset."""
    try:
        deleted = preset_store.delete_custom(preset_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Custom preset not found.")
        return {"deleted": True, "preset_id": preset_id}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/jobs")
async def create_scan_job(
    files: List[UploadFile] = File(...),
    crops: Optional[str] = Form(None),
    rotations: Optional[str] = Form(None),
    preset_id: str = Form("auto"),
    custom_settings: Optional[str] = Form(None),
    output_format: str = Form("pdf_searchable"),
):
    """Enqueues a document scanning job for one or more pages."""
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    parsed_crops = json.loads(crops) if crops else []
    parsed_rotations = json.loads(rotations) if rotations else []
    parsed_settings = json.loads(custom_settings) if custom_settings else None

    workspace = new_job_workspace()
    try:
        saved_paths = await save_uploads(files, input_dir(workspace))
        job = Job(
            kind=JobKind.SCANNER_PROCESS,
            workspace=workspace,
            payload={
                "input_paths": [str(p) for p in saved_paths],
                "crops": parsed_crops,
                "rotations": parsed_rotations,
                "preset_id": preset_id,
                "custom_settings": parsed_settings,
                "output_format": output_format,
            },
        )
        task_queue.submit(job)
        return {"job_id": job.id}
    except Exception:
        cleanup_dir(workspace)
        raise


@router.get("/jobs/{job_id}")
def get_scanner_job_status(job_id: str):
    """Checks the status and progress of a scanner job."""
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found or expired.")
    return job.to_public_dict()


@router.delete("/jobs/{job_id}")
def cancel_scanner_job(job_id: str):
    """Cancels a pending or processing scanner job."""
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


@router.get("/jobs/{job_id}/download/{file_index}")
def download_scanner_result(job_id: str, file_index: int, response: Response):
    """Downloads a produced file from a finished scanner job."""
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found or expired.")
    if file_index < 0 or file_index >= len(job.result_files):
        raise HTTPException(status_code=404, detail="Requested file index not found.")

    result = job.result_files[file_index]
    file_path = Path(result.path)
    if not file_path.exists():
        raise HTTPException(status_code=410, detail="Output file is no longer available.")

    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return FileResponse(path=file_path, filename=result.name, media_type=result.media_type)
