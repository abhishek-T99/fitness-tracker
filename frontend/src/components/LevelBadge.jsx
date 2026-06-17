import clsx from "clsx";

const TIER_CONFIG = {
  rookie:   { label: "Rookie",   bg: "bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-300" },
  amateur:  { label: "Amateur",  bg: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300" },
  athlete:  { label: "Athlete",  bg: "bg-slate-300 text-slate-800 dark:bg-slate-600 dark:text-slate-100" },
  warrior:  { label: "Warrior",  bg: "bg-yellow-300 text-yellow-900 dark:bg-yellow-700/60 dark:text-yellow-200" },
  legend:   { label: "Legend",   bg: "bg-purple-200 text-purple-800 dark:bg-purple-900/50 dark:text-purple-300" },
  elite:    { label: "Elite",    bg: "bg-blue-500 text-white dark:bg-blue-600" },
  immortal: { label: "Immortal", bg: "bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 text-white" },
};

export default function LevelBadge({ tier, level, size = "sm" }) {
  const config = TIER_CONFIG[tier] ?? TIER_CONFIG.rookie;
  const sizeClass = size === "lg"
    ? "px-3 py-1 text-sm font-bold gap-1.5"
    : "px-2 py-0.5 text-xs font-semibold gap-1";

  return (
    <span className={clsx("rounded-full inline-flex items-center", config.bg, sizeClass)}>
      {level != null && <span>Lv.{level}</span>}
      <span>{config.label}</span>
    </span>
  );
}
