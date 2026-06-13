import { Plus, SkipForward } from "lucide-react";

function pad(n) {
  return String(n).padStart(2, "0");
}

function formatTime(seconds) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${pad(m)}:${pad(s)}`;
}

export default function RestTimer({ secondsLeft, secondsTotal, nextLabel, onSkip, onAdd }) {
  const pct = secondsTotal > 0 ? secondsLeft / secondsTotal : 0;
  const urgent = secondsLeft <= 5;

  // Ring geometry — sized so the inner clear zone (r − strokeWidth/2) comfortably
  // fits the timer text.  224 px canvas, r=88, strokeWidth=12:
  //   inner clear radius = 88 − 6 = 82 px  →  164 px diameter for text  ✓
  const SIZE = 224;
  const CX   = SIZE / 2;        // 112
  const R    = 88;
  const SW   = 12;
  const CIRC = 2 * Math.PI * R;
  const dashOffset = CIRC * (1 - pct);

  const ringColor  = urgent ? "#ef4444" : "#0ea5e9";
  const textColor  = urgent ? "text-rose-400" : "text-white";

  return (
    <div className="flex flex-col items-center gap-8 py-6">

      {/* Label */}
      <p className="text-xs font-semibold tracking-[0.2em] uppercase text-slate-400">
        Rest
      </p>

      {/* Ring + timer */}
      <div className="relative" style={{ width: SIZE, height: SIZE }}>
        {/* SVG ring — behind the text via z-index */}
        <svg
          className="absolute inset-0 -rotate-90"
          width={SIZE}
          height={SIZE}
          viewBox={`0 0 ${SIZE} ${SIZE}`}
          style={{ zIndex: 0 }}
        >
          {/* Track */}
          <circle
            cx={CX} cy={CX} r={R}
            fill="none"
            stroke="rgba(255,255,255,0.12)"
            strokeWidth={SW}
          />
          {/* Progress */}
          <circle
            cx={CX} cy={CX} r={R}
            fill="none"
            stroke={ringColor}
            strokeWidth={SW}
            strokeLinecap="round"
            strokeDasharray={CIRC}
            strokeDashoffset={dashOffset}
            style={{ transition: "stroke-dashoffset 0.9s linear, stroke 0.3s" }}
          />
        </svg>

        {/* Timer text — in front of the SVG */}
        <div
          className="absolute inset-0 flex items-center justify-center"
          style={{ zIndex: 1 }}
        >
          <span className={`text-5xl font-bold tabular-nums leading-none ${textColor}`}>
            {formatTime(secondsLeft)}
          </span>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-3">
        {[15, 30].map((s) => (
          <button
            key={s}
            onClick={() => onAdd(s)}
            className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl border border-white/20 text-sm font-medium text-white/80 hover:bg-white/10 transition"
          >
            <Plus className="w-3.5 h-3.5" />
            {s}s
          </button>
        ))}
        <button
          onClick={onSkip}
          className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 transition"
        >
          <SkipForward className="w-4 h-4" />
          Skip rest
        </button>
      </div>

      {/* Up next */}
      {nextLabel && (
        <p className="text-sm text-white/50 text-center px-4">
          Up next —{" "}
          <span className="font-medium text-white/80">{nextLabel}</span>
        </p>
      )}
    </div>
  );
}
