"""
Health Check Router
"""

from datetime import datetime, timezone
from fastapi import APIRouter
from backend.app.schemas import HealthCheckResponse
from backend.app.db.connection import is_database_connected
from backend.app.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthCheckResponse)
def get_health():
    db_ok = is_database_connected()
    return HealthCheckResponse(
        status="healthy" if db_ok else "degraded",
        database_connected=db_ok,
        database_uri_configured=settings.mongodb_uri.split("@")[-1],  # mask any credentials if present
        version=settings.algorithm_version,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
