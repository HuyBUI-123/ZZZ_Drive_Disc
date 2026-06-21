
export const keysConfig = [
  ["sub_ATK_per", "roll_ATK_per", "added_ATK_per", '%ATK'],
  ["sub_HP_per", "roll_HP_per", "added_HP_per", '%HP'],
  ["sub_DEF_per", "roll_DEF_per", "added_DEF_per", '%DEF'],
  ["sub_ATK", "roll_ATK", "added_ATK", 'ATK'],
  ["sub_HP", "roll_HP", "added_HP", 'HP'],
  ["sub_DEF", "roll_DEF", "added_DEF", 'DEF'],
  ["sub_PEN", "roll_PEN", "added_PEN", 'PEN'],
  ["sub_AP", "roll_AP", "added_AP", 'AP'],
  ["sub_Crit_Rate", "roll_Crit_Rate", "added_Crit_Rate", 'Crit Rate'],
  ["sub_Crit_DMG", "roll_Crit_DMG", "added_Crit_DMG", 'Crit DMG'],
  [null, null, "added_None", "None"]
] as const;

/**
 * Creates mapping objects from keysConfig for different data transformations
 */
export const createMappings = () => {
  const substatKeyToMainStat: Record<string, string> = {};
  const levelingSubstatKeyToMainStat: Record<string, string> = {};
  const substatToLevelingKeys: Record<string, string> = {};
  const addedToMainStatKey: Record<string, string> = {};

  keysConfig.forEach(mapping => {
    const [subKey, rollKey, addedKey, value] = mapping;
    if (subKey) substatKeyToMainStat[subKey] = value;
    if (rollKey) levelingSubstatKeyToMainStat[rollKey] = value;
    if (subKey && rollKey) substatToLevelingKeys[subKey] = rollKey;
    if (addedKey) addedToMainStatKey[addedKey] = value;
  });

  return {
    substatKeyToMainStat,
    levelingSubstatKeyToMainStat,
    substatToLevelingKeys,
    addedToMainStatKey,
  };
};

// Define the type for the leveling data item based on the backend response
export interface LevelingDataItem {
  type: string | null;
  mainStat: string | null;
  TypeCount: number;
  substatCount: number;
  TotalRoll: number;
  [key: string]: any; // Allow dynamic access for sub_*, roll_*, added_* keys
}

/**
 * Calculates overall leveling statistics
 */
export const calculateLevelingOverall = (levelingData: LevelingDataItem[]) => {
  const mappings = createMappings();
  const {
    substatKeyToMainStat,
    levelingSubstatKeyToMainStat,
    substatToLevelingKeys,
    addedToMainStatKey,
  } = mappings;

  // Calculate substat totals
  const substatTotals = levelingData.reduce((acc, item) => {
    Object.keys(item).forEach(key => {
      if (key.startsWith('sub_') && item.mainStat !== substatKeyToMainStat[key]) {
        acc[key] = (acc[key] || 0) + (item[key] as number);
      }
    });
    return acc;
  }, {} as Record<string, number>);

  // Calculate total substat counts
  // This is the DIVISOR logic the user emphasized:
  // Sum of substatCount for all items EXCEPT where main_stat matches the substat being calculated
  const totalSubstatCounts = Object.keys(substatKeyToMainStat).reduce((acc, key) => {
    acc[key] = levelingData.reduce((sum, item) => {
      if (item.mainStat !== substatKeyToMainStat[key]) {
        return sum + item.substatCount;
      }
      return sum;
    }, 0);
    return acc;
  }, {} as Record<string, number>);

  // Calculate leveling counts (Rolls)
  const levelingCount = levelingData.reduce((acc, item) => {
    Object.keys(item).forEach(key => {
      if (key.startsWith('roll_') && item.mainStat !== levelingSubstatKeyToMainStat[key]) {
        acc[key] = (acc[key] || 0) + (item[key] as number);
      }
    });
    return acc;
  }, {} as Record<string, number>);

  // Calculate total leveling counts (Total Rolls)
  const totalLevelingCount = Object.keys(levelingSubstatKeyToMainStat).reduce((acc, key) => {
    acc[key] = levelingData.reduce((sum, item) => {
      if (item.mainStat !== levelingSubstatKeyToMainStat[key]) {
        return sum + item.TotalRoll;
      }
      return sum;
    }, 0);
    return acc;
  }, {} as Record<string, number>);

  // Create substat distribution
  const substatDistribution = Object.keys(substatTotals).map(key => {
    const rollKey = substatToLevelingKeys[key];
    const substatLabel = substatKeyToMainStat[key];
    
    const appearancePercentage = totalSubstatCounts[key] ? (substatTotals[key]! / totalSubstatCounts[key]!) * 100 : 0;
    const rollPercentage = (rollKey && totalLevelingCount[rollKey]) ? (levelingCount[rollKey]! / totalLevelingCount[rollKey]!) * 100 : 0;

    return {
      substat: substatLabel,
      appearancePercentage,
      rollPercentage,
      substatcount: substatTotals[key] ?? 0,
      rollcount: rollKey ? (levelingCount[rollKey] ?? 0) : 0,
    };
  }).sort((a, b) => b.appearancePercentage - a.appearancePercentage);

  // Calculate added substat distribution
  const addedSubstatDistribution = levelingData.reduce((acc, item) => {
    Object.keys(item).forEach(key => {
      if (key.startsWith('added_')) {
        acc[key] = (acc[key] || 0) + (item[key] as number);
      }
    });
    return acc;
  }, {} as Record<string, number>);

  const totalAdded = levelingData.reduce((acc, item) => {
    Object.keys(item).forEach(key => {
      if (key.startsWith('added_') && item.mainStat !== addedToMainStatKey[key]) {
         acc += (item[key] as number);
      }
    });
    return acc;
  }, 0);

  const addedSubstatData = Object.keys(addedSubstatDistribution).map(key => ({
    substat: addedToMainStatKey[key],
    percentage: totalAdded ? (addedSubstatDistribution[key]! / totalAdded) * 100 : 0,
    count: addedSubstatDistribution[key] ?? 0,
  })).sort((a, b) => b.count - a.count);

  return {
    substatDistribution,
    addedSubstatData,
  };
};

/**
 * Calculates specific leveling statistics for filtered data
 */
export const calculateLevelingSpecific = (levelingData: LevelingDataItem[], selectedType: string, selectedMainStat: string) => {
  const mappings = createMappings();
  const {
    substatKeyToMainStat,
    levelingSubstatKeyToMainStat,
    substatToLevelingKeys,
    addedToMainStatKey,
  } = mappings;

  const filteredLevelingData = levelingData.filter(
    item => item.type === selectedType && item.mainStat === selectedMainStat
  );

  // Calculate substat totals for filtered data
  const substatTotals = filteredLevelingData.reduce((acc, item) => {
    Object.keys(item).forEach(key => {
      if (key.startsWith('sub_')) {
         acc[key] = (acc[key] || 0) + (item[key] as number);
      }
    });
    return acc;
  }, {} as Record<string, number>);

  // Calculate total substat counts for filtered data
  const totalSubstatCounts = Object.keys(substatKeyToMainStat).reduce((acc, key) => {
    acc[key] = filteredLevelingData.reduce((sum, item) => {
      return sum + item.substatCount;
    }, 0);
    return acc;
  }, {} as Record<string, number>);

  // Calculate leveling counts for filtered data
  const levelingCount = filteredLevelingData.reduce((acc, item) => {
    Object.keys(item).forEach(key => {
      if (key.startsWith('roll_')) {
        acc[key] = (acc[key] || 0) + (item[key] as number);
      }
    });
    return acc;
  }, {} as Record<string, number>);

  // Calculate total leveling counts for filtered data
  const totalLevelingCount = Object.keys(levelingSubstatKeyToMainStat).reduce((acc, key) => {
    acc[key] = filteredLevelingData.reduce((sum, item) => {
      return sum + item.TotalRoll;
    }, 0);
    return acc;
  }, {} as Record<string, number>);

  // Create substat distribution for filtered data
  const substatDistribution = Object.keys(substatTotals).map(key => {
    const rollKey = substatToLevelingKeys[key];
    const substatLabel = substatKeyToMainStat[key];
    
    return {
      substat: substatLabel,
      appearancePercentage: totalSubstatCounts[key] ? (substatTotals[key]! / totalSubstatCounts[key]!) * 100 : 0,
      rollPercentage: (rollKey && totalLevelingCount[rollKey]) ? (levelingCount[rollKey]! / totalLevelingCount[rollKey]!) * 100 : 0,
      substatcount: substatTotals[key] ?? 0,
      rollcount: rollKey ? (levelingCount[rollKey] ?? 0) : 0,
    };
  }).sort((a, b) => b.appearancePercentage - a.appearancePercentage);

  // Calculate added substat distribution for filtered data
  const addedSubstatDistribution = filteredLevelingData.reduce((acc, item) => {
    Object.keys(item).forEach(key => {
      if (key.startsWith('added_')) {
        acc[key] = (acc[key] || 0) + (item[key] as number);
      }
    });
    return acc;
  }, {} as Record<string, number>);

  const totalAdded = filteredLevelingData.reduce((acc, item) => {
    Object.keys(item).forEach(key => {
      if (key.startsWith('added_') && item.mainStat !== addedToMainStatKey[key]) {
         acc += (item[key] as number);
      }
    });
    return acc;
  }, 0);

  const addedSubstatData = Object.keys(addedSubstatDistribution).map(key => ({
    substat: addedToMainStatKey[key],
    percentage: totalAdded ? (addedSubstatDistribution[key]! / totalAdded) * 100 : 0,
    count: addedSubstatDistribution[key] ?? 0,
  })).sort((a, b) => b.count - a.count);

  return {
    substatDistribution,
    addedSubstatData,
  };
};

/**
 * Gets unique types from leveling data
 */
export const getUniqueTypes = (levelingData: LevelingDataItem[]) => {
  return levelingData
    .map(item => item.type)
    .filter((value, index, self) => value && self.indexOf(value) === index) as string[];
};

/**
 * Gets unique main stats for a specific type from leveling data
 */
export const getUniqueMainStats = (levelingData: LevelingDataItem[], selectedType: string) => {
  return levelingData
    .filter(item => item.type === selectedType)
    .map(item => item.mainStat)
    .filter((value, index, self) => value && self.indexOf(value) === index) as string[];
};

export interface ArtifactRollDataItem {
  hp: number | null;
  atk: number | null;
  def: number | null;
  percentHP: number | null;
  percentATK: number | null;
  percentDEF: number | null;
  pen: number | null;
  ap: number | null;
  critRate: number | null;
  critDMG: number | null;
  lHP: number | null;
  lATK: number | null;
  lDEF: number | null;
  lPercentHP: number | null;
  lPercentATK: number | null;
  lPercentDEF: number | null;
  lPEN: number | null;
  lAP: number | null;
  lCritRate: number | null;
  lCritDMG: number | null;
  addedSubstat: string | null;
}

type ArtifactPresenceKey = 'hp' | 'atk' | 'def' | 'percentHP' | 'percentATK' | 'percentDEF' | 'pen' | 'ap' | 'critRate' | 'critDMG';
type ArtifactRollKey = 'lHP' | 'lATK' | 'lDEF' | 'lPercentHP' | 'lPercentATK' | 'lPercentDEF' | 'lPEN' | 'lAP' | 'lCritRate' | 'lCritDMG';

const SUBSTAT_TO_PRESENCE_KEY: Record<string, ArtifactPresenceKey> = {
  'HP': 'hp',
  'ATK': 'atk',
  'DEF': 'def',
  '%HP': 'percentHP',
  '%ATK': 'percentATK',
  '%DEF': 'percentDEF',
  'PEN': 'pen',
  'AP': 'ap',
  'Crit Rate': 'critRate',
  'Crit DMG': 'critDMG',
};

const SUBSTAT_TO_ROLL_KEY: Record<string, ArtifactRollKey> = {
  'HP': 'lHP',
  'ATK': 'lATK',
  'DEF': 'lDEF',
  '%HP': 'lPercentHP',
  '%ATK': 'lPercentATK',
  '%DEF': 'lPercentDEF',
  'PEN': 'lPEN',
  'AP': 'lAP',
  'Crit Rate': 'lCritRate',
  'Crit DMG': 'lCritDMG',
};

export interface RollDistributionBucket {
  rolls: number;
  count: number;
  percentage: number;
}

export interface RollDistributionResult {
  distribution: RollDistributionBucket[];
  appearancePercentage: number;
  totalArtifacts: number;
  hasAllSubstatsCount: number;
}

export const calculateRollDistribution = (
  artifactData: ArtifactRollDataItem[],
  selectedSubstats: string[],
): RollDistributionResult => {
  const empty: RollDistributionResult = {
    distribution: [0, 1, 2, 3, 4, 5].map(rolls => ({ rolls, count: 0, percentage: 0 })),
    appearancePercentage: 0,
    totalArtifacts: artifactData.length,
    hasAllSubstatsCount: 0,
  };

  if (!selectedSubstats.length || !artifactData.length) return empty;

  const buckets: Record<number, number> = { 0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
  let hasAllSubstatsCount = 0;
  const total = artifactData.length;

  const artifactHasSubstat = (artifact: ArtifactRollDataItem, sub: string): boolean => {
    const presenceKey = SUBSTAT_TO_PRESENCE_KEY[sub];
    return (
      (presenceKey !== undefined && (artifact[presenceKey] ?? 0) === 1) ||
      artifact.addedSubstat === sub
    );
  };


  for (const artifact of artifactData) {
    const hasAllChosen = selectedSubstats.every(sub => artifactHasSubstat(artifact, sub));
    if (!hasAllChosen) continue;

    hasAllSubstatsCount++;

    const totalRolls = selectedSubstats.reduce((sum, sub) => {
      const key = SUBSTAT_TO_ROLL_KEY[sub];
      return sum + (key !== undefined ? (artifact[key] ?? 0) : 0);
    }, 0);

    if (totalRolls >= 0 && totalRolls <= 5) {
      buckets[totalRolls] = (buckets[totalRolls] ?? 0) + 1;
    }
  }

  return {
    distribution: [0, 1, 2, 3, 4, 5].map(rolls => ({
      rolls,
      count: buckets[rolls] ?? 0,
      percentage: hasAllSubstatsCount > 0 ? ((buckets[rolls] ?? 0) / hasAllSubstatsCount) * 100 : 0,
    })),
    appearancePercentage: total > 0 ? (hasAllSubstatsCount / total) * 100 : 0,
    totalArtifacts: total,
    hasAllSubstatsCount,
  };
};


// Re-export existing functions if needed, or just rely on these new ones.
// The existing functions were for Substats section. I should probably keep them or adapt them.
// For now, I'll add the Substat functions back in to avoid breaking the Substat section.

// Mapping from database column keys to display labels
const SUBSTAT_KEY_TO_LABEL: Record<string, string> = {
  sub_ATK_per: "%ATK",
  sub_HP_per: "%HP",
  sub_DEF_per: "%DEF",
  sub_ATK: "ATK",
  sub_HP: "HP",
  sub_DEF: "DEF",
  sub_PEN: "PEN",
  sub_AP: "AP",
  sub_Crit_Rate: "Crit Rate",
  sub_Crit_DMG: "Crit DMG",
};

/**
 * Calculates overall substat statistics
 */
export const calculateSubstatOverall = (substatData: any[]) => {
  // Initialize totals
  const substatTotals: Record<string, number> = {};
  const totalSubstatCounts: Record<string, number> = {};

  // Initialize with 0
  Object.keys(SUBSTAT_KEY_TO_LABEL).forEach(key => {
    substatTotals[key] = 0;
    totalSubstatCounts[key] = 0;
  });

  substatData.forEach(item => {
    Object.keys(SUBSTAT_KEY_TO_LABEL).forEach(key => {
      const label = SUBSTAT_KEY_TO_LABEL[key];
      
      // Only count if this substat is NOT the main stat
      if (item.mainStat !== label) {
        // Add the count of this substat
        substatTotals[key] = (substatTotals[key] || 0) + (item[key] || 0);
        
        // Add to the total possible pool (total artifacts that COULD have this substat)
        // i.e., artifacts where this is not the main stat
        totalSubstatCounts[key] = (totalSubstatCounts[key] || 0) + (item.artifactCount || 0);
      }
    });
  });

  return Object.keys(substatTotals).map(key => ({
    substat: SUBSTAT_KEY_TO_LABEL[key] ?? key,
    percentage: (totalSubstatCounts[key] ?? 0) > 0 
      ? ((substatTotals[key] ?? 0) / (totalSubstatCounts[key] ?? 1)) * 100 
      : 0,
    count: substatTotals[key] ?? 0,
  }));
};

/**
 * Calculates specific substat statistics for selected type and main stat
 */
export const calculateSubstatSpecific = (
  substatData: any[], 
  selectedType: string | null, 
  selectedMainStat: string | null
) => {
  if (!selectedType || !selectedMainStat) return [];

  const data = substatData.find(
    item => item.type === selectedType && item.mainStat === selectedMainStat
  );

  if (!data) {
    return [];
  }

  return Object.keys(SUBSTAT_KEY_TO_LABEL).map(key => {
    const label = SUBSTAT_KEY_TO_LABEL[key]!;
    // If the substat is the same as the main stat, it can't exist as a substat
    if (label === selectedMainStat) return null;

    return {
      substat: label,
      percentage: data.substatCount > 0 
        ? ((data[key] as number) / data.substatCount) * 100 
        : 0,
      count: data[key] as number,
    };
  }).filter((item): item is { substat: string; percentage: number; count: number } => item !== null);
};
