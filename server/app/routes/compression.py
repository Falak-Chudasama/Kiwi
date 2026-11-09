from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.files import cleanup_dir, input_dir, new_job_workspace
from app.core.formats import COMPRESSIBLE_EXTENSIONS, extension_of
from app.core.uploads import save_uploads
from app.models.job import Job, JobKind
from app.services.compression import CompressionLevel
from app.workers.queue import task_queue

router = APIRouter(prefix="/api/compress", tags=["compression"])


@router.post("")
async def compress(file: UploadFile = File(...), level: str = Form(...)):
    # Validate parameters BEFORE creating workspace
    try:
        parsed_level = CompressionLevel(level.lower().strip())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid compression level '{level}'. Choose from: low, medium, high, extreme.",
        )

    source_ext = extension_of(file.filename or "")
    if source_ext not in COMPRESSIBLE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Compression is not supported for .{source_ext} files. Supported: {', '.join(sorted(COMPRESSIBLE_EXTENSIONS))}.",
        )

    workspace = new_job_workspace()
    try:
        saved = await save_uploads([file], input_dir(workspace))
        job = Job(
            kind=JobKind.COMPRESS_FILE,
            workspace=workspace,
            payload={"input_paths": [str(p) for p in saved], "level": parsed_level.value},
        )
        task_queue.submit(job)
        return {"job_id": job.id}
    except Exception:
        cleanup_dir(workspace)
        raise
