import { useQuery } from "@tanstack/react-query";
import * as Icons from "lucide-react";

import PageHeader from "../components/PageHeader.jsx";
import { achievementsApi } from "../api/endpoints.js";

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

  const catalogList = catalog?.results || catalog || [];
  const unlockedList = unlocked?.results || unlocked || [];
  const unlockedIds = new Set(unlockedList.map((u) => u.achievement));

  return (
    <div>
      <PageHeader
        title="Achievements"
        subtitle={`${unlockedList.length} of ${catalogList.length} unlocked`}
      />

      <div className="card p-5 mb-6 flex items-center gap-6">
        <div className="text-center">
          <p className="text-3xl font-bold text-brand-600">{streak?.current_days ?? 0}</p>
          <p className="text-xs text-slate-500">Day streak</p>
        </div>
        <div className="h-12 w-px bg-slate-200" />
        <div className="text-center">
          <p className="text-3xl font-bold text-amber-500">{streak?.longest_days ?? 0}</p>
          <p className="text-xs text-slate-500">Longest streak</p>
        </div>
        <div className="h-12 w-px bg-slate-200" />
        <div className="text-center">
          <p className="text-3xl font-bold text-emerald-600">{unlockedList.length}</p>
          <p className="text-xs text-slate-500">Badges earned</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {catalogList.map((a) => {
          const Icon = Icons[capitalize(a.icon)] || Icons.Trophy;
          const earned = unlockedIds.has(a.id);
          return (
            <div
              key={a.id}
              className={`card p-5 text-center transition ${
                earned ? "" : "opacity-50 grayscale"
              }`}
            >
              <div
                className={`mx-auto h-14 w-14 rounded-full flex items-center justify-center mb-3 ${
                  earned ? "bg-amber-100 text-amber-600 dark:bg-amber-500/15 dark:text-amber-400" : "bg-slate-100 text-slate-400"
                }`}
              >
                <Icon className="w-7 h-7" />
              </div>
              <h3 className="font-semibold text-sm">{a.name}</h3>
              <p className="text-xs text-slate-500 mt-1">{a.description}</p>
              {!earned && (
                <p className="text-xs text-slate-400 mt-2">Threshold: {a.threshold}</p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function capitalize(s) {
  if (!s) return "Trophy";
  // lucide-react exports PascalCase: "rocket" → "Rocket".
  return s
    .split(/[-_]/)
    .map((p) => p.charAt(0).toUpperCase() + p.slice(1))
    .join("");
}
