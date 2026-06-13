import { useQuery } from "@tanstack/react-query";
import * as Icons from "lucide-react";

import PageHeader from "../components/PageHeader.jsx";
import { achievementsApi } from "../api/endpoints.js";

// ── Category display metadata ─────────────────────────────────────────────────
const CATEGORIES = {
  workout_count:   { label: "Workout Milestones", icon: "Dumbbell", color: "brand"   },
  streak_days:     { label: "Streak",             icon: "Flame",    color: "orange"  },
  volume_total:    { label: "Lifting Volume",     icon: "Dumbbell", color: "violet"  },
  workout_minutes: { label: "Time Trained",       icon: "Clock",    color: "indigo"  },
  calorie_burn:    { label: "Calories Burned",    icon: "Zap",      color: "rose"    },
  distance_km:     { label: "Distance Covered",   icon: "MapPin",   color: "emerald" },
  early_bird:      { label: "Early Bird",         icon: "Sun",      color: "amber"   },
  night_owl:       { label: "Night Owl",          icon: "Moon",     color: "slate"   },
  goals_completed: { label: "Goals Achieved",     icon: "Target",   color: "green"   },
};

// Rarity tier by index within a kind (bronze → platinum)
const RARITY = [
  { label: "Bronze",   ring: "ring-amber-600/50",  bg: "bg-amber-500/15",  text: "text-amber-500"  },
  { label: "Silver",   ring: "ring-slate-400/50",  bg: "bg-slate-400/15",  text: "text-slate-400"  },
  { label: "Gold",     ring: "ring-yellow-400/60", bg: "bg-yellow-400/15", text: "text-yellow-500" },
  { label: "Platinum", ring: "ring-cyan-400/60",   bg: "bg-cyan-400/10",   text: "text-cyan-400"   },
];

const COLOR_MAP = {
  brand:   "text-brand-500",   orange: "text-orange-500",
  violet:  "text-violet-500",  indigo: "text-indigo-500",
  rose:    "text-rose-500",    emerald: "text-emerald-500",
  amber:   "text-amber-500",   slate:  "text-slate-400",
  green:   "text-green-500",
};

function lucideIcon(name) {
  if (!name) return Icons.Trophy;
  const key = name.split(/[-_]/).map((p) => p.charAt(0).toUpperCase() + p.slice(1)).join("");
  return Icons[key] || Icons.Trophy;
}

function BadgeCard({ achievement, earned, unlockedAt, rankInKind }) {
  const Icon = lucideIcon(achievement.icon);
  const rarity = RARITY[Math.min(rankInKind, RARITY.length - 1)];
  return (
    <div className={[
      "relative flex flex-col items-center text-center rounded-2xl p-5 border transition-all duration-200",
      earned
        ? `bg-surface border-slate-200 shadow-sm hover:shadow-md ring-2 ${rarity.ring}`
        : "bg-slate-50 dark:bg-slate-100/5 border-slate-200 opacity-50 grayscale",
    ].join(" ")}>
      {earned && (
        <span className={`absolute top-2 right-2 text-[10px] font-bold uppercase tracking-widest ${rarity.text}`}>
          {rarity.label}
        </span>
      )}
      <div className={[
        "h-14 w-14 rounded-full flex items-center justify-center mb-3 ring-2",
        earned ? `${rarity.bg} ${rarity.ring}` : "bg-slate-100 ring-transparent",
      ].join(" ")}>
        <Icon className={`w-7 h-7 ${earned ? rarity.text : "text-slate-400"}`} />
      </div>
      <h3 className="font-semibold text-sm leading-snug text-slate-900">{achievement.name}</h3>
      <p className="text-xs text-slate-500 mt-1 leading-relaxed">{achievement.description}</p>
      {earned && unlockedAt ? (
        <p className="text-[10px] text-slate-400 mt-2">
          Unlocked {new Date(unlockedAt).toLocaleDateString()}
        </p>
      ) : !earned ? (
        <p className="text-xs text-slate-400 mt-2 font-mono">
          Goal: {achievement.threshold.toLocaleString()}
        </p>
      ) : null}
    </div>
  );
}

function CategoryProgress({ achievements, unlockedIds }) {
  const earnedCount = achievements.filter((a) => unlockedIds.has(a.id)).length;
  const next = achievements.find((a) => !unlockedIds.has(a.id));
  return (
    <div className="mb-4">
      <div className="flex justify-between text-xs text-slate-500 mb-1.5">
        <span>{earnedCount} / {achievements.length} unlocked</span>
        {next
          ? <span>Next: <span className="font-medium text-slate-700">{next.name}</span></span>
          : <span className="text-emerald-500 font-medium">All unlocked!</span>}
      </div>
      <div className="h-1.5 rounded-full bg-slate-100 overflow-hidden">
        <div
          className="h-full rounded-full bg-brand-500 transition-all duration-700"
          style={{ width: `${(earnedCount / achievements.length) * 100}%` }}
        />
      </div>
    </div>
  );
}

export default function Achievements() {
  const { data: catalog } = useQuery({
    queryKey: ["achievementCatalog"],
    queryFn: achievementsApi.catalog,
  });
  const { data: unlocked } = useQuery({
    queryKey: ["userAchievements"],
    queryFn: achievementsApi.unlocked,
  });
  const { data: streak } = useQuery({
    queryKey: ["streak"],
    queryFn: achievementsApi.streak,
  });

  const catalogList  = catalog?.results  || catalog  || [];
  const unlockedList = unlocked?.results || unlocked || [];

  const unlockedMap = new Map(unlockedList.map((u) => [u.achievement, u.unlocked_at]));
  const unlockedIds = new Set(unlockedMap.keys());

  // Group by kind in the order defined by CATEGORIES
  const byKind = catalogList.reduce((acc, a) => {
    (acc[a.kind] = acc[a.kind] || []).push(a);
    return acc;
  }, {});

  const totalEarned = unlockedIds.size;
  const totalBadges = catalogList.length;
  const overallPct  = totalBadges > 0 ? Math.round((totalEarned / totalBadges) * 100) : 0;

  return (
    <div>
      <PageHeader title="Achievements" subtitle={`${totalEarned} of ${totalBadges} unlocked`} />

      {/* Hero stats bar */}
      <div className="card p-5 mb-8 flex items-center gap-6 flex-wrap">
        <div className="text-center min-w-[72px]">
          <p className="text-3xl font-bold text-brand-600">{streak?.current_days ?? 0}</p>
          <p className="text-xs text-slate-500 mt-0.5">Day streak</p>
        </div>
        <div className="h-12 w-px bg-slate-200" />
        <div className="text-center min-w-[72px]">
          <p className="text-3xl font-bold text-amber-500">{streak?.longest_days ?? 0}</p>
          <p className="text-xs text-slate-500 mt-0.5">Longest streak</p>
        </div>
        <div className="h-12 w-px bg-slate-200" />
        <div className="text-center min-w-[72px]">
          <p className="text-3xl font-bold text-emerald-600">{totalEarned}</p>
          <p className="text-xs text-slate-500 mt-0.5">Badges earned</p>
        </div>
        <div className="h-12 w-px bg-slate-200" />
        <div className="flex-1 min-w-[160px]">
          <div className="flex justify-between text-xs text-slate-500 mb-1.5">
            <span>Overall progress</span>
            <span>{overallPct}%</span>
          </div>
          <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-brand-500 to-emerald-500 transition-all duration-700"
              style={{ width: `${overallPct}%` }}
            />
          </div>
        </div>
      </div>

      {/* One section per category */}
      <div className="space-y-10">
        {Object.entries(CATEGORIES).map(([kind, meta]) => {
          const achievements = byKind[kind];
          if (!achievements?.length) return null;
          const CatIcon = Icons[meta.icon] || Icons.Trophy;
          const iconColor = COLOR_MAP[meta.color] || COLOR_MAP.brand;
          const earnedInCat = achievements.filter((a) => unlockedIds.has(a.id)).length;

          return (
            <section key={kind}>
              <div className="flex items-center gap-2 mb-1">
                <CatIcon className={`w-4 h-4 ${iconColor}`} />
                <h2 className="font-semibold text-slate-900">{meta.label}</h2>
                <span className="text-xs text-slate-400">{earnedInCat}/{achievements.length}</span>
              </div>

              <CategoryProgress achievements={achievements} unlockedIds={unlockedIds} />

              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                {achievements.map((a, idx) => (
                  <BadgeCard
                    key={a.id}
                    achievement={a}
                    earned={unlockedIds.has(a.id)}
                    unlockedAt={unlockedMap.get(a.id)}
                    rankInKind={idx}
                  />
                ))}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}
