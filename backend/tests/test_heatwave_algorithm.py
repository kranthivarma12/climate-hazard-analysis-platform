"""
Unit Tests for Heatwave Detection Algorithm
============================================
Validates baseline percentile thresholding, episode detection, boundary handling,
and data-quality rules against deterministic synthetic cases.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import date, timedelta
from backend.app.services.heatwave_algorithm import (
    calculate_baseline_threshold,
    detect_heatwaves,
    compute_annual_aggregates,
    HeatwaveEvent
)


def test_threshold_known_synthetic_dataset():
    """Validates 95th percentile calculation against known distribution."""
    # 100 days from 1.0 to 100.0
    dates = [date(1991, 1, 1) + timedelta(days=i) for i in range(100)]
    temps = [float(i + 1) for i in range(100)]
    df = pd.DataFrame({"date": dates, "temperature_2m_max": temps})

    # With min_completeness_ratio set low for this test:
    threshold, valid_count, expected = calculate_baseline_threshold(
        df, baseline_start=1991, baseline_end=1991, min_completeness_ratio=0.1
    )
    # np.percentile of 1..100 at 95% is 95.05
    expected_threshold = round(float(np.percentile(range(1, 101), 95)), 2)
    assert threshold == expected_threshold
    assert valid_count == 100


def test_insufficient_baseline_data_raises_error():
    """Fails cleanly when observations fail the required completeness ratio."""
    dates = [date(1991, 1, 1) + timedelta(days=i) for i in range(50)]
    temps = [30.0] * 50
    df = pd.DataFrame({"date": dates, "temperature_2m_max": temps})

    # Baseline 1991-2020 has ~10958 days, 50 days is well below 80%
    with pytest.raises(ValueError, match="Insufficient baseline observations"):
        calculate_baseline_threshold(df, baseline_start=1991, baseline_end=2020, min_completeness_ratio=0.8)


def test_duplicate_dates_and_missing_values_cleaned():
    """Ensures duplicate dates are deduplicated and NaNs handled."""
    df = pd.DataFrame({
        "date": ["1995-06-01", "1995-06-01", "1995-06-02", "1995-06-03"],
        "temperature_2m_max": [35.0, 36.0, np.nan, 38.0]
    })
    threshold = 30.0
    events = detect_heatwaves(df, threshold=threshold)
    # 06-02 is NaN, breaking continuity; thus neither segment meets 3 days
    assert len(events) == 0


def test_exactly_two_hot_days_no_heatwave():
    """Two consecutive days above threshold must not trigger an event (minimum 3 required)."""
    df = pd.DataFrame({
        "date": ["2000-07-01", "2000-07-02", "2000-07-03", "2000-07-04"],
        "temperature_2m_max": [35.0, 35.0, 25.0, 25.0]
    })
    events = detect_heatwaves(df, threshold=30.0)
    assert len(events) == 0


def test_exactly_three_consecutive_hot_days_one_heatwave():
    """Exactly three consecutive days above threshold produces exactly 1 heatwave event."""
    df = pd.DataFrame({
        "date": ["2000-07-01", "2000-07-02", "2000-07-03", "2000-07-04"],
        "temperature_2m_max": [32.0, 34.0, 33.0, 28.0]
    })
    events = detect_heatwaves(df, threshold=30.0)
    assert len(events) == 1
    ev = events[0]
    assert ev.start_date == "2000-07-01"
    assert ev.end_date == "2000-07-03"
    assert ev.duration == 3
    assert ev.peak_temperature == 34.0
    assert ev.mean_temperature == 33.0
    assert ev.mean_exceedance == 3.0


def test_four_or_more_consecutive_hot_days_one_event():
    """Five consecutive days above threshold produces a single 5-day event."""
    df = pd.DataFrame({
        "date": ["2000-07-01", "2000-07-02", "2000-07-03", "2000-07-04", "2000-07-05", "2000-07-06"],
        "temperature_2m_max": [31.0, 32.0, 33.0, 34.0, 35.0, 20.0]
    })
    events = detect_heatwaves(df, threshold=30.0)
    assert len(events) == 1
    assert events[0].duration == 5
    assert events[0].peak_temperature == 35.0


def test_below_threshold_day_breaks_episode():
    """A cool day in the middle breaks an episode into separate non-qualifying runs."""
    df = pd.DataFrame({
        "date": ["2000-07-01", "2000-07-02", "2000-07-03", "2000-07-04", "2000-07-05"],
        "temperature_2m_max": [35.0, 35.0, 28.0, 35.0, 35.0]  # 2 hot, 1 cool, 2 hot
    })
    events = detect_heatwaves(df, threshold=30.0)
    assert len(events) == 0


def test_missing_calendar_day_breaks_episode():
    """A skipped date in the series breaks continuity, preventing an event."""
    # 2000-07-03 is omitted from the table entirely
    df = pd.DataFrame({
        "date": ["2000-07-01", "2000-07-02", "2000-07-04", "2000-07-05"],
        "temperature_2m_max": [35.0, 35.0, 35.0, 35.0]
    })
    events = detect_heatwaves(df, threshold=30.0)
    assert len(events) == 0


def test_events_spanning_calendar_year_boundary():
    """
    Events extending across Dec 31 -> Jan 2:
    - Detected as a continuous single event
    - Event days allocated properly to respective calendar years without double counting
    """
    df = pd.DataFrame({
        "date": [
            "2000-12-30", "2000-12-31",
            "2001-01-01", "2001-01-02", "2001-01-03"
        ],
        "temperature_2m_max": [35.0, 35.0, 36.0, 36.0, 20.0]
    })
    events = detect_heatwaves(df, threshold=30.0)
    assert len(events) == 1
    ev = events[0]
    assert ev.start_date == "2000-12-30"
    assert ev.end_date == "2001-01-02"
    assert ev.duration == 4

    aggs = compute_annual_aggregates(df, events, start_year=2000, end_year=2001)
    agg_2000 = next(a for a in aggs if a.year == 2000)
    agg_2001 = next(a for a in aggs if a.year == 2001)

    # 2 days fall in 2000, 2 days fall in 2001
    assert agg_2000.heatwave_days == 2
    assert agg_2001.heatwave_days == 2
    # Total heatwave days across years matches event duration
    assert agg_2000.heatwave_days + agg_2001.heatwave_days == 4
    # Event is attributed to start year for event_count
    assert agg_2000.event_count == 1
    assert agg_2001.event_count == 0
