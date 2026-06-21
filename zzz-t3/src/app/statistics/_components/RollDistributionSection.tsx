
"use client";

import React, { useState } from 'react';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { api } from '~/trpc/react';
import { artifactConfig } from '~/lib/constants';
import {
  calculateRollDistribution,
  getUniqueTypes,
  getUniqueMainStats,
  type LevelingDataItem,
} from '~/lib/statisticsCalculations';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
);

interface RollDistributionSectionProps {
  levelingData: LevelingDataItem[];
  selectedSet: string | null;
  isLoading: boolean;
}

export const RollDistributionSection: React.FC<RollDistributionSectionProps> = ({
  levelingData,
  selectedSet,
  isLoading,
}) => {
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [selectedMainStat, setSelectedMainStat] = useState<string | null>(null);
  const [selectedSubstats, setSelectedSubstats] = useState<string[]>([]);

  const uniqueTypes = getUniqueTypes(levelingData);
  const uniqueMainStats = selectedType ? getUniqueMainStats(levelingData, selectedType) : [];
  const availableSubstats = artifactConfig.allSubstats.filter(s => s !== selectedMainStat);

  const handleTypeSelection = (type: string) => {
    setSelectedType(type);
    setSelectedMainStat(null);
    setSelectedSubstats([]);
  };

  const handleMainStatSelection = (mainStat: string) => {
    setSelectedMainStat(mainStat);
    setSelectedSubstats([]);
  };

  const toggleSubstat = (sub: string) => {
    setSelectedSubstats(prev => {
      if (prev.includes(sub)) return prev.filter(s => s !== sub);
      if (prev.length >= 4) return prev;
      return [...prev, sub];
    });
  };

  const { data: rollData, isLoading: isLoadingRollData } = api.statistics.getRollDistributionData.useQuery(
    { set: selectedSet, type: selectedType!, mainStat: selectedMainStat! },
    { enabled: !!selectedType && !!selectedMainStat },
  );

  const result =
    selectedSubstats.length > 0 && rollData
      ? calculateRollDistribution(rollData, selectedSubstats)
      : null;

  const chartData = result
    ? {
        labels: ['0 Rolls', '1 Roll', '2 Rolls', '3 Rolls', '4 Rolls', '5 Rolls'],
        datasets: [
          {
            type: 'bar' as const,
            label: '% of Artifacts',
            data: result.distribution.map(d => parseFloat(d.percentage.toFixed(2))),
            backgroundColor: '#667eea',
            borderWidth: 0,
            hoverBorderWidth: 2,
            hoverBorderColor: '#fff',
          },
          {
            type: 'line' as const,
            label: `All Substats Present (${result.appearancePercentage.toFixed(1)}%)`,
            data: Array(6).fill(parseFloat(result.appearancePercentage.toFixed(2))),
            borderColor: '#f5576c',
            borderWidth: 2,
            borderDash: [6, 4],
            pointRadius: 0,
            fill: false,
            tension: 0,
          },
        ],
      }
    : null;

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          padding: 20,
          color: '#9ca3af',
          font: { size: 12, weight: 'bold' as const },
        },
      },
      tooltip: {
        callbacks: {
          label: (context: any) => `${context.dataset.label}: ${(context.parsed.y as number).toFixed(2)}%`,
        },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        grid: { color: 'rgba(255, 255, 255, 0.1)' },
        ticks: {
          color: '#9ca3af',
          callback: (v: any) => `${v}%`,
        },
        title: { display: true, text: '% of Artifacts', color: '#9ca3af' },
      },
      x: {
        grid: { display: false },
        ticks: { color: '#9ca3af' },
        title: { display: true, text: 'Total Rolls into Selected Substats', color: '#9ca3af' },
      },
    },
  };

  if (isLoading) {
    return (
      <div className="flex h-[400px] flex-col items-center justify-center rounded-xl bg-slate-800/50 text-gray-400">
        <div className="mb-4 h-8 w-8 animate-spin rounded-full border-4 border-slate-600 border-t-yellow-500"></div>
        <p>Loading roll distribution data...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Step 1: Type */}
      <div className="space-y-2">
        <p className="text-sm font-medium text-gray-300 flex items-center gap-2">
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-blue-500/20 text-xs font-bold text-blue-300 border border-blue-500/30">1</span>
          Select Artifact Type:
        </p>
        <div className="flex flex-wrap gap-2 rounded-xl bg-slate-900 p-2 border border-slate-800">
          {uniqueTypes.map(type => (
            <button
              key={type}
              className={`flex-1 rounded-lg px-4 py-2.5 text-sm font-medium transition-all hover:scale-105 ${
                selectedType === type
                  ? 'bg-slate-700 text-white shadow-md'
                  : 'text-gray-400 hover:bg-slate-800 hover:text-gray-200'
              }`}
              onClick={() => handleTypeSelection(type)}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Step 2: Main Stat */}
      {selectedType && (
        <div className="space-y-2">
          <p className="text-sm font-medium text-gray-300 flex items-center gap-2">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-blue-500/20 text-xs font-bold text-blue-300 border border-blue-500/30">2</span>
            Select Main Stat for {selectedType}:
          </p>
          <div className="flex flex-wrap gap-2 rounded-xl bg-slate-900 p-2 border border-slate-800">
            {uniqueMainStats.map(mainStat => (
              <button
                key={mainStat}
                className={`flex-1 rounded-lg px-4 py-2 text-sm font-medium transition-all hover:scale-105 ${
                  selectedMainStat === mainStat
                    ? 'bg-slate-700 text-white shadow-md'
                    : 'text-gray-400 hover:bg-slate-800 hover:text-gray-200'
                }`}
                onClick={() => handleMainStatSelection(mainStat)}
              >
                {mainStat}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Step 3: Substats */}
      {selectedType && selectedMainStat && (
        <div className="space-y-2">
          <p className="text-sm font-medium text-gray-300 flex items-center gap-2">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-blue-500/20 text-xs font-bold text-blue-300 border border-blue-500/30">3</span>
            Select Substats to Monitor:
            <span className="text-xs text-gray-500">({selectedSubstats.length}/4 selected)</span>
          </p>
          <div className="flex flex-wrap gap-2 rounded-xl bg-slate-900 p-2 border border-slate-800">
            {availableSubstats.map(sub => {
              const isSelected = selectedSubstats.includes(sub);
              const isDisabled = !isSelected && selectedSubstats.length >= 4;
              return (
                <button
                  key={sub}
                  disabled={isDisabled}
                  className={`rounded-lg px-4 py-2 text-sm font-medium transition-all ${
                    isSelected
                      ? 'bg-yellow-600 text-white shadow-md'
                      : isDisabled
                      ? 'text-gray-600 cursor-not-allowed'
                      : 'text-gray-400 hover:bg-slate-800 hover:text-gray-200'
                  }`}
                  onClick={() => toggleSubstat(sub)}
                >
                  {sub}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Content */}
      {!selectedType || !selectedMainStat ? (
        <div className="flex h-64 flex-col items-center justify-center gap-4 rounded-xl bg-slate-800/50 border border-slate-700/50">
          <div className="text-center">
            <p className="text-lg font-medium text-gray-300">Select a Type and Main Stat</p>
            <p className="text-sm text-gray-400 mt-2">Choose artifact type and main stat above to begin</p>
          </div>
        </div>
      ) : !selectedSubstats.length ? (
        <div className="flex h-64 flex-col items-center justify-center gap-4 rounded-xl bg-slate-800/50 border border-slate-700/50">
          <div className="text-center">
            <p className="text-lg font-medium text-gray-300">Select at Least One Substat</p>
            <p className="text-sm text-gray-400 mt-2">Choose the substats you want to monitor above</p>
          </div>
        </div>
      ) : isLoadingRollData ? (
        <div className="flex h-64 flex-col items-center justify-center rounded-xl bg-slate-800/50 text-gray-400">
          <div className="mb-4 h-8 w-8 animate-spin rounded-full border-4 border-slate-600 border-t-yellow-500"></div>
          <p>Loading artifact data...</p>
        </div>
      ) : !result || result.totalArtifacts === 0 ? (
        <div className="flex h-64 flex-col items-center justify-center gap-4 rounded-xl bg-slate-800/50 border border-slate-700/50">
          <div className="text-center">
            <p className="text-lg font-medium text-gray-300">No Data Available</p>
            <p className="text-sm text-gray-400 mt-2">No leveled artifacts found for this type and main stat combination</p>
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-6 w-full">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Chart */}
            <div className="flex flex-col p-6 bg-slate-800/50 rounded-xl border border-slate-800 min-h-[420px]">
              <div className="mb-4 text-center">
                <h2 className="text-xl font-bold text-white">Roll Distribution</h2>
                <p className="text-xs text-gray-400 mt-1">
                  Monitoring: {selectedSubstats.join(', ')}
                </p>
              </div>
              <div className="flex-1 relative min-h-0">
                {chartData && <Bar data={chartData as any} options={chartOptions} />}
              </div>
            </div>

            {/* Table */}
            <div className="flex flex-col p-6 bg-slate-800/50 rounded-xl border border-slate-800 min-h-[420px]">
              <div className="mb-4 text-center">
                <h2 className="text-xl font-bold text-white">Distribution Counts</h2>
                <p className="text-xs text-gray-400 mt-1">
                  Drive Discs with chosen substats: {result.hasAllSubstatsCount} / {result.totalArtifacts} total
                </p>
              </div>
              <div className="flex-1">
                <table className="w-full text-sm text-left text-gray-300">
                  <thead className="text-xs text-gray-400 uppercase bg-slate-900/50 sticky top-0">
                    <tr>
                      <th className="px-4 py-3 rounded-tl-lg">Rolls into Substats</th>
                      <th className="px-4 py-3 text-right">Count</th>
                      <th className="px-4 py-3 rounded-tr-lg text-right">% of Total</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-700">
                    {result.distribution.map(row => (
                      <tr key={row.rolls} className="hover:bg-slate-700/50 transition-colors">
                        <td className="px-4 py-3 font-medium text-white">{row.rolls} Roll{row.rolls !== 1 ? 's' : ''}</td>
                        <td className="px-4 py-3 text-right tabular-nums">{row.count}</td>
                        <td className="px-4 py-3 text-right tabular-nums">{row.percentage.toFixed(2)}%</td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot className="bg-slate-900/50 font-semibold">
                    <tr>
                      <td className="px-4 py-3 rounded-bl-lg text-yellow-400">All Substats Present</td>
                      <td className="px-4 py-3 text-right tabular-nums text-yellow-400">{result.hasAllSubstatsCount}</td>
                      <td className="px-4 py-3 rounded-br-lg text-right tabular-nums text-yellow-400">{result.appearancePercentage.toFixed(2)}%</td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
