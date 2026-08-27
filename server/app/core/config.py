from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Kiwi"
    max_upload_mb: int = 4096
    job_ttl_seconds: int = 300
    cleanup_interval_seconds: int = 30
    worker_count: int = 2
    cors_origins: list[str] = ["*"]
    soffice_bin: str = "soffice"
    tesseract_bin: str = "tesseract"
    ghostscript_bin: str = "gswin64c"
    ffmpeg_bin: str = "ffmpeg"

    class Config:
        env_file = ".env"
        env_prefix = "KIWI_"


settings = Settings()
