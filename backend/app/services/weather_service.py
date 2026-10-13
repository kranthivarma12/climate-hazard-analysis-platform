"""
Open-Meteo Historical Weather Ingestion and Quality Control Service
"""

import logging
from datetime import datetime, date, timezone
from typing import Dict, Any, List, Tuple, Optional
import httpx
import numpy as np
import pandas as pd
from backend.app.config import settings
from backend.app.db.repository import repository

logger = logging.getLogger("climate_hazard.weather")

# Physical temperature sanity bounds on Earth (Celsius)
MIN_PLAUSIBLE_TEMP_C = -90.0
MAX_PLAUSIBLE_TEMP_C = 65.0


class WeatherServiceError(Exception):
    pass


class OpenMeteoWeatherService:
    def __init__(self, client: Optional[httpx.Client] = None):
        self._client = client

    def get_client(self) -> httpx.Client:
        if self._client:
            return self._client
        return httpx.Client(timeout=settings.request_timeout_seconds)

    def validate_coordinates(self, latitude: float, longitude: float):
        if not (-90.0 <= latitude <= 90.0):
            raise WeatherServiceError(f"Invalid latitude: {latitude}. Must be between -90.0 and 90.0.")
        if not (-180.0 <= longitude <= 180.0):
            raise WeatherServiceError(f"Invalid longitude: {longitude}. Must be between -180.0 and 180.0.")

    def validate_date_range(self, start_date: str, end_date: str):
        try:
            s = datetime.strptime(start_date, "%Y-%m-%d").date()
            e = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError as e:
            raise WeatherServiceError(f"Invalid date format: {e}. Expected YYYY-MM-DD.")
        if s > e:
            raise WeatherServiceError(f"Start date {start_date} is after end date {end_date}.")
        if s.year < 1940:
            raise WeatherServiceError(f"Historical weather archive only supports years 1940 and newer.")
        today = date.today()
        if e > today:
            raise WeatherServiceError(f"End date {end_date} cannot be in the future.")

    def fetch_weather_series(
        self,
        latitude: float,
        longitude: float,
        start_year: int,
        end_year: int,
        baseline_start: int,
        baseline_end: int,
        force_refresh: bool = False
    ) -> Tuple[pd.DataFrame, Dict[str, Any], Dict[str, Any]]:
        """
        Retrieves complete daily temperature and precipitation dataset spanning both analysis
        and baseline years, utilizing cached daily observations where present.
        
        Returns:
            (clean_df, data_quality_metrics, source_metadata)
        """
        self.validate_coordinates(latitude, longitude)

        # Spanning date boundaries
        min_year = min(start_year, baseline_start)
        max_year = max(end_year, baseline_end)
        start_date = f"{min_year}-01-01"
        end_date = f"{max_year}-12-31"
        self.validate_date_range(start_date, end_date)

        lat_r = round(latitude, 4)
        lon_r = round(longitude, 4)

        # Check existing cached records
        cached_records = []
        if not force_refresh:
            cached_records = repository.get_daily_weather_records(lat_r, lon_r, start_date, end_date)

        expected_days = (datetime.strptime(end_date, "%Y-%m-%d").date() - datetime.strptime(start_date, "%Y-%m-%d").date()).days + 1

        # If cache has >= 95% of expected days with both temperature and precipitation present
        cache_valid_count = sum(1 for r in cached_records if "temperature_2m_max" in r and "precipitation_sum" in r)
        if cache_valid_count >= expected_days * 0.95 and not force_refresh:
            logger.info(f"Using {len(cached_records)} cached daily weather observations for ({lat_r}, {lon_r})")
            raw_dates = [r["date"] for r in cached_records]
            raw_temps = [r.get("temperature_2m_max") for r in cached_records]
            raw_precips = [r.get("precipitation_sum") for r in cached_records]
            source_meta = {
                "source": "MongoDB weather_daily cache",
                "archive_endpoint": settings.open_meteo_archive_url,
                "cached_records_count": len(cached_records),
                "cache_hit": True
            }
        else:
            logger.info(f"Fetching weather archive from Open-Meteo for ({lat_r}, {lon_r}) {start_date} to {end_date}")
            raw_dates, raw_temps, raw_precips, source_meta = self._call_open_meteo(lat_r, lon_r, start_date, end_date)
            # Store in cache
            new_records = [
                {"date": d, "temperature_2m_max": t, "precipitation_sum": p}
                for d, t, p in zip(raw_dates, raw_temps, raw_precips)
            ]
            repository.save_daily_weather_records(lat_r, lon_r, new_records)

        # Quality control and DataFrame construction
        clean_df, quality_metrics = self._clean_and_validate_data(
            raw_dates, raw_temps, raw_precips, start_date, end_date, baseline_start, baseline_end
        )

        return clean_df, quality_metrics, source_meta

    def _call_open_meteo(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str
    ) -> Tuple[List[str], List[Optional[float]], List[Optional[float]], Dict[str, Any]]:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "daily": ["temperature_2m_max", "precipitation_sum"],
            "timezone": "UTC"
        }

        try:
            with self.get_client() as client:
                resp = client.get(settings.open_meteo_archive_url, params=params)
        except httpx.TimeoutException:
            raise WeatherServiceError("Open-Meteo API request timed out after 30 seconds.")
        except httpx.RequestError as e:
            raise WeatherServiceError(f"Network error communicating with Open-Meteo API: {str(e)}")

        if resp.status_code != 200:
            error_reason = resp.text[:300]
            raise WeatherServiceError(
                f"Open-Meteo API returned error status {resp.status_code}: {error_reason}"
            )

        try:
            data = resp.json()
        except Exception:
            raise WeatherServiceError("Open-Meteo returned invalid JSON response.")

        if "daily" not in data or "time" not in data["daily"] or "temperature_2m_max" not in data["daily"]:
            raise WeatherServiceError("Open-Meteo response is missing required daily time-series fields.")

        dates = data["daily"]["time"]
        temps = data["daily"]["temperature_2m_max"]
        precips = data["daily"].get("precipitation_sum", [None] * len(dates))

        meta = {
            "source": "Open-Meteo Historical Weather API (ERA5 Reanalysis / Archive)",
            "archive_endpoint": settings.open_meteo_archive_url,
            "elevation": data.get("elevation"),
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "timezone": data.get("timezone"),
            "retrieval_timestamp": datetime.now(timezone.utc).isoformat(),
            "cache_hit": False
        }

        return dates, temps, precips, meta

    def _clean_and_validate_data(
        self,
        dates: List[str],
        temps: List[Optional[float]],
        precips: List[Optional[float]],
        start_date: str,
        end_date: str,
        baseline_start: int,
        baseline_end: int
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        raw_df = pd.DataFrame({
            "date": dates,
            "temperature_2m_max": temps,
            "precipitation_sum": precips
        })
        raw_df['date'] = pd.to_datetime(raw_df['date'])

        # Deduplicate dates
        raw_df = raw_df.sort_values('date').drop_duplicates(subset=['date'])

        # Enforce continuous index
        s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        e_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        expected_days = (e_date - s_date).days + 1
        full_idx = pd.date_range(start=s_date, end=e_date, freq='D')
        df = raw_df.set_index('date').reindex(full_idx)
        df.index.name = 'date'
        df = df.reset_index()

        # Conservative quality rules
        invalid_temps_rejected = 0
        cleaned_temps = []
        for val in df['temperature_2m_max']:
            if pd.isna(val):
                cleaned_temps.append(np.nan)
            else:
                f_val = float(val)
                if f_val < MIN_PLAUSIBLE_TEMP_C or f_val > MAX_PLAUSIBLE_TEMP_C:
                    cleaned_temps.append(np.nan)
                    invalid_temps_rejected += 1
                else:
                    cleaned_temps.append(f_val)

        invalid_precip_rejected = 0
        cleaned_precips = []
        for val in df['precipitation_sum']:
            if pd.isna(val):
                cleaned_precips.append(np.nan)
            else:
                f_val = float(val)
                # Physical bounds: precipitation must be >= 0 and <= 1000 mm/day
                if f_val < 0.0 or f_val > 1000.0:
                    cleaned_precips.append(np.nan)
                    invalid_precip_rejected += 1
                else:
                    cleaned_precips.append(f_val)

        df['temperature_2m_max'] = cleaned_temps
        df['precipitation_sum'] = cleaned_precips

        # Quality metrics
        valid_count = int(df['temperature_2m_max'].dropna().count())
        valid_precip_count = int(df['precipitation_sum'].dropna().count())
        missing_count = expected_days - valid_count
        completeness = round((valid_count / expected_days) * 100.0, 2) if expected_days > 0 else 0.0

        # Baseline completeness
        baseline_mask = (df['date'].dt.year >= baseline_start) & (df['date'].dt.year <= baseline_end)
        b_df = df.loc[baseline_mask]
        b_expected = (date(baseline_end, 12, 31) - date(baseline_start, 1, 1)).days + 1
        b_valid = int(b_df['temperature_2m_max'].dropna().count())
        b_completeness = round((b_valid / b_expected) * 100.0, 2) if b_expected > 0 else 0.0

        quality_metrics = {
            "total_expected_days": expected_days,
            "valid_observations": valid_count,
            "valid_precipitation_observations": valid_precip_count,
            "missing_days": missing_count,
            "completeness_percentage": completeness,
            "baseline_valid_days": b_valid,
            "baseline_completeness_percentage": b_completeness,
            "invalid_temperatures_rejected": invalid_temps_rejected,
            "invalid_precipitation_rejected": invalid_precip_rejected
        }

        df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        return df, quality_metrics


weather_service = OpenMeteoWeatherService()
