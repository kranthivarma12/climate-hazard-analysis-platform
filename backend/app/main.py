"""
FastAPI Application Entry Point
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.app.config import settings
from backend.app.db.connection import init_indexes
from backend.app.routers import health, regions, analysis, events

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("climate_hazard")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Climate Hazard Analysis Platform backend...")
    init_indexes()
    yield
    logger.info("Shutting down Climate Hazard Analysis Platform backend...")


app = FastAPI(
    title=settings.app_name,
    version=settings.algorithm_version,
    description="Scientific Climate Hazard Analysis API for Historical Heatwave Detection and Baseline Modeling",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(health.router, prefix=settings.api_v1_prefix)
app.include_router(regions.router, prefix=settings.api_v1_prefix)
app.include_router(analysis.router, prefix=settings.api_v1_prefix)
app.include_router(events.router, prefix=settings.api_v1_prefix)


@app.get("/")
def root():
    return {
        "service": settings.app_name,
        "version": settings.algorithm_version,
        "docs_url": "/docs",
        "health_check": f"{settings.api_v1_prefix}/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.backend_host, port=settings.backend_port, reload=True)
