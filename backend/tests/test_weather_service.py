"""
Unit Tests for Open-Meteo Weather Service
=========================================
Tests coordinate validation, temperature and precipitation quality screening,
and network timeout/error handling using mocks.
"""

import pytest
import httpx
from unittest.mock import MagicMock
from backend.app.services.weather_service import (
    OpenMeteoWeatherService,
    WeatherServiceError,
    MIN_PLAUSIBLE_TEMP_C,
    MAX_PLAUSIBLE_TEMP_C
)


def test_invalid_coordinates_raise_error():
    service = OpenMeteoWeatherService()
    with pytest.raises(WeatherServiceError, match="Invalid latitude"):
        service.validate_coordinates(95.0, 0.0)
    with pytest.raises(WeatherServiceError, match="Invalid longitude"):
        service.validate_coordinates(0.0, 200.0)


def test_invalid_date_range_raise_error():
    service = OpenMeteoWeatherService()
    with pytest.raises(WeatherServiceError, match="is after end date"):
        service.validate_date_range("2020-01-01", "2010-01-01")


def test_impossible_temperature_and_precipitation_screening():
    service = OpenMeteoWeatherService()
    dates = ["2000-01-01", "2000-01-02", "2000-01-03", "2000-01-04"]
    temps = [25.0, 75.0, -100.0, None]
    precips = [10.0, -5.0, 1500.0, None] # negative and >1000mm rejected

    clean_df, quality_metrics = service._clean_and_validate_data(
        dates, temps, precips, "2000-01-01", "2000-01-04", 2000, 2000
    )

    assert quality_metrics["invalid_temperatures_rejected"] == 2
    assert quality_metrics["invalid_precipitation_rejected"] == 2
    assert quality_metrics["valid_observations"] == 1
    assert clean_df["temperature_2m_max"].isna().sum() == 3
    assert clean_df["precipitation_sum"].isna().sum() == 3


def test_mocked_open_meteo_success_response():
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "latitude": 48.85,
        "longitude": 2.35,
        "elevation": 35.0,
        "timezone": "UTC",
        "daily": {
            "time": ["2000-07-01", "2000-07-02", "2000-07-03"],
            "temperature_2m_max": [31.5, 33.2, 32.1],
            "precipitation_sum": [0.0, 15.2, 2.4]
        }
    }

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.__enter__.return_value = mock_client
    mock_client.get.return_value = mock_resp

    service = OpenMeteoWeatherService(client=mock_client)
    dates, temps, precips, meta = service._call_open_meteo(48.85, 2.35, "2000-07-01", "2000-07-03")

    assert len(dates) == 3
    assert temps == [31.5, 33.2, 32.1]
    assert precips == [0.0, 15.2, 2.4]
    assert meta["latitude"] == 48.85


def test_mocked_open_meteo_timeout_error():
    mock_client = MagicMock(spec=httpx.Client)
    mock_client.__enter__.return_value = mock_client
    mock_client.get.side_effect = httpx.TimeoutException("Connection timed out")

    service = OpenMeteoWeatherService(client=mock_client)
    with pytest.raises(WeatherServiceError, match="timed out"):
        service._call_open_meteo(48.85, 2.35, "2000-07-01", "2000-07-03")
