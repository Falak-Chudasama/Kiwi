import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Kiwi"
    max_upload_mb: int = 512
    max_request_mb: int = 1024
    max_file_count: int = 100
    max_archive_entries: int = 10000
    max_archive_uncompressed_mb: int = 2048
    max_queue_size: int = 100
    max_queue_wait_seconds: int = 300
    max_job_duration_seconds: int = 600
    job_ttl_seconds: int = 300
    cleanup_interval_seconds: int = 15
    worker_count: int = 2
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ]
    soffice_bin: str = "soffice"
    tesseract_bin: str = "tesseract"
    ghostscript_bin: str = "gswin64c"
    ffmpeg_bin: str = "ffmpeg"
    pandoc_bin: str = "pandoc"

    class Config:
        env_file = ".env"
        env_prefix = "KIWI_"


settings = Settings()
