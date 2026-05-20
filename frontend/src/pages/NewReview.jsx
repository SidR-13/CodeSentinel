import { useState, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { submitReview, validatePR } from "../api/reviews";
import { useSSE } from "../hooks/useSSE";
import Navbar from "../components/Navbar";

const STEPS = [
  { key: "fetching_pr", label: "Fetching PR from GitHub" },
  { key: "fetching_diff", label: "Fetching diff" },
  { key: "building_graph", label: "Building dependency graph" },
  { key: "truncating", label: "Preparing AI context" },
  { key: "reviewing", label: "Analyzing with Claude AI" },
  { key: "scoring", label: "Calculating score" },
  { key: "saving", label: "Saving results" },
];

const GH_PR_RE = /^https:\/\/github\.com\/[\w.-]+\/[\w.-]+\/pull\/\d+\/?$/;

function ProgressBar({ progress }) {
  return (
    <div className="w-full bg-gray-800 rounded-full h-2">
      <div
        className="bg-blue-500 h-2 rounded-full transition-all duration-500"
        style={{ width: `${progress}%` }}
      />
    </div>
  );
}

function SizeWarning({ changedFiles }) {
  if (!changedFiles || changedFiles <= 20) return null;
  const isVeryLarge = changedFiles > 50;
  return (
    <div className="flex items-start gap-2 bg-yellow-900/30 border border-yellow-700/60 rounded-lg px-4 py-3 text-yellow-300 text-sm">
      <span className="shrink-0 mt-0.5">⚠</span>
      <span>
        {isVeryLarge
          ? `Very large PR (${changedFiles} files) — only the first 10 files will be reviewed.`
          : `Large PR (${changedFiles} files) — review may be truncated to fit the AI context window.`}
      </span>
    </div>
  );
}

export default function NewReview() {
  const navigate = useNavigate();
  const [prUrl, setPrUrl] = useState("");
  const [reviewId, setReviewId] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [currentEvent, setCurrentEvent] = useState(null);
  const [changedFiles, setChangedFiles] = useState(null);
  const validateTimeout = useRef(null);

  const handleEvent = useCallback((event) => {
    setCurrentEvent(event);
  }, []);

  const handleDone = useCallback((event) => {
    if (event.status === "completed") {
      setTimeout(() => navigate(`/reviews/${reviewId}`), 800);
    }
  }, [reviewId, navigate]);

  const handleSSEError = useCallback((msg) => {
    setError(`Stream error: ${msg}`);
  }, []);

  useSSE(reviewId, { onEvent: handleEvent, onDone: handleDone, onError: handleSSEError });

  function handleUrlChange(e) {
    const val = e.target.value;
    setPrUrl(val);
    setChangedFiles(null);

    clearTimeout(validateTimeout.current);
    if (!GH_PR_RE.test(val.trim())) return;

    validateTimeout.current = setTimeout(async () => {
      try {
        const { data } = await validatePR(val.trim());
        if (data.valid && data.changed_files != null) {
          setChangedFiles(data.changed_files);
        }
      } catch {
        // silent — validation is best-effort
      }
    }, 600);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const { data } = await submitReview(prUrl.trim());
      setReviewId(data.id);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(detail || "Failed to submit review");
      setSubmitting(false);
    }
  }

  const isStreaming = !!reviewId;
  const progress = currentEvent?.progress ?? 0;
  const stepLabel = currentEvent?.message ?? "";
  const failed = currentEvent?.status === "failed";

  return (
    <div className="min-h-screen bg-gray-950">
      <Navbar />

      <div className="max-w-2xl mx-auto px-4 py-16">
        <div className="text-center mb-10">
          <h1 className="text-2xl font-bold text-white mb-2">New Code Review</h1>
          <p className="text-gray-400 text-sm">Paste a GitHub Pull Request URL to start an AI review</p>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8">
          {!isStreaming ? (
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">GitHub PR URL</label>
                <input
                  type="url"
                  required
                  value={prUrl}
                  onChange={handleUrlChange}
                  placeholder="https://github.com/owner/repo/pull/123"
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 font-mono text-sm"
                />
              </div>

              <SizeWarning changedFiles={changedFiles} />

              {error && (
                <div className="bg-red-900/40 border border-red-700 rounded-lg px-4 py-3 text-red-300 text-sm">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={submitting}
                className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-lg transition-colors"
              >
                {submitting ? "Submitting…" : "Start Review"}
              </button>

              <p className="text-center text-xs text-gray-500">
                Review runs asynchronously — usually takes 10–30 seconds
              </p>
            </form>
          ) : (
            <div className="space-y-6">
              <div className="text-center">
                {failed ? (
                  <p className="text-red-400 font-semibold">Review failed</p>
                ) : progress === 100 ? (
                  <p className="text-green-400 font-semibold">Complete! Redirecting…</p>
                ) : (
                  <p className="text-blue-400 font-semibold animate-pulse">Reviewing…</p>
                )}
              </div>

              <ProgressBar progress={progress} />
              <p className="text-center text-sm text-gray-400">{progress}% — {stepLabel}</p>

              <div className="space-y-2 mt-4">
                {STEPS.map((step) => {
                  const currentIdx = STEPS.findIndex((s) => s.key === currentEvent?.step);
                  const stepIdx = STEPS.findIndex((s) => s.key === step.key);
                  const done = stepIdx < currentIdx || (stepIdx === currentIdx && progress === 100);
                  const active = step.key === currentEvent?.step && progress < 100;

                  return (
                    <div key={step.key} className={`flex items-center gap-3 text-sm ${
                      done ? "text-green-400" : active ? "text-blue-400" : "text-gray-600"
                    }`}>
                      <span className="w-4 text-center">
                        {done ? "✓" : active ? "⟳" : "○"}
                      </span>
                      {step.label}
                    </div>
                  );
                })}
              </div>

              {failed && (
                <div className="bg-red-900/40 border border-red-700 rounded-lg px-4 py-3 text-red-300 text-sm">
                  {currentEvent?.message || "Review failed. Please try again."}
                  <button
                    onClick={() => { setReviewId(null); setCurrentEvent(null); setSubmitting(false); }}
                    className="block mt-2 text-red-400 underline text-xs"
                  >
                    Try again
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
