"""
Drought Detection Algorithm Module — Standardized Precipitation Index (SPI)
=============================================================================
Calculates the Standardized Precipitation Index (SPI-3) using monthly aggregation
and parametric 2-parameter Gamma distribution fitting with zero-precipitation probability adjustment.
Complies with WMO Guidelines on the Standardized Precipitation Index (WMO-No. 1090).

Drought Classification (WMO/McKee):
- SPI > -1.0: No drought
- -1.0 to > -1.5: Moderate drought
- -1.5 to > -2.0: Severe drought
- SPI <= -2.0: Extreme drought
"""

from dataclasses import dataclass, asdict
from datetime import date, datetime
from typing import List, Dict, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats


@dataclass
class DroughtEvent:
    start_date: str          # YYYY-MM
    end_date: str            # YYYY-MM
    duration_months: int
    min_spi: float           # Lowest SPI reached (most negative)
    mean_spi: float          # Average SPI during event
    cumulative_severity: float # Sum of |SPI| for all drought months
    drought_category: str    # "Moderate" | "Severe" | "Extreme"

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AnnualDroughtAggregate:
    year: int
    event_count: int
    drought_months: int
    min_spi: Optional[float]
    mean_spi: Optional[float]
    cumulative_severity: float
    total_annual_precip_mm: float
    valid_months: int
    missing_months: int

    def to_dict(self) -> Dict:
        return asdict(self)


def aggregate_daily_to_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates daily precipitation to monthly totals (YYYY-MM).
    Requires 'date' and 'precipitation_sum' (mm).
    """
    if df.empty or 'precipitation_sum' not in df.columns:
        raise ValueError("DataFrame must contain 'date' and 'precipitation_sum' columns.")

    work = df.copy()
    work['date'] = pd.to_datetime(work['date'])
    work['year_month'] = work['date'].dt.to_period('M')

    monthly = work.groupby('year_month').agg(
        total_precip=('precipitation_sum', lambda s: s.sum(min_count=20)), # Require at least 20 valid days
        valid_days=('precipitation_sum', lambda s: s.dropna().count()),
        days_in_month=('date', 'count')
    ).reset_index()

    monthly['year'] = monthly['year_month'].dt.year
    monthly['month'] = monthly['year_month'].dt.month
    monthly['date_str'] = monthly['year_month'].astype(str)
    return monthly


def calculate_spi(
    monthly_df: pd.DataFrame,
    accumulation_window: int = 3,
    baseline_start: int = 1991,
    baseline_end: int = 2020
) -> pd.DataFrame:
    """
    Calculates SPI for a given accumulation window (e.g., SPI-3).
    Fits Gamma distribution for each of the 12 calendar months independently
    using the documented baseline reference period.
    """
    df = monthly_df.sort_values(['year', 'month']).copy()

    # Calculate rolling accumulated precipitation
    df['accum_precip'] = df['total_precip'].rolling(window=accumulation_window, min_periods=accumulation_window).sum()

    # Baseline mask
    baseline_mask = (df['year'] >= baseline_start) & (df['year'] <= baseline_end)
    baseline_data = df[baseline_mask]

    spi_values = [np.nan] * len(df)

    for m in range(1, 13):
        # Fit distribution using baseline observations for calendar month m
        month_baseline = baseline_data[baseline_data['month'] == m]['accum_precip'].dropna().values

        if len(month_baseline) < 15:
            # Insufficient samples to fit Gamma distribution reliably
            continue

        # Zero precipitation handling (probability of zero)
        zeros_count = np.sum(month_baseline <= 0.0)
        q = zeros_count / len(month_baseline)
        pos_baseline = month_baseline[month_baseline > 0.0]

        if len(pos_baseline) < 5:
            continue

        try:
            # Fit Gamma distribution via SciPy (loc fixed to 0 for standard 2-parameter Gamma)
            shape, loc, scale = stats.gamma.fit(pos_baseline, floc=0)
        except Exception:
            # Fallback method of moments
            mean_val = np.mean(pos_baseline)
            var_val = np.var(pos_baseline, ddof=1)
            if var_val <= 0:
                continue
            shape = (mean_val ** 2) / var_val
            scale = var_val / mean_val
            loc = 0

        # Calculate SPI for all occurrences of month m across the entire series
        month_indices = df[df['month'] == m].index
        for idx in month_indices:
            x = df.loc[idx, 'accum_precip']
            if pd.isna(x):
                continue
            if x <= 0.0:
                # Value at or near zero
                prob = max(1e-6, q)
            else:
                gamma_cdf = stats.gamma.cdf(x, a=shape, loc=loc, scale=scale)
                prob = q + (1.0 - q) * gamma_cdf

            # Safeguard cumulative probability within (0, 1) bounds
            prob = min(max(prob, 1e-6), 1.0 - 1e-6)
            # Transform to standard normal quantile
            z = stats.norm.ppf(prob)
            spi_values[idx] = float(np.clip(z, -4.0, 4.0))

    df['spi'] = spi_values
    return df


def detect_drought_events(spi_df: pd.DataFrame, threshold: float = -1.0) -> List[DroughtEvent]:
    """
    Identifies drought episodes when SPI <= threshold (-1.0).
    Categorizes events:
    - Moderate: -1.5 < min_spi <= -1.0
    - Severe: -2.0 < min_spi <= -1.5
    - Extreme: min_spi <= -2.0
    """
    events: List[DroughtEvent] = []
    current_run: List[Dict] = []

    for _, row in spi_df.iterrows():
        spi = row['spi']
        if pd.notna(spi) and spi <= threshold:
            current_run.append({
                'date_str': row['date_str'],
                'spi': float(spi)
            })
        else:
            if len(current_run) >= 1: # At least 1 drought month
                events.append(_create_drought_event(current_run))
            current_run = []

    if len(current_run) >= 1:
        events.append(_create_drought_event(current_run))

    return events


def _create_drought_event(run: List[Dict]) -> DroughtEvent:
    start_d = run[0]['date_str']
    end_d = run[-1]['date_str']
    duration = len(run)
    spis = [r['spi'] for r in run]
    min_spi = min(spis)
    mean_spi = float(np.mean(spis))
    severity = float(np.sum([abs(s) for s in spis]))

    if min_spi <= -2.0:
        cat = "Extreme"
    elif min_spi <= -1.5:
        cat = "Severe"
    else:
        cat = "Moderate"

    return DroughtEvent(
        start_date=start_d,
        end_date=end_d,
        duration_months=duration,
        min_spi=round(min_spi, 2),
        mean_spi=round(mean_spi, 2),
        cumulative_severity=round(severity, 2),
        drought_category=cat
    )


def compute_annual_drought_aggregates(
    spi_df: pd.DataFrame,
    events: List[DroughtEvent],
    start_year: int,
    end_year: int
) -> List[AnnualDroughtAggregate]:
    """
    Computes calendar-year aggregates for drought frequency, drought months, min SPI, and annual precipitation.
    """
    aggregates: List[AnnualDroughtAggregate] = []

    for y in range(start_year, end_year + 1):
        year_rows = spi_df[spi_df['year'] == y]
        valid_months = int(year_rows['total_precip'].dropna().count())
        missing_months = 12 - valid_months
        total_precip = float(year_rows['total_precip'].sum()) if valid_months > 0 else 0.0

        # Drought months in this calendar year
        drought_mask = year_rows['spi'] <= -1.0
        drought_month_rows = year_rows[drought_mask]
        drought_months_count = int(drought_month_rows.shape[0])

        # Min and mean SPI
        all_spis = year_rows['spi'].dropna()
        min_spi = round(float(all_spis.min()), 2) if not all_spis.empty else None
        mean_spi = round(float(all_spis.mean()), 2) if not all_spis.empty else None

        # Cumulative severity in year
        drought_spis = drought_month_rows['spi'].dropna()
        cum_sev = round(float(np.sum([abs(s) for s in drought_spis])), 2) if not drought_spis.empty else 0.0

        # Events starting in year y
        year_events = [ev for ev in events if int(ev.start_date.split('-')[0]) == y]
        event_count = len(year_events)

        aggregates.append(
            AnnualDroughtAggregate(
                year=y,
                event_count=event_count,
                drought_months=drought_months_count,
                min_spi=min_spi,
                mean_spi=mean_spi,
                cumulative_severity=cum_sev,
                total_annual_precip_mm=round(total_precip, 1),
                valid_months=valid_months,
                missing_months=missing_months
            )
        )

    return aggregates
