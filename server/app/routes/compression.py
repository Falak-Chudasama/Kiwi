from fastapi import APIRouter, File, Form, UploadFile

from app.core.uploads import save_uploads
from app.models.job import Job, JobKind
from app.workers.queue import task_queue

router = APIRouter(prefix="/api/compress", tags=["compression"])


@router.post("")
async def compress(file: UploadFile = File(...), level: str = Form(...)):
    saved = await save_uploads([file])
    job = Job(
        kind=JobKind.COMPRESS_FILE,
        payload={"input_paths": [str(p) for p in saved], "level": level},
    )
    task_queue.submit(job)
    return {"job_id": job.id}
