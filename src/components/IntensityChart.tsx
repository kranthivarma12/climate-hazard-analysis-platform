import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { AnnualAggregate } from '../types';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface IntensityChartProps {
  aggregates: AnnualAggregate[];
  threshold: number;
}

export const IntensityChart: React.FC<IntensityChartProps> = ({ aggregates, threshold }) => {
  const years = aggregates.map((a) => a.year);
  const maxTemps = aggregates.map((a) => a.max_intensity ?? null);
  const meanTemps = aggregates.map((a) => a.mean_intensity ?? null);
  const thresholdLine = years.map(() => threshold);

  const chartData = {
    labels: years.map(String),
    datasets: [
      {
        label: 'Peak Temperature (°C)',
        data: maxTemps,
        borderColor: 'rgb(244, 63, 94)',
        backgroundColor: 'rgba(244, 63, 94, 0.8)',
        borderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6,
        spanGaps: true,
      },
      {
        label: 'Mean Heatwave Temp (°C)',
        data: meanTemps,
        borderColor: 'rgb(251, 191, 36)',
        backgroundColor: 'rgba(251, 191, 36, 0.8)',
        borderWidth: 1.5,
        borderDash: [3, 3],
        pointRadius: 3,
        spanGaps: true,
      },
      {
        label: `P95 Threshold Baseline (${threshold.toFixed(1)}°C)`,
        data: thresholdLine,
        borderColor: 'rgba(148, 163, 184, 0.8)',
        borderWidth: 1.5,
        borderDash: [6, 4],
        pointRadius: 0,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          color: '#94a3b8',
          font: { family: 'JetBrains Mono', size: 11 },
          boxWidth: 14,
        },
      },
      tooltip: {
        backgroundColor: '#0f172a',
        borderColor: '#334155',
        borderWidth: 1,
        titleColor: '#f8fafc',
        bodyColor: '#cbd5e1',
        titleFont: { family: 'JetBrains Mono', size: 12 },
        bodyFont: { family: 'JetBrains Mono', size: 11 },
        padding: 10,
        callbacks: {
          label: (context: any) => {
            const val = context.raw;
            if (val === null || val === undefined) return `${context.dataset.label}: No episodes`;
            return `${context.dataset.label}: ${val.toFixed(1)}°C`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: { color: 'rgba(51, 65, 85, 0.3)' },
        ticks: {
          color: '#94a3b8',
          font: { family: 'JetBrains Mono', size: 10 },
          maxRotation: 45,
        },
      },
      y: {
        grid: { color: 'rgba(51, 65, 85, 0.3)' },
        ticks: {
          color: '#94a3b8',
          font: { family: 'JetBrains Mono', size: 10 },
          callback: (value: any) => `${value}°C`,
        },
        title: {
          display: true,
          text: 'Temperature (°C)',
          color: '#94a3b8',
          font: { family: 'Plus Jakarta Sans', size: 11 },
        },
      },
    },
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-sm font-semibold text-white">Annual Heatwave Intensity (°C)</h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Maximum and mean daily maximum temperatures observed during heatwave events vs P95 baseline.
          </p>
        </div>
      </div>
      <div className="h-64 sm:h-72">
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
};
