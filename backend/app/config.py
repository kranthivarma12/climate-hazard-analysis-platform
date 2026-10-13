"""
Application Configuration
"""

import os
from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Climate Hazard Analysis Platform"
    api_v1_prefix: str = "/api/v1"
    mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017/climate_hazard")
    db_name: str = "climate_hazard"
    backend_port: int = int(os.getenv("BACKEND_PORT", "8001"))
    backend_host: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    open_meteo_archive_url: str = "https://archive-api.open-meteo.com/v1/archive"
    request_timeout_seconds: float = 30.0
    algorithm_version: str = "1.0.0"
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "*"
    ]


settings = Settings()
