"""
Repository Layer for Weather Observations and Analysis Caching
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from pymongo.errors import PyMongoError, DuplicateKeyError
from backend.app.db.connection import get_database, is_database_connected

logger = logging.getLogger("climate_hazard.repository")


class RepositoryError(Exception):
    pass


class ClimateRepository:
    def __init__(self):
        pass

    def get_cached_analysis(
        self,
        latitude: float,
        longitude: float,
        start_year: int,
        end_year: int,
        baseline_start: int,
        baseline_end: int,
        hazard: str,
        algorithm_version: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves cached analysis result if present.
        """
        if not is_database_connected():
            return None

        try:
            db = get_database()
            query = {
                "latitude": round(latitude, 4),
                "longitude": round(longitude, 4),
                "start_year": start_year,
                "end_year": end_year,
                "baseline_start": baseline_start,
                "baseline_end": baseline_end,
                "hazard": hazard,
                "algorithm_version": algorithm_version
            }
            doc = db["analysis_results"].find_one(query)
            if doc:
                doc.pop("_id", None)
                return doc
            return None
        except PyMongoError as err:
            logger.warning(f"Error querying analysis cache: {err}")
            return None

    def save_analysis(
        self,
        analysis_data: Dict[str, Any]
    ) -> bool:
        """
        Stores analysis result with full cache key and calculated_at timestamp.
        """
        if not is_database_connected():
            return False

        try:
            db = get_database()
            doc = dict(analysis_data)
            # Ensure coordinates are rounded
            doc["latitude"] = round(doc["coordinates"]["latitude"], 4)
            doc["longitude"] = round(doc["coordinates"]["longitude"], 4)
            doc["start_year"] = doc["requested_period"]["start_year"]
            doc["end_year"] = doc["requested_period"]["end_year"]
            doc["baseline_start"] = doc["baseline_period"]["baseline_start"]
            doc["baseline_end"] = doc["baseline_period"]["baseline_end"]
            doc["calculated_at"] = datetime.now(timezone.utc).isoformat()

            query = {
                "latitude": doc["latitude"],
                "longitude": doc["longitude"],
                "start_year": doc["start_year"],
                "end_year": doc["end_year"],
                "baseline_start": doc["baseline_start"],
                "baseline_end": doc["baseline_end"],
                "hazard": doc["hazard"],
                "algorithm_version": doc["algorithm_version"]
            }

            db["analysis_results"].replace_one(query, doc, upsert=True)
            return True
        except PyMongoError as err:
            logger.warning(f"Error saving analysis to cache: {err}")
            return False

    def invalidate_analysis_cache(
        self,
        latitude: float,
        longitude: float,
        start_year: int,
        end_year: int,
        baseline_start: int,
        baseline_end: int,
        hazard: str,
        algorithm_version: str
    ) -> int:
        """
        Invalidates cached analysis for given parameters.
        """
        if not is_database_connected():
            return 0

        try:
            db = get_database()
            query = {
                "latitude": round(latitude, 4),
                "longitude": round(longitude, 4),
                "start_year": start_year,
                "end_year": end_year,
                "baseline_start": baseline_start,
                "baseline_end": baseline_end,
                "hazard": hazard,
                "algorithm_version": algorithm_version
            }
            res = db["analysis_results"].delete_many(query)
            return res.deleted_count
        except PyMongoError as err:
            logger.warning(f"Error deleting cached analysis: {err}")
            return 0

    def get_daily_weather_records(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """
        Fetches cached daily weather records for coordinate and date range.
        """
        if not is_database_connected():
            return []

        try:
            db = get_database()
            query = {
                "latitude": round(latitude, 4),
                "longitude": round(longitude, 4),
                "date": {"$gte": start_date, "$lte": end_date}
            }
            cursor = db["weather_daily"].find(query).sort("date", 1)
            records = []
            for doc in cursor:
                doc.pop("_id", None)
                records.append(doc)
            return records
        except PyMongoError as err:
            logger.warning(f"Error fetching daily weather records: {err}")
            return []

    def save_daily_weather_records(
        self,
        latitude: float,
        longitude: float,
        records: List[Dict[str, Any]]
    ) -> int:
        """
        Upserts daily weather observations.
        """
        if not is_database_connected() or not records:
            return 0

        try:
            from pymongo import UpdateOne
            db = get_database()
            ops = []
            now_iso = datetime.now(timezone.utc).isoformat()
            lat_r = round(latitude, 4)
            lon_r = round(longitude, 4)

            for rec in records:
                filter_q = {
                    "latitude": lat_r,
                    "longitude": lon_r,
                    "date": rec["date"]
                }
                update_doc = {
                    "$set": {
                        "latitude": lat_r,
                        "longitude": lon_r,
                        "date": rec["date"],
                        "temperature_2m_max": rec.get("temperature_2m_max"),
                        "precipitation_sum": rec.get("precipitation_sum"),
                        "source": "open-meteo-archive",
                        "retrieved_at": now_iso
                    }
                }
                ops.append(UpdateOne(filter_q, update_doc, upsert=True))

            if ops:
                res = db["weather_daily"].bulk_write(ops, ordered=False)
                return res.upserted_count + res.modified_count
            return 0
        except PyMongoError as err:
            logger.warning(f"Error saving daily records: {err}")
            return 0


repository = ClimateRepository()
