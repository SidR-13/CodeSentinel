export default function ScoreGauge({ score }) {
  const value = score ?? 0;

  // SVG arc gauge: half-circle, radius 60, stroke-dasharray trick
  const radius = 60;
  const circumference = Math.PI * radius; // half circle
  const progress = Math.min(100, Math.max(0, value));
  const dashOffset = circumference * (1 - progress / 100);

  const color =
    value >= 80 ? "#22c55e" : value >= 60 ? "#eab308" : "#ef4444";

  const label =
    value >= 80 ? "Excellent" : value >= 60 ? "Good" : "Needs Attention";

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-40 h-24 overflow-hidden">
        <svg
          viewBox="0 0 140 80"
          className="w-full h-full"
        >
          {/* Background track */}
          <path
            d="M 10 70 A 60 60 0 0 1 130 70"
            fill="none"
            stroke="#374151"
            strokeWidth="12"
            strokeLinecap="round"
          />
          {/* Colored progress arc */}
          <path
            d="M 10 70 A 60 60 0 0 1 130 70"
            fill="none"
            stroke={color}
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            style={{ transition: "stroke-dashoffset 0.8s ease, stroke 0.4s ease" }}
          />
        </svg>
        {/* Score number in center */}
        <div className="absolute inset-0 flex flex-col items-center justify-end pb-1">
          <span className="text-3xl font-bold" style={{ color }}>
            {score !== null && score !== undefined ? value.toFixed(0) : "—"}
          </span>
        </div>
      </div>
      <p className="text-xs text-gray-500 mt-1 uppercase tracking-wider">{label}</p>
      <p className="text-gray-500 text-xs">out of 100</p>
    </div>
  );
}
