from fastapi import APIRouter

from app.core.formats import engine_status

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/status")
def get_status():
    engines = engine_status()
    return {
        "engines": engines,
        "missing_count": sum(1 for e in engines if not e["installed"]),
    }
