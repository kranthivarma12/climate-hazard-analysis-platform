"""
Heavy Rainfall Detection Algorithm Module — ETCCDI R95p Wet-Day Percentile
=============================================================================
Calculates the local 95th-percentile threshold of wet-day daily precipitation (R95p),
where a wet day is defined as precipitation >= 1.0 mm.
Identifies heavy rainfall days and groups consecutive qualifying days into extreme rainfall episodes.
Complies with ETCCDI (Expert Team on Climate Change Detection and Indices) standards.
"""

from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Tuple
import numpy as np
import pandas as pd


@dataclass
class HeavyRainfallEvent:
    start_date: str
    end_date: str
    duration: int               # Calendar days
    peak_daily_precipitation: float # Max single-day precipitation (mm)
    total_event_precipitation: float # Total accumulated precipitation during event (mm)
    mean_daily_precipitation: float
    mean_exceedance: float      # Mean mm above R95p threshold

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AnnualHeavyRainfallAggregate:
    year: int
    event_count: int
    heavy_rainfall_days: int
    max_daily_precipitation: Optional[float]
    total_heavy_rainfall_mm: float
    annual_total_precipitation_mm: float
    mean_event_duration: Optional[float]
    valid_days: int
    missing_days: int

    def to_dict(self) -> Dict:
        return asdict(self)


def calculate_wet_day_threshold(
    df: pd.DataFrame,
    baseline_start: int,
    baseline_end: int,
    min_wet_threshold_mm: float = 1.0,
    percentile: float = 95.0,
    min_wet_days: int = 50
) -> Tuple[float, int, int]:
    """
    Calculates the 95th percentile threshold of wet-day precipitation (R95p)
    from valid days with precipitation >= min_wet_threshold_mm in the baseline period.

    Returns:
        (r95p_threshold_mm, total_wet_days, total_valid_days)
    """
    if df.empty or 'precipitation_sum' not in df.columns or 'date' not in df.columns:
        raise ValueError("DataFrame must contain 'date' and 'precipitation_sum' columns.")

    work = df.copy()
    work['date'] = pd.to_datetime(work['date'])
    work = work.sort_values('date').drop_duplicates(subset=['date'])

    mask = (work['date'].dt.year >= baseline_start) & (work['date'].dt.year <= baseline_end)
    baseline_df = work.loc[mask]

    valid_precip = baseline_df['precipitation_sum'].dropna()
    total_valid_days = len(valid_precip)

    wet_days = valid_precip[valid_precip >= min_wet_threshold_mm]
    wet_count = len(wet_days)

    if wet_count < min_wet_days:
        raise ValueError(
            f"Insufficient wet days ({wet_count} found, minimum {min_wet_days} required) in baseline {baseline_start}-{baseline_end} "
            f"to establish a reliable R95p precipitation threshold."
        )

    threshold = float(np.percentile(wet_days.values, percentile))
    return round(threshold, 2), wet_count, total_valid_days


def detect_heavy_rainfall_events(
    df: pd.DataFrame,
    threshold: float,
    min_wet_threshold_mm: float = 1.0
) -> List[HeavyRainfallEvent]:
    """
    Identifies heavy rainfall days where daily precipitation >= threshold (R95p)
    and groups consecutive qualifying days into episodes (duration >= 1 day).
    Missing dates or non-qualifying days break continuity.
    """
    if df.empty:
        return []

    work = df.copy()
    work['date'] = pd.to_datetime(work['date'])
    work = work.sort_values('date').drop_duplicates(subset=['date'])

    min_date = work['date'].min()
    max_date = work['date'].max()
    full_idx = pd.date_range(start=min_date, end=max_date, freq='D')
    work = work.set_index('date').reindex(full_idx)
    work.index.name = 'date'

    events: List[HeavyRainfallEvent] = []
    current_run: List[Tuple[date, float]] = []

    for d, row in work.iterrows():
        precip = row['precipitation_sum']
        is_heavy = pd.notna(precip) and float(precip) >= threshold and float(precip) >= min_wet_threshold_mm

        if is_heavy:
            current_run.append((d.date(), float(precip)))
        else:
            if len(current_run) >= 1:
                events.append(_create_heavy_rainfall_event(current_run, threshold))
            current_run = []

    if len(current_run) >= 1:
        events.append(_create_heavy_rainfall_event(current_run, threshold))

    return events


def _create_heavy_rainfall_event(run: List[Tuple[date, float]], threshold: float) -> HeavyRainfallEvent:
    start_d = run[0][0].isoformat()
    end_d = run[-1][0].isoformat()
    duration = len(run)
    precips = [p for _, p in run]
    peak = max(precips)
    total = float(np.sum(precips))
    mean_val = float(np.mean(precips))
    mean_exceed = float(np.mean([p - threshold for p in precips]))

    return HeavyRainfallEvent(
        start_date=start_d,
        end_date=end_d,
        duration=duration,
        peak_daily_precipitation=round(peak, 1),
        total_event_precipitation=round(total, 1),
        mean_daily_precipitation=round(mean_val, 1),
        mean_exceedance=round(mean_exceed, 1)
    )


def compute_annual_heavy_rainfall_aggregates(
    df: pd.DataFrame,
    events: List[HeavyRainfallEvent],
    threshold: float,
    start_year: int,
    end_year: int
) -> List[AnnualHeavyRainfallAggregate]:
    """
    Computes calendar-year aggregates for heavy rainfall frequency, heavy rain days,
    peak single-day precipitation, and total rainfall.
    """
    work = df.copy()
    work['date'] = pd.to_datetime(work['date'])
    work = work.sort_values('date').drop_duplicates(subset=['date'])

    aggregates: List[AnnualHeavyRainfallAggregate] = []

    for y in range(start_year, end_year + 1):
        year_start = date(y, 1, 1)
        year_end = date(y, 12, 31)
        expected_days = (year_end - year_start).days + 1

        year_data = work[work['date'].dt.year == y]
        valid_days = int(year_data['precipitation_sum'].dropna().count())
        missing_days = max(0, expected_days - valid_days)

        annual_total_precip = float(year_data['precipitation_sum'].dropna().sum()) if valid_days > 0 else 0.0

        # Heavy rainfall days in year
        heavy_days_series = year_data['precipitation_sum'].dropna()
        heavy_mask = (heavy_days_series >= threshold) & (heavy_days_series >= 1.0)
        heavy_days_count = int(heavy_mask.sum())

        max_daily = round(float(heavy_days_series.max()), 1) if not heavy_days_series.empty else None
        total_heavy_precip = round(float(heavy_days_series[heavy_mask].sum()), 1) if heavy_days_count > 0 else 0.0

        # Events starting in year y
        year_events = [ev for ev in events if int(ev.start_date.split('-')[0]) == y]
        event_count = len(year_events)
        mean_duration = round(float(np.mean([ev.duration for ev in year_events])), 2) if year_events else None

        aggregates.append(
            AnnualHeavyRainfallAggregate(
                year=y,
                event_count=event_count,
                heavy_rainfall_days=heavy_days_count,
                max_daily_precipitation=max_daily,
                total_heavy_rainfall_mm=total_heavy_precip,
                annual_total_precipitation_mm=round(annual_total_precip, 1),
                mean_event_duration=mean_duration,
                valid_days=valid_days,
                missing_days=missing_days
            )
        )

    return aggregates
