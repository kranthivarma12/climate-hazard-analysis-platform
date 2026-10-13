import React from 'react';
import { Download, Database, RefreshCw, Compass } from 'lucide-react';
import { HazardType } from '../types';

interface HeaderProps {
  currentHazard: HazardType;
  onSelectHazard: (h: HazardType) => void;
  onExportCsv?: () => void;
  onRefreshCache?: () => void;
  isRefreshing?: boolean;
  hasData?: boolean;
  dbConnected?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  currentHazard,
  onSelectHazard,
  onExportCsv,
  onRefreshCache,
  isRefreshing,
  hasData,
  dbConnected = true,
}) => {
  return (
    <header className="sticky top-0 z-30 bg-slate-900 border-b border-slate-800 text-slate-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-6">
        {/* Zone 1: Brand Wordmark */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="w-8 h-8 rounded bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-mono font-bold text-sm">
            CS
          </div>
          <div>
            <a href="#" className="text-base sm:text-lg font-bold tracking-tight text-white whitespace-nowrap">
              ClimaScope
            </a>
            <span className="hidden sm:inline-block ml-2 text-[11px] font-mono text-slate-400 uppercase tracking-wider">
              Climate Hazard Intelligence
            </span>
          </div>
        </div>

        {/* Zone 2: Navigation Links */}
        <nav className="hidden lg:flex items-center gap-5 text-xs sm:text-sm font-medium text-slate-300">
          <a href="#overview" className="hover:text-white transition-colors whitespace-nowrap shrink-0">
            Overview
          </a>
          <a href="#map" className="hover:text-white transition-colors whitespace-nowrap shrink-0">
            Region Explorer
          </a>
          <a href="#trends" className="hover:text-white transition-colors whitespace-nowrap shrink-0">
            Historical Trends
          </a>
          <a href="#events" className="hover:text-white transition-colors whitespace-nowrap shrink-0">
            Detected Events
          </a>
          <a href="#methodology" className="hover:text-white transition-colors whitespace-nowrap shrink-0">
            Methodology
          </a>
        </nav>

        {/* Zone 3: Primary Actions */}
        <div className="flex items-center gap-3 shrink-0">
          {hasData && onRefreshCache && (
            <button
              onClick={onRefreshCache}
              disabled={isRefreshing}
              title="Recalculate & refresh cache from Open-Meteo"
              className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-300 bg-slate-800 border border-slate-700 rounded-md hover:bg-slate-700 hover:text-white transition-colors whitespace-nowrap disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
              <span>Refresh Cache</span>
            </button>
          )}

          {hasData && onExportCsv && (
            <button
              onClick={onExportCsv}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-slate-900 bg-emerald-400 rounded-md hover:bg-emerald-300 transition-colors whitespace-nowrap shadow-sm"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export CSV</span>
            </button>
          )}

          <div className="hidden xl:flex items-center gap-1.5 text-xs font-mono text-slate-400 border-l border-slate-800 pl-3">
            <Database className="w-3.5 h-3.5 text-slate-400" />
            <span>MongoDB: {dbConnected ? 'Active' : 'Offline'}</span>
          </div>
        </div>
      </div>
    </header>
  );
};
