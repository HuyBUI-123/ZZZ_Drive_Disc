import { z } from "zod";
import { createTRPCRouter, protectedProcedure } from "~/server/api/trpc";
import { artifactItself, artifactLeveling } from "~/server/db/schema";
import { and, eq, sql } from "drizzle-orm";

export const statisticsRouter = createTRPCRouter({
  getMainStats: protectedProcedure
    .input(
      z.object({
        set: z.string().nullable().optional(),
      }),
    )
    .query(async ({ ctx, input }) => {
      const conditions = [eq(artifactItself.userId, ctx.session.user.id)];
      if (input.set) {
        conditions.push(eq(artifactItself.set, input.set));
      }

      // 1. Get Type Distribution
      const typeStats = await ctx.db
        .select({
          type: artifactItself.type,
          count: sql<number>`count(*)`.mapWith(Number),
        })
        .from(artifactItself)
        .where(and(...conditions))
        .groupBy(artifactItself.type);

      const totalArtifacts = typeStats.reduce((acc, curr) => acc + curr.count, 0);
      
      const typePercentages = typeStats.map((stat) => ({
        substat: stat.type, // Using 'substat' key to match frontend expectation for label
        count: stat.count,
        percentage: totalArtifacts > 0 ? (stat.count / totalArtifacts) * 100 : 0,
      }));

      // 2. Get Main Stat Distribution (grouped by Type and MainStat)
      const mainStats = await ctx.db
        .select({
          type: artifactItself.type,
          mainStat: artifactItself.mainStat,
          count: sql<number>`count(*)`.mapWith(Number),
        })
        .from(artifactItself)
        .where(and(...conditions))
        .groupBy(artifactItself.type, artifactItself.mainStat);

      // We need to calculate percentages relative to the total count of that specific TYPE
      // But the original code seemed to calculate percentage relative to the specific type group?
      // Let's look at the original SQL:
      // SELECT "Type", "Main_Stat", COUNT(*) * 100.0 / (SELECT COUNT(*) FROM "Artifact_itself" WHERE "Type" = t."Type")
      
      // So we need the total count per type to calculate the percentage correctly.
      const countByType: Record<string, number> = {};
      typeStats.forEach(t => {
        if (t.type) countByType[t.type] = t.count;
      });

      const mainStatPercentages = mainStats.map((stat) => {
        const typeTotal = stat.type ? countByType[stat.type] || 0 : 0;
        return {
          type: stat.type,
          substat: stat.mainStat, // Using 'substat' key for label
          count: stat.count,
          percentage: typeTotal > 0 ? (stat.count / typeTotal) * 100 : 0,
        };
      });

      return {
        typePercentages,
        mainStatPercentages,
      };
    }),

  getSubstats: protectedProcedure
    .input(
      z.object({
        set: z.string().nullable().optional(),
      }),
    )
    .query(async ({ ctx, input }) => {
      const conditions = [eq(artifactItself.userId, ctx.session.user.id)];
      if (input.set) {
        conditions.push(eq(artifactItself.set, input.set));
      }

      // We need to aggregate substat counts grouped by Type and MainStat
      // The original SQL query summed up the boolean flags (0 or 1) for each substat
      // In our schema, we have integer columns for substats (0 or 1)
      
      const result = await ctx.db
        .select({
          type: artifactItself.type,
          mainStat: artifactItself.mainStat,
          artifactCount: sql<number>`count(*)`.mapWith(Number),
          
          // Summing up the presence of each substat
          sub_ATK_per: sql<number>`sum(${artifactItself.percentATK})`.mapWith(Number),
          sub_HP_per: sql<number>`sum(${artifactItself.percentHP})`.mapWith(Number),
          sub_DEF_per: sql<number>`sum(${artifactItself.percentDEF})`.mapWith(Number),
          sub_ATK: sql<number>`sum(${artifactItself.atk})`.mapWith(Number),
          sub_HP: sql<number>`sum(${artifactItself.hp})`.mapWith(Number),
          sub_DEF: sql<number>`sum(${artifactItself.def})`.mapWith(Number),
          sub_PEN: sql<number>`sum(${artifactItself.pen})`.mapWith(Number),
          sub_AP: sql<number>`sum(${artifactItself.ap})`.mapWith(Number),
          sub_Crit_Rate: sql<number>`sum(${artifactItself.critRate})`.mapWith(Number),
          sub_Crit_DMG: sql<number>`sum(${artifactItself.critDMG})`.mapWith(Number),
          
          // Total count of all substats combined
          substatCount: sql<number>`sum(
            ${artifactItself.percentATK} + ${artifactItself.percentHP} + ${artifactItself.percentDEF} + 
            ${artifactItself.atk} + ${artifactItself.hp} + ${artifactItself.def} + 
            ${artifactItself.pen} + ${artifactItself.ap} + 
            ${artifactItself.critRate} + ${artifactItself.critDMG}
          )`.mapWith(Number),
        })
        .from(artifactItself)
        .where(and(...conditions))
        .groupBy(artifactItself.type, artifactItself.mainStat);

      return result;
    }),

  getLevelingStats: protectedProcedure
    .input(
      z.object({
        set: z.string().nullable().optional(),
      }),
    )
    .query(async ({ ctx, input }) => {
      const conditions = [eq(artifactItself.userId, ctx.session.user.id)];
      if (input.set) {
        conditions.push(eq(artifactItself.set, input.set));
      }

      const result = await ctx.db
        .select({
          type: artifactItself.type,
          mainStat: artifactItself.mainStat,
          TypeCount: sql<number>`count(*)`.mapWith(Number),
          
          // Substat Presence (from artifactItself)
          sub_ATK_per: sql<number>`sum(${artifactItself.percentATK})`.mapWith(Number),
          sub_HP_per: sql<number>`sum(${artifactItself.percentHP})`.mapWith(Number),
          sub_DEF_per: sql<number>`sum(${artifactItself.percentDEF})`.mapWith(Number),
          sub_ATK: sql<number>`sum(${artifactItself.atk})`.mapWith(Number),
          sub_HP: sql<number>`sum(${artifactItself.hp})`.mapWith(Number),
          sub_DEF: sql<number>`sum(${artifactItself.def})`.mapWith(Number),
          sub_PEN: sql<number>`sum(${artifactItself.pen})`.mapWith(Number),
          sub_AP: sql<number>`sum(${artifactItself.ap})`.mapWith(Number),
          sub_Crit_Rate: sql<number>`sum(${artifactItself.critRate})`.mapWith(Number),
          sub_Crit_DMG: sql<number>`sum(${artifactItself.critDMG})`.mapWith(Number),
          
          substatCount: sql<number>`sum(
            ${artifactItself.percentATK} + ${artifactItself.percentHP} + ${artifactItself.percentDEF} + 
            ${artifactItself.atk} + ${artifactItself.hp} + ${artifactItself.def} + 
            ${artifactItself.pen} + ${artifactItself.ap} + 
            ${artifactItself.critRate} + ${artifactItself.critDMG}
          )`.mapWith(Number),

          // Roll Counts (from artifactLeveling)
          roll_HP: sql<number>`sum(${artifactLeveling.lHP})`.mapWith(Number),
          roll_ATK: sql<number>`sum(${artifactLeveling.lATK})`.mapWith(Number),
          roll_DEF: sql<number>`sum(${artifactLeveling.lDEF})`.mapWith(Number),
          roll_HP_per: sql<number>`sum(${artifactLeveling.lPercentHP})`.mapWith(Number),
          roll_ATK_per: sql<number>`sum(${artifactLeveling.lPercentATK})`.mapWith(Number),
          roll_DEF_per: sql<number>`sum(${artifactLeveling.lPercentDEF})`.mapWith(Number),
          roll_AP: sql<number>`sum(${artifactLeveling.lAP})`.mapWith(Number),
          roll_PEN: sql<number>`sum(${artifactLeveling.lPEN})`.mapWith(Number),
          roll_Crit_Rate: sql<number>`sum(${artifactLeveling.lCritRate})`.mapWith(Number),
          roll_Crit_DMG: sql<number>`sum(${artifactLeveling.lCritDMG})`.mapWith(Number),

          TotalRoll: sql<number>`sum(
            ${artifactLeveling.lHP} + ${artifactLeveling.lATK} + ${artifactLeveling.lDEF} + 
            ${artifactLeveling.lPercentHP} + ${artifactLeveling.lPercentATK} + ${artifactLeveling.lPercentDEF} + 
            ${artifactLeveling.lAP} + ${artifactLeveling.lPEN} + 
            ${artifactLeveling.lCritRate} + ${artifactLeveling.lCritDMG}
          )`.mapWith(Number),

          // Added Substats
          added_ATK: sql<number>`sum(case when ${artifactLeveling.addedSubstat} = 'ATK' then 1 else 0 end)`.mapWith(Number),
          added_DEF: sql<number>`sum(case when ${artifactLeveling.addedSubstat} = 'DEF' then 1 else 0 end)`.mapWith(Number),
          added_HP: sql<number>`sum(case when ${artifactLeveling.addedSubstat} = 'HP' then 1 else 0 end)`.mapWith(Number),
          added_ATK_per: sql<number>`sum(case when ${artifactLeveling.addedSubstat} = '%ATK' then 1 else 0 end)`.mapWith(Number),
          added_DEF_per: sql<number>`sum(case when ${artifactLeveling.addedSubstat} = '%DEF' then 1 else 0 end)`.mapWith(Number),
          added_HP_per: sql<number>`sum(case when ${artifactLeveling.addedSubstat} = '%HP' then 1 else 0 end)`.mapWith(Number),
          added_PEN: sql<number>`sum(case when ${artifactLeveling.addedSubstat} = 'PEN' then 1 else 0 end)`.mapWith(Number),
          added_AP: sql<number>`sum(case when ${artifactLeveling.addedSubstat} = 'AP' then 1 else 0 end)`.mapWith(Number),
          added_Crit_Rate: sql<number>`sum(case when ${artifactLeveling.addedSubstat} = 'Crit Rate' then 1 else 0 end)`.mapWith(Number),
          added_Crit_DMG: sql<number>`sum(case when ${artifactLeveling.addedSubstat} = 'Crit DMG' then 1 else 0 end)`.mapWith(Number),
          added_None: sql<number>`sum(case when ${artifactLeveling.addedSubstat} = 'None' then 1 else 0 end)`.mapWith(Number),
        })
        .from(artifactLeveling)
        .innerJoin(artifactItself, eq(artifactLeveling.id, artifactItself.id))
        .where(and(...conditions))
        .groupBy(artifactItself.type, artifactItself.mainStat);

      return result;
    }),
  
  getRollDistributionData: protectedProcedure
    .input(
      z.object({
        set: z.string().nullable().optional(),
        type: z.string(),
        mainStat: z.string(),
      }),
    )
    .query(async ({ ctx, input }) => {
      const conditions = [
        eq(artifactItself.userId, ctx.session.user.id),
        eq(artifactItself.type, input.type),
        eq(artifactItself.mainStat, input.mainStat),
      ];
      if (input.set) {
        conditions.push(eq(artifactItself.set, input.set));
      }

      return await ctx.db
        .select({
          hp: artifactItself.hp,
          atk: artifactItself.atk,
          def: artifactItself.def,
          percentHP: artifactItself.percentHP,
          percentATK: artifactItself.percentATK,
          percentDEF: artifactItself.percentDEF,
          pen: artifactItself.pen,
          ap: artifactItself.ap,
          critRate: artifactItself.critRate,
          critDMG: artifactItself.critDMG,
          lHP: artifactLeveling.lHP,
          lATK: artifactLeveling.lATK,
          lDEF: artifactLeveling.lDEF,
          lPercentHP: artifactLeveling.lPercentHP,
          lPercentATK: artifactLeveling.lPercentATK,
          lPercentDEF: artifactLeveling.lPercentDEF,
          lAP: artifactLeveling.lAP,
          lPEN: artifactLeveling.lPEN,
          lCritRate: artifactLeveling.lCritRate,
          lCritDMG: artifactLeveling.lCritDMG,
          addedSubstat: artifactLeveling.addedSubstat,
        })
        .from(artifactLeveling)
        .innerJoin(artifactItself, eq(artifactLeveling.id, artifactItself.id))
        .where(and(...conditions));
    }),

  getAvailableSets: protectedProcedure.query(async ({ ctx }) => {
    const sets = await ctx.db
      .selectDistinct({ set: artifactItself.set })
      .from(artifactItself)
      .where(eq(artifactItself.userId, ctx.session.user.id))
      .orderBy(artifactItself.set);
      
    return sets
      .map((s) => s.set)
      .filter((s): s is string => s !== null);
  }),
});
