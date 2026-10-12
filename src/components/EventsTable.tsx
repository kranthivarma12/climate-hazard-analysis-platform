import React, { useState, useMemo } from 'react';
import { ArrowUpDown, Download, Filter, Search } from 'lucide-react';
import { HeatwaveEvent } from '../types';

interface EventsTableProps {
  events: HeatwaveEvent[];
  threshold: number;
}

type SortField = 'start_date' | 'duration' | 'peak_temperature' | 'mean_exceedance';
type SortOrder = 'asc' | 'desc';

export const EventsTable: React.FC<EventsTableProps> = ({ events, threshold }) => {
  const [sortField, setSortField] = useState<SortField>('start_date');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [minDurationFilter, setMinDurationFilter] = useState<number>(3);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const pageSize = 10;

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const filteredAndSorted = useMemo(() => {
    return events
      .filter((ev) => {
        if (ev.duration < minDurationFilter) return false;
        if (searchTerm) {
          const term = searchTerm.toLowerCase();
          return ev.start_date.includes(term) || ev.end_date.includes(term);
        }
        return true;
      })
      .sort((a, b) => {
        let valA: any = a[sortField];
        let valB: any = b[sortField];
        if (sortField === 'start_date') {
          return sortOrder === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
        }
        return sortOrder === 'asc' ? valA - valB : valB - valA;
      });
  }, [events, sortField, sortOrder, minDurationFilter, searchTerm]);

  const totalPages = Math.max(1, Math.ceil(filteredAndSorted.length / pageSize));
  const paginatedEvents = filteredAndSorted.slice((page - 1) * pageSize, page * pageSize);

  const exportEventsCsv = () => {
    if (!events.length) return;
    const headers = ['Start Date', 'End Date', 'Duration (Days)', 'Peak Temp (°C)', 'Mean Temp (°C)', 'Mean Exceedance (°C)', 'Threshold (°C)'];
    const rows = filteredAndSorted.map((e) => [
      e.start_date,
      e.end_date,
      e.duration,
      e.peak_temperature,
      e.mean_temperature,
      e.mean_exceedance,
      threshold,
    ]);
    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `heatwave_events_${events[0]?.start_date?.slice(0, 4) || 'records'}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h3 className="text-sm font-semibold text-white">Chronological Heatwave Event Log</h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Detected episodes meeting threshold criteria ({threshold.toFixed(1)}°C baseline P95, duration ≥ 3 days).
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {/* Min Duration Filter */}
          <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-700 rounded px-2 py-1 text-xs text-slate-300">
            <Filter className="w-3 h-3 text-slate-400" />
            <span className="font-mono">Min days:</span>
            <select
              value={minDurationFilter}
              onChange={(e) => {
                setMinDurationFilter(parseInt(e.target.value, 10));
                setPage(1);
              }}
              className="bg-transparent text-amber-400 font-mono font-medium focus:outline-none"
            >
              <option value={3}>3+</option>
              <option value={5}>5+</option>
              <option value={7}>7+</option>
              <option value={10}>10+</option>
            </select>
          </div>

          {/* Search by year/month */}
          <div className="relative">
            <Search className="w-3 h-3 absolute left-2.5 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search date (YYYY-MM)..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(1);
              }}
              className="bg-slate-950 border border-slate-700 text-xs text-slate-200 rounded pl-7 pr-2.5 py-1 focus:outline-none focus:border-amber-400 font-mono"
            />
          </div>

          <button
            onClick={exportEventsCsv}
            disabled={!filteredAndSorted.length}
            className="inline-flex items-center gap-1 px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 border border-slate-700 rounded transition-colors disabled:opacity-50"
          >
            <Download className="w-3 h-3" />
            <span>CSV</span>
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto mt-3">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-800 text-[11px] font-mono uppercase text-slate-400 tracking-wider">
              <th
                onClick={() => handleSort('start_date')}
                className="py-2.5 px-3 cursor-pointer hover:text-white"
              >
                <div className="flex items-center gap-1">
                  <span>Start Date</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="py-2.5 px-3">End Date</th>
              <th
                onClick={() => handleSort('duration')}
                className="py-2.5 px-3 cursor-pointer hover:text-white"
              >
                <div className="flex items-center gap-1">
                  <span>Duration</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th
                onClick={() => handleSort('peak_temperature')}
                className="py-2.5 px-3 cursor-pointer hover:text-white"
              >
                <div className="flex items-center gap-1">
                  <span>Peak Temp</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="py-2.5 px-3">Mean Temp</th>
              <th
                onClick={() => handleSort('mean_exceedance')}
                className="py-2.5 px-3 cursor-pointer hover:text-white"
              >
                <div className="flex items-center gap-1">
                  <span>Mean Exceedance</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono">
            {paginatedEvents.length > 0 ? (
              paginatedEvents.map((ev, idx) => (
                <tr key={`${ev.start_date}-${idx}`} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-2.5 px-3 text-slate-200 font-medium">{ev.start_date}</td>
                  <td className="py-2.5 px-3 text-slate-400">{ev.end_date}</td>
                  <td className="py-2.5 px-3 text-white font-semibold">
                    <span className="px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                      {ev.duration} days
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-rose-400 font-semibold">{ev.peak_temperature.toFixed(1)}°C</td>
                  <td className="py-2.5 px-3 text-slate-300">{ev.mean_temperature.toFixed(1)}°C</td>
                  <td className="py-2.5 px-3 text-amber-300">+{ev.mean_exceedance.toFixed(1)}°C</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-500 font-sans">
                  No heatwave episodes found matching the specified duration filter and date search.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
        <div>
          Showing {filteredAndSorted.length > 0 ? (page - 1) * pageSize + 1 : 0} to{' '}
          {Math.min(page * pageSize, filteredAndSorted.length)} of {filteredAndSorted.length} episodes
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-2.5 py-1 rounded bg-slate-950 border border-slate-800 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <span className="px-2 font-mono text-slate-300">
            {page} / {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-2.5 py-1 rounded bg-slate-950 border border-slate-800 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
};
