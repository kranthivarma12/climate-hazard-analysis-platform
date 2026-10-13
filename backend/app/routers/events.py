"""
Events and Cache Management Router
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query, HTTPException, status
from backend.app.schemas import CacheRefreshRequest
from backend.app.routers.analysis import run_climate_analysis
from backend.app.db.repository import repository
from backend.app.config import settings

router = APIRouter(tags=["Events & Cache"])


@router.get("/events", response_model=List[Dict[str, Any]])
def get_hazard_events(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    start_year: int = Query(1990, ge=1950, le=2024),
    end_year: int = Query(2020, ge=1950, le=2024),
    hazard: str = Query("heatwave"),
    baseline_start: int = Query(1991, ge=1950, le=2024),
    baseline_end: int = Query(2020, ge=1950, le=2024),
    min_duration: Optional[int] = Query(None, ge=1, description="Minimum duration filter")
):
    analysis = run_climate_analysis(
        latitude=latitude,
        longitude=longitude,
        start_year=start_year,
        end_year=end_year,
        hazard=hazard,
        baseline_start=baseline_start,
        baseline_end=baseline_end,
        force_refresh=False
    )
    events = analysis["events"]
    if min_duration is not None:
        events = [
            e for e in events
            if e.get("duration", e.get("duration_months", 0)) >= min_duration
        ]
    return events


@router.post("/cache/refresh")
def refresh_cache(req: CacheRefreshRequest):
    """
    Invalidates cached analysis results and re-runs the computation pipeline.
    """
    deleted_count = repository.invalidate_analysis_cache(
        latitude=req.latitude,
        longitude=req.longitude,
        start_year=req.start_year,
        end_year=req.end_year,
        baseline_start=req.baseline_start,
        baseline_end=req.baseline_end,
        hazard=req.hazard.lower(),
        algorithm_version=settings.algorithm_version
    )

    fresh_analysis = run_climate_analysis(
        latitude=req.latitude,
        longitude=req.longitude,
        start_year=req.start_year,
        end_year=req.end_year,
        hazard=req.hazard,
        baseline_start=req.baseline_start,
        baseline_end=req.baseline_end,
        force_refresh=True
    )

    return {
        "status": "cache_refreshed",
        "invalidated_entries": deleted_count,
        "new_calculated_at": fresh_analysis["source_metadata"].get("retrieval_timestamp")
    }
