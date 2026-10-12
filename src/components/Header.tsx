import React from 'react';
import { Download, Database, RefreshCw } from 'lucide-react';

interface HeaderProps {
  onExportCsv?: () => void;
  onRefreshCache?: () => void;
  isRefreshing?: boolean;
  hasData?: boolean;
  dbConnected?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  onExportCsv,
  onRefreshCache,
  isRefreshing,
  hasData,
  dbConnected = true,
}) => {
  return (
    <header className="sticky top-0 z-30 bg-slate-900 border-b border-slate-800 text-slate-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-8">
        {/* Zone 1: Brand Wordmark */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="w-8 h-8 rounded bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 font-mono font-bold text-sm">
            CH
          </div>
          <a href="#" className="text-base sm:text-lg font-bold tracking-tight text-white whitespace-nowrap">
            Climate Hazard Analysis Platform
          </a>
        </div>

        {/* Zone 2: Navigation Links */}
        <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-300">
          <a href="#overview" className="hover:text-white transition-colors whitespace-nowrap shrink-0">
            Overview
          </a>
          <a href="#trends" className="hover:text-white transition-colors whitespace-nowrap shrink-0">
            Historical Trends
          </a>
          <a href="#events" className="hover:text-white transition-colors whitespace-nowrap shrink-0">
            Detected Episodes
          </a>
          <a href="#methodology" className="hover:text-white transition-colors whitespace-nowrap shrink-0">
            Methodology & Data
          </a>
        </nav>

        {/* Zone 3: Primary Action */}
        <div className="flex items-center gap-3 shrink-0">
          {hasData && onRefreshCache && (
            <button
              onClick={onRefreshCache}
              disabled={isRefreshing}
              title="Force recalculation and refresh cache from Open-Meteo"
              className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-300 bg-slate-800 border border-slate-700 rounded-md hover:bg-slate-700 hover:text-white transition-colors whitespace-nowrap disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
              <span>Refresh Cache</span>
            </button>
          )}

          {hasData && onExportCsv && (
            <button
              onClick={onExportCsv}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-slate-900 bg-amber-400 rounded-md hover:bg-amber-300 transition-colors whitespace-nowrap shadow-sm"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export CSV</span>
            </button>
          )}

          <div className="hidden lg:flex items-center gap-1.5 text-xs font-mono text-slate-400 border-l border-slate-800 pl-3">
            <Database className="w-3.5 h-3.5 text-slate-400" />
            <span>MongoDB: {dbConnected ? 'Active' : 'Offline'}</span>
          </div>
        </div>
      </div>
    </header>
  );
};
