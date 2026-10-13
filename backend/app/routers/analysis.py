"""
Multi-Hazard Climate Analysis Endpoint
Supports Heatwave (95th Pctile), Drought (SPI-3), and Heavy Rainfall (ETCCDI R95p).
"""

import logging
from typing import Optional
from fastapi import APIRouter, Query, HTTPException, status
import numpy as np
from backend.app.config import settings
from backend.app.schemas import AnalysisResponse, AnalysisSummary
from backend.app.db.repository import repository
from backend.app.services.weather_service import weather_service, WeatherServiceError
from backend.app.services.heatwave_algorithm import (
    calculate_baseline_threshold as calculate_heatwave_threshold,
    detect_heatwaves,
    compute_annual_aggregates as compute_heatwave_annual_aggs
)
from backend.app.services.drought_algorithm import (
    aggregate_daily_to_monthly,
    calculate_spi,
    detect_drought_events,
    compute_annual_drought_aggregates
)
from backend.app.services.heavy_rainfall_algorithm import (
    calculate_wet_day_threshold,
    detect_heavy_rainfall_events,
    compute_annual_heavy_rainfall_aggregates
)
from backend.app.services.trend_analysis import (
    generate_heatwave_trend_report,
    generate_drought_trend_report,
    generate_heavy_rainfall_trend_report
)

logger = logging.getLogger("climate_hazard.analysis")
router = APIRouter(tags=["Analysis"])

SUPPORTED_HAZARDS = {"heatwave", "drought", "heavy_rainfall"}


@router.get("/analysis", response_model=AnalysisResponse)
def run_climate_analysis(
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees"),
    start_year: int = Query(1990, ge=1950, le=2024, description="Analysis start year (inclusive)"),
    end_year: int = Query(2020, ge=1950, le=2024, description="Analysis end year (inclusive)"),
    hazard: str = Query("heatwave", description="Hazard type: 'heatwave' | 'drought' | 'heavy_rainfall'"),
    baseline_start: int = Query(1991, ge=1950, le=2024, description="Baseline reference start year"),
    baseline_end: int = Query(2020, ge=1950, le=2024, description="Baseline reference end year"),
    force_refresh: bool = Query(False, description="Bypass cache and force recalculation")
):
    norm_hazard = hazard.lower().strip()
    if norm_hazard not in SUPPORTED_HAZARDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported hazard '{hazard}'. Supported hazards: {', '.join(sorted(SUPPORTED_HAZARDS))}."
        )

    if start_year > end_year:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Start year ({start_year}) cannot be greater than end year ({end_year})."
        )

    if baseline_start > baseline_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Baseline start year ({baseline_start}) cannot be greater than baseline end year ({baseline_end})."
        )

    lat_r = round(latitude, 4)
    lon_r = round(longitude, 4)

    # 1. Check MongoDB Analysis Cache
    if not force_refresh:
        cached_result = repository.get_cached_analysis(
            lat_r, lon_r, start_year, end_year, baseline_start, baseline_end,
            hazard=norm_hazard, algorithm_version=settings.algorithm_version
        )
        if cached_result:
            logger.info(f"Analysis Cache HIT for ({lat_r}, {lon_r}) {norm_hazard} {start_year}-{end_year}")
            cached_result["cache_status"] = "HIT"
            return cached_result

    # 2. Ingest & Screen Historical Weather Series (Temperature & Precipitation)
    try:
        clean_df, data_quality, source_meta = weather_service.fetch_weather_series(
            latitude=lat_r,
            longitude=lon_r,
            start_year=start_year,
            end_year=end_year,
            baseline_start=baseline_start,
            baseline_end=baseline_end,
            force_refresh=force_refresh
        )
    except WeatherServiceError as err:
        logger.error(f"Weather ingestion failed: {err}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(err))
    except Exception as err:
        logger.exception("Unexpected error during weather data ingestion")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Data ingestion error: {str(err)}")

    # 3. Hazard-Specific Algorithm Execution
    if norm_hazard == "heatwave":
        try:
            threshold, _, _ = calculate_heatwave_threshold(
                clean_df, baseline_start, baseline_end, min_completeness_ratio=0.80
            )
        except ValueError as err:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(err))

        events_all = detect_heatwaves(clean_df, threshold=threshold, min_consecutive_days=3)
        analysis_events = [
            ev for ev in events_all
            if int(ev.start_date.split("-")[0]) >= start_year and int(ev.start_date.split("-")[0]) <= end_year
        ]
        annual_aggs = compute_heatwave_annual_aggs(clean_df, analysis_events, start_year, end_year)
        trend_report = generate_heatwave_trend_report(annual_aggs, analysis_events, threshold)

        total_events = len(analysis_events)
        total_days = sum(a.heatwave_days for a in annual_aggs)
        mean_dur = round(float(np.mean([ev.duration for ev in analysis_events])), 2) if total_events > 0 else None
        longest_dur = max((ev.duration for ev in analysis_events), default=None)
        hottest_temp = max((ev.peak_temperature for ev in analysis_events), default=None)

        summary = AnalysisSummary(
            total_events=total_events,
            primary_exposure_metric=total_days,
            primary_exposure_label="Heatwave Days",
            mean_event_duration=mean_dur,
            duration_unit="days",
            longest_event_duration=longest_dur,
            peak_metric_value=hottest_temp,
            peak_metric_label="Peak Temperature (°C)",
            threshold_value=threshold,
            threshold_label="P95 Baseline Threshold (°C)",
            baseline_period=f"{baseline_start}–{baseline_end}",
            analysis_period=f"{start_year}–{end_year}"
        )
        threshold_val = threshold

    elif norm_hazard == "drought":
        monthly_df = aggregate_daily_to_monthly(clean_df)
        spi_df = calculate_spi(
            monthly_df,
            accumulation_window=3,
            baseline_start=baseline_start,
            baseline_end=baseline_end
        )
        # Filter monthly spi to analysis period
        analysis_spi = spi_df[(spi_df['year'] >= start_year) & (spi_df['year'] <= end_year)].copy()
        events_all = detect_drought_events(analysis_spi, threshold=-1.0)
        annual_aggs = compute_annual_drought_aggregates(analysis_spi, events_all, start_year, end_year)
        trend_report = generate_drought_trend_report(annual_aggs, events_all, f"{baseline_start}–{baseline_end}")

        total_events = len(events_all)
        total_months = sum(a.drought_months for a in annual_aggs)
        mean_dur = round(float(np.mean([ev.duration_months for ev in events_all])), 2) if total_events > 0 else None
        longest_dur = max((ev.duration_months for ev in events_all), default=None)
        min_spi_val = min((ev.min_spi for ev in events_all), default=None)

        summary = AnalysisSummary(
            total_events=total_events,
            primary_exposure_metric=total_months,
            primary_exposure_label="Drought Months",
            mean_event_duration=mean_dur,
            duration_unit="months",
            longest_event_duration=longest_dur,
            peak_metric_value=min_spi_val,
            peak_metric_label="Lowest SPI-3 Intensity",
            threshold_value=-1.0,
            threshold_label="Drought Threshold (SPI <= -1.0)",
            baseline_period=f"{baseline_start}–{baseline_end}",
            analysis_period=f"{start_year}–{end_year}"
        )
        threshold_val = -1.0

    elif norm_hazard == "heavy_rainfall":
        try:
            threshold, _, _ = calculate_wet_day_threshold(
                clean_df, baseline_start, baseline_end, min_wet_threshold_mm=1.0, percentile=95.0
            )
        except ValueError as err:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(err))

        events_all = detect_heavy_rainfall_events(clean_df, threshold=threshold, min_wet_threshold_mm=1.0)
        analysis_events = [
            ev for ev in events_all
            if int(ev.start_date.split("-")[0]) >= start_year and int(ev.start_date.split("-")[0]) <= end_year
        ]
        annual_aggs = compute_annual_heavy_rainfall_aggregates(clean_df, analysis_events, threshold, start_year, end_year)
        trend_report = generate_heavy_rainfall_trend_report(annual_aggs, analysis_events, threshold)

        total_events = len(analysis_events)
        total_days = sum(a.heavy_rainfall_days for a in annual_aggs)
        mean_dur = round(float(np.mean([ev.duration for ev in analysis_events])), 2) if total_events > 0 else None
        longest_dur = max((ev.duration for ev in analysis_events), default=None)
        max_rain = max((ev.peak_daily_precipitation for ev in analysis_events), default=None)

        summary = AnalysisSummary(
            total_events=total_events,
            primary_exposure_metric=total_days,
            primary_exposure_label="Heavy Rain Days",
            mean_event_duration=mean_dur,
            duration_unit="days",
            longest_event_duration=longest_dur,
            peak_metric_value=max_rain,
            peak_metric_label="Max 1-Day Rain (mm)",
            threshold_value=threshold,
            threshold_label="R95p Wet-Day Threshold (mm/day)",
            baseline_period=f"{baseline_start}–{baseline_end}",
            analysis_period=f"{start_year}–{end_year}"
        )
        threshold_val = threshold

    result = {
        "region_info": {
            "latitude": lat_r,
            "longitude": lon_r,
            "display_name": f"{lat_r}°N/S, {lon_r}°E/W"
        },
        "coordinates": {"latitude": lat_r, "longitude": lon_r},
        "requested_period": {"start_year": start_year, "end_year": end_year},
        "baseline_period": {"baseline_start": baseline_start, "baseline_end": baseline_end},
        "hazard": norm_hazard,
        "algorithm_version": settings.algorithm_version,
        "threshold": threshold_val,
        "summary": summary.model_dump(),
        "trend_report": trend_report.to_dict(),
        "annual_aggregates": [a.to_dict() for a in annual_aggs],
        "events": [e.to_dict() for e in (events_all if norm_hazard == "drought" else analysis_events)],
        "data_quality": data_quality,
        "source_metadata": source_meta,
        "cache_status": "MISS"
    }

    # 4. Save to MongoDB cache
    repository.save_analysis(result)

    return result
