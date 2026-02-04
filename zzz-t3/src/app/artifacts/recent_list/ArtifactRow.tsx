"use client";

import React, { useState } from "react";
import { type RouterOutputs } from "~/trpc/react";
import { EditArtifactModal } from "./EditArtifactModal";
import { LevelArtifactModal } from "./LevelArtifactModal";

type Artifact = RouterOutputs["artifact"]["getAll"]["artifacts"][number];

interface ArtifactRowProps {
  artifact: Artifact;
  onRefresh: () => void;
}

export function ArtifactRow({ artifact, onRefresh }: ArtifactRowProps) {
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isLevelingModalOpen, setIsLevelingModalOpen] = useState(false);

  const hasLevelingData = artifact.leveling;

  const renderCheckbox = (value: number | null) => (
    <div className="flex justify-center">
      <span className={`text-lg font-bold ${value === 1 ? "text-green-500" : "text-transparent"}`}>
        {value === 1 ? "✓" : "·"}
      </span>
    </div>
  );

  return (
    <>
      <tr className="border-b border-slate-800 hover:bg-slate-800/50 transition-colors">
        <td className="p-3 font-medium text-white">{artifact.set}</td>
        <td className="p-3 text-gray-300">{artifact.type}</td>
        <td className="p-3 text-yellow-500 font-medium">{artifact.mainStat}</td>
        <td className="p-3 text-center text-gray-300">{artifact.numberOfSubstat}</td>
        <td className="p-3">{renderCheckbox(artifact.percentATK)}</td>
        <td className="p-3">{renderCheckbox(artifact.percentHP)}</td>
        <td className="p-3">{renderCheckbox(artifact.percentDEF)}</td>
        <td className="p-3">{renderCheckbox(artifact.atk)}</td>
        <td className="p-3">{renderCheckbox(artifact.hp)}</td>
        <td className="p-3">{renderCheckbox(artifact.def)}</td>
        <td className="p-3">{renderCheckbox(artifact.pen)}</td>
        <td className="p-3">{renderCheckbox(artifact.ap)}</td>
        <td className="p-3">{renderCheckbox(artifact.critRate)}</td>
        <td className="p-3">{renderCheckbox(artifact.critDMG)}</td>
        <td className="p-3 text-gray-400">{artifact.whereGotIt}</td>
        <td className="p-3">
          <span className={`rounded px-2 py-1 text-xs font-bold ${
            artifact.score === "Marvelous" ? "bg-yellow-500/20 text-yellow-400" :
            artifact.score === "Excellent" ? "bg-purple-500/20 text-purple-400" :
            artifact.score === "Good" ? "bg-blue-500/20 text-blue-400" :
            artifact.score === "Usable" ? "bg-green-500/20 text-green-400" :
            artifact.score === "Trash" ? "bg-red-500/20 text-red-400" :
            artifact.score === "Complete trash" ? "bg-red-950/40 text-red-500" :
            "bg-gray-700 text-gray-400"
          }`}>
            {artifact.score}
          </span>
        </td>
        <td className="p-3">
          <div className="flex gap-2">
            {hasLevelingData ? (
              <button
                onClick={() => setIsLevelingModalOpen(true)}
                className="flex items-center gap-1 rounded bg-blue-600/20 px-3 py-1.5 text-sm font-medium text-blue-400 hover:bg-blue-600/30 transition-colors"
              >
                Change
              </button>
            ) : (
              <>
                <button
                  onClick={() => setIsEditModalOpen(true)}
                  className="flex items-center gap-1 rounded bg-slate-700 px-3 py-1.5 text-sm font-medium text-gray-300 hover:bg-slate-600 transition-colors"
                >
                  Edit
                </button>
                <button
                  onClick={() => setIsLevelingModalOpen(true)}
                  className="flex items-center gap-1 rounded bg-green-600/20 px-3 py-1.5 text-sm font-medium text-green-400 hover:bg-green-600/30 transition-colors"
                >
                  Level
                </button>
              </>
            )}
          </div>
        </td>
      </tr>

      {isEditModalOpen && (
        <EditArtifactModal
          artifact={artifact}
          onClose={() => setIsEditModalOpen(false)}
          onUpdateSuccess={onRefresh}
        />
      )}

      {isLevelingModalOpen && (
        <LevelArtifactModal
          artifact={artifact}
          onClose={() => setIsLevelingModalOpen(false)}
          onUpdateSuccess={onRefresh}
        />
      )}
    </>
  );
}
