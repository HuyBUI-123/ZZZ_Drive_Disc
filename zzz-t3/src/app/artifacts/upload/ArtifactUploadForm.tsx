"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "~/trpc/react";
import { artifactConfig } from "~/lib/constants";

interface ParsedArtifact {
  set: string;
  type: string;
  mainStat: string;
  numberOfSubstats: number;
  substats: string[];
  score: string;
  source: string;
}

interface ValidatedEntry {
  index: number;
  data: ParsedArtifact | null;
  errors: string[];
}

const validTypes = artifactConfig.artifactTypes.map((t) => t.value);

function validateEntry(raw: unknown, index: number): ValidatedEntry {
  const errors: string[] = [];
  const r = raw as Record<string, unknown>;

  const str = (k: string) => (typeof r[k] === "string" ? (r[k] as string) : "");

  if (!str("set")) errors.push("missing set");
  if (!validTypes.includes(str("type"))) errors.push(`invalid type "${str("type")}"`);
  if (!str("mainStat")) errors.push("missing mainStat");
  if (!str("score")) errors.push("missing score");
  if (!str("source")) errors.push("missing source");

  const n = r.numberOfSubstats;
  if (n !== 3 && n !== 4) errors.push("numberOfSubstats must be 3 or 4");

  const subs = Array.isArray(r.substats) ? (r.substats as string[]) : null;
  if (!subs) {
    errors.push("substats must be an array");
  } else if ((n === 3 || n === 4) && subs.length !== n) {
    errors.push(`substats count (${subs.length}) != numberOfSubstats (${n})`);
  }

  if (errors.length > 0) {
    return { index, data: null, errors };
  }

  return {
    index,
    data: {
      set: str("set"),
      type: str("type"),
      mainStat: str("mainStat"),
      numberOfSubstats: n as number,
      substats: subs!,
      score: str("score"),
      source: str("source"),
    },
    errors: [],
  };
}

export default function ArtifactUploadForm() {
  const router = useRouter();
  const [fileName, setFileName] = useState<string | null>(null);
  const [entries, setEntries] = useState<ValidatedEntry[]>([]);
  const [parseError, setParseError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [pastedText, setPastedText] = useState("");
  const [notification, setNotification] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  const createMany = api.artifact.createMany.useMutation({
    onSuccess: (res) => {
      setNotification({
        type: "success",
        message: `Uploaded ${res.count} drive disc(s) successfully!`,
      });
      setEntries([]);
      setFileName(null);
      router.refresh();
    },
    onError: (error) => {
      setNotification({ type: "error", message: `Error: ${error.message}` });
    },
  });

  const parseJsonText = (text: string, source: string) => {
    setNotification(null);
    setParseError(null);
    setEntries([]);
    setFileName(source);

    let json: unknown;
    try {
      json = JSON.parse(text);
    } catch {
      setParseError("Not valid JSON.");
      return;
    }

    if (!Array.isArray(json)) {
      setParseError("Expected a JSON array of drive discs.");
      return;
    }

    setEntries(json.map((item, i) => validateEntry(item, i)));
  };

  const handleFile = async (file: File) => {
    parseJsonText(await file.text(), file.name);
  };

  const handleLoadPasted = () => {
    if (!pastedText.trim()) {
      setParseError("Paste some JSON first.");
      return;
    }
    parseJsonText(pastedText, "pasted JSON");
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    const f = e.dataTransfer.files?.[0];
    if (f) void handleFile(f);
  };

  const valid = entries.filter((e) => e.data !== null);
  const invalid = entries.filter((e) => e.data === null);

  const handleUpload = () => {
    if (valid.length === 0) return;
    createMany.mutate({ artifacts: valid.map((e) => e.data!) });
  };

  return (
    <div className="mx-auto max-w-4xl rounded-xl bg-slate-800/50 p-8 shadow-xl backdrop-blur-sm">
      {/* Notification */}
      {notification && (
        <div
          className={`mb-6 flex items-center justify-between rounded-md border px-4 py-3 shadow-lg ${
            notification.type === "success"
              ? "border-green-500/50 bg-green-500/20 text-green-200"
              : "border-red-500/50 bg-red-500/20 text-red-200"
          }`}
        >
          <span className="font-medium">{notification.message}</span>
          <button
            onClick={() => setNotification(null)}
            className="ml-4 rounded-full p-1 hover:bg-white/10"
            type="button"
          >
            ✕
          </button>
        </div>
      )}

      {/* File picker + drop zone */}
      <label
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={(e) => {
          e.preventDefault();
          setDragActive(false);
        }}
        onDrop={handleDrop}
        className={`mb-6 flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed px-6 py-10 text-center transition-colors ${
          dragActive
            ? "border-purple-500 bg-purple-500/10"
            : "border-gray-600 bg-slate-800/50 hover:border-purple-500"
        }`}
      >
        <span className="text-lg font-medium text-gray-200">
          {fileName ?? "Choose a JSON file or drag it here"}
        </span>
        <span className="mt-1 text-sm text-gray-400">
          Exported from the scanner (drive_discs_export.json)
        </span>
        <input
          type="file"
          accept="application/json,.json"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) void handleFile(f);
          }}
        />
      </label>

      {/* Paste box (alternative to a file) */}
      <div className="mb-6">
        <div className="mb-2 flex items-center gap-3">
          <span className="text-sm text-gray-300">…or paste JSON</span>
          <span className="text-xs text-gray-500">
            (use the scanner&apos;s &quot;Copy JSON&quot; button)
          </span>
        </div>
        <textarea
          value={pastedText}
          onChange={(e) => setPastedText(e.target.value)}
          placeholder='[ { "set": "...", "type": "...", ... } ]'
          rows={5}
          className="w-full rounded-md border border-gray-600 bg-slate-800 px-3 py-2 font-mono text-sm text-white focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
        />
        <button
          type="button"
          onClick={handleLoadPasted}
          className="mt-2 rounded-md bg-slate-700 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-600"
        >
          Load pasted JSON
        </button>
      </div>

      {parseError && (
        <p className="mb-4 rounded-md border border-red-500/50 bg-red-500/20 px-4 py-3 text-red-200">
          {parseError}
        </p>
      )}

      {/* Summary */}
      {entries.length > 0 && (
        <>
          <div className="mb-4 flex gap-4 text-sm">
            <span className="rounded-md bg-slate-700 px-3 py-1 text-gray-200">
              Total: {entries.length}
            </span>
            <span className="rounded-md bg-green-500/20 px-3 py-1 text-green-300">
              Valid: {valid.length}
            </span>
            <span className="rounded-md bg-red-500/20 px-3 py-1 text-red-300">
              Invalid: {invalid.length}
            </span>
          </div>

          {/* Invalid details */}
          {invalid.length > 0 && (
            <div className="mb-4 max-h-48 overflow-y-auto rounded-md border border-red-500/30 bg-slate-900/50 p-3 text-sm">
              {invalid.map((e) => (
                <div key={e.index} className="text-red-300">
                  Row {e.index + 1}: {e.errors.join(", ")}
                </div>
              ))}
              <p className="mt-2 text-xs text-gray-400">
                Invalid rows will be skipped. Fix them in the JSON and re-upload if needed.
              </p>
            </div>
          )}

          {/* Valid preview */}
          {valid.length > 0 && (
            <div className="mb-6 max-h-64 overflow-y-auto rounded-md border border-slate-700 bg-slate-900/50">
              <table className="w-full text-left text-sm">
                <thead className="sticky top-0 bg-slate-800 text-gray-300">
                  <tr>
                    <th className="px-3 py-2">Set</th>
                    <th className="px-3 py-2">Slot</th>
                    <th className="px-3 py-2">Main</th>
                    <th className="px-3 py-2">Substats</th>
                    <th className="px-3 py-2">Score</th>
                  </tr>
                </thead>
                <tbody>
                  {valid.map((e) => (
                    <tr key={e.index} className="border-t border-slate-700/50 text-gray-200">
                      <td className="px-3 py-2">{e.data!.set}</td>
                      <td className="px-3 py-2">{e.data!.type}</td>
                      <td className="px-3 py-2">{e.data!.mainStat}</td>
                      <td className="px-3 py-2">{e.data!.substats.join(", ")}</td>
                      <td className="px-3 py-2">{e.data!.score}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <button
            type="button"
            onClick={handleUpload}
            disabled={valid.length === 0 || createMany.isPending}
            className={`w-full rounded-md py-3 font-bold text-white transition-all ${
              valid.length === 0 || createMany.isPending
                ? "cursor-not-allowed bg-gray-600 opacity-50"
                : "bg-purple-600 shadow-lg hover:bg-purple-700 hover:shadow-purple-500/25"
            }`}
          >
            {createMany.isPending
              ? "Uploading..."
              : `Upload ${valid.length} drive disc(s)`}
          </button>
        </>
      )}
    </div>
  );
}
