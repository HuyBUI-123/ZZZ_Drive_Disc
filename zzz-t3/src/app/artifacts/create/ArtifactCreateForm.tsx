"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Select, { type StylesConfig } from "react-select";
import { api } from "~/trpc/react";
import { artifactConfig } from "~/lib/constants";

interface Option {
  value: string;
  label: string;
}

// Custom styles for React Select to match dark theme
const customStyles: StylesConfig<Option, false> = {
  control: (provided, state) => ({
    ...provided,
    backgroundColor: "#1e293b", // slate-800
    borderColor: state.isFocused ? "#a855f7" : "#4b5563", // purple-500 : gray-600
    color: "white",
    boxShadow: state.isFocused ? "0 0 0 1px #a855f7" : "none",
    "&:hover": {
      borderColor: "#a855f7",
    },
  }),
  menu: (provided) => ({
    ...provided,
    backgroundColor: "#334155", // slate-700
    zIndex: 50,
  }),
  option: (provided, state) => ({
    ...provided,
    backgroundColor: state.isSelected
      ? "#a855f7" // purple-500
      : state.isFocused
        ? "#475569" // slate-600
        : "#334155", // slate-700
    color: "white",
    cursor: "pointer",
    ":active": {
      backgroundColor: "#a855f7",
    },
  }),
  singleValue: (provided) => ({
    ...provided,
    color: "white",
  }),
  input: (provided) => ({
    ...provided,
    color: "white",
  }),
  placeholder: (provided) => ({
    ...provided,
    color: "#9ca3af", // gray-400
  }),
};

export default function ArtifactCreateForm() {
  const router = useRouter();
  const [notification, setNotification] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  const initialFormData = {
    set: "",
    type: "",
    mainStat: "",
    numberOfSubstats: "",
    substats: [] as string[],
    score: "",
    source: "",
  };

  const [formData, setFormData] = useState(initialFormData);

  const createArtifact = api.artifact.create.useMutation({
    onSuccess: () => {
      setNotification({
        type: "success",
        message: "Drive Disc created successfully!",
      });
      setFormData(initialFormData);
      router.refresh();
      window.scrollTo({ top: 0, behavior: "smooth" });
    },
    onError: (error) => {
      setNotification({ type: "error", message: `Error: ${error.message}` });
      window.scrollTo({ top: 0, behavior: "smooth" });
    },
  });

  // Helper to convert string options to { value, label } for React Select
  const toOption = (val: string) => (val ? { value: val, label: val } : null);
  const toOptions = (vals: string[]) =>
    vals.map((v) => ({ value: v, label: v }));

  const handleSelectChange = (
    field: string,
    selectedOption: { value: string; label: string } | null,
  ) => {
    const value = selectedOption ? selectedOption.value : "";
    setFormData((prev) => ({
      ...prev,
      [field]: value,
      // Reset dependent fields
      ...(field === "type" && {
        mainStat: "",
        substats: [],
        numberOfSubstats: "",
      }),
      ...(field === "mainStat" && { substats: [] }),
    }));
  };

  const handleSubstatChange = (substat: string, checked: boolean) => {
    setFormData((prev) => ({
      ...prev,
      substats: checked
        ? [...prev.substats, substat]
        : prev.substats.filter((s) => s !== substat),
    }));
  };

  // Filter available substats (exclude main stat)
  const availableSubstats = artifactConfig.allSubstats.filter(
    (s) => s !== formData.mainStat
  );

  // Validation
  const isSubmitDisabled =
    !formData.set ||
    !formData.type ||
    !formData.mainStat ||
    !formData.numberOfSubstats ||
    !formData.score ||
    !formData.source ||
    formData.substats.length !== parseInt(formData.numberOfSubstats);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createArtifact.mutate({
      set: formData.set,
      type: formData.type,
      mainStat: formData.mainStat,
      numberOfSubstats: parseInt(formData.numberOfSubstats),
      substats: formData.substats,
      score: formData.score,
      source: formData.source,
    });
  };

  // Progress Calculation
  const steps = [
    { name: "Set", completed: !!formData.set },
    { name: "Type", completed: !!formData.type },
    { name: "Main Stat", completed: !!formData.mainStat },
    { name: "Count", completed: !!formData.numberOfSubstats },
    {
      name: "Substats",
      completed:
        !!formData.numberOfSubstats &&
        formData.substats.length === parseInt(formData.numberOfSubstats),
    },
    { name: "Score", completed: !!formData.score },
    { name: "Source", completed: !!formData.source },
  ];
  const completedSteps = steps.filter((s) => s.completed).length;
  const progressPercent = (completedSteps / steps.length) * 100;

  return (
    <div className="mx-auto max-w-4xl rounded-xl bg-slate-800/50 p-8 shadow-xl backdrop-blur-sm">
      {/* Progress Bar */}
      <div className="mb-8">
        <div className="mb-2 flex justify-between text-sm text-gray-300">
          <span>Form Progress</span>
          <span>
            {completedSteps}/{steps.length} completed
          </span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-slate-700">
          <div
            className="h-full bg-purple-500 transition-all duration-500 ease-out"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
        <div className="mt-2 flex justify-between px-1">
          {steps.map((step, i) => (
            <div
              key={i}
              className={`h-2 w-2 rounded-full ${
                step.completed ? "bg-purple-500" : "bg-slate-600"
              }`}
              title={step.name}
            />
          ))}
        </div>
      </div>

      {/* Notification */}
      {notification && (
        <div
          className={`mb-6 flex items-center justify-between rounded-md border px-4 py-3 shadow-lg transition-all ${
            notification.type === "success"
              ? "border-green-500/50 bg-green-500/20 text-green-200"
              : "border-red-500/50 bg-red-500/20 text-red-200"
          }`}
        >
          <span className="font-medium">{notification.message}</span>
          <button
            onClick={() => setNotification(null)}
            className="ml-4 rounded-full p-1 transition-colors hover:bg-white/10"
            type="button"
          >
            ✕
          </button>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Artifact Set */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-200">
            Drive Disc Set
          </label>
          <Select
            instanceId="artifact-set-select"
            options={toOptions(artifactConfig.artifactSets)}
            value={toOption(formData.set)}
            onChange={(val) => handleSelectChange("set", val)}
            placeholder="Select Drive Disc Set..."
            styles={customStyles}
            isClearable
          />
        </div>

        {/* Type */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-200">
            Drive Disc Slot
          </label>
          <Select
            instanceId="artifact-type-select"
            options={artifactConfig.artifactTypes}
            value={toOption(formData.type)}
            onChange={(val) => handleSelectChange("type", val)}
            placeholder="Select Slot..."
            styles={customStyles}
            isClearable
          />
        </div>

        {/* Main Stat */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-200">
            Main Stat
          </label>
          <Select
            instanceId="main-stat-select"
            options={
              formData.type
                ? artifactConfig.mainStatsOptions[formData.type] ?? []
                : []
            }
            value={toOption(formData.mainStat)}
            onChange={(val) => handleSelectChange("mainStat", val)}
            placeholder={
              formData.type ? "Select Main Stat..." : "Select Type first"
            }
            isDisabled={!formData.type}
            styles={customStyles}
            isClearable
          />
        </div>

        {/* Number of Substats */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-200">
            Number of Substats
          </label>
          <select
            className="w-full rounded-md border border-gray-600 bg-slate-800 px-3 py-2 text-white focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500 disabled:opacity-50"
            value={formData.numberOfSubstats}
            onChange={(e) =>
              handleSelectChange("numberOfSubstats", {
                value: e.target.value,
                label: e.target.value,
              })
            }
            disabled={!formData.mainStat}
          >
            <option value="">Select Number</option>
            <option value="3">3</option>
            <option value="4">4</option>
          </select>
        </div>

        {/* Substats Selection */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-200">
            Substats
          </label>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
            {availableSubstats.map((substat) => (
              <label
                key={substat}
                className={`flex cursor-pointer items-center justify-center rounded-md border p-2 text-sm transition-colors ${
                  formData.substats.includes(substat)
                    ? "border-purple-500 bg-purple-500/20 text-white"
                    : "border-gray-600 bg-slate-800 text-gray-300 hover:bg-slate-700"
                } ${!formData.numberOfSubstats ? "cursor-not-allowed opacity-50" : ""}`}
              >
                <input
                  type="checkbox"
                  className="hidden"
                  checked={formData.substats.includes(substat)}
                  onChange={(e) =>
                    handleSubstatChange(substat, e.target.checked)
                  }
                  disabled={!formData.numberOfSubstats}
                />
                {substat}
              </label>
            ))}
          </div>
          {/* Feedback Message */}
          {formData.numberOfSubstats && (
            <p
              className={`text-sm ${
                formData.substats.length === parseInt(formData.numberOfSubstats)
                  ? "text-green-400"
                  : "text-yellow-400"
              }`}
            >
              Selected: {formData.substats.length} / {formData.numberOfSubstats}
            </p>
          )}
        </div>

        {/* Score */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-200">
            Score
          </label>
          <Select
            instanceId="score-select"
            options={toOptions(artifactConfig.scores)}
            value={toOption(formData.score)}
            onChange={(val) => handleSelectChange("score", val)}
            placeholder="Select Score..."
            styles={customStyles}
            isClearable
            maxMenuHeight={400}
          />
        </div>

        {/* Source */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-200">
            Where got it?
          </label>
          <Select
            instanceId="source-select"
            options={toOptions(artifactConfig.sources)}
            value={toOption(formData.source)}
            onChange={(val) => handleSelectChange("source", val)}
            placeholder="Select Source..."
            styles={customStyles}
            isClearable
            maxMenuHeight={400}
          />
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isSubmitDisabled || createArtifact.isPending}
          className={`w-full rounded-md py-3 font-bold text-white transition-all ${
            isSubmitDisabled || createArtifact.isPending
              ? "cursor-not-allowed bg-gray-600 opacity-50"
              : "bg-purple-600 hover:bg-purple-700 shadow-lg hover:shadow-purple-500/25"
          }`}
        >
          {createArtifact.isPending ? "Creating..." : "Create Artifact"}
        </button>
      </form>
    </div>
  );
}