import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { ControlPanel } from './components/ControlPanel';
import { KpiStrip } from './components/KpiStrip';
import { FrequencyChart } from './components/FrequencyChart';
import { DaysChart } from './components/DaysChart';
import { IntensityChart } from './components/IntensityChart';
import { EventsTable } from './components/EventsTable';
import { InsightsSection } from './components/InsightsSection';
import { DataQualityCard } from './components/DataQualityCard';
import { MethodologySection } from './components/MethodologySection';
import { fetchAnalysis, fetchRegions, refreshCache, fetchHealth } from './api/client';
import { AnalysisParams, AnalysisResponse, RegionPreset } from './types';
import { AlertCircle, RefreshCw, BarChart2 } from 'lucide-react';

const DEFAULT_PARAMS: AnalysisParams = {
  latitude: 33.4484, // Phoenix, AZ
  longitude: -112.074,
  start_year: 1990,
  end_year: 2020,
  hazard: 'heatwave',
  baseline_start: 1991,
  baseline_end: 2020,
};

export default function App() {
  const [params, setParams] = useState<AnalysisParams>(DEFAULT_PARAMS);
  const [regions, setRegions] = useState<RegionPreset[]>([]);
  const [data, setData] = useState<AnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [dbConnected, setDbConnected] = useState<boolean>(true);

  // Initialize presets and health check
  useEffect(() => {
    fetchRegions()
      .then((r) => setRegions(r))
      .catch((err) => console.warn('Could not load preset regions:', err));

    fetchHealth()
      .then((h) => setDbConnected(h.database_connected))
      .catch(() => setDbConnected(false));
  }, []);

  // Execute analysis
  const executeAnalysis = useCallback(
    async (overrideParams?: AnalysisParams, isRefreshCall = false) => {
      const activeParams = overrideParams || params;
      if (isRefreshCall) {
        setIsRefreshing(true);
      } else {
        setIsLoading(true);
      }
      setError(null);

      try {
        const result = await fetchAnalysis(activeParams);
        setData(result);
      } catch (err: any) {
        setError(err.message || 'An error occurred during climate hazard analysis.');
      } finally {
        setIsLoading(false);
        setIsRefreshing(false);
      }
    },
    [params]
  );

  // Initial load on component mount
  useEffect(() => {
    executeAnalysis();
  }, []);

  // Force cache refresh
  const handleRefreshCache = async () => {
    if (!data) return;
    setIsRefreshing(true);
    try {
      await refreshCache(params);
      await executeAnalysis({ ...params, force_refresh: true }, true);
    } catch (err: any) {
      setError(`Cache refresh failed: ${err.message}`);
      setIsRefreshing(false);
    }
  };

  // Export complete annual aggregates CSV
  const handleExportAnnualCsv = () => {
    if (!data) return;
    const headers = [
      'Year',
      'Event Count',
      'Heatwave Days',
      'Mean Duration (Days)',
      'Mean Intensity (°C)',
      'Peak Intensity (°C)',
      'Valid Days',
      'Missing Days',
    ];
    const rows = data.annual_aggregates.map((a) => [
      a.year,
      a.event_count,
      a.heatwave_days,
      a.mean_duration ?? '',
      a.mean_intensity ?? '',
      a.max_intensity ?? '',
      a.valid_days,
      a.missing_days,
    ]);
    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `heatwave_annual_analysis_${params.start_year}_${params.end_year}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-amber-500 selection:text-slate-950">
      {/* 3-Zone Navigation Header */}
      <Header
        onExportCsv={handleExportAnnualCsv}
        onRefreshCache={handleRefreshCache}
        isRefreshing={isRefreshing}
        hasData={data !== null}
        dbConnected={dbConnected}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Interactive Configuration Console */}
        <section aria-label="Hazard Configuration">
          <ControlPanel
            regions={regions}
            params={params}
            onChangeParams={setParams}
            onAnalyze={() => executeAnalysis()}
            isLoading={isLoading}
          />
        </section>

        {/* Loading State Banner */}
        {isLoading && (
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-8 flex flex-col items-center justify-center text-center">
            <div className="w-8 h-8 border-3 border-amber-400 border-t-transparent rounded-full animate-spin mb-3" />
            <h3 className="text-sm font-semibold text-white">Ingesting ERA5 Archive & Executing Heatwave Detection</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-md">
              Validating coordinates ({params.latitude.toFixed(2)}°, {params.longitude.toFixed(2)}°), computing 1991–2020 95th-percentile baseline threshold, and testing contiguous episode runs...
            </p>
          </div>
        )}

        {/* Error / Retry State */}
        {error && !isLoading && (
          <div className="bg-rose-950/30 border border-rose-500/40 rounded-lg p-5 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-rose-200">Analysis Pipeline Failed</h3>
              <p className="text-xs text-rose-300 mt-1">{error}</p>
              <button
                onClick={() => executeAnalysis()}
                className="mt-3 px-3 py-1.5 bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/40 text-rose-200 text-xs font-medium rounded transition-colors inline-flex items-center gap-1.5"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Retry Analysis</span>
              </button>
            </div>
          </div>
        )}

        {/* Data Display Content */}
        {data && !isLoading && (
          <>
            {/* KPI Strip */}
            <section id="overview" aria-label="Key Performance Indicators">
              <KpiStrip data={data} />
            </section>

            {/* Historical Trends Visualizations */}
            <section id="trends" aria-label="Historical Trends" className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <FrequencyChart
                  aggregates={data.annual_aggregates}
                  trend={data.trend_report.event_trend}
                />
                <DaysChart
                  aggregates={data.annual_aggregates}
                  trend={data.trend_report.days_trend}
                />
              </div>

              {/* Intensity Chart full width */}
              <IntensityChart
                aggregates={data.annual_aggregates}
                threshold={data.threshold_celsius}
              />
            </section>

            {/* Empirical Insights */}
            <section aria-label="Algorithmic Insights">
              <InsightsSection trendReport={data.trend_report} />
            </section>

            {/* Detected Events Table */}
            <section id="events" aria-label="Detected Episodes Table">
              <EventsTable
                events={data.events}
                threshold={data.threshold_celsius}
              />
            </section>

            {/* Data Quality & Provenance */}
            <section aria-label="Data Quality">
              <DataQualityCard
                metrics={data.data_quality}
                sourceMetadata={data.source_metadata}
                cacheStatus={data.cache_status}
              />
            </section>

            {/* Methodology & Science Documentation */}
            <section id="methodology" aria-label="Methodology Framework">
              <MethodologySection />
            </section>
          </>
        )}

        {/* Empty State */}
        {!data && !isLoading && !error && (
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-12 text-center">
            <BarChart2 className="w-10 h-10 text-slate-600 mx-auto mb-3" />
            <h3 className="text-base font-semibold text-white">No Analysis Loaded</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Select a global region preset or enter custom geographic coordinates above, then click Execute Analysis.
            </p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-500 font-mono">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <span>Climate Hazard Analysis Platform · Open-Meteo ERA5 Archive · WMO Reference Climatology</span>
          <span>FastAPI + MongoDB + React + Chart.js</span>
        </div>
      </footer>
    </div>
  );
}
