import React from 'react';
import { Lightbulb, Info, AlertTriangle, ArrowRight } from 'lucide-react';
import { TrendReport } from '../types';

interface InsightsSectionProps {
  trendReport: TrendReport;
}

export const InsightsSection: React.FC<InsightsSectionProps> = ({ trendReport }) => {
  const { event_trend, days_trend, comparison, insights, limitations } = trendReport;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
      <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
        <Lightbulb className="w-4 h-4 text-amber-400" />
        <h3 className="text-sm font-semibold text-white">Empirical Climate Insights & Comparative Trends</h3>
      </div>

      {/* Early vs Late Comparison Metric Banner */}
      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Early vs Late Events */}
        <div className="p-3.5 bg-slate-950 border border-slate-800 rounded-md">
          <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400 flex items-center justify-between">
            <span>Period Shift: Annual Episode Frequency</span>
            <span className="text-amber-400 font-semibold">{comparison.event_percent_change_display}</span>
          </div>
          <div className="mt-2 flex items-center justify-between text-xs font-mono">
            <div>
              <span className="text-slate-400 block text-[10px]">Early ({comparison.early_period_label})</span>
              <span className="text-base font-bold text-slate-200">{(comparison.early_mean_events?.toFixed(2) ?? 'N/A')}</span>
              <span className="text-[11px] text-slate-400 ml-1">ev/yr</span>
            </div>
            <ArrowRight className="w-4 h-4 text-slate-600" />
            <div className="text-right">
              <span className="text-slate-400 block text-[10px]">Late ({comparison.late_period_label})</span>
              <span className="text-base font-bold text-amber-300">{(comparison.late_mean_events?.toFixed(2) ?? 'N/A')}</span>
              <span className="text-[11px] text-slate-400 ml-1">ev/yr</span>
            </div>
          </div>
          <p className="mt-2 text-[11px] text-slate-400">
            Calculated as unweighted arithmetic means across respective decadal windows.
          </p>
        </div>

        {/* Early vs Late Days */}
        <div className="p-3.5 bg-slate-950 border border-slate-800 rounded-md">
          <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400 flex items-center justify-between">
            <span>Period Shift: Annual Heatwave Days</span>
            <span className="text-amber-400 font-semibold">{comparison.days_percent_change_display}</span>
          </div>
          <div className="mt-2 flex items-center justify-between text-xs font-mono">
            <div>
              <span className="text-slate-400 block text-[10px]">Early ({comparison.early_period_label})</span>
              <span className="text-base font-bold text-slate-200">{(comparison.early_mean_days?.toFixed(1) ?? 'N/A')}</span>
              <span className="text-[11px] text-slate-400 ml-1">days/yr</span>
            </div>
            <ArrowRight className="w-4 h-4 text-slate-600" />
            <div className="text-right">
              <span className="text-slate-400 block text-[10px]">Late ({comparison.late_period_label})</span>
              <span className="text-base font-bold text-amber-300">{(comparison.late_mean_days?.toFixed(1) ?? 'N/A')}</span>
              <span className="text-[11px] text-slate-400 ml-1">days/yr</span>
            </div>
          </div>
          <p className="mt-2 text-[11px] text-slate-400">
            Reflects change in total cumulative annual days exceeding the regional baseline threshold.
          </p>
        </div>
      </div>

      {/* Generated Insights List */}
      <div className="mt-4 space-y-2">
        <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono">
          Computed Algorithmic Findings
        </h4>
        <ul className="space-y-1.5 text-xs text-slate-300 leading-relaxed">
          {insights.map((insight, idx) => (
            <li key={idx} className="flex items-start gap-2">
              <span className="text-amber-400 font-mono mt-0.5">Â·</span>
              <span>{insight}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Scientific Limitations & Assumptions */}
      <div className="mt-4 pt-3 border-t border-slate-800/80">
        <div className="flex items-center gap-1.5 text-xs font-mono text-slate-400 mb-1.5">
          <Info className="w-3.5 h-3.5 text-slate-400" />
          <span>Scientific Assumptions & Known Model Boundaries</span>
        </div>
        <ul className="space-y-1 text-[11px] text-slate-400 leading-relaxed pl-5 list-disc">
          {limitations.map((limit, idx) => (
            <li key={idx}>{limit}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};

