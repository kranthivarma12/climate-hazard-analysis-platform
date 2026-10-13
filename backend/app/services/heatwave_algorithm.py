"""
Heatwave Detection Algorithm Module
====================================
Implements empirical 95th percentile baseline thresholding and episode detection.
Complies with WMO / climate hazard definitions:
- Baseline period (default 1991-2020) regional 95th percentile threshold
- Heatwave episode: at least 3 consecutive valid days strictly exceeding the threshold
- Missing dates or values strictly break continuity
- Boundary-aware: multi-year spanning episodes allocate event days to respective calendar years
"""

from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Tuple
import numpy as np
import pandas as pd


@dataclass
class HeatwaveEvent:
    start_date: str
    end_date: str
    duration: int
    peak_temperature: float
    mean_temperature: float
    mean_exceedance: float

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AnnualAggregate:
    year: int
    event_count: int
    heatwave_days: int
    mean_duration: Optional[float]
    mean_intensity: Optional[float]
    max_intensity: Optional[float]
    valid_days: int
    missing_days: int

    def to_dict(self) -> Dict:
        return asdict(self)


def calculate_baseline_threshold(
    df: pd.DataFrame,
    baseline_start: int,
    baseline_end: int,
    min_completeness_ratio: float = 0.80,
    percentile: float = 95.0
) -> Tuple[float, int, int]:
    """
    Calculate the regional percentile threshold from valid daily max temperatures in the baseline period.
    
    Parameters:
        df: DataFrame with 'date' (datetime or str YYYY-MM-DD) and 'temperature_2m_max' (float/NaN)
        baseline_start: Start year (inclusive), e.g. 1991
        baseline_end: End year (inclusive), e.g. 2020
        min_completeness_ratio: Minimum ratio of valid days required over the baseline period
        percentile: Percentile rank (default 95.0)

    Returns:
        (threshold_celsius, valid_count, expected_count)
    """
    if df.empty or 'date' not in df.columns or 'temperature_2m_max' not in df.columns:
        raise ValueError("Input DataFrame must contain 'date' and 'temperature_2m_max' columns.")

    work_df = df.copy()
    work_df['date'] = pd.to_datetime(work_df['date'])
    work_df = work_df.sort_values('date').drop_duplicates(subset=['date'])

    mask = (work_df['date'].dt.year >= baseline_start) & (work_df['date'].dt.year <= baseline_end)
    baseline_df = work_df.loc[mask]

    start_d = date(baseline_start, 1, 1)
    end_d = date(baseline_end, 12, 31)
    expected_days = (end_d - start_d).days + 1

    valid_temps = baseline_df['temperature_2m_max'].dropna()
    valid_count = len(valid_temps)

    required_min = int(expected_days * min_completeness_ratio)
    if valid_count < required_min:
        raise ValueError(
            f"Insufficient baseline observations for {baseline_start}-{baseline_end}. "
            f"Found {valid_count} valid days, required at least {required_min} "
            f"({min_completeness_ratio * 100:.0f}% of {expected_days} expected calendar days)."
        )

    # Compute empirical percentile with linear interpolation
    threshold = float(np.percentile(valid_temps.values, percentile))
    return round(threshold, 2), valid_count, expected_days


def detect_heatwaves(
    df: pd.DataFrame,
    threshold: float,
    min_consecutive_days: int = 3
) -> List[HeatwaveEvent]:
    """
    Detect heatwave episodes in a chronological daily temperature series.
    An episode requires at least min_consecutive_days consecutive valid days with temp > threshold.
    Any missing day, NaN, or temp <= threshold terminates the episode.
    """
    if df.empty:
        return []

    work_df = df.copy()
    work_df['date'] = pd.to_datetime(work_df['date'])
    work_df = work_df.sort_values('date').drop_duplicates(subset=['date'])

    # Build continuous daily index to guarantee missing dates act as breaks
    min_date = work_df['date'].min()
    max_date = work_df['date'].max()
    full_idx = pd.date_range(start=min_date, end=max_date, freq='D')
    work_df = work_df.set_index('date').reindex(full_idx)
    work_df.index.name = 'date'

    events: List[HeatwaveEvent] = []
    current_run: List[Tuple[date, float]] = []

    for d, row in work_df.iterrows():
        temp = row['temperature_2m_max']
        is_hot = pd.notna(temp) and float(temp) > threshold

        if is_hot:
            current_run.append((d.date(), float(temp)))
        else:
            if len(current_run) >= min_consecutive_days:
                events.append(_create_event(current_run, threshold))
            current_run = []

    # Final check if series ends during an active heatwave
    if len(current_run) >= min_consecutive_days:
        events.append(_create_event(current_run, threshold))

    return events


def _create_event(run: List[Tuple[date, float]], threshold: float) -> HeatwaveEvent:
    start_d = run[0][0].isoformat()
    end_d = run[-1][0].isoformat()
    duration = len(run)
    temps = [t for _, t in run]
    peak_temp = max(temps)
    mean_temp = float(np.mean(temps))
    mean_exceed = float(np.mean([t - threshold for t in temps]))

    return HeatwaveEvent(
        start_date=start_d,
        end_date=end_d,
        duration=duration,
        peak_temperature=round(peak_temp, 2),
        mean_temperature=round(mean_temp, 2),
        mean_exceedance=round(mean_exceed, 2)
    )


def compute_annual_aggregates(
    df: pd.DataFrame,
    events: List[HeatwaveEvent],
    start_year: int,
    end_year: int
) -> List[AnnualAggregate]:
    """
    Compute calendar-year aggregates for heatwave frequency, duration, intensity, and data completeness.
    Spanning events allocate heatwave days to their respective calendar years without double-counting.
    Episodes are attributed to their start year for episode count and duration metrics.
    """
    work_df = df.copy()
    work_df['date'] = pd.to_datetime(work_df['date'])
    work_df = work_df.sort_values('date').drop_duplicates(subset=['date'])

    # Map each heatwave day to a date set
    heatwave_dates: Dict[date, float] = {}
    for ev in events:
        s = datetime.strptime(ev.start_date, "%Y-%m-%d").date()
        e = datetime.strptime(ev.end_date, "%Y-%m-%d").date()
        cur = s
        while cur <= e:
            heatwave_dates[cur] = ev.peak_temperature
            cur += timedelta(days=1)

    aggregates: List[AnnualAggregate] = []

    for y in range(start_year, end_year + 1):
        year_start = date(y, 1, 1)
        year_end = date(y, 12, 31)
        expected_days_in_year = (year_end - year_start).days + 1

        year_data = work_df[(work_df['date'].dt.year == y)]
        valid_days = int(year_data['temperature_2m_max'].dropna().count())
        missing_days = max(0, expected_days_in_year - valid_days)

        # Events starting in this calendar year
        year_events = [
            ev for ev in events
            if datetime.strptime(ev.start_date, "%Y-%m-%d").date().year == y
        ]
        event_count = len(year_events)

        # Actual heatwave days falling within this calendar year
        hw_days_count = 0
        hw_temps_in_year: List[float] = []
        cur = year_start
        while cur <= year_end:
            if cur in heatwave_dates:
                hw_days_count += 1
                row = work_df[work_df['date'].dt.date == cur]
                if not row.empty and pd.notna(row['temperature_2m_max'].values[0]):
                    hw_temps_in_year.append(float(row['temperature_2m_max'].values[0]))
            cur += timedelta(days=1)

        mean_duration = round(float(np.mean([ev.duration for ev in year_events])), 2) if year_events else None
        mean_intensity = round(float(np.mean(hw_temps_in_year)), 2) if hw_temps_in_year else None
        max_intensity = round(float(np.max(hw_temps_in_year)), 2) if hw_temps_in_year else None

        aggregates.append(
            AnnualAggregate(
                year=y,
                event_count=event_count,
                heatwave_days=hw_days_count,
                mean_duration=mean_duration,
                mean_intensity=mean_intensity,
                max_intensity=max_intensity,
                valid_days=valid_days,
                missing_days=missing_days
            )
        )

    return aggregates
