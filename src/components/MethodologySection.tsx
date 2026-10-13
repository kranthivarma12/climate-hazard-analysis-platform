import React from 'react';
import { BookOpen, HelpCircle } from 'lucide-react';

export const MethodologySection: React.FC = () => {
  return (
    <div id="methodology" className="bg-slate-900 border border-slate-800 rounded-lg p-5">
      <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
        <BookOpen className="w-4 h-4 text-amber-400" />
        <h3 className="text-sm font-semibold text-white">Methodology & Scientific Framework</h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-4 text-xs text-slate-300">
        {/* Pillar 1 */}
        <div className="space-y-2">
          <div className="font-mono text-amber-400 uppercase tracking-wider text-[11px] font-semibold">
            01. Threshold Derivation
          </div>
          <h4 className="font-semibold text-white text-sm">Climatological 95th Percentile Baseline</h4>
          <p className="text-slate-400 leading-relaxed text-[11px]">
            A fixed empirical regional threshold (T_95) is computed from daily maximum 2-meter air temperatures (T_max) across a 30-year reference baseline (default WMO 1991–2020 climatology).
          </p>
          <div className="p-2.5 bg-slate-950 border border-slate-800 rounded font-mono text-[10px] text-slate-300">
            Threshold = Percentile(T_max[1991..2020], 95.0)
          </div>
          <p className="text-slate-400 leading-relaxed text-[11px]">
            A minimum of 80% observational completeness is strictly enforced over the baseline period to prevent small-sample bias.
          </p>
        </div>

        {/* Pillar 2 */}
        <div className="space-y-2">
          <div className="font-mono text-amber-400 uppercase tracking-wider text-[11px] font-semibold">
            02. Episode Detection
          </div>
          <h4 className="font-semibold text-white text-sm">3-Day Minimum Consecutive Run Rule</h4>
          <p className="text-slate-400 leading-relaxed text-[11px]">
            A heatwave episode is formally identified when daily maximum temperature strictly exceeds the 95th-percentile threshold (T_max &gt; T_95) for at least three consecutive valid calendar days.
          </p>
          <div className="p-2.5 bg-slate-950 border border-slate-800 rounded font-mono text-[10px] text-slate-300">
            Duration = (End_Date - Start_Date) + 1 &ge; 3 days
          </div>
          <p className="text-slate-400 leading-relaxed text-[11px]">
            Any calendar day with missing temperature data or T_max &le; T_95 acts as an immediate termination of the continuous run.
          </p>
        </div>

        {/* Pillar 3 */}
        <div className="space-y-2">
          <div className="font-mono text-amber-400 uppercase tracking-wider text-[11px] font-semibold">
            03. Trend & Boundary Logic
          </div>
          <h4 className="font-semibold text-white text-sm">Decadal Regression & Boundary Split</h4>
          <p className="text-slate-400 leading-relaxed text-[11px]">
            Episodes spanning calendar-year boundaries (e.g., Dec 30 to Jan 3) allocate their respective heatwave days to the matching calendar years without double-counting.
          </p>
          <div className="p-2.5 bg-slate-950 border border-slate-800 rounded font-mono text-[10px] text-slate-300">
            Decadal Slope = OLS_Slope(Annual_Counts) &times; 10
          </div>
          <p className="text-slate-400 leading-relaxed text-[11px]">
            Statistical significance is evaluated using SciPy two-sided t-test ($p &lt; 0.05$). Period comparison percentages avoid division-by-zero on zero-event baselines.
          </p>
        </div>
      </div>
    </div>
  );
};
