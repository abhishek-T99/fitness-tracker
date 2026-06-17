import clsx from "clsx";
import { useLevelContext } from "../contexts/LevelContext.jsx";

export default function XPBar({ compact = false, className = "" }) {
  const ctx = useLevelContext();
  const profile = ctx?.profile;
  if (!profile) return null;

  const pct = Math.min(profile.xp_progress_pct ?? 0, 100);

  return (
    <div className={clsx("w-full", compact ? "space-y-0.5" : "space-y-1", className)}>
      {!compact && (
        <div className="flex justify-between text-xs text-ink-400 px-0.5">
          <span>{(profile.xp_in_current_level ?? 0).toLocaleString()} XP</span>
          <span>{(profile.xp_for_next_level ?? 0).toLocaleString()} to next</span>
        </div>
      )}
      <div className={clsx("w-full rounded-full overflow-hidden", compact ? "h-1.5 bg-ink-700" : "h-2 bg-ink-800")}>
        <div
          className="h-full rounded-full bg-gradient-to-r from-brand-500 to-brand-400 transition-all duration-700 ease-out"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
