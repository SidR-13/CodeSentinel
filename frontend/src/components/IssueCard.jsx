import { useState } from "react";

const SEVERITY_STYLES = {
  CRITICAL: "bg-red-950 border-red-700 text-red-400",
  HIGH: "bg-orange-950 border-orange-700 text-orange-400",
  MEDIUM: "bg-yellow-950 border-yellow-700 text-yellow-400",
  LOW: "bg-gray-800 border-gray-700 text-gray-400",
};

const SEVERITY_BADGE = {
  CRITICAL: "bg-red-900 text-red-300",
  HIGH: "bg-orange-900 text-orange-300",
  MEDIUM: "bg-yellow-900 text-yellow-300",
  LOW: "bg-gray-700 text-gray-300",
};

export default function IssueCard({ issue, isCrossFile = false }) {
  const [expanded, setExpanded] = useState(false);
  const sev = (issue.severity || "LOW").toUpperCase();
  const borderStyle = SEVERITY_STYLES[sev] || SEVERITY_STYLES.LOW;
  const badgeStyle = SEVERITY_BADGE[sev] || SEVERITY_BADGE.LOW;

  let affectedFiles = [];
  if (isCrossFile && issue.affected_files) {
    try {
      affectedFiles = JSON.parse(issue.affected_files);
    } catch {
      affectedFiles = [];
    }
  }

  return (
    <div className={`border rounded-xl overflow-hidden transition-all ${borderStyle}`}>
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full text-left px-5 py-4 flex items-start gap-3"
      >
        {/* Severity badge */}
        <span className={`shrink-0 text-xs font-bold px-2 py-0.5 rounded ${badgeStyle}`}>
          {sev}
        </span>

        <div className="flex-1 min-w-0">
          {/* File + line */}
          {!isCrossFile && issue.file_path && (
            <p className="text-xs text-gray-500 font-mono mb-1">
              {issue.file_path}
              {issue.line_number ? `:${issue.line_number}` : ""}
            </p>
          )}
          {isCrossFile && affectedFiles.length > 0 && (
            <p className="text-xs text-gray-500 font-mono mb-1">
              {affectedFiles.join(", ")}
            </p>
          )}
          {/* Description */}
          <p className="text-sm text-gray-200 leading-snug">{issue.description}</p>
        </div>

        <span className="text-gray-600 text-xs shrink-0 mt-0.5">
          {expanded ? "▲" : "▼"}
        </span>
      </button>

      {expanded && issue.suggestion && (
        <div className="px-5 pb-4 pt-0 border-t border-gray-700/50 bg-gray-900/50">
          <p className="text-xs text-gray-400 uppercase tracking-wider mb-2 mt-3">Suggestion</p>
          <p className="text-sm text-gray-300 leading-relaxed">{issue.suggestion}</p>

          {issue.code_snippet && (
            <>
              <p className="text-xs text-gray-400 uppercase tracking-wider mb-2 mt-4">Code Snippet</p>
              <pre className="text-xs font-mono bg-gray-950 rounded-lg p-3 overflow-x-auto text-gray-300">
                {issue.code_snippet}
              </pre>
            </>
          )}
        </div>
      )}
    </div>
  );
}
