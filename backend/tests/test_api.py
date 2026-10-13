"""
Integration Tests for FastAPI Endpoints Across All Hazards
============================================================
Tests API routes, multi-hazard routing (heatwave, drought, heavy_rainfall),
data validation, caching, and health endpoint.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import pandas as pd
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database_connected" in data
    assert "supported_hazards" in data
    assert "drought" in data["supported_hazards"]
    assert "heavy_rainfall" in data["supported_hazards"]


def test_regions_endpoint():
    response = client.get("/api/v1/regions")
    assert response.status_code == 200
    regions = response.json()
    assert len(regions) >= 5
    assert any(r["name"] == "Phoenix" for r in regions)
    assert any(r["name"] == "Paris" for r in regions)


def test_regions_search_endpoint():
    response = client.get("/api/v1/regions/search", params={"q": "Madrid"})
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1
    assert any("Madrid" in r["name"] for r in results)


def test_analysis_invalid_hazard():
    response = client.get("/api/v1/analysis", params={
        "latitude": 33.44,
        "longitude": -112.07,
        "hazard": "unknown_hazard"
    })
    assert response.status_code == 400
    assert "Unsupported hazard" in response.json()["detail"]


def test_analysis_invalid_year_range():
    response = client.get("/api/v1/analysis", params={
        "latitude": 33.44,
        "longitude": -112.07,
        "start_year": 2020,
        "end_year": 1990
    })
    assert response.status_code == 400


@patch("backend.app.services.weather_service.weather_service.fetch_weather_series")
def test_analysis_heatwave_hazard(mock_fetch):
    dates = pd.date_range("1990-01-01", "2020-12-31", freq="D")
    temps = [20.0] * len(dates)
    precips = [5.0] * len(dates)
    df = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "temperature_2m_max": temps,
        "precipitation_sum": precips
    })
    # Add heatwave in July 2000
    df.loc[(df["date"] >= "2000-07-10") & (df["date"] <= "2000-07-14"), "temperature_2m_max"] = 42.0

    mock_quality = {
        "total_expected_days": len(dates),
        "valid_observations": len(dates),
        "missing_days": 0,
        "completeness_percentage": 100.0,
        "baseline_valid_days": 10958,
        "baseline_completeness_percentage": 100.0,
        "invalid_temperatures_rejected": 0,
        "invalid_precipitation_rejected": 0
    }
    mock_meta = {"source": "Mock Test", "archive_endpoint": "https://test.local", "cache_hit": False}
    mock_fetch.return_value = (df, mock_quality, mock_meta)

    resp = client.get("/api/v1/analysis", params={
        "latitude": 48.85, "longitude": 2.35, "hazard": "heatwave", "force_refresh": True
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["hazard"] == "heatwave"
    assert data["summary"]["primary_exposure_label"] == "Heatwave Days"
    assert len(data["events"]) >= 1


@patch("backend.app.services.weather_service.weather_service.fetch_weather_series")
def test_analysis_heavy_rainfall_hazard(mock_fetch):
    dates = pd.date_range("1990-01-01", "2020-12-31", freq="D")
    temps = [20.0] * len(dates)
    precips = [5.0] * len(dates)
    df = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "temperature_2m_max": temps,
        "precipitation_sum": precips
    })
    # Add extreme rain storm in Oct 2005 (85mm)
    df.loc[df["date"] == "2005-10-15", "precipitation_sum"] = 85.0

    mock_quality = {
        "total_expected_days": len(dates),
        "valid_observations": len(dates),
        "missing_days": 0,
        "completeness_percentage": 100.0,
        "baseline_valid_days": 10958,
        "baseline_completeness_percentage": 100.0,
        "invalid_temperatures_rejected": 0,
        "invalid_precipitation_rejected": 0
    }
    mock_meta = {"source": "Mock Test", "archive_endpoint": "https://test.local", "cache_hit": False}
    mock_fetch.return_value = (df, mock_quality, mock_meta)

    resp = client.get("/api/v1/analysis", params={
        "latitude": 48.85, "longitude": 2.35, "hazard": "heavy_rainfall", "force_refresh": True
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["hazard"] == "heavy_rainfall"
    assert data["summary"]["primary_exposure_label"] == "Heavy Rain Days"
    assert data["summary"]["peak_metric_value"] >= 85.0


@patch("backend.app.services.weather_service.weather_service.fetch_weather_series")
def test_analysis_drought_hazard(mock_fetch):
    dates = pd.date_range("1990-01-01", "2020-12-31", freq="D")
    temps = [20.0] * len(dates)
    # Most days 3mm
    precips = [3.0] * len(dates)
    df = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "temperature_2m_max": temps,
        "precipitation_sum": precips
    })
    # Complete drought in 2012
    df.loc[df["date"].str.startswith("2012"), "precipitation_sum"] = 0.0

    mock_quality = {
        "total_expected_days": len(dates),
        "valid_observations": len(dates),
        "missing_days": 0,
        "completeness_percentage": 100.0,
        "baseline_valid_days": 10958,
        "baseline_completeness_percentage": 100.0,
        "invalid_temperatures_rejected": 0,
        "invalid_precipitation_rejected": 0
    }
    mock_meta = {"source": "Mock Test", "archive_endpoint": "https://test.local", "cache_hit": False}
    mock_fetch.return_value = (df, mock_quality, mock_meta)

    resp = client.get("/api/v1/analysis", params={
        "latitude": 48.85, "longitude": 2.35, "hazard": "drought", "force_refresh": True
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["hazard"] == "drought"
    assert data["summary"]["primary_exposure_label"] == "Drought Months"
    assert data["summary"]["duration_unit"] == "months"
