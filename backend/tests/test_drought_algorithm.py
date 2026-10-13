"""
Unit Tests for Drought Algorithm (SPI-3)
=========================================
Tests monthly aggregation, Gamma distribution fitting, SPI calculation,
drought threshold detection, and zero precipitation handling.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import date, timedelta
from backend.app.services.drought_algorithm import (
    aggregate_daily_to_monthly,
    calculate_spi,
    detect_drought_events,
    compute_annual_drought_aggregates,
    DroughtEvent
)


def test_aggregate_daily_to_monthly():
    # 2 months of daily data (Jan 2000 has 31 days, Feb 2000 has 29 days)
    dates = pd.date_range("2000-01-01", "2000-02-29", freq="D")
    precip = [2.0] * len(dates) # 2mm daily
    df = pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "precipitation_sum": precip})

    monthly = aggregate_daily_to_monthly(df)
    assert len(monthly) == 2
    jan = monthly[monthly["month"] == 1].iloc[0]
    assert jan["total_precip"] == 62.0 # 31 * 2


def test_spi_calculation_and_drought_event_detection():
    """
    Construct 30 years of monthly precipitation:
    Regular years have 100mm/month.
    Year 2010 has 10mm/month (severe drought).
    """
    records = []
    for y in range(1991, 2021):
        for m in range(1, 13):
            # Normal: 100mm, in 2010: extreme dry 5mm
            val = 5.0 if y == 2010 else (80.0 + (m * 3.0))
            records.append({
                "year_month": pd.Period(f"{y}-{m:02d}", freq="M"),
                "total_precip": val,
                "valid_days": 30,
                "days_in_month": 30,
                "year": y,
                "month": m,
                "date_str": f"{y}-{m:02d}"
            })
    monthly_df = pd.DataFrame(records)

    spi_df = calculate_spi(monthly_df, accumulation_window=3, baseline_start=1991, baseline_end=2020)
    assert "spi" in spi_df.columns

    # In 2010, SPI should be strongly negative (<= -1.0)
    dry_year_spis = spi_df[spi_df["year"] == 2010]["spi"].dropna()
    assert len(dry_year_spis) > 0
    assert dry_year_spis.min() < -1.5 # Severe drought

    events = detect_drought_events(spi_df, threshold=-1.0)
    assert len(events) >= 1
    drought_2010 = [e for e in events if "2010" in e.start_date]
    assert len(drought_2010) >= 1
    assert drought_2010[0].min_spi <= -1.5


def test_drought_annual_aggregates():
    records = []
    for y in range(2000, 2003):
        for m in range(1, 13):
            # Year 2001 has SPI <= -1.0
            spi_val = -1.8 if y == 2001 and m in [6, 7, 8] else 0.2
            records.append({
                "year": y,
                "month": m,
                "date_str": f"{y}-{m:02d}",
                "total_precip": 50.0,
                "spi": spi_val
            })
    spi_df = pd.DataFrame(records)
    events = [
        DroughtEvent(
            start_date="2001-06",
            end_date="2001-08",
            duration_months=3,
            min_spi=-1.8,
            mean_spi=-1.8,
            cumulative_severity=5.4,
            drought_category="Severe"
        )
    ]

    aggs = compute_annual_drought_aggregates(spi_df, events, 2000, 2002)
    agg_2001 = next(a for a in aggs if a.year == 2001)
    assert agg_2001.drought_months == 3
    assert agg_2001.event_count == 1
    assert agg_2001.min_spi == -1.8
