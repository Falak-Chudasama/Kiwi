import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class JobKind(str, Enum):
    DOCUMENT_CONVERT = "document_convert"
    IMAGE_CONVERT = "image_convert"
    PDF_MERGE = "pdf_merge"
    PDF_SPLIT = "pdf_split"
    PDF_TO_IMAGES = "pdf_to_images"
    IMAGES_TO_PDF = "images_to_pdf"
    PDF_ROTATE = "pdf_rotate"
    PDF_REORDER = "pdf_reorder"
    PDF_PROTECT = "pdf_protect"
    PDF_UNLOCK = "pdf_unlock"
    PDF_WATERMARK = "pdf_watermark"
    PDF_OCR = "pdf_ocr"
    COMPRESS_FILE = "compress_file"
    ARCHIVE_CREATE = "archive_create"
    ARCHIVE_EXTRACT = "archive_extract"


@dataclass
class ResultFile:
    path: str
    name: str
    size: int
    media_type: str = "application/octet-stream"

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "size": self.size,
            "media_type": self.media_type,
        }


@dataclass
class Job:
    kind: JobKind
    payload: dict[str, Any]
    workspace: Path
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    status: JobStatus = JobStatus.QUEUED
    progress: int = 0
    error: str | None = None
    result_files: list[ResultFile] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def touch(self) -> None:
        self.updated_at = time.time()

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind.value,
            "status": self.status.value,
            "progress": self.progress,
            "error": self.error,
            "result_files": [item.to_public_dict() for item in self.result_files],
        }
