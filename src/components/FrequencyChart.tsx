import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Chart } from 'react-chartjs-2';
import { AnnualAggregate, RegressionMetrics } from '../types';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface FrequencyChartProps {
  aggregates: AnnualAggregate[];
  trend: RegressionMetrics;
}

export const FrequencyChart: React.FC<FrequencyChartProps> = ({ aggregates, trend }) => {
  const years = aggregates.map((a) => a.year);
  const eventCounts = aggregates.map((a) => a.event_count);

  // Compute regression line points: y = slope * year + intercept
  const trendPoints = years.map((y) => {
    const val = trend.slope_per_year * y + trend.intercept;
    return Math.max(0, parseFloat(val.toFixed(2)));
  });

  const chartData = {
    labels: years.map(String),
    datasets: [
      {
        type: 'bar' as const,
        label: 'Heatwave Episodes',
        data: eventCounts,
        backgroundColor: 'rgba(245, 158, 11, 0.75)',
        borderColor: 'rgb(245, 158, 11)',
        borderWidth: 1,
        borderRadius: 3,
        barPercentage: 0.7,
      },
      {
        type: 'line' as const,
        label: `Linear Trend (${trend.slope_per_decade > 0 ? '+' : ''}${trend.slope_per_decade.toFixed(2)} ev/decade)`,
        data: trendPoints,
        borderColor: trend.direction === 'increasing' ? 'rgb(244, 63, 94)' : 'rgb(56, 189, 248)',
        borderWidth: 2,
        borderDash: [5, 4],
        pointRadius: 0,
        pointHoverRadius: 4,
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
          stepSize: 1,
        },
        title: {
          display: true,
          text: 'Number of Episodes',
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
          <h3 className="text-sm font-semibold text-white">Annual Heatwave Frequency</h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Total distinct episodes exceeding baseline 95th percentile for ≥3 consecutive days.
          </p>
        </div>
      </div>
      <div className="h-64 sm:h-72">
        <Chart type="bar" data={chartData as any} options={options as any} />
      </div>
    </div>
  );
};
