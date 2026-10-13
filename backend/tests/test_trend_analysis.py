"""
Unit Tests for Trend Analysis and Insights
==========================================
Tests linear regression slopes, decadal conversion, statistical significance,
and zero-baseline percentage change handling.
"""

import pytest
from backend.app.services.trend_analysis import (
    compute_linear_trend,
    compare_early_vs_late,
    generate_trend_report
)
from backend.app.services.heatwave_algorithm import AnnualAggregate, HeatwaveEvent


def test_regression_increasing_direction_and_units():
    """Slope should be in events per year, and decadal slope 10x slope per year."""
    years = [2000, 2001, 2002, 2003, 2004]
    values = [1.0, 2.0, 3.0, 4.0, 5.0]  # slope = 1.0 event/year -> 10.0 events/decade

    res = compute_linear_trend(years, values)
    assert res.slope_per_year == 1.0
    assert res.slope_per_decade == 10.0
    assert res.direction == "increasing"
    assert res.r_squared == 1.0
    assert res.statistically_significant is True  # perfect correlation p < 0.05


def test_regression_decreasing_direction():
    years = [2000, 2001, 2002, 2003]
    values = [10.0, 8.0, 6.0, 4.0]  # slope = -2.0 / yr

    res = compute_linear_trend(years, values)
    assert res.slope_per_year == -2.0
    assert res.slope_per_decade == -20.0
    assert res.direction == "decreasing"


def test_regression_stable_zero_slope():
    years = [2000, 2001, 2002]
    values = [3.0, 3.0, 3.0]

    res = compute_linear_trend(years, values)
    assert res.slope_per_year == 0.0
    assert res.slope_per_decade == 0.0
    assert res.direction == "stable"
    assert res.statistically_significant is False


def test_undefined_percent_change_when_baseline_is_zero():
    """When early period average is 0, percentage change must be flagged undefined."""
    aggs = [
        AnnualAggregate(year=2000, event_count=0, heatwave_days=0, mean_duration=None, mean_intensity=None, max_intensity=None, valid_days=365, missing_days=0),
        AnnualAggregate(year=2001, event_count=0, heatwave_days=0, mean_duration=None, mean_intensity=None, max_intensity=None, valid_days=365, missing_days=0),
        AnnualAggregate(year=2010, event_count=2, heatwave_days=8, mean_duration=4.0, mean_intensity=35.0, max_intensity=37.0, valid_days=365, missing_days=0),
        AnnualAggregate(year=2011, event_count=3, heatwave_days=12, mean_duration=4.0, mean_intensity=36.0, max_intensity=38.0, valid_days=365, missing_days=0),
    ]

    comp = compare_early_vs_late(aggs)
    assert comp.early_mean_events == 0.0
    assert comp.late_mean_events == 2.5
    assert comp.event_percent_change is None
    assert "Undefined" in comp.event_percent_change_display


def test_generate_trend_report_outputs():
    aggs = [
        AnnualAggregate(year=2000 + i, event_count=i, heatwave_days=i * 3, mean_duration=3.0, mean_intensity=32.0, max_intensity=34.0, valid_days=365, missing_days=0)
        for i in range(10)
    ]
    events = [
        HeatwaveEvent(start_date="2005-07-01", end_date="2005-07-05", duration=5, peak_temperature=38.5, mean_temperature=36.2, mean_exceedance=3.2)
    ]
    report = generate_trend_report(aggs, events, threshold=33.0)
    assert len(report.insights) >= 4
    assert len(report.limitations) >= 3
    assert report.event_trend.direction == "increasing"
