"""
Unit Tests for Heavy Rainfall Algorithm (ETCCDI R95p)
=====================================================
Tests wet-day percentile calculation (R95p), heavy rainfall episode detection,
consecutive event grouping, and annual aggregates.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import date, timedelta
from backend.app.services.heavy_rainfall_algorithm import (
    calculate_wet_day_threshold,
    detect_heavy_rainfall_events,
    compute_annual_heavy_rainfall_aggregates,
    HeavyRainfallEvent
)


def test_wet_day_threshold_calculation():
    # 100 wet days with precipitation from 1.0 to 100.0 mm
    dates = [date(1991, 1, 1) + timedelta(days=i) for i in range(100)]
    precips = [float(i + 1) for i in range(100)]
    df = pd.DataFrame({"date": [d.isoformat() for d in dates], "precipitation_sum": precips})

    threshold, wet_count, total_v = calculate_wet_day_threshold(
        df, baseline_start=1991, baseline_end=1991, min_wet_threshold_mm=1.0, percentile=95.0, min_wet_days=50
    )
    expected_threshold = round(float(np.percentile(range(1, 101), 95.0)), 2)
    assert threshold == expected_threshold
    assert wet_count == 100


def test_insufficient_wet_days_raises_error():
    dates = [date(1991, 1, 1) + timedelta(days=i) for i in range(20)]
    precips = [5.0] * 20
    df = pd.DataFrame({"date": [d.isoformat() for d in dates], "precipitation_sum": precips})

    with pytest.raises(ValueError, match="Insufficient wet days"):
        calculate_wet_day_threshold(df, baseline_start=1991, baseline_end=1991, min_wet_days=50)


def test_detect_heavy_rainfall_events_single_and_multi_day():
    df = pd.DataFrame({
        "date": ["2000-08-01", "2000-08-02", "2000-08-03", "2000-08-04", "2000-08-05"],
        "precipitation_sum": [50.0, 60.0, 0.0, 70.0, 0.5] # 2-day storm (01-02), 1-day storm (04)
    })
    threshold = 40.0
    events = detect_heavy_rainfall_events(df, threshold=threshold)

    assert len(events) == 2
    # Event 1: 2 days
    assert events[0].start_date == "2000-08-01"
    assert events[0].end_date == "2000-08-02"
    assert events[0].duration == 2
    assert events[0].peak_daily_precipitation == 60.0
    assert events[0].total_event_precipitation == 110.0

    # Event 2: 1 day
    assert events[1].start_date == "2000-08-04"
    assert events[1].end_date == "2000-08-04"
    assert events[1].duration == 1
    assert events[1].peak_daily_precipitation == 70.0


def test_heavy_rainfall_annual_aggregates():
    df = pd.DataFrame({
        "date": [
            "2000-01-01", "2000-01-02", "2000-01-03",
            "2001-01-01", "2001-01-02"
        ],
        "precipitation_sum": [45.0, 55.0, 5.0, 10.0, 15.0]
    })
    events = [
        HeavyRainfallEvent(
            start_date="2000-01-01",
            end_date="2000-01-02",
            duration=2,
            peak_daily_precipitation=55.0,
            total_event_precipitation=100.0,
            mean_daily_precipitation=50.0,
            mean_exceedance=15.0
        )
    ]
    aggs = compute_annual_heavy_rainfall_aggregates(df, events, threshold=40.0, start_year=2000, end_year=2001)

    agg_2000 = next(a for a in aggs if a.year == 2000)
    assert agg_2000.event_count == 1
    assert agg_2000.heavy_rainfall_days == 2
    assert agg_2000.max_daily_precipitation == 55.0
    assert agg_2000.total_heavy_rainfall_mm == 100.0

    agg_2001 = next(a for a in aggs if a.year == 2001)
    assert agg_2001.event_count == 0
    assert agg_2001.heavy_rainfall_days == 0
