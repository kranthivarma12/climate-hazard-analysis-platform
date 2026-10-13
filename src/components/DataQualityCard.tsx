import React from 'react';
import { CheckCircle2, AlertCircle, Database, ShieldCheck } from 'lucide-react';
import { DataQualityMetrics } from '../types';

interface DataQualityCardProps {
  metrics: DataQualityMetrics;
  sourceMetadata: {
    source: string;
    archive_endpoint: string;
    elevation?: number;
    timezone?: string;
    retrieval_timestamp?: string;
    cache_hit: boolean;
  };
  cacheStatus: 'HIT' | 'MISS';
}

export const DataQualityCard: React.FC<DataQualityCardProps> = ({
  metrics,
  sourceMetadata,
  cacheStatus,
}) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <h3 className="text-sm font-semibold text-white">Data Quality & Observational Completeness</h3>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="text-slate-400">Cache:</span>
          <span
            className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
              cacheStatus === 'HIT'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
            }`}
          >
            {cacheStatus === 'HIT' ? 'MONGODB HIT' : 'OPEN-METEO INGEST'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 text-xs font-mono">
        <div className="p-2.5 bg-slate-950 border border-slate-800 rounded">
          <span className="text-slate-400 text-[10px] block">ANALYSIS COMPLETENESS</span>
          <span className="text-base font-bold text-white tabular-nums">
            {metrics.completeness_percentage.toFixed(1)}%
          </span>
          <span className="text-[10px] text-slate-400 block mt-0.5">
            {metrics.valid_observations} / {metrics.total_expected_days} days
          </span>
        </div>

        <div className="p-2.5 bg-slate-950 border border-slate-800 rounded">
          <span className="text-slate-400 text-[10px] block">BASELINE COMPLETENESS</span>
          <span className="text-base font-bold text-white tabular-nums">
            {metrics.baseline_completeness_percentage.toFixed(1)}%
          </span>
          <span className="text-[10px] text-slate-400 block mt-0.5">
            {metrics.baseline_valid_days} valid baseline days
          </span>
        </div>

        <div className="p-2.5 bg-slate-950 border border-slate-800 rounded">
          <span className="text-slate-400 text-[10px] block">MISSING OBSERVATIONS</span>
          <span className="text-base font-bold text-slate-300 tabular-nums">
            {metrics.missing_days}
          </span>
          <span className="text-[10px] text-slate-400 block mt-0.5">
            Treated as episode breaks
          </span>
        </div>

        <div className="p-2.5 bg-slate-950 border border-slate-800 rounded">
          <span className="text-slate-400 text-[10px] block">ANOMALIES SCREENED</span>
          <span className="text-base font-bold text-slate-300 tabular-nums">
            {metrics.invalid_temperatures_rejected}
          </span>
          <span className="text-[10px] text-slate-400 block mt-0.5">
            Outside [-90°C, 65°C] bounds
          </span>
        </div>
      </div>

      <div className="mt-3 text-[11px] text-slate-400 space-y-1 pt-2 border-t border-slate-800/60 font-mono">
        <div>Source: {sourceMetadata.source}</div>
        {sourceMetadata.elevation !== undefined && (
          <div>Grid Elevation: {sourceMetadata.elevation} m · Timezone: {sourceMetadata.timezone || 'UTC'}</div>
        )}
        {sourceMetadata.retrieval_timestamp && (
          <div>Ingestion Timestamp: {sourceMetadata.retrieval_timestamp}</div>
        )}
      </div>
    </div>
  );
};
