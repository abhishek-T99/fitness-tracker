import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import {
  Dumbbell,
  Flame,
  Timer,
  TrendingUp,
  Apple,
  Trophy,
  Target,
  Zap,
  CheckCircle2,
} from "lucide-react";
import { format, parseISO, subDays } from "date-fns";

import PageHeader from "../components/PageHeader.jsx";
import StatCard from "../components/StatCard.jsx";
import StepsCounter from "../components/StepsCounter.jsx";
import LevelBadge from "../components/LevelBadge.jsx";
import {
  workoutsApi,
  measurementsApi,
  mealsApi,
  goalsApi,
  achievementsApi,
  levelsApi,
} from "../api/endpoints.js";
import { useAuth } from "../contexts/AuthContext.jsx";
import { useLevelContext } from "../contexts/LevelContext.jsx";

export default function Dashboard() {
  const { user } = useAuth();

  const { data: stats } = useQuery({ queryKey: ["workoutStats"], queryFn: workoutsApi.stats });
  const { data: weight } = useQuery({
    queryKey: ["weightHistory"],
    queryFn: () => measurementsApi.weightHistory(60),
  });
  const { data: goals } = useQuery({ queryKey: ["goals"], queryFn: goalsApi.list });
  const { data: streak } = useQuery({ queryKey: ["streak"], queryFn: achievementsApi.streak });

  // Build last-14-days workout count chart
  const dailyCounts = stats?.daily_counts || {};
  const chartData = Array.from({ length: 14 }, (_, i) => {
    const d = subDays(new Date(), 13 - i);
    const key = format(d, "yyyy-MM-dd");
    return { day: format(d, "MMM d"), workouts: dailyCounts[key] || 0 };
  });

  const weightData = (weight || []).map((row) => ({
    date: format(parseISO(row.recorded_at), "MMM d"),
    weight: parseFloat(row.weight_kg),
  }));

  const activeGoals = (goals?.results || goals || []).filter((g) => g.status === "active");

  return (
    <div>
      <PageHeader
        title={`Hi, ${user?.first_name || user?.username}`}
        subtitle="Here's your fitness snapshot."
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard
          icon={Dumbbell}
          label="Workouts this week"
          value={stats?.this_week?.workouts ?? 0}
          hint={`${stats?.last_30_days ?? 0} in last 30 days`}
        />
        <StatCard
          icon={Timer}
          label="Minutes this week"
          value={stats?.this_week?.minutes ?? 0}
          accent="indigo"
        />
        <StatCard
          icon={Flame}
          label="Calories burned"
          value={stats?.this_week?.calories ?? 0}
          accent="rose"
          hint="this week"
        />
        <StatCard
          icon={TrendingUp}
          label="Current streak"
          value={`${streak?.current_days ?? 0} days`}
          accent="emerald"
          hint={`Longest: ${streak?.longest_days ?? 0} days`}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="card">
          <div className="card-header">
            <h3 className="font-semibold">Workouts (last 14 days)</h3>
          </div>
          <div className="card-body h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.3} />
                <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="workouts" fill="#0ea5e9" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="font-semibold">Body weight trend</h3>
          </div>
          <div className="card-body h-72">
            {weightData.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center gap-2 text-slate-400 dark:text-slate-500">
                <TrendingUp className="w-8 h-8 opacity-40" />
                <p className="text-sm">Log a measurement to see your trend.</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={weightData}>
                  <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.3} />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis domain={["auto", "auto"]} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="weight"
                    stroke="#0ea5e9"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <XPCard />
        <NutritionDonutCard />
        <WeeklyChallengesCard />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card">
          <div className="card-header">
            <h3 className="font-semibold flex items-center gap-2">
              <Target className="w-4 h-4 text-rose-600" /> Active goals
            </h3>
            <Link to="/goals" className="text-xs text-brand-600 hover:underline">
              View →
            </Link>
          </div>
          <div className="card-body space-y-3">
            {activeGoals.length === 0 && (
              <p className="text-sm text-slate-500">No active goals yet.</p>
            )}
            {activeGoals.slice(0, 4).map((g) => (
              <div key={g.id}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-700 font-medium">{g.title}</span>
                  <span className="text-slate-500">{g.progress_percent}%</span>
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-brand-500"
                    style={{ width: `${g.progress_percent}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <StepsCounter />

        <div className="card">
          <div className="card-header">
            <h3 className="font-semibold flex items-center gap-2">
              <Trophy className="w-4 h-4 text-amber-500" /> Quick actions
            </h3>
          </div>
          <div className="card-body space-y-2">
            <Link to="/workouts/new" className="btn-primary w-full">
              + Log a workout
            </Link>
            <Link to="/nutrition" className="btn-secondary w-full">
              + Log a meal
            </Link>
            <Link to="/measurements" className="btn-secondary w-full">
              + Record weight
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

function XPCard() {
  const ctx = useLevelContext();
  const profile = ctx?.profile;

  if (!profile) return null;

  const pct = Math.min(profile.xp_progress_pct ?? 0, 100);

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="font-semibold flex items-center gap-2">
          <Zap className="w-4 h-4 text-brand-500" /> Level Progress
        </h3>
        <Link to="/profile" className="text-xs text-brand-600 hover:underline">
          View profile →
        </Link>
      </div>
      <div className="card-body space-y-4">
        <div className="flex items-center gap-3">
          <div className="h-14 w-14 rounded-full bg-brand-500/15 ring-2 ring-brand-500/30 flex items-center justify-center shrink-0">
            <span className="text-xl font-extrabold text-brand-600">{profile.level}</span>
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <LevelBadge tier={profile.tier} level={null} size="sm" />
              <span className="text-xs text-slate-500">{profile.athlete_class_display}</span>
            </div>
            <p className="text-xs text-slate-500">
              {(profile.total_xp ?? 0).toLocaleString()} total XP
              {profile.prestige_count > 0 && (
                <span className="ml-2 text-yellow-500 font-bold">✦{profile.prestige_count} Prestige</span>
              )}
            </p>
          </div>
        </div>
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-slate-500">
            <span>{(profile.xp_in_current_level ?? 0).toLocaleString()} XP</span>
            <span>{(profile.xp_for_next_level ?? 0).toLocaleString()} to next level</span>
          </div>
          <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-brand-500 to-brand-400 rounded-full transition-all duration-700"
              style={{ width: `${pct}%` }}
            />
          </div>
          <p className="text-right text-xs text-slate-400">{pct.toFixed(1)}%</p>
        </div>
        {profile.recent_transactions?.length > 0 && (
          <div className="space-y-1">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">Recent XP</p>
            {profile.recent_transactions.slice(0, 3).map((tx) => (
              <div key={tx.id} className="flex justify-between text-xs">
                <span className="text-slate-600 truncate">{tx.reason}</span>
                <span className="text-brand-600 font-semibold ml-2 shrink-0">+{tx.amount}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function WeeklyChallengesCard() {
  const { data } = useQuery({
    queryKey: ["weeklyChallenges"],
    queryFn: levelsApi.challenges,
    staleTime: 60_000,
  });

  const challenges = data?.challenges ?? [];

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="font-semibold flex items-center gap-2">
          <Trophy className="w-4 h-4 text-amber-500" /> Weekly Challenges
        </h3>
        {data?.resets_in_secs != null && (
          <span className="text-xs text-slate-400">
            Resets in {Math.ceil(data.resets_in_secs / 3600)}h
          </span>
        )}
      </div>
      <div className="card-body space-y-4">
        {challenges.length === 0 ? (
          <p className="text-sm text-slate-500">No challenges this week yet.</p>
        ) : (
          challenges.map((uc) => {
            const ch = uc.challenge;
            const pct = uc.progress_pct ?? 0;
            return (
              <div key={uc.id} className="space-y-1.5">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-1.5 min-w-0">
                    {uc.completed ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                    ) : (
                      <div className="w-4 h-4 rounded-full border-2 border-slate-300 shrink-0" />
                    )}
                    <span className={`text-sm font-medium truncate ${uc.completed ? "text-slate-400 line-through" : "text-slate-700"}`}>
                      {ch.description}
                    </span>
                  </div>
                  <span className="text-xs text-brand-600 font-semibold shrink-0">+{ch.xp_reward} XP</span>
                </div>
                <div className="ml-5.5">
                  <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${uc.completed ? "bg-emerald-500" : "bg-brand-500"}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {uc.current_value}/{ch.target_value}
                  </p>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

const MACRO_CONFIG = [
  { key: "protein_g", label: "Protein", kcalPerG: 4,  color: "#3b82f6" },
  { key: "carbs_g",   label: "Carbs",   kcalPerG: 4,  color: "#10b981" },
  { key: "fat_g",     label: "Fat",     kcalPerG: 9,  color: "#f59e0b" },
];

function NutritionDonutCard() {
  const { data: dailyNutrition } = useQuery({
    queryKey: ["dailyNutrition"],
    queryFn: () => mealsApi.dailySummary(),
  });

  const totals      = dailyNutrition?.totals   ?? {};
  const calories    = totals.calories           ?? 0;
  const calorieGoal = dailyNutrition?.calorie_goal ?? null;

  const macros = MACRO_CONFIG.map((m) => ({
    ...m,
    grams: Math.round(totals[m.key] ?? 0),
    kcal:  Math.round((totals[m.key] ?? 0) * m.kcalPerG),
  }));

  const totalMacroKcal = macros.reduce((s, m) => s + m.kcal, 0);
  const hasData        = totalMacroKcal > 0;
  const goalPct        = calorieGoal ? Math.min(100, Math.round((calories / calorieGoal) * 100)) : null;

  // Donut segments — fall back to a neutral placeholder ring when no data
  const chartData = hasData
    ? macros.map((m) => ({ name: m.label, value: m.kcal, color: m.color }))
    : [{ name: "empty", value: 1, color: "rgb(var(--c-slate-200))" }];

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="font-semibold flex items-center gap-2">
          <Apple className="w-4 h-4 text-emerald-600" /> Today's Macros
        </h3>
        <Link to="/nutrition" className="text-xs text-brand-600 hover:underline">
          View →
        </Link>
      </div>
      <div className="card-body">
        <div className="flex items-center gap-4">
          {/* Donut chart */}
          <div className="relative w-28 h-28 shrink-0">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={34}
                  outerRadius={52}
                  dataKey="value"
                  startAngle={90}
                  endAngle={-270}
                  strokeWidth={0}
                >
                  {chartData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                {hasData && <Tooltip formatter={(v, name) => [`${v} kcal`, name]} />}
              </PieChart>
            </ResponsiveContainer>
            {/* Center label */}
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-base font-extrabold text-slate-900 leading-none">
                {Math.round(calories)}
              </span>
              <span className="text-[10px] text-slate-500 mt-0.5">kcal</span>
            </div>
          </div>

          {/* Macro legend with mini proportion bars */}
          <div className="flex-1 space-y-2.5 min-w-0">
            {macros.map((m) => {
              const pct = totalMacroKcal > 0 ? Math.round((m.kcal / totalMacroKcal) * 100) : 0;
              return (
                <div key={m.key}>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <div className="flex items-center gap-1.5">
                      <div className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: m.color }} />
                      <span className="text-slate-600">{m.label}</span>
                    </div>
                    <span className="font-semibold text-slate-700 tabular-nums">
                      {m.grams}g
                      <span className="text-slate-400 font-normal ml-1">{pct}%</span>
                    </span>
                  </div>
                  <div className="h-1 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{ width: `${pct}%`, backgroundColor: m.color }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Calorie goal progress */}
        {calorieGoal && (
          <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800">
            <div className="flex justify-between text-xs text-slate-500 mb-1.5">
              <span>Daily goal</span>
              <span className={goalPct >= 100 ? "text-emerald-600 font-semibold" : ""}>
                {Math.round(calories)} / {calorieGoal} kcal
                {goalPct != null && <span className="ml-1 text-slate-400">({goalPct}%)</span>}
              </span>
            </div>
            <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-700 ${goalPct >= 100 ? "bg-emerald-500" : "bg-brand-500"}`}
                style={{ width: `${goalPct}%` }}
              />
            </div>
          </div>
        )}

        {!hasData && (
          <p className="text-xs text-slate-400 text-center mt-3">
            Log a meal to see your macro breakdown.
          </p>
        )}
      </div>
    </div>
  );
}
