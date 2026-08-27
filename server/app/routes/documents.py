from fastapi import APIRouter, File, Form, UploadFile

from app.core.formats import extension_of, valid_document_targets
from app.core.uploads import save_uploads
from app.models.job import Job, JobKind
from app.workers.queue import task_queue

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("/targets")
def get_targets(filename: str):
    source_ext = extension_of(filename)
    return {"source_ext": source_ext, "targets": valid_document_targets(source_ext)}


@router.post("/convert")
async def convert(file: UploadFile = File(...), target_ext: str = Form(...)):
    saved = await save_uploads([file])
    job = Job(
        kind=JobKind.DOCUMENT_CONVERT,
        payload={"input_paths": [str(p) for p in saved], "target_ext": target_ext},
    )
    task_queue.submit(job)
    return {"job_id": job.id}
