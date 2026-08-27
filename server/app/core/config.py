from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    app_name: str = "Kiwi"
    storage_dir: Path = BASE_DIR / "storage"
    uploads_dir: Path = BASE_DIR / "storage" / "uploads"
    outputs_dir: Path = BASE_DIR / "storage" / "outputs"
    max_upload_mb: int = 4096
    job_ttl_seconds: int = 3600
    worker_count: int = 2
    cors_origins: list[str] = ["*"]
    soffice_bin: str = "soffice"
    tesseract_bin: str = "tesseract"
    ffmpeg_bin: str = "ffmpeg"

    class Config:
        env_file = ".env"
        env_prefix = "KIWI_"


settings = Settings()
settings.uploads_dir.mkdir(parents=True, exist_ok=True)
settings.outputs_dir.mkdir(parents=True, exist_ok=True)
