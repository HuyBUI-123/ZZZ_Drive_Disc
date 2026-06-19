"use client";

import React, { useState } from 'react';
import Select, { type CSSObjectWithLabel } from 'react-select';
import { api } from "~/trpc/react";
import { MainStatSection } from './_components/MainStatSection';
import { SubstatSection } from './_components/SubstatSection';
import { LevelingSection } from './_components/LevelingSection';
import { RollDistributionSection } from './_components/RollDistributionSection';

const customStyles = {
  control: (provided: CSSObjectWithLabel) => ({
    ...provided,
    backgroundColor: "#1f2937", // bg-gray-800
    borderColor: "#374151", // border-gray-700
    color: "white",
    minHeight: "42px",
  }),
  menu: (provided: CSSObjectWithLabel) => ({
    ...provided,
    backgroundColor: "#1f2937",
    zIndex: 9999,
  }),
  option: (provided: CSSObjectWithLabel, state: { isFocused: boolean }) => ({
    ...provided,
    backgroundColor: state.isFocused ? "#374151" : "#1f2937",
    color: "white",
  }),
  singleValue: (provided: CSSObjectWithLabel) => ({
    ...provided,
    color: "white",
  }),
  input: (provided: CSSObjectWithLabel) => ({
    ...provided,
    color: "white",
  }),
  placeholder: (provided: CSSObjectWithLabel) => ({
    ...provided,
    color: "#9ca3af",
  }),
};

export default function StatisticsPage() {
  const [selectedCategory, setSelectedCategory] = useState('Main Stat');
  const [selectedSet, setSelectedSet] = useState<string | null>(null);
  const [showGuide, setShowGuide] = useState(false);

  
  // Main Stat State
  const [selectedMainStatChart, setSelectedMainStatChart] = useState('Types');

  // Substat State
  const [selectedSubstatChart, setSelectedSubstatChart] = useState('Overall');

  // Data Fetching
  const { data: availableSets } = api.statistics.getAvailableSets.useQuery();
  
  const { data: mainStatData, isLoading: isLoadingMainStats } = api.statistics.getMainStats.useQuery(
    { set: selectedSet },
    { enabled: selectedCategory === 'Main Stat' }
  );

  const { data: substatData, isLoading: isLoadingSubstats } = api.statistics.getSubstats.useQuery(
    { set: selectedSet },
    { enabled: selectedCategory === 'Substats' }
  );

  // We also need mainStatData for the "Specific" tab in Substats section to populate dropdowns
  // So we should fetch it if we are in Substats section too
  const { data: mainStatDataForSubstats } = api.statistics.getMainStats.useQuery(
    { set: selectedSet },
    { enabled: selectedCategory === 'Substats' }
  );

  const { data: levelingData, isLoading: isLoadingLeveling } = api.statistics.getLevelingStats.useQuery(
    { set: selectedSet },
    { enabled: selectedCategory === 'Leveling' || selectedCategory === 'Roll Distribution' }
  );

  const renderContent = () => {
    switch (selectedCategory) {
      case 'Main Stat':
        return (
          <MainStatSection
            selectedChart={selectedMainStatChart}
            setSelectedChart={setSelectedMainStatChart}
            typeData={mainStatData?.typePercentages ?? []}
            mainStatData={mainStatData?.mainStatPercentages ?? []}
            isLoading={isLoadingMainStats}
          />
        );
      case 'Substats':
        return (
          <SubstatSection
            selectedSubstatChart={selectedSubstatChart}
            setSelectedSubstatChart={setSelectedSubstatChart}
            substatData={substatData ?? []}
            typeData={mainStatDataForSubstats?.typePercentages ?? []}
            mainStatData={mainStatDataForSubstats?.mainStatPercentages ?? []}
            isLoading={isLoadingSubstats}
          />
        );
      case 'Leveling':
        return (
          <LevelingSection
            levelingData={levelingData ?? []}
            isLoading={isLoadingLeveling}
          />
        );
      case 'Roll Distribution':
        return (
          <RollDistributionSection
            levelingData={levelingData ?? []}
            selectedSet={selectedSet}
            isLoading={isLoadingLeveling}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen p-8 pt-8">
      <div className="container mx-auto max-w-7xl space-y-8">
        {/* Header */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-2">
              <h1 className="text-4xl font-bold text-white">Drive Disc Statistics</h1>
              <p className="text-lg text-gray-400">Explore comprehensive data insights and patterns</p>
            </div>
            <button
              onClick={() => setShowGuide(!showGuide)}
              className="flex items-center gap-2 rounded-lg bg-blue-600/20 px-4 py-2 text-sm font-medium text-blue-400 transition-all hover:bg-blue-600/30 hover:text-blue-300 border border-blue-600/30"
            >
              
              <span>{showGuide ? 'Hide Guide' : 'Show Guide'}</span>
            </button>
          </div>

          {/* Guide Section */}
          {showGuide && (
            <div className="rounded-xl bg-gradient-to-br from-blue-900/30 to-purple-900/30 p-6 border border-blue-800/50 backdrop-blur-sm">
              <h3 className="mb-4 text-xl font-semibold text-white flex items-center gap-2">
                
                How to Use Statistics
              </h3>
              <div className="grid gap-4 md:grid-cols-3">
                <div className="rounded-lg bg-slate-800/50 p-4 border border-slate-700">
                  <h4 className="mb-2 font-semibold text-yellow-400">Main Stat</h4>
                  <p className="text-sm text-gray-300">
                    View distribution of Drive Discs Slot and their main stats distribution. Click tabs to switch between different views.
                  </p>
                </div>
                <div className="rounded-lg bg-slate-800/50 p-4 border border-slate-700">
                  <h4 className="mb-2 font-semibold text-yellow-400">Substats</h4>
                  <p className="text-sm text-gray-300">
                    Analyze substat distributions. Use <strong>Overall</strong> for general stats or <strong>Specific</strong> to filter by slot and main stat.
                  </p>
                </div>
                <div className="rounded-lg bg-slate-800/50 p-4 border border-slate-700">
                  <h4 className="mb-2 font-semibold text-yellow-400">Leveling</h4>
                  <p className="text-sm text-gray-300">
                    Track which substats appear and get upgraded during leveling. Choose <strong>Overall</strong> or drill down with <strong>Specific</strong>.
                  </p>
                </div>
              </div>
              <div className="mt-4 rounded-lg bg-green-900/20 p-3 border border-green-700/30">
                <p className="text-sm text-green-300">
                  💡 <strong>Tip:</strong> Use the "Filter by Drive Disc Set" dropdown to focus on specific drive disc sets, or leave it empty to see data across all sets.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Controls */}
        <div className="flex flex-col gap-6 rounded-xl bg-slate-900 p-6 shadow-lg border border-slate-800 lg:flex-row lg:items-center lg:justify-between">
          {/* Category Tabs */}
          <div className="flex flex-wrap gap-2">
            {[
              { id: 'Main Stat' },
              { id: 'Substats' },
              { id: 'Leveling' },
              { id: 'Roll Distribution' },
            ].map((category) => (
              <button
                key={category.id}
                onClick={() => setSelectedCategory(category.id)}
                className={`flex items-center gap-2 rounded-lg px-6 py-3 font-medium transition-all ${
                  selectedCategory === category.id
                    ? 'bg-yellow-600 text-white shadow-lg shadow-yellow-600/20'
                    : 'bg-slate-800 text-gray-400 hover:bg-slate-700 hover:text-white'
                }`}
              >
                
                <span>{category.id}</span>
              </button>
            ))}
          </div>

          {/* Set Filter */}
          <div className="w-full lg:w-80">
            <label className="mb-2 flex items-center gap-2 text-sm font-medium text-gray-400">
              Filter by Drive Disc Set
              <span className="text-xs text-gray-500">(Optional)</span>
            </label>
            <Select
              instanceId="set-select"
              options={availableSets?.map((set) => ({ value: set, label: set })) ?? []}
              value={selectedSet ? { value: selectedSet, label: selectedSet } : null}
              onChange={(option) => setSelectedSet(option?.value ?? null)}
              styles={customStyles}
              placeholder="All Sets"
              isClearable
            />
          </div>
        </div>

        {/* Content Area */}
        <div className="min-h-[500px]">
          {renderContent()}
        </div>
      </div>
    </div>
  );
}
