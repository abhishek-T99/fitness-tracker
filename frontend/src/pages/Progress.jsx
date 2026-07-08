/**
 * Progress page — five tabs:
 *  1. Body      — weight + body-fat % trend
 *  2. Strength  — exercise selector + estimated 1RM over time
 *  3. Volume    — weekly volume stacked by muscle + muscle balance section
 *  4. Records   — all-time PR board + progressive overload streaks
 *  5. Sessions  — RPE trend, duration trend, density, DOW heatmap, cardio summary
 *
 * Plus a GitHub-style workout calendar heatmap at the top of the page.
 *
 * Dark-mode colour contract (see index.css):
 *   The `slate` scale is INVERTED in dark mode — slate-50…400 are dark fills/borders,
 *   slate-500…900 are light text colours.  Never use dark:bg-slate-700+ (resolves to
 *   near-white fills) or dark:text-slate-300- (resolves to near-black text).
 *   Use bg-surface for card-like floating elements; omit dark: overrides for
 *   any slate class that already adapts correctly via the CSS-variable remap.
 */
import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis,
} from "recharts";
import { format, parseISO } from "date-fns";
import {
  TrendingUp, Scale, Dumbbell, BarChart2, Search,
  Trophy, Flame, Activity, Clock, Zap, Heart, MapPin,
} from "lucide-react";

import PageHeader from "../components/PageHeader.jsx";
import WorkoutCalendar from "../components/WorkoutCalendar.jsx";
import { progressApi, exercisesApi, achievementsApi } from "../api/endpoints.js";
import { qk } from "../api/queryKeys.js";
import { useAuth } from "../contexts/AuthContext.jsx";

// ── Colour palette for muscle groups ─────────────────────────────────────────
const MUSCLE_COLORS = {
  chest:      "#3b82f6",
  back:       "#10b981",
  shoulders:  "#f59e0b",
  biceps:     "#8b5cf6",
  triceps:    "#ec4899",
  forearms:   "#06b6d4",
  core:       "#f97316",
  quads:      "#14b8a6",
  hamstrings: "#a78bfa",
  glutes:     "#fb7185",
  calves:     "#84cc16",
  full_body:  "#6366f1",
  cardio:     "#64748b",
};

const MUSCLE_LABELS = {
  chest: "Chest", back: "Back", shoulders: "Shoulders",
  biceps: "Biceps", triceps: "Triceps", forearms: "Forearms",
  core: "Core", quads: "Quads", hamstrings: "Hamstrings",
  glutes: "Glutes", calves: "Calves", full_body: "Full Body", cardio: "Cardio",
};

// ── Shared chart styles ───────────────────────────────────────────────────────
const CHART_MARGIN = { top: 8, right: 16, left: 0, bottom: 0 };

// bg-surface: white in light (#fff), card-dark in dark (#111B2E) — no dark: override needed.
function ChartTooltipStyle({ active, payload, label, unit = "" }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-surface border border-slate-200 rounded-lg px-3 py-2 shadow-lg text-xs">
      <p className="font-semibold text-slate-700 mb-1">{label}</p>
      {payload.map((p) => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.name}: {typeof p.value === "number" ? p.value.toFixed(1) : p.value}{unit}
        </p>
      ))}
    </div>
  );
}

function EmptyChart({ message = "No data yet" }) {
  return (
    <div className="h-48 flex items-center justify-center text-slate-400 text-sm">
      {message}
    </div>
  );
}

function Skeleton() {
  return (
    <div className="h-48 flex items-end gap-1 px-4 pb-2 animate-pulse">
      {Array.from({ length: 20 }).map((_, i) => (
        <div
          key={i}
          className="flex-1 bg-slate-200 rounded-t"
          style={{ height: `${20 + Math.random() * 70}%` }}
        />
      ))}
    </div>
  );
}

// ── Shared controls ───────────────────────────────────────────────────────────
function DaysSelector({ value, onChange }) {
  return (
    <div className="flex items-center gap-2 ml-auto">
      <span className="text-xs text-slate-500">Period:</span>
      {[
        { label: "30d", v: 30 },
        { label: "90d", v: 90 },
        { label: "180d", v: 180 },
        { label: "1y", v: 365 },
      ].map(({ label, v }) => (
        <button
          key={v}
          onClick={() => onChange(v)}
          className={`px-2.5 py-1 rounded text-xs font-medium transition-colors
            ${value === v
              ? "bg-brand-500 text-white"
              : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

function WeeksSelector({ value, onChange, options = [4, 8, 12, 24] }) {
  return (
    <div className="flex items-center gap-2 ml-auto">
      <span className="text-xs text-slate-500">Weeks:</span>
      {options.map((w) => (
        <button
          key={w}
          onClick={() => onChange(w)}
          className={`px-2.5 py-1 rounded text-xs font-medium transition-colors
            ${value === w
              ? "bg-brand-500 text-white"
              : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
        >
          {w}w
        </button>
      ))}
    </div>
  );
}

// ── Tab: Body composition ─────────────────────────────────────────────────────
function BodyTab({ days, onDaysChange }) {
  const { data = [], isLoading } = useQuery({
    queryKey: qk.measurements.bodyComposition(days),
    queryFn: () => progressApi.bodyComposition(days),
  });

  const formatted = useMemo(() =>
    data.map((d) => ({
      date: format(parseISO(d.recorded_at), "MMM d"),
      weight: d.weight_kg,
      bodyFat: d.body_fat_percent,
    })),
  [data]);

  const hasWeight  = formatted.some((d) => d.weight !== null);
  const hasBodyFat = formatted.some((d) => d.bodyFat !== null);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <DaysSelector value={days} onChange={onDaysChange} />
      </div>

      <div className="card p-5">
        <h3 className="font-semibold mb-4 flex items-center gap-2">
          <Scale className="w-4 h-4 text-brand-500" /> Body Weight
        </h3>
        {isLoading ? <Skeleton /> : !hasWeight ? <EmptyChart message="Log your weight in Measurements to see your trend" /> : (
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={formatted} margin={CHART_MARGIN}>
              <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="opacity-10" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis domain={["auto", "auto"]} tick={{ fontSize: 11 }} tickFormatter={(v) => `${v} kg`} width={60} />
              <Tooltip content={<ChartTooltipStyle unit=" kg" />} />
              <Line type="monotone" dataKey="weight" name="Weight" stroke="#3b82f6" strokeWidth={2}
                dot={formatted.length < 30 ? { r: 3 } : false} connectNulls />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="card p-5">
        <h3 className="font-semibold mb-4 flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-brand-500" /> Body Fat %
        </h3>
        {isLoading ? <Skeleton /> : !hasBodyFat ? <EmptyChart message="Record body fat % in Measurements to see your trend" /> : (
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={formatted} margin={CHART_MARGIN}>
              <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="opacity-10" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis domain={["auto", "auto"]} tick={{ fontSize: 11 }} tickFormatter={(v) => `${v}%`} width={48} />
              <Tooltip content={<ChartTooltipStyle unit="%" />} />
              <Line type="monotone" dataKey="bodyFat" name="Body fat" stroke="#10b981" strokeWidth={2}
                dot={formatted.length < 30 ? { r: 3 } : false} connectNulls />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}

// ── Tab: Strength progression ─────────────────────────────────────────────────
function StrengthTab({ days, onDaysChange }) {
  const [search, setSearch]       = useState("");
  const [selectedEx, setSelected] = useState(null);

  const { data: exercises = [] } = useQuery({
    queryKey: qk.exercises.list({ page_size: 200, category: "strength" }),
    queryFn: () => exercisesApi.list({ page_size: 200, category: "strength" }),
    select: (d) => (d.results ?? d),
  });

  const filtered = useMemo(() =>
    exercises.filter((e) => e.name.toLowerCase().includes(search.toLowerCase())).slice(0, 8),
  [exercises, search]);

  const { data: history = [], isLoading } = useQuery({
    queryKey: qk.workouts.strengthHistory(selectedEx?.id, days),
    queryFn: () => progressApi.strengthHistory(selectedEx.id, days),
    enabled: !!selectedEx,
  });

  const formatted = useMemo(() =>
    history.map((d) => ({
      date: format(parseISO(d.date), "MMM d"),
      "Est. 1RM": d.estimated_1rm,
      "Max weight": d.max_weight,
    })),
  [history]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <DaysSelector value={days} onChange={onDaysChange} />
      </div>

      <div className="card p-4">
        <div className="relative mb-3">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search exercise…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input pl-9 w-full"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          {filtered.map((e) => (
            <button
              key={e.id}
              onClick={() => { setSelected(e); setSearch(""); }}
              className={`px-3 py-1.5 rounded-full text-sm font-medium border transition-colors
                ${selectedEx?.id === e.id
                  ? "bg-brand-500 text-white border-brand-500"
                  : "bg-surface border-slate-200 text-slate-700 hover:border-brand-400"
                }`}
            >
              {e.name}
            </button>
          ))}
          {exercises.length === 0 && <p className="text-sm text-slate-400">No strength exercises found.</p>}
        </div>
      </div>

      <div className="card p-5">
        <h3 className="font-semibold mb-1">{selectedEx ? selectedEx.name : "Select an exercise above"}</h3>
        {selectedEx && <p className="text-xs text-slate-400 mb-4">Estimated 1RM using the Epley formula (weight × (1 + reps/30))</p>}
        {!selectedEx ? (
          <EmptyChart message="Pick an exercise to view your strength progression" />
        ) : isLoading ? <Skeleton /> : history.length === 0 ? (
          <EmptyChart message={`No logged sets for ${selectedEx.name} in the last ${days} days`} />
        ) : (
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={formatted} margin={CHART_MARGIN}>
              <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="opacity-10" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis domain={["auto", "auto"]} tick={{ fontSize: 11 }} tickFormatter={(v) => `${v} kg`} width={60} />
              <Tooltip content={<ChartTooltipStyle unit=" kg" />} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Line type="monotone" dataKey="Est. 1RM" stroke="#3b82f6" strokeWidth={2.5} dot={{ r: 4 }} />
              <Line type="monotone" dataKey="Max weight" stroke="#10b981" strokeWidth={1.5} strokeDasharray="4 2" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}

// ── Tab: Volume by muscle + muscle balance ────────────────────────────────────
function VolumeTab({ weeks, onWeeksChange }) {
  const [balanceWeeks, setBalanceWeeks] = useState(8);

  const { data = [], isLoading } = useQuery({
    queryKey: qk.workouts.volumeByMuscle(weeks),
    queryFn: () => progressApi.volumeByMuscle(weeks),
  });

  const { data: balance = {}, isLoading: balanceLoading } = useQuery({
    queryKey: qk.workouts.muscleBalance(balanceWeeks),
    queryFn: () => progressApi.muscleBalance(balanceWeeks),
  });

  const { pivoted, muscles } = useMemo(() => {
    const weekMap = {};
    const muscleSet = new Set();
    for (const row of data) {
      if (!weekMap[row.week_start]) weekMap[row.week_start] = { week: row.week_start };
      weekMap[row.week_start][row.muscle_group] = row.volume_kg;
      muscleSet.add(row.muscle_group);
    }
    const pivoted = Object.values(weekMap)
      .sort((a, b) => a.week.localeCompare(b.week))
      .map((w) => ({ ...w, week: format(parseISO(w.week), "MMM d") }));
    return { pivoted, muscles: [...muscleSet] };
  }, [data]);

  const radarData = useMemo(() => {
    if (!balance.muscle_shares) return [];
    return balance.muscle_shares.slice(0, 8).map((s) => ({
      muscle: MUSCLE_LABELS[s.muscle] || s.muscle,
      share: s.share_pct,
    }));
  }, [balance]);

  const pushPullRatio  = balance.push_pull_ratio;
  const upperLowerRatio = balance.upper_lower_ratio;

  function RatioBar({ label, value, idealMin = 0.8, idealMax = 1.2 }) {
    if (value == null) return (
      <div className="flex items-center justify-between text-sm">
        <span className="text-slate-500">{label}</span>
        <span className="text-slate-400 text-xs">No data</span>
      </div>
    );
    const isBalanced = value >= idealMin && value <= idealMax;
    return (
      <div>
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm text-slate-600">{label}</span>
          <span className={`text-sm font-bold tabular-nums ${isBalanced ? "text-emerald-500" : "text-amber-500"}`}>
            {value.toFixed(2)}
            <span className="text-xs font-normal text-slate-400 ml-1">
              {isBalanced ? "balanced" : value > idealMax ? "push-heavy" : "pull-heavy"}
            </span>
          </span>
        </div>
        {/* bg-slate-100: light grey in light (#F1F5F9), dark navy in dark (#1E2A42) */}
        <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${isBalanced ? "bg-emerald-400" : "bg-amber-400"}`}
            style={{ width: `${Math.min(value / 2, 1) * 100}%` }}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <WeeksSelector value={weeks} onChange={onWeeksChange} />
      </div>

      <div className="card p-5">
        <h3 className="font-semibold mb-1">Weekly Volume by Muscle Group</h3>
        <p className="text-xs text-slate-400 mb-4">Total weight lifted (kg × reps), warmup sets excluded</p>

        {isLoading ? <Skeleton /> : pivoted.length === 0 ? (
          <EmptyChart message="Complete workouts with weighted sets to see volume breakdown" />
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={pivoted} margin={CHART_MARGIN}>
              <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="opacity-10" />
              <XAxis dataKey="week" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} width={40} />
              <Tooltip
                content={({ active, payload, label }) => {
                  if (!active || !payload?.length) return null;
                  const total = payload.reduce((s, p) => s + (p.value || 0), 0);
                  return (
                    <div className="bg-surface border border-slate-200 rounded-lg px-3 py-2 shadow-lg text-xs max-w-48">
                      <p className="font-semibold mb-1">{label}</p>
                      {payload.filter((p) => p.value).map((p) => (
                        <p key={p.dataKey} style={{ color: p.fill }}>
                          {MUSCLE_LABELS[p.dataKey] || p.dataKey}: {Math.round(p.value).toLocaleString()} kg
                        </p>
                      ))}
                      <p className="border-t border-slate-200 mt-1 pt-1 font-medium text-slate-600">
                        Total: {Math.round(total).toLocaleString()} kg
                      </p>
                    </div>
                  );
                }}
              />
              <Legend formatter={(v) => MUSCLE_LABELS[v] || v} wrapperStyle={{ fontSize: 10 }} />
              {muscles.map((m) => (
                <Bar key={m} dataKey={m} stackId="a" fill={MUSCLE_COLORS[m] || "#94a3b8"}
                  radius={muscles.indexOf(m) === muscles.length - 1 ? [2, 2, 0, 0] : [0, 0, 0, 0]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Muscle Balance */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold">Muscle Balance</h3>
          <WeeksSelector value={balanceWeeks} onChange={setBalanceWeeks} options={[4, 8, 12]} />
        </div>

        {balanceLoading ? <Skeleton /> : balance.total_volume_kg === 0 ? (
          <EmptyChart message="Complete weighted workouts to see muscle balance" />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Ratios</h4>
              <RatioBar label="Push / Pull" value={pushPullRatio} idealMin={0.8} idealMax={1.2} />
              <RatioBar label="Upper / Lower" value={upperLowerRatio} idealMin={1.0} idealMax={2.5} />

              {/* bg-slate-100: subtle fill (#F1F5F9 light / #1E2A42 dark) */}
              <div className="grid grid-cols-2 gap-3 pt-2">
                {[
                  { label: "Push", value: balance.push_volume_kg, color: "#3b82f6" },
                  { label: "Pull", value: balance.pull_volume_kg, color: "#10b981" },
                  { label: "Upper", value: balance.upper_volume_kg, color: "#f59e0b" },
                  { label: "Lower", value: balance.lower_volume_kg, color: "#8b5cf6" },
                ].map(({ label, value, color }) => (
                  <div key={label} className="bg-slate-100 rounded-lg p-3">
                    <p className="text-[10px] font-semibold uppercase tracking-wider mb-1" style={{ color }}>
                      {label}
                    </p>
                    <p className="text-lg font-bold tabular-nums text-slate-900">
                      {Math.round(value || 0).toLocaleString()}
                      <span className="text-xs font-normal text-slate-400 ml-1">kg</span>
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">Muscle Share</h4>
              {radarData.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="currentColor" className="opacity-10" />
                    <PolarAngleAxis dataKey="muscle" tick={{ fontSize: 10 }} />
                    <PolarRadiusAxis tick={false} axisLine={false} />
                    <Radar dataKey="share" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.25} strokeWidth={1.5} />
                  </RadarChart>
                </ResponsiveContainer>
              ) : (
                <EmptyChart message="No data" />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Tab: Personal Records ─────────────────────────────────────────────────────
function RecordsTab() {
  const { data: prs = [], isLoading: prsLoading } = useQuery({
    queryKey: qk.workouts.personalRecords(),
    queryFn: progressApi.personalRecords,
  });

  const { data: streaks = [], isLoading: streaksLoading } = useQuery({
    queryKey: qk.workouts.overloadStreaks(),
    queryFn: progressApi.overloadStreaks,
  });

  return (
    <div className="space-y-6">
      {/* PR Board */}
      <div className="card p-5">
        <h3 className="font-semibold mb-4 flex items-center gap-2">
          <Trophy className="w-4 h-4 text-brand-500" /> Personal Records
        </h3>
        {prsLoading ? <Skeleton /> : prs.length === 0 ? (
          <EmptyChart message="Complete weighted workouts to see your PRs here" />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                {/* text-slate-400: muted (#94a3b8 light / #7C8BA5 dark) — no dark: override needed */}
                <tr className="text-left text-slate-400 text-xs uppercase tracking-wider border-b border-slate-200">
                  <th className="pb-2.5 font-medium">Exercise</th>
                  <th className="pb-2.5 font-medium">Muscle</th>
                  <th className="pb-2.5 font-medium text-right">Est. 1RM</th>
                  <th className="pb-2.5 font-medium text-right">Max Weight</th>
                  <th className="pb-2.5 font-medium text-right">Max Reps</th>
                  <th className="pb-2.5 font-medium"></th>
                </tr>
              </thead>
              {/* divide-slate-200: #E2E8F0 light / #26344E dark — visible in both modes */}
              <tbody className="divide-y divide-slate-200">
                {prs.map((pr) => (
                  <tr key={pr.exercise_id} className="group hover:bg-slate-100 transition-colors">
                    {/* text-slate-800: #1E293B light / #DEE6F3 dark — main body text in both modes */}
                    <td className="py-2.5 font-medium text-slate-800 pr-4">{pr.exercise_name}</td>
                    <td className="py-2.5 pr-4">
                      <span
                        className="inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wide text-white"
                        style={{ backgroundColor: MUSCLE_COLORS[pr.primary_muscle] || "#94a3b8" }}
                      >
                        {MUSCLE_LABELS[pr.primary_muscle] || pr.primary_muscle}
                      </span>
                    </td>
                    {/* text-slate-700: label colour — #334155 light / #CBD5E8 dark */}
                    <td className="py-2.5 text-right font-mono font-semibold text-slate-700">
                      {pr.pr_1rm.toFixed(1)} <span className="text-slate-400 text-xs">kg</span>
                    </td>
                    <td className="py-2.5 text-right font-mono text-slate-600">
                      {pr.pr_weight.toFixed(1)} <span className="text-slate-400 text-xs">kg</span>
                    </td>
                    <td className="py-2.5 text-right font-mono text-slate-600">
                      {pr.pr_reps}
                    </td>
                    <td className="py-2.5 pl-4">
                      {pr.has_recent_pr && (
                        <span className="px-2 py-0.5 bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400 text-[10px] rounded-full font-semibold whitespace-nowrap">
                          New PR
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Progressive Overload Streaks */}
      <div className="card p-5">
        <h3 className="font-semibold mb-1 flex items-center gap-2">
          <Flame className="w-4 h-4 text-brand-500" /> Progressive Overload Streaks
        </h3>
        <p className="text-xs text-slate-400 mb-4">
          Consecutive sessions where estimated 1RM improved over the previous session
        </p>

        {streaksLoading ? <Skeleton /> : streaks.length === 0 ? (
          <EmptyChart message="Keep beating your previous session to build a streak" />
        ) : (
          <div className="space-y-3">
            {streaks.map((s) => (
              // border-slate-200: #E2E8F0 light / #26344E dark — clean separator
              <div key={s.exercise_id} className="flex items-center justify-between py-2 border-b border-slate-200 last:border-0">
                <div className="min-w-0">
                  <p className="font-medium text-sm text-slate-800 truncate">{s.exercise_name}</p>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Since {format(parseISO(s.streak_since), "MMM d, yyyy")} &middot; last session {format(parseISO(s.last_session_date), "MMM d")}
                  </p>
                </div>
                <div className="text-right ml-4 shrink-0">
                  <p className="text-2xl font-bold tabular-nums text-brand-500 leading-none">{s.current_streak}</p>
                  <p className="text-[10px] text-slate-400 mt-0.5">sessions</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Tab: Session analytics ────────────────────────────────────────────────────
function SessionsTab({ days, onDaysChange, weeks, onWeeksChange }) {
  const { data: rpeTrend = [], isLoading: rpeLoading } = useQuery({
    queryKey: qk.workouts.rpeTrend(days),
    queryFn: () => progressApi.rpeTrend(days),
  });

  const { data: durationTrend = [], isLoading: durationLoading } = useQuery({
    queryKey: qk.workouts.durationTrend(weeks),
    queryFn: () => progressApi.durationTrend(weeks),
  });

  const { data: density = [], isLoading: densityLoading } = useQuery({
    queryKey: qk.workouts.sessionDensity(weeks),
    queryFn: () => progressApi.sessionDensity(weeks),
  });

  const { data: dowData = [], isLoading: dowLoading } = useQuery({
    queryKey: qk.workouts.dowHeatmap(weeks),
    queryFn: () => progressApi.dowHeatmap(weeks),
  });

  const { data: cardio = {}, isLoading: cardioLoading } = useQuery({
    queryKey: qk.workouts.cardioSummary(days),
    queryFn: () => progressApi.cardioSummary(days),
  });

  const rpeFormatted = useMemo(() =>
    rpeTrend.map((d) => ({ week: format(parseISO(d.week_start), "MMM d"), "Avg RPE": d.avg_rpe })),
  [rpeTrend]);

  const durationFormatted = useMemo(() =>
    durationTrend.map((d) => ({ week: format(parseISO(d.week_start), "MMM d"), "Avg (min)": d.avg_duration_min })),
  [durationTrend]);

  const densityFormatted = useMemo(() =>
    density.map((d) => ({ week: format(parseISO(d.week_start), "MMM d"), "kg / min": d.density_kg_per_min })),
  [density]);

  const weeklyDistFormatted = useMemo(() =>
    (cardio.weekly_distance || []).map((d) => ({
      week: format(parseISO(d.week_start), "MMM d"),
      "Distance (km)": d.distance_km,
    })),
  [cardio]);

  const maxDow = dowData.reduce((m, d) => Math.max(m, d.workout_count), 0);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3 justify-end">
        <WeeksSelector value={weeks} onChange={onWeeksChange} />
        <DaysSelector value={days} onChange={onDaysChange} />
      </div>

      {/* RPE Trend */}
      <div className="card p-5">
        <h3 className="font-semibold mb-1 flex items-center gap-2">
          <Zap className="w-4 h-4 text-brand-500" /> Average RPE per Week
        </h3>
        <p className="text-xs text-slate-400 mb-4">Session-level perceived exertion (1–10 scale)</p>
        {rpeLoading ? <Skeleton /> : rpeFormatted.length === 0 ? (
          <EmptyChart message="Log RPE on your workouts to see this trend" />
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={rpeFormatted} margin={CHART_MARGIN}>
              <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="opacity-10" />
              <XAxis dataKey="week" tick={{ fontSize: 11 }} />
              <YAxis domain={[1, 10]} tick={{ fontSize: 11 }} width={30} />
              <Tooltip content={<ChartTooltipStyle />} />
              <Line type="monotone" dataKey="Avg RPE" stroke="#f59e0b" strokeWidth={2.5} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Duration + Density side by side */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card p-5">
          <h3 className="font-semibold mb-1 flex items-center gap-2">
            <Clock className="w-4 h-4 text-brand-500" /> Avg Session Duration
          </h3>
          <p className="text-xs text-slate-400 mb-4">Minutes per session, weekly average</p>
          {durationLoading ? <Skeleton /> : durationFormatted.length === 0 ? (
            <EmptyChart message="Log session duration to track this trend" />
          ) : (
            <ResponsiveContainer width="100%" height={180}>
              <LineChart data={durationFormatted} margin={CHART_MARGIN}>
                <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="opacity-10" />
                <XAxis dataKey="week" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} tickFormatter={(v) => `${v}m`} width={36} />
                <Tooltip content={<ChartTooltipStyle unit=" min" />} />
                <Line type="monotone" dataKey="Avg (min)" stroke="#8b5cf6" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="card p-5">
          <h3 className="font-semibold mb-1 flex items-center gap-2">
            <Zap className="w-4 h-4 text-brand-500" /> Workout Density
          </h3>
          <p className="text-xs text-slate-400 mb-4">kg lifted per minute of session time</p>
          {densityLoading ? <Skeleton /> : densityFormatted.length === 0 ? (
            <EmptyChart message="Needs both weighted sets and session duration logged" />
          ) : (
            <ResponsiveContainer width="100%" height={180}>
              <LineChart data={densityFormatted} margin={CHART_MARGIN}>
                <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="opacity-10" />
                <XAxis dataKey="week" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} tickFormatter={(v) => `${v}`} width={36} />
                <Tooltip content={<ChartTooltipStyle unit=" kg/min" />} />
                <Line type="monotone" dataKey="kg / min" stroke="#ec4899" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Day-of-week heatmap */}
      <div className="card p-5">
        <h3 className="font-semibold mb-1 flex items-center gap-2">
          <Activity className="w-4 h-4 text-brand-500" /> Training by Day of Week
        </h3>
        <p className="text-xs text-slate-400 mb-5">Workout frequency and average volume per weekday</p>
        {dowLoading ? <Skeleton /> : (
          <div className="grid grid-cols-7 gap-2">
            {dowData.map((d) => {
              const intensity = maxDow > 0 ? d.workout_count / maxDow : 0;
              return (
                <div key={d.day_of_week} className="text-center">
                  <p className="text-[10px] font-semibold text-slate-400 mb-2">{d.day_name.slice(0, 3)}</p>
                  <div
                    className={`mx-auto w-10 h-10 rounded-lg flex items-center justify-center text-sm font-bold transition-colors ${
                      intensity === 0 ? "text-slate-400" : "text-blue-500"
                    }`}
                    style={{
                      backgroundColor: intensity > 0
                        ? `rgba(59,130,246,${0.12 + intensity * 0.6})`
                        : undefined,
                    }}
                    title={`${d.workout_count} sessions · avg ${d.avg_volume_kg.toLocaleString()} kg`}
                  >
                    {d.workout_count > 0 ? d.workout_count : "–"}
                  </div>
                  {d.avg_volume_kg > 0 && (
                    <p className="text-[9px] text-slate-400 mt-1.5 leading-none">
                      {d.avg_volume_kg >= 1000
                        ? `${(d.avg_volume_kg / 1000).toFixed(1)}k`
                        : Math.round(d.avg_volume_kg)} kg
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Cardio Summary */}
      <div className="card p-5">
        <h3 className="font-semibold mb-4 flex items-center gap-2">
          <Heart className="w-4 h-4 text-brand-500" /> Cardio Summary
        </h3>
        {cardioLoading ? <Skeleton /> : cardio.total_sessions === 0 ? (
          <EmptyChart message="Log distance or heart rate on workouts to track cardio" />
        ) : (
          <div className="space-y-5">
            {/* bg-slate-100: subtle fill (#F1F5F9 light / #1E2A42 dark) */}
            <div className="grid grid-cols-3 gap-4">
              {[
                { icon: MapPin,   label: "Total Distance", value: `${(cardio.total_distance_km || 0).toFixed(1)} km`, color: "#3b82f6" },
                { icon: Activity, label: "Sessions",       value: cardio.total_sessions,                              color: "#10b981" },
                { icon: Heart,    label: "Avg Heart Rate", value: cardio.avg_hr_bpm != null ? `${cardio.avg_hr_bpm} bpm` : "—", color: "#ef4444" },
              ].map(({ icon: Icon, label, value, color }) => (
                <div key={label} className="bg-slate-100 rounded-xl p-4 text-center">
                  <Icon className="w-5 h-5 mx-auto mb-2" style={{ color }} />
                  {/* text-slate-900: #0F172A light / #E6EDF7 dark — heading weight */}
                  <p className="text-xl font-bold tabular-nums text-slate-900">{value}</p>
                  <p className="text-[10px] text-slate-400 mt-1 uppercase tracking-wide font-medium">{label}</p>
                </div>
              ))}
            </div>

            {weeklyDistFormatted.length > 0 && (
              <div>
                <p className="text-xs text-slate-400 mb-3">Weekly distance (km)</p>
                <ResponsiveContainer width="100%" height={160}>
                  <BarChart data={weeklyDistFormatted} margin={CHART_MARGIN}>
                    <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="opacity-10" />
                    <XAxis dataKey="week" tick={{ fontSize: 10 }} />
                    <YAxis tick={{ fontSize: 10 }} tickFormatter={(v) => `${v}km`} width={40} />
                    <Tooltip content={<ChartTooltipStyle unit=" km" />} />
                    <Bar dataKey="Distance (km)" fill="#3b82f6" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Calendar stats sidebar ────────────────────────────────────────────────────
function CalendarStatsSidebar({ streak = {}, heatmapData = [] }) {
  const { totalWorkouts, avgPerWeek } = useMemo(() => {
    const total = heatmapData.reduce((s, d) => s + d.workout_count, 0);
    if (!total) return { totalWorkouts: 0, avgPerWeek: "0.0" };
    const firstStr = heatmapData.reduce(
      (min, d) => (d.date < min ? d.date : min),
      heatmapData[0].date,
    );
    const weeks = Math.max(1, (Date.now() - new Date(firstStr).getTime()) / (7 * 24 * 60 * 60 * 1000));
    return { totalWorkouts: total, avgPerWeek: (total / weeks).toFixed(1) };
  }, [heatmapData]);

  const stats = [
    { label: "Current Streak", value: streak.current_days ?? 0, unit: "days" },
    { label: "Best Streak",    value: streak.longest_days  ?? 0, unit: "days" },
    { label: "Total Workouts", value: totalWorkouts,              unit: null  },
    { label: "Avg / Week",     value: avgPerWeek,                 unit: null  },
  ];

  return (
    // border-slate-200: #E2E8F0 light / #26344E dark — visible separator in both modes
    <div className="shrink-0 w-44 pl-6 ml-2 border-l border-slate-200 flex flex-col justify-center gap-5">
      {stats.map(({ label, value, unit }) => (
        <div key={label}>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-slate-400 mb-1 leading-none">
            {label}
          </p>
          {/* text-slate-900: #0F172A light / #E6EDF7 dark — heading colour */}
          <p className="text-2xl font-bold text-slate-900 leading-none tabular-nums">
            {value}
            {unit && <span className="text-xs font-normal text-slate-400 ml-1">{unit}</span>}
          </p>
        </div>
      ))}
    </div>
  );
}

const TABS = [
  { id: "body",     label: "Body",     icon: Scale },
  { id: "strength", label: "Strength", icon: Dumbbell },
  { id: "volume",   label: "Volume",   icon: BarChart2 },
  { id: "records",  label: "Records",  icon: Trophy },
  { id: "sessions", label: "Sessions", icon: Activity },
];

// ── Page ─────────────────────────────────────────────────────────────────────
export default function Progress() {
  const [activeTab, setActiveTab] = useState("body");
  const [days,  setDays]  = useState(90);
  const [weeks, setWeeks] = useState(12);

  const { user } = useAuth();

  const HEATMAP_START = user?.date_joined ? new Date(user.date_joined) : null;
  const HEATMAP_END   = HEATMAP_START
    ? new Date(new Date(HEATMAP_START).setFullYear(HEATMAP_START.getFullYear() + 1))
    : null;

  const heatmapDays = HEATMAP_START
    ? Math.min(Math.max(Math.ceil((Date.now() - HEATMAP_START.getTime()) / 86_400_000), 1), 730)
    : 365;

  const { data: heatmapData = [] } = useQuery({
    queryKey: qk.workouts.activityHeatmap(heatmapDays),
    queryFn: () => progressApi.activityHeatmap(heatmapDays),
    enabled: !!HEATMAP_START,
  });

  const { data: streak = {} } = useQuery({
    queryKey: qk.achievements.streak(),
    queryFn: achievementsApi.streak,
  });

  return (
    <div>
      <PageHeader
        title="Progress"
        subtitle="Your fitness journey at a glance"
        icon={<TrendingUp className="w-5 h-5" />}
      />

      {/* Calendar heatmap + stats */}
      <div className="card p-5 mb-6">
        {/* text-slate-700: #334155 light / #CBD5E8 dark — correct label colour, no dark: needed */}
        <h3 className="font-semibold mb-4 text-sm text-slate-700">Workout Activity</h3>
        <div className="flex items-start">
          <div className="flex-1 min-w-0 overflow-x-auto">
            <WorkoutCalendar
              data={heatmapData}
              gridStartDate={HEATMAP_START}
              gridEndDate={HEATMAP_END}
            />
          </div>
          <CalendarStatsSidebar streak={streak} heatmapData={heatmapData} />
        </div>
      </div>

      {/* Tabs — bg-slate-100: #F1F5F9 light / #1E2A42 dark */}
      <div className="flex gap-1 p-1 bg-slate-100 rounded-xl mb-6 overflow-x-auto">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all whitespace-nowrap px-3
              ${activeTab === id
                ? "bg-white dark:bg-slate-200 text-brand-600 dark:text-brand-400 shadow-sm"
                : "text-slate-500 hover:text-slate-700"
              }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {activeTab === "body"     && <BodyTab     days={days}  onDaysChange={setDays} />}
      {activeTab === "strength" && <StrengthTab days={days}  onDaysChange={setDays} />}
      {activeTab === "volume"   && <VolumeTab   weeks={weeks} onWeeksChange={setWeeks} />}
      {activeTab === "records"  && <RecordsTab />}
      {activeTab === "sessions" && <SessionsTab days={days} onDaysChange={setDays} weeks={weeks} onWeeksChange={setWeeks} />}
    </div>
  );
}
