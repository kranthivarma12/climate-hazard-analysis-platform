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
  missing_days: number;
  completeness_percentage: number;
  baseline_valid_days: number;
  baseline_completeness_percentage: number;
  invalid_temperatures_rejected: number;
}

export interface HeatwaveEvent {
  start_date: string;
  end_date: string;
  duration: number;
  peak_temperature: number;
  mean_temperature: number;
  mean_exceedance: number;
}

export interface AnnualAggregate {
  year: number;
  event_count: number;
  heatwave_days: number;
  mean_duration: number | null;
  mean_intensity: number | null;
  max_intensity: number | null;
  valid_days: number;
  missing_days: number;
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
  early_mean_events: number;
  early_mean_days: number;
  late_period_label: string;
  late_start_year: number;
  late_end_year: number;
  late_mean_events: number;
  late_mean_days: number;
  event_percent_change: number | null;
  event_percent_change_display: string;
  days_percent_change: number | null;
  days_percent_change_display: string;
}

export interface TrendReport {
  event_trend: RegressionMetrics;
  days_trend: RegressionMetrics;
  comparison: ComparisonMetrics;
  insights: string[];
  limitations: string[];
}

export interface AnalysisSummary {
  total_events: number;
  total_heatwave_days: number;
  mean_event_duration: number | null;
  hottest_event_temperature: number | null;
  longest_event_duration: number | null;
  threshold_celsius: number;
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
  hazard: string;
  algorithm_version: string;
  threshold_celsius: number;
  summary: AnalysisSummary;
  trend_report: TrendReport;
  annual_aggregates: AnnualAggregate[];
  events: HeatwaveEvent[];
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
  hazard: string;
  baseline_start: number;
  baseline_end: number;
  force_refresh?: boolean;
}
