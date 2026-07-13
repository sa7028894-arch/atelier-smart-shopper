export default function MatchDial({ score }) {
  const radius = 22;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color = score >= 70 ? "#7FA37A" : score >= 40 ? "#D9BA72" : "#B4694A";

  return (
    <div className="relative w-14 h-14 shrink-0" aria-hidden="false" role="img" aria-label={`${score} percent match`}>
      <svg width="56" height="56" viewBox="0 0 56 56" className="-rotate-90">
        <circle cx="28" cy="28" r={radius} fill="none" stroke="#262A3D" strokeWidth="4" />
        <circle
          cx="28"
          cy="28"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="4"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="font-mono text-[11px] text-parchment">{score}%</span>
      </div>
    </div>
  );
}
