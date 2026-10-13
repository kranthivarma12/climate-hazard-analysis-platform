import React from 'react';
import { Flame, CloudSun, CloudRain, Clock, Thermometer, TrendingUp, TrendingDown, Minus, Droplets } from 'lucide-react';
import { AnalysisResponse } from '../types';

interface KpiStripProps {
  data: AnalysisResponse;
}

export const KpiStrip: React.FC<KpiStripProps> = ({ data }) => {
  const { summary, trend_report, hazard } = data;
  const { event_trend } = trend_report;

  const trendIcon =
    event_trend.direction === 'increasing' ? (
      <TrendingUp className="w-3.5 h-3.5 text-rose-400" />
    ) : event_trend.direction === 'decreasing' ? (
      <TrendingDown className="w-3.5 h-3.5 text-emerald-400" />
    ) : (
      <Minus className="w-3.5 h-3.5 text-slate-400" />
    );

  const trendColor =
    event_trend.direction === 'increasing'
      ? 'text-rose-400'
      : event_trend.direction === 'decreasing'
      ? 'text-emerald-400'
      : 'text-slate-300';

  const hazardIcon =
    hazard === 'heatwave' ? (
      <Flame className="w-3.5 h-3.5 text-amber-400" />
    ) : hazard === 'drought' ? (
      <CloudSun className="w-3.5 h-3.5 text-orange-400" />
    ) : (
      <CloudRain className="w-3.5 h-3.5 text-cyan-400" />
    );

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3.5">
      {/* KPI 1: Total Hazard Episodes */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
        <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400 flex items-center justify-between">
          <span>{hazard === 'heatwave' ? 'Heatwaves' : hazard === 'drought' ? 'Drought Events' : 'Heavy Rain Events'}</span>
          {hazardIcon}
        </div>
        <div className="mt-2 flex items-baseline">
          <span className="text-2xl lg:text-3xl font-mono font-bold text-white tabular-nums">
            {summary.total_events}
          </span>
          <span className="text-xs font-mono text-slate-400 ml-1.5">events</span>
        </div>
        <div className="mt-1 text-[11px] text-slate-400">
          Period: {summary.analysis_period}
        </div>
      </div>

      {/* KPI 2: Primary Cumulative Exposure Metric */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
        <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400 flex items-center justify-between">
          <span>{summary.primary_exposure_label}</span>
          <Clock className="w-3.5 h-3.5 text-amber-400" />
        </div>
        <div className="mt-2 flex items-baseline">
          <span className="text-2xl lg:text-3xl font-mono font-bold text-white tabular-nums">
            {summary.primary_exposure_metric}
          </span>
          <span className="text-xs font-mono text-slate-400 ml-1.5">{summary.duration_unit}</span>
        </div>
        <div className="mt-1 text-[11px] text-slate-400">
          Cumulative exposure across span
        </div>
      </div>

      {/* KPI 3: Mean Event Duration */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
        <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400 flex items-center justify-between">
          <span>Mean Event Duration</span>
          <Clock className="w-3.5 h-3.5 text-blue-400" />
        </div>
        <div className="mt-2 flex items-baseline">
          <span className="text-2xl lg:text-3xl font-mono font-bold text-white tabular-nums">
            {summary.mean_event_duration !== null ? summary.mean_event_duration.toFixed(1) : '—'}
          </span>
          <span className="text-xs font-mono text-slate-400 ml-1.5">
            {summary.duration_unit}/event
          </span>
        </div>
        <div className="mt-1 text-[11px] text-slate-400">
          Max: {summary.longest_event_duration ?? '—'} {summary.duration_unit}
        </div>
      </div>

      {/* KPI 4: Threshold or Peak Anomaly */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
        <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400 flex items-center justify-between truncate">
          <span className="truncate">{summary.threshold_label.split('(')[0]}</span>
          {hazard === 'heatwave' ? (
            <Thermometer className="w-3.5 h-3.5 text-rose-400" />
          ) : (
            <Droplets className="w-3.5 h-3.5 text-cyan-400" />
          )}
        </div>
        <div className="mt-2 flex items-baseline">
          <span className="text-2xl lg:text-3xl font-mono font-bold text-white tabular-nums">
            {summary.threshold_value !== null ? summary.threshold_value.toFixed(1) : '—'}
          </span>
          <span className="text-xs font-mono text-slate-400 ml-1.5">
            {hazard === 'heatwave' ? '°C' : hazard === 'drought' ? 'SPI' : 'mm/day'}
          </span>
        </div>
        <div className="mt-1 text-[11px] text-slate-400">
          Baseline: {summary.baseline_period}
        </div>
      </div>

      {/* KPI 5: Decadal Trend Rate */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 col-span-2 md:col-span-1">
        <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400 flex items-center justify-between">
          <span>Decadal Trend Rate</span>
          {trendIcon}
        </div>
        <div className="mt-2 flex items-baseline">
          <span className={`text-2xl lg:text-3xl font-mono font-bold ${trendColor} tabular-nums`}>
            {event_trend.slope_per_decade > 0 ? `+${event_trend.slope_per_decade.toFixed(2)}` : event_trend.slope_per_decade.toFixed(2)}
          </span>
          <span className="text-xs font-mono text-slate-400 ml-1.5">ev/decade</span>
        </div>
        <div className="mt-1 text-[11px] flex items-center gap-1.5">
          <span className="font-mono text-slate-300">p = {event_trend.p_value.toFixed(3)}</span>
          <span className="text-slate-600">·</span>
          <span className={`text-[10px] font-mono ${event_trend.statistically_significant ? 'text-emerald-400 font-semibold' : 'text-slate-500'}`}>
            {event_trend.statistically_significant ? 'p < 0.05 Sig.' : 'Not Sig.'}
          </span>
        </div>
      </div>
    </div>
  );
};
