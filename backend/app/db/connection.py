"""
MongoDB Database Connection and Index Management
"""

import logging
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from backend.app.config import settings

logger = logging.getLogger("climate_hazard.db")

_client: Optional[MongoClient] = None
_db: Optional[Database] = None


def get_mongo_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=2500,
            connectTimeoutMS=2500
        )
    return _client


def get_database() -> Database:
    global _db
    if _db is None:
        client = get_mongo_client()
        # Extract db name if specified in URI, otherwise default to settings.db_name
        try:
            default_db = client.get_default_database()
            _db = default_db if default_db is not None else client[settings.db_name]
        except Exception:
            _db = client[settings.db_name]
    return _db


def init_indexes() -> bool:
    """
    Initializes unique indexes for weather_daily and analysis_results collections.
    Returns True if successful, False if MongoDB is unavailable.
    """
    try:
        db = get_database()
        # Verify connection
        db.command("ping")

        # 1. weather_daily collection unique observation key
        db["weather_daily"].create_index(
            [("latitude", 1), ("longitude", 1), ("date", 1)],
            unique=True,
            name="uniq_lat_lon_date"
        )

        # 2. analysis_results collection unique cache key
        db["analysis_results"].create_index(
            [
                ("latitude", 1),
                ("longitude", 1),
                ("start_year", 1),
                ("end_year", 1),
                ("baseline_start", 1),
                ("baseline_end", 1),
                ("hazard", 1),
                ("algorithm_version", 1)
            ],
            unique=True,
            name="uniq_analysis_cache_key"
        )
        logger.info("MongoDB indexes successfully verified and initialized.")
        return True
    except Exception as exc:
        logger.warning(f"Could not initialize MongoDB indexes: {exc}")
        return False


def is_database_connected() -> bool:
    try:
        client = get_mongo_client()
        client.admin.command("ping")
        return True
    except Exception:
        return False
