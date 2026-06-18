import { useQuery } from "@tanstack/react-query";
import { Crown, Medal, Users, Star } from "lucide-react";
import PageHeader from "../components/PageHeader.jsx";
import LevelBadge from "../components/LevelBadge.jsx";
import { levelsApi } from "../api/endpoints.js";

function RankIcon({ rank }) {
  if (rank === 1) return <Crown className="w-5 h-5 text-yellow-400" aria-label="1st place" />;
  if (rank === 2) return <Medal className="w-5 h-5 text-slate-400" aria-label="2nd place" />;
  if (rank === 3) return <Medal className="w-5 h-5 text-amber-600" aria-label="3rd place" />;
  return <span className="text-sm font-bold text-slate-400 w-5 text-center" aria-label={`${rank}th place`}>#{rank}</span>;
}

function UserInitials({ displayName, avatar }) {
  if (avatar) {
    return (
      <img
        src={avatar}
        alt={displayName}
        className="h-10 w-10 rounded-full object-cover ring-2 ring-slate-200"
      />
    );
  }
  return (
    <div className="h-10 w-10 rounded-full bg-brand-600 text-white flex items-center justify-center font-bold text-sm ring-2 ring-slate-200">
      {(displayName?.[0] || "?").toUpperCase()}
    </div>
  );
}

export default function Leaderboard() {
  const { data: entries = [], isLoading } = useQuery({
    queryKey: ["leaderboard"],
    queryFn: levelsApi.leaderboard,
    staleTime: 60_000,
  });

  const selfEntry = entries.find((e) => e.is_self);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Leaderboard"
        subtitle="How you stack up against friends this season"
      />

      {selfEntry && (
        <div className="card bg-gradient-to-r from-brand-50 to-purple-50 dark:from-brand-900/20 dark:to-purple-900/20 border-brand-200 dark:border-brand-800">
          <div className="card-body flex items-center gap-4">
            <div className="flex items-center justify-center w-10">
              <RankIcon rank={selfEntry.rank} />
            </div>
            <UserInitials displayName={selfEntry.display_name} avatar={selfEntry.avatar} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <p className="font-bold text-slate-900 dark:text-white">
                  You — {selfEntry.display_name}
                </p>
                {selfEntry.prestige_count > 0 && (
                  <span className="inline-flex items-center gap-0.5 text-xs font-bold text-yellow-500">
                    <Star className="w-3 h-3 fill-yellow-400 stroke-yellow-500" />
                    {selfEntry.prestige_count}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 mt-0.5">
                <LevelBadge tier={selfEntry.tier} level={selfEntry.level} />
                <span className="text-xs text-slate-500">{selfEntry.athlete_class_display}</span>
              </div>
            </div>
            <div className="text-right">
              <p className="text-xl font-extrabold text-brand-600">{selfEntry.total_xp.toLocaleString()}</p>
              <p className="text-xs text-slate-500">total XP</p>
            </div>
          </div>
        </div>
      )}

      <div className="card">
        <div className="card-header flex items-center gap-2">
          <Users className="w-4 h-4 text-slate-500" />
          <h3 className="font-semibold">All Competitors</h3>
          <span className="ml-auto text-xs text-slate-400">{entries.length} player{entries.length !== 1 ? "s" : ""}</span>
        </div>
        <div className="divide-y divide-slate-100 dark:divide-slate-800">
          {isLoading ? (
            <p className="text-center text-slate-500 py-10">Loading…</p>
          ) : entries.length === 0 ? (
            <div className="py-12 text-center text-slate-500">
              <Users className="w-8 h-8 mx-auto mb-3 text-slate-300" />
              <p>No competitors yet.</p>
              <p className="text-sm mt-1">Add friends to compete on the leaderboard.</p>
            </div>
          ) : (
            entries.map((entry) => (
              <div
                key={entry.user_id}
                className={`flex items-center gap-4 px-4 py-3 transition-colors ${
                  entry.is_self ? "bg-brand-50/60 dark:bg-brand-900/10" : "hover:bg-slate-50 dark:hover:bg-slate-800/40"
                }`}
              >
                <div className="flex items-center justify-center w-8 shrink-0">
                  <RankIcon rank={entry.rank} />
                </div>
                <UserInitials displayName={entry.display_name} avatar={entry.avatar} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <p className="font-semibold text-slate-900 dark:text-white truncate">
                      {entry.display_name}
                    </p>
                    {entry.is_self && (
                      <span className="text-xs font-medium text-brand-600 bg-brand-50 dark:bg-brand-500/15 px-1.5 py-0.5 rounded-full shrink-0">You</span>
                    )}
                    {entry.prestige_count > 0 && (
                      <span className="inline-flex items-center gap-0.5 text-xs font-bold text-yellow-500 shrink-0">
                        <Star className="w-3 h-3 fill-yellow-400 stroke-yellow-500" />
                        {entry.prestige_count}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                    <LevelBadge tier={entry.tier} level={entry.level} />
                    <span className="text-xs text-slate-500">{entry.athlete_class_display}</span>
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <p className="font-bold text-slate-900 dark:text-white">
                    {entry.total_xp.toLocaleString()}
                  </p>
                  <p className="text-xs text-slate-500">XP</p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
