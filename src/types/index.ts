export type HazardType = 'heatwave' | 'drought' | 'heavy_rainfall';

export interface RegionPreset {
  id: string;
  name: string;
  country: string;
  latitude: number;
  longitude: number;
  description: string;
}

export interface DataQualityMetrics {
  total_expected_days: number;
  valid_observations: number;
  valid_precipitation_observations?: number;
  missing_days: number;
  completeness_percentage: number;
  baseline_valid_days: number;
  baseline_completeness_percentage: number;
  invalid_temperatures_rejected: number;
  invalid_precipitation_rejected?: number;
}

export interface HeatwaveEvent {
  start_date: string;
  end_date: string;
  duration: number;
  peak_temperature: number;
  mean_temperature: number;
  mean_exceedance: number;
}

export interface DroughtEvent {
  start_date: string;
  end_date: string;
  duration_months: number;
  min_spi: number;
  mean_spi: number;
  cumulative_severity: number;
  drought_category: string;
}

export interface HeavyRainfallEvent {
  start_date: string;
  end_date: string;
  duration: number;
  peak_daily_precipitation: number;
  total_event_precipitation: number;
  mean_daily_precipitation: number;
  mean_exceedance: number;
}

export type HazardEvent = HeatwaveEvent | DroughtEvent | HeavyRainfallEvent | Record<string, any>;

export interface AnnualAggregate {
  year: number;
  event_count: number;
  // Heatwave fields
  heatwave_days?: number;
  mean_intensity?: number | null;
  max_intensity?: number | null;
  // Drought fields
  drought_months?: number;
  min_spi?: number | null;
  mean_spi?: number | null;
  total_annual_precip_mm?: number;
  // Heavy rainfall fields
  heavy_rainfall_days?: number;
  max_daily_precipitation?: number | null;
  total_heavy_rainfall_mm?: number;
  annual_total_precipitation_mm?: number;
  // Shared
  mean_duration?: number | null;
  mean_event_duration?: number | null;
  valid_days?: number;
  missing_days?: number;
  valid_months?: number;
  missing_months?: number;
  [key: string]: any;
}

export interface RegressionMetrics {
  slope_per_year: number;
  slope_per_decade: number;
  intercept: number;
  r_squared: number;
  p_value: number;
  std_err: number;
  direction: 'increasing' | 'decreasing' | 'stable';
  statistically_significant: boolean;
}

export interface ComparisonMetrics {
  early_period_label: string;
  early_start_year: number;
  early_end_year: number;
  early_mean_events: float;
  early_mean_days: float;
  late_period_label: string;
  late_start_year: number;
  late_end_year: number;
  late_mean_events: float;
  late_mean_days: float;
  event_percent_change: number | null;
  event_percent_change_display: string;
  days_percent_change: number | null;
  days_percent_change_display: string;
}

type float = number;

export interface TrendReport {
  event_trend: RegressionMetrics;
  days_trend: RegressionMetrics;
  comparison: ComparisonMetrics;
  insights: string[];
  limitations: string[];
}

export interface AnalysisSummary {
  total_events: number;
  primary_exposure_metric: number;
  primary_exposure_label: string;
  mean_event_duration: number | null;
  duration_unit: 'days' | 'months';
  longest_event_duration: number | null;
  peak_metric_value: number | null;
  peak_metric_label: string;
  threshold_value: number | null;
  threshold_label: string;
  baseline_period: string;
  analysis_period: string;
}

export interface AnalysisResponse {
  region_info: {
    latitude: number;
    longitude: number;
    display_name: string;
  };
  coordinates: {
    latitude: number;
    longitude: number;
  };
  requested_period: {
    start_year: number;
    end_year: number;
  };
  baseline_period: {
    baseline_start: number;
    baseline_end: number;
  };
  hazard: HazardType;
  algorithm_version: string;
  threshold: number | null;
  summary: AnalysisSummary;
  trend_report: TrendReport;
  annual_aggregates: AnnualAggregate[];
  events: HazardEvent[];
  data_quality: DataQualityMetrics;
  source_metadata: {
    source: string;
    archive_endpoint: string;
    elevation?: number;
    latitude?: number;
    longitude?: number;
    timezone?: string;
    retrieval_timestamp?: string;
    cache_hit: boolean;
  };
  cache_status: 'HIT' | 'MISS';
}

export interface AnalysisParams {
  latitude: number;
  longitude: number;
  start_year: number;
  end_year: number;
  hazard: HazardType;
  baseline_start: number;
  baseline_end: number;
  force_refresh?: boolean;
}
