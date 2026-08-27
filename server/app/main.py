from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.files import cleanup_stale_workspaces
from app.routes import archives, compression, documents, images, jobs, pdf
from app.workers.handlers import register_all_handlers
from app.workers.queue import task_queue

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(images.router)
app.include_router(pdf.router)
app.include_router(compression.router)
app.include_router(archives.router)
app.include_router(jobs.router)


@app.on_event("startup")
def on_startup() -> None:
    cleanup_stale_workspaces(settings.job_ttl_seconds)
    register_all_handlers()
    task_queue.start()


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": settings.app_name}
