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
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { AnnualAggregate, RegressionMetrics } from '../types';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface DaysChartProps {
  aggregates: AnnualAggregate[];
  trend: RegressionMetrics;
}

export const DaysChart: React.FC<DaysChartProps> = ({ aggregates, trend }) => {
  const years = aggregates.map((a) => a.year);
  const hwDays = aggregates.map((a) => a.heatwave_days);

  const trendPoints = years.map((y) => {
    const val = trend.slope_per_year * y + trend.intercept;
    return Math.max(0, parseFloat(val.toFixed(2)));
  });

  const chartData = {
    labels: years.map(String),
    datasets: [
      {
        label: 'Heatwave Days / Year',
        data: hwDays,
        borderColor: 'rgb(251, 146, 60)',
        backgroundColor: 'rgba(251, 146, 60, 0.12)',
        fill: true,
        tension: 0.25,
        borderWidth: 2,
        pointBackgroundColor: 'rgb(251, 146, 60)',
        pointBorderColor: '#0f172a',
        pointBorderWidth: 1.5,
        pointRadius: 3,
        pointHoverRadius: 5,
      },
      {
        label: `Days Trend (${trend.slope_per_decade > 0 ? '+' : ''}${trend.slope_per_decade.toFixed(1)} days/decade)`,
        data: trendPoints,
        borderColor: 'rgb(148, 163, 184)',
        borderWidth: 1.5,
        borderDash: [4, 4],
        pointRadius: 0,
        fill: false,
        tension: 0,
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
        beginAtZero: true,
        grid: { color: 'rgba(51, 65, 85, 0.3)' },
        ticks: {
          color: '#94a3b8',
          font: { family: 'JetBrains Mono', size: 10 },
        },
        title: {
          display: true,
          text: 'Cumulative Heatwave Days',
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
          <h3 className="text-sm font-semibold text-white">Heatwave Exposure (Days / Year)</h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Total calendar days belonging to qualifying heatwave episodes within each year.
          </p>
        </div>
      </div>
      <div className="h-64 sm:h-72">
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
};
