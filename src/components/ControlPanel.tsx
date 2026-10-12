import React, { useState, useEffect } from 'react';
import { Search, ChevronDown, ChevronUp, MapPin, Calendar, Sliders, AlertCircle } from 'lucide-react';
import { AnalysisParams, RegionPreset } from '../types';

interface ControlPanelProps {
  regions: RegionPreset[];
  params: AnalysisParams;
  onChangeParams: (newParams: AnalysisParams) => void;
  onAnalyze: () => void;
  isLoading: boolean;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
  regions,
  params,
  onChangeParams,
  onAnalyze,
  isLoading,
}) => {
  const [selectedRegionId, setSelectedRegionId] = useState<string>('phoenix');
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  // Sync preset selection with lat/lon
  const handleRegionSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const rId = e.target.value;
    setSelectedRegionId(rId);
    if (rId === 'custom') return;

    const found = regions.find((r) => r.id === rId);
    if (found) {
      onChangeParams({
        ...params,
        latitude: found.latitude,
        longitude: found.longitude,
      });
      setValidationError(null);
    }
  };

  const handleCustomLatChange = (latVal: number) => {
    setSelectedRegionId('custom');
    onChangeParams({ ...params, latitude: latVal });
  };

  const handleCustomLonChange = (lonVal: number) => {
    setSelectedRegionId('custom');
    onChangeParams({ ...params, longitude: lonVal });
  };

  // Validate inputs
  useEffect(() => {
    if (params.latitude < -90 || params.latitude > 90) {
      setValidationError('Latitude must be between -90.0° and 90.0°');
    } else if (params.longitude < -180 || params.longitude > 180) {
      setValidationError('Longitude must be between -180.0° and 180.0°');
    } else if (params.start_year > params.end_year) {
      setValidationError(`Start year (${params.start_year}) cannot exceed end year (${params.end_year})`);
    } else if (params.baseline_start > params.baseline_end) {
      setValidationError('Baseline start year cannot exceed baseline end year');
    } else {
      setValidationError(null);
    }
  }, [params]);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 shadow-sm">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Sliders className="w-4 h-4 text-amber-400" />
            <span>Hazard Configuration & Region Selector</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Empirical historical heatwave identification using daily maximum temperatures from Open-Meteo ERA5 archive.
          </p>
        </div>

        {/* Hazard Selector */}
        <div className="flex items-center gap-2 self-start lg:self-auto">
          <label className="text-xs font-mono uppercase text-slate-400">Hazard:</label>
          <div className="inline-flex rounded-md p-1 bg-slate-950 border border-slate-800">
            <button
              type="button"
              className="px-3 py-1 text-xs font-semibold rounded bg-amber-500/20 text-amber-300 border border-amber-500/30"
            >
              Heatwave (Active)
            </button>
            <button
              type="button"
              disabled
              title="Drought algorithm currently in scientific development"
              className="px-3 py-1 text-xs font-medium text-slate-500 cursor-not-allowed"
            >
              Drought (Planned)
            </button>
            <button
              type="button"
              disabled
              title="Extreme rainfall algorithm currently in scientific development"
              className="px-3 py-1 text-xs font-medium text-slate-500 cursor-not-allowed"
            >
              Rainfall (Planned)
            </button>
          </div>
        </div>
      </div>

      {/* Primary Grid Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
        {/* Region Preset */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5 flex items-center gap-1">
            <MapPin className="w-3.5 h-3.5 text-slate-400" />
            <span>Target Region Preset</span>
          </label>
          <select
            value={selectedRegionId}
            onChange={handleRegionSelect}
            className="w-full bg-slate-950 border border-slate-700 text-slate-200 text-sm rounded-md px-3 py-2 focus:outline-none focus:border-amber-400"
          >
            {regions.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}, {r.country} ({r.latitude.toFixed(2)}°, {r.longitude.toFixed(2)}°)
              </option>
            ))}
            <option value="custom">Custom Coordinates (Manual Entry)</option>
          </select>
        </div>

        {/* Coordinates Manual Inputs */}
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Latitude (°N/S)
            </label>
            <input
              type="number"
              step="0.0001"
              value={params.latitude}
              onChange={(e) => handleCustomLatChange(parseFloat(e.target.value) || 0)}
              className="w-full bg-slate-950 border border-slate-700 text-slate-200 text-sm font-mono rounded-md px-2.5 py-2 focus:outline-none focus:border-amber-400 tabular-nums"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Longitude (°E/W)
            </label>
            <input
              type="number"
              step="0.0001"
              value={params.longitude}
              onChange={(e) => handleCustomLonChange(parseFloat(e.target.value) || 0)}
              className="w-full bg-slate-950 border border-slate-700 text-slate-200 text-sm font-mono rounded-md px-2.5 py-2 focus:outline-none focus:border-amber-400 tabular-nums"
            />
          </div>
        </div>

        {/* Year Range */}
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5 flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              <span>Start Year</span>
            </label>
            <input
              type="number"
              min={1950}
              max={2024}
              value={params.start_year}
              onChange={(e) =>
                onChangeParams({ ...params, start_year: parseInt(e.target.value, 10) || 1990 })
              }
              className="w-full bg-slate-950 border border-slate-700 text-slate-200 text-sm font-mono rounded-md px-2.5 py-2 focus:outline-none focus:border-amber-400 tabular-nums"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              End Year
            </label>
            <input
              type="number"
              min={1950}
              max={2024}
              value={params.end_year}
              onChange={(e) =>
                onChangeParams({ ...params, end_year: parseInt(e.target.value, 10) || 2020 })
              }
              className="w-full bg-slate-950 border border-slate-700 text-slate-200 text-sm font-mono rounded-md px-2.5 py-2 focus:outline-none focus:border-amber-400 tabular-nums"
            />
          </div>
        </div>

        {/* Analyze Button */}
        <div className="flex flex-col justify-end">
          <button
            onClick={onAnalyze}
            disabled={isLoading || validationError !== null}
            className="w-full h-10 px-4 bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold text-sm rounded-md transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
                <span>Processing Open-Meteo Data...</span>
              </>
            ) : (
              <>
                <Search className="w-4 h-4" />
                <span>Execute Analysis</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Validation Warning */}
      {validationError && (
        <div className="mt-3 flex items-center gap-2 p-2.5 bg-rose-500/10 border border-rose-500/30 rounded-md text-xs text-rose-300">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{validationError}</span>
        </div>
      )}

      {/* Advanced Baseline Accordion */}
      <div className="mt-4 pt-3 border-t border-slate-800/80">
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="text-xs font-mono text-slate-400 hover:text-slate-200 flex items-center gap-1.5 transition-colors"
        >
          {showAdvanced ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          <span>Advanced Baseline Settings (Default Climatology: 1991–2020 WMO Standard)</span>
        </button>

        {showAdvanced && (
          <div className="mt-3 p-3 bg-slate-950 border border-slate-800 rounded-md grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1">
                Baseline Start Year
              </label>
              <input
                type="number"
                min={1950}
                max={2024}
                value={params.baseline_start}
                onChange={(e) =>
                  onChangeParams({
                    ...params,
                    baseline_start: parseInt(e.target.value, 10) || 1991,
                  })
                }
                className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs font-mono rounded px-2.5 py-1.5 focus:outline-none focus:border-amber-400"
              />
            </div>
            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1">
                Baseline End Year
              </label>
              <input
                type="number"
                min={1950}
                max={2024}
                value={params.baseline_end}
                onChange={(e) =>
                  onChangeParams({
                    ...params,
                    baseline_end: parseInt(e.target.value, 10) || 2020,
                  })
                }
                className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs font-mono rounded px-2.5 py-1.5 focus:outline-none focus:border-amber-400"
              />
            </div>
            <div className="sm:col-span-2 md:col-span-1 flex flex-col justify-end">
              <span className="text-[11px] text-slate-400 leading-relaxed">
                The 95th percentile threshold is derived from daily max temperatures across this reference baseline.
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
