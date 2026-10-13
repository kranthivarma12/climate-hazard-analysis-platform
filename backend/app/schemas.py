"""
Pydantic Schemas for Multi-Hazard Validation and API Responses
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field


class RegionPreset(BaseModel):
    id: str
    name: str
    country: str
    latitude: float
    longitude: float
    description: str


class DataQualityMetrics(BaseModel):
    total_expected_days: int
    valid_observations: int
    valid_precipitation_observations: Optional[int] = None
    missing_days: int
    completeness_percentage: float
    baseline_valid_days: int
    baseline_completeness_percentage: float
    invalid_temperatures_rejected: int
    invalid_precipitation_rejected: Optional[int] = 0


class RegressionMetrics(BaseModel):
    slope_per_year: float
    slope_per_decade: float
    intercept: float
    r_squared: float
    p_value: float
    std_err: float
    direction: str
    statistically_significant: bool


class ComparisonMetrics(BaseModel):
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


class TrendReportSchema(BaseModel):
    event_trend: RegressionMetrics
    days_trend: RegressionMetrics
    comparison: ComparisonMetrics
    insights: List[str]
    limitations: List[str]


class AnalysisSummary(BaseModel):
    total_events: int
    primary_exposure_metric: int # heatwave days, drought months, or heavy rain days
    primary_exposure_label: str  # "Heatwave Days", "Drought Months", "Heavy Rain Days"
    mean_event_duration: Optional[float]
    duration_unit: str           # "days" | "months"
    longest_event_duration: Optional[int]
    peak_metric_value: Optional[float]
    peak_metric_label: str
    threshold_value: Optional[float]
    threshold_label: str
    baseline_period: str
    analysis_period: str


class AnalysisResponse(BaseModel):
    region_info: Dict[str, Any]
    coordinates: Dict[str, float]
    requested_period: Dict[str, int]
    baseline_period: Dict[str, int]
    hazard: str                  # "heatwave" | "drought" | "heavy_rainfall"
    algorithm_version: str
    threshold: Optional[float] = None
    summary: AnalysisSummary
    trend_report: TrendReportSchema
    annual_aggregates: List[Dict[str, Any]]
    events: List[Dict[str, Any]]
    data_quality: DataQualityMetrics
    source_metadata: Dict[str, Any]
    cache_status: str            # "HIT" | "MISS"


class CacheRefreshRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    start_year: int = Field(default=1990, ge=1950, le=2024)
    end_year: int = Field(default=2020, ge=1950, le=2024)
    baseline_start: int = Field(default=1991, ge=1950, le=2024)
    baseline_end: int = Field(default=2020, ge=1950, le=2024)
    hazard: str = "heatwave"


class HealthCheckResponse(BaseModel):
    status: str
    database_connected: bool
    database_uri_configured: str
    version: str
    timestamp: str
    supported_hazards: List[str] = ["heatwave", "drought", "heavy_rainfall"]
