"""
Trend Analysis and Statistical Insights Module
==============================================
Uses SciPy linear regression (scipy.stats.linregress) to compute decadal trends.
Supports Heatwave, Drought (SPI-3), and Heavy Rainfall (R95p) hazards.
Provides statistical significance metrics (p-value, R-squared) and compares early vs late periods.
Guards against zero-division for percentage change calculations.
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
import numpy as np
from scipy import stats


@dataclass
class RegressionResult:
    slope_per_year: float
    slope_per_decade: float
    intercept: float
    r_squared: float
    p_value: float
    std_err: float
    direction: str  # "increasing" | "decreasing" | "stable"
    statistically_significant: bool  # p_value < 0.05

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PeriodComparison:
    early_period_label: str
    early_start_year: int
    early_end_year: int
    early_mean_events: float
    early_mean_days: float
    late_period_label: str
    late_start_year: int
    late_end_year: int
    late_mean_events: float
    late_mean_days: float
    event_percent_change: Optional[float]
    event_percent_change_display: str
    days_percent_change: Optional[float]
    days_percent_change_display: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class TrendAnalysisReport:
    event_trend: RegressionResult
    days_trend: RegressionResult
    comparison: PeriodComparison
    insights: List[str]
    limitations: List[str]

    def to_dict(self) -> Dict:
        return {
            "event_trend": self.event_trend.to_dict(),
            "days_trend": self.days_trend.to_dict(),
            "comparison": self.comparison.to_dict(),
            "insights": self.insights,
            "limitations": self.limitations
        }


def compute_linear_trend(years: List[int], values: List[float]) -> RegressionResult:
    """
    Fits an ordinary least squares regression line y = slope * x + intercept using SciPy.
    """
    if len(years) < 2:
        return RegressionResult(
            slope_per_year=0.0,
            slope_per_decade=0.0,
            intercept=0.0,
            r_squared=0.0,
            p_value=1.0,
            std_err=0.0,
            direction="stable",
            statistically_significant=False
        )

    x = np.array(years, dtype=float)
    y = np.array(values, dtype=float)

    if np.all(y == y[0]):
        return RegressionResult(
            slope_per_year=0.0,
            slope_per_decade=0.0,
            intercept=float(y[0]),
            r_squared=0.0,
            p_value=1.0,
            std_err=0.0,
            direction="stable",
            statistically_significant=False
        )

    res = stats.linregress(x, y)
    slope = float(res.slope)
    slope_decade = float(slope * 10.0)
    r2 = float(res.rvalue ** 2) if not np.isnan(res.rvalue) else 0.0
    p_val = float(res.pvalue) if not np.isnan(res.pvalue) else 1.0
    std_err = float(res.stderr) if not np.isnan(res.stderr) else 0.0

    if abs(slope) < 0.001:
        direction = "stable"
    elif slope > 0:
        direction = "increasing"
    else:
        direction = "decreasing"

    return RegressionResult(
        slope_per_year=round(slope, 4),
        slope_per_decade=round(slope_decade, 3),
        intercept=round(float(res.intercept), 3),
        r_squared=round(r2, 4),
        p_value=round(p_val, 4),
        std_err=round(std_err, 4),
        direction=direction,
        statistically_significant=(p_val < 0.05)
    )


def compare_early_vs_late(
    years_or_aggs: Any,
    event_counts: Optional[List[float]] = None,
    days_or_months: Optional[List[float]] = None,
    unit_label: str = "days/yr"
) -> PeriodComparison:
    """
    Compares the earliest decade/half with the latest decade/half.
    Handles zero base cases without ZeroDivisionError.
    Accepts either (aggregates_list) or (years, event_counts, days_or_months).
    """
    if event_counts is None and days_or_months is None and isinstance(years_or_aggs, list):
        if not years_or_aggs:
            years = []
            ev_counts = []
            dm_vals = []
        else:
            first = years_or_aggs[0]
            if hasattr(first, 'year'):
                years = [a.year for a in years_or_aggs]
                ev_counts = [float(a.event_count) for a in years_or_aggs]
                dm_vals = [float(getattr(a, 'heatwave_days', getattr(a, 'drought_months', getattr(a, 'heavy_rainfall_days', 0)))) for a in years_or_aggs]
            else:
                years = []
                ev_counts = []
                dm_vals = []
    else:
        years = years_or_aggs
        ev_counts = event_counts or []
        dm_vals = days_or_months or []
    total_years = len(years)
    if total_years == 0:
        return PeriodComparison(
            early_period_label="N/A", early_start_year=0, early_end_year=0,
            early_mean_events=0.0, early_mean_days=0.0,
            late_period_label="N/A", late_start_year=0, late_end_year=0,
            late_mean_events=0.0, late_mean_days=0.0,
            event_percent_change=None, event_percent_change_display="Undefined (no data)",
            days_percent_change=None, days_percent_change_display="Undefined (no data)"
        )

    window_size = min(10, max(1, total_years // 2))
    early_years = years[:window_size]
    late_years = years[-window_size:]

    early_start = early_years[0]
    early_end = early_years[-1]
    late_start = late_years[0]
    late_end = late_years[-1]

    early_events_mean = float(np.mean(ev_counts[:window_size]))
    early_days_mean = float(np.mean(dm_vals[:window_size]))
    late_events_mean = float(np.mean(ev_counts[-window_size:]))
    late_days_mean = float(np.mean(dm_vals[-window_size:]))

    # Event percentage change
    if early_events_mean == 0.0:
        if late_events_mean == 0.0:
            ev_pct = 0.0
            ev_pct_disp = "0.0% (both periods 0 events/yr)"
        else:
            ev_pct = None
            ev_pct_disp = f"Undefined (+{late_events_mean:.2f} events/yr from zero baseline)"
    else:
        ev_pct = round(((late_events_mean - early_events_mean) / early_events_mean) * 100.0, 1)
        prefix = "+" if ev_pct > 0 else ""
        ev_pct_disp = f"{prefix}{ev_pct}%"

    # Days / Months percentage change
    if early_days_mean == 0.0:
        if late_days_mean == 0.0:
            days_pct = 0.0
            days_pct_disp = f"0.0% (both periods 0 {unit_label})"
        else:
            days_pct = None
            days_pct_disp = f"Undefined (+{late_days_mean:.1f} {unit_label} from zero baseline)"
    else:
        days_pct = round(((late_days_mean - early_days_mean) / early_days_mean) * 100.0, 1)
        prefix = "+" if days_pct > 0 else ""
        days_pct_disp = f"{prefix}{days_pct}%"

    return PeriodComparison(
        early_period_label=f"{early_start}–{early_end}",
        early_start_year=early_start,
        early_end_year=early_end,
        early_mean_events=round(early_events_mean, 2),
        early_mean_days=round(early_days_mean, 2),
        late_period_label=f"{late_start}–{late_end}",
        late_start_year=late_start,
        late_end_year=late_end,
        late_mean_events=round(late_events_mean, 2),
        late_mean_days=round(late_days_mean, 2),
        event_percent_change=ev_pct,
        event_percent_change_display=ev_pct_disp,
        days_percent_change=days_pct,
        days_percent_change_display=days_pct_disp
    )


def generate_heatwave_trend_report(
    aggregates: List[Any],
    events: List[Any],
    threshold: float
) -> TrendAnalysisReport:
    years = [a.year for a in aggregates]
    event_counts = [float(a.event_count) for a in aggregates]
    hw_days = [float(a.heatwave_days) for a in aggregates]

    event_trend = compute_linear_trend(years, event_counts)
    days_trend = compute_linear_trend(years, hw_days)
    comparison = compare_early_vs_late(years, event_counts, hw_days, unit_label="days/yr")

    insights = []
    sig_text = "statistically significant (p < 0.05)" if event_trend.statistically_significant else "not statistically significant at p < 0.05"

    if event_trend.slope_per_decade > 0:
        insights.append(
            f"Heatwave frequency exhibited an upward trajectory of +{event_trend.slope_per_decade:.2f} episodes per decade (p = {event_trend.p_value:.3f}, {sig_text})."
        )
    elif event_trend.slope_per_decade < 0:
        insights.append(
            f"Heatwave frequency trended downward by {event_trend.slope_per_decade:.2f} episodes per decade (p = {event_trend.p_value:.3f}, {sig_text})."
        )
    else:
        insights.append("Heatwave frequency remained stationary across the analyzed timeframe (slope: 0.00 episodes/decade).")

    insights.append(
        f"Annual heatwave days evolved at a decadal rate of {days_trend.slope_per_decade:+.1f} days/decade (R² = {days_trend.r_squared:.2f})."
    )
    insights.append(
        f"Comparing {comparison.early_period_label} to {comparison.late_period_label}, mean annual heatwave days changed from {comparison.early_mean_days:.1f} to {comparison.late_mean_days:.1f} days/yr ({comparison.days_percent_change_display})."
    )

    if events:
        hottest = max(events, key=lambda e: e.peak_temperature)
        longest = max(events, key=lambda e: e.duration)
        insights.append(
            f"The peak daily maximum temperature recorded was {hottest.peak_temperature}°C ({hottest.start_date} to {hottest.end_date}). "
            f"The longest continuous heatwave episode lasted {longest.duration} days ({longest.start_date} to {longest.end_date})."
        )
    else:
        insights.append("No qualifying heatwave episodes (>= 3 consecutive days above P95) were detected in the requested range.")

    limitations = [
        "A regional 95th-percentile baseline threshold is used; regional microclimates and day-of-year seasonal windows can add local nuance.",
        "Missing daily observations act as hard episode breaks, which may cause conservative duration estimation in sparse reporting intervals.",
        "Linear regressions indicate historical rate of change over the selected span and should not be used as unconstrained extrapolation."
    ]

    return TrendAnalysisReport(
        event_trend=event_trend,
        days_trend=days_trend,
        comparison=comparison,
        insights=insights,
        limitations=limitations
    )


def generate_drought_trend_report(
    aggregates: List[Any],
    events: List[Any],
    baseline_period: str
) -> TrendAnalysisReport:
    years = [a.year for a in aggregates]
    event_counts = [float(a.event_count) for a in aggregates]
    drought_months = [float(a.drought_months) for a in aggregates]

    event_trend = compute_linear_trend(years, event_counts)
    months_trend = compute_linear_trend(years, drought_months)
    comparison = compare_early_vs_late(years, event_counts, drought_months, unit_label="months/yr")

    insights = []
    sig_text = "statistically significant (p < 0.05)" if event_trend.statistically_significant else "not statistically significant at p < 0.05"

    if event_trend.slope_per_decade > 0:
        insights.append(
            f"Drought frequency (SPI-3 <= -1.0) trended upward by +{event_trend.slope_per_decade:.2f} events per decade (p = {event_trend.p_value:.3f}, {sig_text})."
        )
    elif event_trend.slope_per_decade < 0:
        insights.append(
            f"Drought frequency decreased by {event_trend.slope_per_decade:.2f} events per decade (p = {event_trend.p_value:.3f}, {sig_text})."
        )
    else:
        insights.append("Drought frequency was stationary across the analysis period (slope: 0.00 events/decade).")

    insights.append(
        f"Annual cumulative drought months changed at a rate of {months_trend.slope_per_decade:+.1f} months/decade (p = {months_trend.p_value:.3f})."
    )
    insights.append(
        f"Comparing {comparison.early_period_label} to {comparison.late_period_label}, mean annual drought exposure evolved from {comparison.early_mean_days:.1f} to {comparison.late_mean_days:.1f} months/yr ({comparison.days_percent_change_display})."
    )

    if events:
        most_severe = min(events, key=lambda e: e.min_spi)
        longest = max(events, key=lambda e: e.duration_months)
        insights.append(
            f"The most severe drought episode reached SPI {most_severe.min_spi} ({most_severe.drought_category} Drought, {most_severe.start_date} to {most_severe.end_date}). "
            f"The longest sustained drought lasted {longest.duration_months} months ({longest.start_date} to {longest.end_date})."
        )
    else:
        insights.append("No meteorological drought episodes (SPI-3 <= -1.0) were detected in the selected period.")

    limitations = [
        "Meteorological drought is indexed using SPI-3 (3-month precipitation accumulation); agricultural or hydrological droughts also depend on evapotranspiration (SPEI) and soil moisture.",
        "Distribution fitting utilizes the two-parameter Gamma distribution with zero-precipitation probability adjustment (WMO standard).",
        "Sparse rainfall in hyper-arid regions can cause non-Gaussian SPI tail distortion; minimum sample size rules are enforced."
    ]

    return TrendAnalysisReport(
        event_trend=event_trend,
        days_trend=months_trend,
        comparison=comparison,
        insights=insights,
        limitations=limitations
    )


def generate_heavy_rainfall_trend_report(
    aggregates: List[Any],
    events: List[Any],
    threshold: float
) -> TrendAnalysisReport:
    years = [a.year for a in aggregates]
    event_counts = [float(a.event_count) for a in aggregates]
    rain_days = [float(a.heavy_rainfall_days) for a in aggregates]

    event_trend = compute_linear_trend(years, event_counts)
    days_trend = compute_linear_trend(years, rain_days)
    comparison = compare_early_vs_late(years, event_counts, rain_days, unit_label="days/yr")

    insights = []
    sig_text = "statistically significant (p < 0.05)" if event_trend.statistically_significant else "not statistically significant at p < 0.05"

    if event_trend.slope_per_decade > 0:
        insights.append(
            f"Heavy rainfall frequency (R95p >= {threshold:.1f} mm/day) increased by +{event_trend.slope_per_decade:.2f} events per decade (p = {event_trend.p_value:.3f}, {sig_text})."
        )
    elif event_trend.slope_per_decade < 0:
        insights.append(
            f"Heavy rainfall frequency decreased by {event_trend.slope_per_decade:.2f} events per decade (p = {event_trend.p_value:.3f}, {sig_text})."
        )
    else:
        insights.append("Heavy rainfall frequency remained stationary across the analyzed years (slope: 0.00 events/decade).")

    insights.append(
        f"Annual heavy rainfall days shifted at a decadal rate of {days_trend.slope_per_decade:+.1f} days/decade (R² = {days_trend.r_squared:.2f})."
    )
    insights.append(
        f"Comparing {comparison.early_period_label} to {comparison.late_period_label}, mean annual heavy rainfall days changed from {comparison.early_mean_days:.1f} to {comparison.late_mean_days:.1f} days/yr ({comparison.days_percent_change_display})."
    )

    if events:
        wettest = max(events, key=lambda e: e.peak_daily_precipitation)
        highest_vol = max(events, key=lambda e: e.total_event_precipitation)
        insights.append(
            f"The maximum recorded single-day precipitation was {wettest.peak_daily_precipitation} mm ({wettest.start_date}). "
            f"The most voluminous storm episode accumulated {highest_vol.total_event_precipitation} mm over {highest_vol.duration} days ({highest_vol.start_date} to {highest_vol.end_date})."
        )
    else:
        insights.append(f"No days exceeding the local R95p wet-day threshold ({threshold:.1f} mm) were detected in the requested period.")

    limitations = [
        "Heavy rainfall is characterized by the ETCCDI R95p index (95th percentile of daily precipitation on wet days >= 1.0 mm). This represents meteorological rainfall extremes and must not be conflated with localized flood inundation.",
        "Reanalysis precipitation represents spatial grid-cell averages (~25-30 km) and may smooth out localized convective cloudbursts.",
        "Convective extreme precipitation exhibits high inter-annual variability; multi-decadal observations are necessary for robust statistical convergence."
    ]

    return TrendAnalysisReport(
        event_trend=event_trend,
        days_trend=days_trend,
        comparison=comparison,
        insights=insights,
        limitations=limitations
    )


# Backward compatibility alias for heatwave
def generate_trend_report(aggregates: List[Any], events: List[Any], threshold: float) -> TrendAnalysisReport:
    return generate_heatwave_trend_report(aggregates, events, threshold)
