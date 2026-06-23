/**
 * Progress page — three tabs:
 *  1. Body     — weight + body-fat % trend (dual line chart)
 *  2. Strength — exercise selector + estimated 1RM over time
 *  3. Volume   — weekly training volume stacked by muscle group
 *
 * Plus a GitHub-style workout calendar heatmap at the top of the page.
 */
import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine,
} from "recharts";
import { format, parseISO, startOfWeek, addDays } from "date-fns";
import { TrendingUp, Scale, Dumbbell, BarChart2, Search } from "lucide-react";

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

function ChartTooltipStyle({ active, payload, label, unit = "" }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2 shadow-lg text-xs">
      <p className="font-semibold text-slate-700 dark:text-slate-200 mb-1">{label}</p>
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

      {/* Weight trend */}
      <div className="card p-5">
        <h3 className="font-semibold mb-4 flex items-center gap-2">
          <Scale className="w-4 h-4 text-brand-500" /> Body Weight
        </h3>
        {isLoading ? <Skeleton /> : !hasWeight ? <EmptyChart message="Log your weight in Measurements to see your trend" /> : (
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={formatted} margin={CHART_MARGIN}>
              <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="opacity-10" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis
                domain={["auto", "auto"]}
                tick={{ fontSize: 11 }}
                tickFormatter={(v) => `${v} kg`}
                width={60}
              />
              <Tooltip content={<ChartTooltipStyle unit=" kg" />} />
              <Line
                type="monotone"
                dataKey="weight"
                name="Weight"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={formatted.length < 30 ? { r: 3 } : false}
                connectNulls
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Body fat trend */}
      <div className="card p-5">
        <h3 className="font-semibold mb-4 flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-brand-500" /> Body Fat %
        </h3>
        {isLoading ? <Skeleton /> : !hasBodyFat ? <EmptyChart message="Record body fat % in Measurements to see your trend" /> : (
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={formatted} margin={CHART_MARGIN}>
              <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="opacity-10" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis
                domain={["auto", "auto"]}
                tick={{ fontSize: 11 }}
                tickFormatter={(v) => `${v}%`}
                width={48}
              />
              <Tooltip content={<ChartTooltipStyle unit="%" />} />
              <Line
                type="monotone"
                dataKey="bodyFat"
                name="Body fat"
                stroke="#10b981"
                strokeWidth={2}
                dot={formatted.length < 30 ? { r: 3 } : false}
                connectNulls
              />
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
    exercises.filter((e) =>
      e.name.toLowerCase().includes(search.toLowerCase())
    ).slice(0, 8),
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

      {/* Exercise search */}
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
                  : "bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:border-brand-400"
                }`}
            >
              {e.name}
            </button>
          ))}
          {exercises.length === 0 && (
            <p className="text-sm text-slate-400">No strength exercises found.</p>
          )}
        </div>
      </div>

      {/* Chart */}
      <div className="card p-5">
        <h3 className="font-semibold mb-1">
          {selectedEx ? selectedEx.name : "Select an exercise above"}
        </h3>
        {selectedEx && (
          <p className="text-xs text-slate-400 mb-4">
            Estimated 1RM using the Epley formula (weight × (1 + reps/30))
          </p>
        )}
        {!selectedEx ? (
          <EmptyChart message="Pick an exercise to view your strength progression" />
        ) : isLoading ? (
          <Skeleton />
        ) : history.length === 0 ? (
          <EmptyChart message={`No logged sets for ${selectedEx.name} in the last ${days} days`} />
        ) : (
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={formatted} margin={CHART_MARGIN}>
              <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="opacity-10" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis
                domain={["auto", "auto"]}
                tick={{ fontSize: 11 }}
                tickFormatter={(v) => `${v} kg`}
                width={60}
              />
              <Tooltip content={<ChartTooltipStyle unit=" kg" />} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Line
                type="monotone"
                dataKey="Est. 1RM"
                stroke="#3b82f6"
                strokeWidth={2.5}
                dot={{ r: 4 }}
              />
              <Line
                type="monotone"
                dataKey="Max weight"
                stroke="#10b981"
                strokeWidth={1.5}
                strokeDasharray="4 2"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}

// ── Tab: Volume by muscle ─────────────────────────────────────────────────────
function VolumeTab({ weeks, onWeeksChange }) {
  const { data = [], isLoading } = useQuery({
    queryKey: qk.workouts.volumeByMuscle(weeks),
    queryFn: () => progressApi.volumeByMuscle(weeks),
  });

  // Pivot: [{ week_start, chest: vol, back: vol, ... }]
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

  return (
    <div className="space-y-4">
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
              <YAxis
                tick={{ fontSize: 11 }}
                tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
                width={40}
              />
              <Tooltip
                content={({ active, payload, label }) => {
                  if (!active || !payload?.length) return null;
                  const total = payload.reduce((s, p) => s + (p.value || 0), 0);
                  return (
                    <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2 shadow-lg text-xs max-w-48">
                      <p className="font-semibold mb-1">{label}</p>
                      {payload.filter((p) => p.value).map((p) => (
                        <p key={p.dataKey} style={{ color: p.fill }}>
                          {MUSCLE_LABELS[p.dataKey] || p.dataKey}: {Math.round(p.value).toLocaleString()} kg
                        </p>
                      ))}
                      <p className="border-t border-slate-100 dark:border-slate-700 mt-1 pt-1 font-medium text-slate-600 dark:text-slate-300">
                        Total: {Math.round(total).toLocaleString()} kg
                      </p>
                    </div>
                  );
                }}
              />
              <Legend
                formatter={(v) => MUSCLE_LABELS[v] || v}
                wrapperStyle={{ fontSize: 10 }}
              />
              {muscles.map((m) => (
                <Bar
                  key={m}
                  dataKey={m}
                  stackId="a"
                  fill={MUSCLE_COLORS[m] || "#94a3b8"}
                  radius={muscles.indexOf(m) === muscles.length - 1 ? [2, 2, 0, 0] : [0, 0, 0, 0]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
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
              : "bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600"
            }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

function WeeksSelector({ value, onChange }) {
  return (
    <div className="flex items-center gap-2 ml-auto">
      <span className="text-xs text-slate-500">Weeks:</span>
      {[4, 8, 12, 24].map((w) => (
        <button
          key={w}
          onClick={() => onChange(w)}
          className={`px-2.5 py-1 rounded text-xs font-medium transition-colors
            ${value === w
              ? "bg-brand-500 text-white"
              : "bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600"
            }`}
        >
          {w}w
        </button>
      ))}
    </div>
  );
}

function Skeleton() {
  return (
    <div className="h-48 flex items-end gap-1 px-4 pb-2 animate-pulse">
      {Array.from({ length: 20 }).map((_, i) => (
        <div
          key={i}
          className="flex-1 bg-slate-200 dark:bg-slate-700 rounded-t"
          style={{ height: `${20 + Math.random() * 70}%` }}
        />
      ))}
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
    <div className="shrink-0 w-44 pl-6 ml-2 border-l border-slate-100 dark:border-slate-700 flex flex-col justify-center gap-5">
      {stats.map(({ label, value, unit }) => (
        <div key={label}>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-slate-400 mb-1 leading-none">
            {label}
          </p>
          <p className="text-2xl font-bold text-slate-900 leading-none tabular-nums">
            {value}
            {unit && (
              <span className="text-xs font-normal text-slate-400 ml-1">{unit}</span>
            )}
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

  // Days from registration to today — covers all past activity in the range
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

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-slate-100 dark:bg-slate-800 rounded-xl mb-6">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all
              ${activeTab === id
                ? "bg-white dark:bg-slate-700 text-brand-600 dark:text-brand-400 shadow-sm"
                : "text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
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
    </div>
  );
}
