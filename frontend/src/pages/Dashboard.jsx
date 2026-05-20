import { useEffect, useState, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { listReviews, deleteReview, getStats, submitReview } from "../api/reviews";
import Navbar from "../components/Navbar";

function relativeTime(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 30) return `${days}d ago`;
  return new Date(dateStr).toLocaleDateString();
}

function ScoreBadge({ score }) {
  if (score === null || score === undefined) return <span className="text-gray-500">—</span>;
  const color = score >= 80 ? "text-green-400" : score >= 60 ? "text-yellow-400" : "text-red-400";
  return (
    <span className={`font-bold ${color}`}>
      {score.toFixed(0)}<span className="text-gray-600 font-normal">/100</span>
    </span>
  );
}

function StatusBadge({ status }) {
  const map = {
    pending:    "bg-gray-700 text-gray-300",
    processing: "bg-blue-900/60 text-blue-300",
    completed:  "bg-green-900/60 text-green-300",
    failed:     "bg-red-900/60 text-red-300",
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${map[status] || map.pending}`}>
      {status}
    </span>
  );
}

function StatCard({ label, value, sub }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <p className="text-gray-400 text-sm">{label}</p>
      <p className="text-2xl font-bold text-white mt-1">{value ?? "—"}</p>
      {sub && <p className="text-xs text-gray-500 mt-0.5">{sub}</p>}
    </div>
  );
}

const SCORE_RANGES = [
  { label: "All scores", value: "" },
  { label: "Excellent (>80)", value: "80+" },
  { label: "Good (60–80)", value: "60-80" },
  { label: "Needs Attention (<60)", value: "<60" },
];

const STATUS_OPTIONS = [
  { label: "All statuses", value: "" },
  { label: "Completed", value: "completed" },
  { label: "Failed", value: "failed" },
  { label: "Pending", value: "pending" },
];

function scoreRangeToParams(range) {
  if (range === "80+") return { scoreMin: 80, scoreMax: null };
  if (range === "60-80") return { scoreMin: 60, scoreMax: 80 };
  if (range === "<60") return { scoreMin: null, scoreMax: 60 };
  return { scoreMin: null, scoreMax: null };
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [reviews, setReviews] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(null);
  const [retrying, setRetrying] = useState(null);
  const [stats, setStats] = useState(null);

  const [repoFilter, setRepoFilter] = useState("");
  const [scoreFilter, setScoreFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [repoInput, setRepoInput] = useState("");
  const debounceRef = useRef(null);

  const perPage = 10;

  const filters = {
    repo: repoFilter,
    status: statusFilter,
    ...scoreRangeToParams(scoreFilter),
  };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [reviewsRes, statsRes] = await Promise.all([
        listReviews(page, perPage, filters),
        getStats(),
      ]);
      setReviews(reviewsRes.data.reviews);
      setTotal(reviewsRes.data.total);
      setStats(statsRes.data);
    } finally {
      setLoading(false);
    }
  }, [page, repoFilter, scoreFilter, statusFilter]);

  useEffect(() => { load(); }, [load]);

  function handleRepoInput(e) {
    const val = e.target.value;
    setRepoInput(val);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setRepoFilter(val.trim());
      setPage(1);
    }, 350);
  }

  function applyRepoFilter(e) {
    e.preventDefault();
    clearTimeout(debounceRef.current);
    setRepoFilter(repoInput.trim());
    setPage(1);
  }

  function clearFilters() {
    setRepoInput("");
    setRepoFilter("");
    setScoreFilter("");
    setStatusFilter("");
    setPage(1);
  }

  const hasActiveFilters = repoFilter || scoreFilter || statusFilter;

  async function handleDelete(id, e) {
    e.stopPropagation();
    if (!confirm("Delete this review?")) return;
    setDeleting(id);
    try {
      await deleteReview(id);
      load();
    } finally {
      setDeleting(null);
    }
  }

  async function handleRetry(review, e) {
    e.stopPropagation();
    setRetrying(review.id);
    try {
      await deleteReview(review.id);
      const { data } = await submitReview(review.pr_url);
      navigate(`/new?id=${data.id}`);
    } catch {
      setRetrying(null);
      load();
    }
  }

  const totalPages = Math.ceil(total / perPage);

  return (
    <div className="min-h-screen bg-gray-950">
      <Navbar />

      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white">Dashboard</h1>
            <p className="text-gray-400 text-sm mt-1">{total} review{total !== 1 ? "s" : ""}{hasActiveFilters ? " (filtered)" : " total"}</p>
          </div>
          <button
            onClick={() => navigate("/new")}
            className="bg-blue-600 hover:bg-blue-500 text-white font-semibold px-5 py-2.5 rounded-lg transition-colors"
          >
            + New Review
          </button>
        </div>

        {/* Stats bar */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <StatCard label="Total Reviews" value={stats?.total} />
          <StatCard
            label="Avg Score"
            value={stats?.avg_score != null ? `${stats.avg_score}` : "—"}
            sub={stats?.completed ? `across ${stats.completed} completed` : null}
          />
          <StatCard label="Total Issues" value={stats?.total_issues} />
          <StatCard
            label="Critical Issues"
            value={<span className={stats?.critical_issues > 0 ? "text-red-400" : ""}>{stats?.critical_issues ?? "—"}</span>}
          />
        </div>

        {/* Filter bar */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl px-5 py-4 mb-4 flex flex-wrap items-end gap-3">
          <form onSubmit={applyRepoFilter} className="flex gap-2 items-end">
            <div>
              <label className="block text-xs text-gray-400 mb-1">Repository</label>
              <input
                type="text"
                value={repoInput}
                onChange={handleRepoInput}
                placeholder="Filter by repo name…"
                className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 w-48"
              />
            </div>
            <button
              type="submit"
              className="px-3 py-2 bg-gray-700 hover:bg-gray-600 text-gray-200 text-sm rounded-lg transition-colors"
            >
              Search
            </button>
          </form>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Score</label>
            <select
              value={scoreFilter}
              onChange={(e) => { setScoreFilter(e.target.value); setPage(1); }}
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
            >
              {SCORE_RANGES.map((r) => (
                <option key={r.value} value={r.value}>{r.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
            >
              {STATUS_OPTIONS.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>

          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="px-3 py-2 text-sm text-gray-400 hover:text-white transition-colors"
            >
              Clear filters
            </button>
          )}
        </div>

        {/* Table */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center h-40 text-gray-400">Loading…</div>
          ) : reviews.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-48 text-gray-500">
              <p className="mb-4">{hasActiveFilters ? "No reviews match your filters." : "No reviews yet."}</p>
              {!hasActiveFilters && (
                <button
                  onClick={() => navigate("/new")}
                  className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm"
                >
                  Submit your first PR
                </button>
              )}
              {hasActiveFilters && (
                <button onClick={clearFilters} className="text-blue-500 hover:text-blue-400 text-sm">
                  Clear filters
                </button>
              )}
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800 text-left text-gray-400 text-xs uppercase tracking-wider">
                  <th className="px-5 py-3">Repository / PR</th>
                  <th className="px-5 py-3">Score</th>
                  <th className="px-5 py-3">Issues</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">When</th>
                  <th className="px-5 py-3"></th>
                </tr>
              </thead>
              <tbody>
                {reviews.map((r) => (
                  <tr
                    key={r.id}
                    onClick={() => r.status === "completed" && navigate(`/reviews/${r.id}`)}
                    className={`border-b border-gray-800 last:border-0 hover:bg-gray-800/50 transition-colors ${
                      r.status === "completed" ? "cursor-pointer" : ""
                    }`}
                  >
                    <td className="px-5 py-4">
                      <p className="font-medium text-white">
                        {r.repo_owner}/{r.repo_name}{" "}
                        <span className="text-gray-500">#{r.pr_number}</span>
                      </p>
                      {r.pr_title && (
                        <p className="text-gray-500 text-xs mt-0.5 truncate max-w-xs">{r.pr_title}</p>
                      )}
                    </td>
                    <td className="px-5 py-4">
                      <ScoreBadge score={r.overall_score} />
                    </td>
                    <td className="px-5 py-4">
                      <span className="text-white">{r.total_issues}</span>
                      {r.critical_issues > 0 && (
                        <span className="ml-2 text-xs text-red-400">{r.critical_issues} critical</span>
                      )}
                    </td>
                    <td className="px-5 py-4">
                      <StatusBadge status={r.status} />
                    </td>
                    <td className="px-5 py-4 text-gray-400 text-xs" title={new Date(r.created_at).toLocaleString()}>
                      {relativeTime(r.created_at)}
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-3">
                        {r.status === "failed" && (
                          <button
                            onClick={(e) => handleRetry(r, e)}
                            disabled={retrying === r.id}
                            className="text-blue-500 hover:text-blue-400 transition-colors text-xs disabled:opacity-50"
                          >
                            {retrying === r.id ? "…" : "Retry"}
                          </button>
                        )}
                        <button
                          onClick={(e) => handleDelete(r.id, e)}
                          disabled={deleting === r.id}
                          className="text-gray-600 hover:text-red-400 transition-colors text-xs disabled:opacity-50"
                        >
                          {deleting === r.id ? "…" : "Delete"}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center gap-2 mt-6">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-4 py-2 bg-gray-800 text-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-700 transition-colors text-sm"
            >
              Previous
            </button>
            <span className="px-4 py-2 text-gray-400 text-sm">{page} / {totalPages}</span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-4 py-2 bg-gray-800 text-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-700 transition-colors text-sm"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
