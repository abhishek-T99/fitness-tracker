/**
 * Nutrition Insights — trends and overall statistics across a date range.
 *
 * Companion to the daily Nutrition page: instead of "what did I eat today",
 * this answers "how have I been eating this week/month/quarter" and how
 * closely I'm tracking against my calorie goal.
 */
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart,
  Pie, PieChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { format, parseISO } from "date-fns";
import { Award, Flame, Target, TrendingDown, TrendingUp, Utensils } from "lucide-react";

import PageHeader from "../components/PageHeader.jsx";
import NutritionTabs from "../components/NutritionTabs.jsx";
import { mealsApi } from "../api/endpoints.js";
import { qk } from "../api/queryKeys.js";

const RANGES = [
  { label: "7 days",  days: 7,  granularity: "day"   },
  { label: "30 days", days: 30, granularity: "day"   },
  { label: "90 days", days: 90, granularity: "week"  },
  { label: "1 year",  days: 365, granularity: "month" },
];

const MACRO_COLORS = {
  protein: "#10b981",
  carbs:   "#f59e0b",
  fat:     "#6366f1",
};

const CHART_MARGIN = { top: 8, right: 16, left: 0, bottom: 0 };

export default function NutritionInsights() {
  const [rangeIdx, setRangeIdx] = useState(1); // default: last 30 days

  const params = useMemo(() => {
    const r = RANGES[rangeIdx];
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - (r.days - 1));
    return {
      start: format(start, "yyyy-MM-dd"),
      end: format(end, "yyyy-MM-dd"),
      granularity: r.granularity,
    };
  }, [rangeIdx]);

  const { data, isLoading, isError } = useQuery({
    queryKey: qk.nutrition.rangeSummary(params),
    queryFn: () => mealsApi.rangeSummary(params),
  });

  return (
    <div>
      <PageHeader
        title="Nutrition"
        subtitle="Overall trends, macro balance, and how consistently you're hitting your goal"
      />

      <NutritionTabs />

      <RangeTabs value={rangeIdx} onChange={setRangeIdx} />

      {isError && (
        <div className="card p-6 text-sm text-rose-600">
          Couldn't load your insights right now. Try again in a moment.
        </div>
      )}

      {isLoading && !data ? (
        <LoadingSkeleton />
      ) : data && (
        <>
          <SummaryCards data={data} />
          <AdherencePanel adherence={data.adherence} />

          <div className="grid gap-4 lg:grid-cols-2 mt-6">
            <CalorieTrendCard buckets={data.buckets} goal={data.adherence.calorie_goal} granularity={params.granularity} />
            <MacroDistributionCard buckets={data.buckets} granularity={params.granularity} />
          </div>

          <div className="grid gap-4 lg:grid-cols-2 mt-4">
            <MacroSplitCard split={data.aggregate.macro_split_pct} />
            <TopFoodsCard foods={data.top_foods} />
          </div>
        </>
      )}
    </div>
  );
}

// ── Range tab bar ───────────────────────────────────────────────────────────

function RangeTabs({ value, onChange }) {
  return (
    <div className="flex flex-wrap gap-2 mb-4">
      {RANGES.map((r, i) => (
        <button
          key={r.label}
          onClick={() => onChange(i)}
          className={`px-3 py-1.5 text-sm rounded-full border transition-colors ${
            value === i
              ? "bg-brand-500 text-white border-brand-500"
              : "bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:border-brand-400"
          }`}
        >
          {r.label}
        </button>
      ))}
    </div>
  );
}

// ── Summary cards ───────────────────────────────────────────────────────────

function SummaryCards({ data }) {
  const { aggregate } = data;
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
      <Stat
        icon={<Flame className="w-4 h-4 text-rose-500" />}
        label="Avg calories / day"
        value={aggregate.avg_calories}
        unit="kcal"
      />
      <Stat
        icon={<Utensils className="w-4 h-4 text-brand-500" />}
        label="Days logged"
        value={`${aggregate.days_logged} / ${aggregate.days_in_range}`}
      />
      <Stat
        icon={<TrendingDown className="w-4 h-4 text-emerald-500" />}
        label="Lowest day"
        value={aggregate.min_calories_day?.value ?? "—"}
        unit={aggregate.min_calories_day ? "kcal" : ""}
        detail={aggregate.min_calories_day && format(parseISO(aggregate.min_calories_day.date), "MMM d")}
      />
      <Stat
        icon={<TrendingUp className="w-4 h-4 text-amber-500" />}
        label="Highest day"
        value={aggregate.max_calories_day?.value ?? "—"}
        unit={aggregate.max_calories_day ? "kcal" : ""}
        detail={aggregate.max_calories_day && format(parseISO(aggregate.max_calories_day.date), "MMM d")}
      />
    </div>
  );
}

function Stat({ icon, label, value, unit, detail }) {
  // The theme inverts the slate scale in dark mode (index.css) — so
  // text-slate-900 is the primary text token in both themes, and
  // text-slate-500 is muted text in both. Don't add `dark:` overrides
  // that swap those; you'll invert them a second time.
  return (
    <div className="card p-4">
      <div className="flex items-center gap-1.5 text-xs font-medium text-slate-600">
        {icon}
        <span>{label}</span>
      </div>
      <p className="text-xl font-bold mt-1 text-slate-900">
        {value}{" "}
        {unit && <span className="text-sm font-normal text-slate-500">{unit}</span>}
      </p>
      {detail && <p className="text-xs text-slate-500 mt-0.5">{detail}</p>}
    </div>
  );
}

// ── Adherence ───────────────────────────────────────────────────────────────

function AdherencePanel({ adherence }) {
  if (adherence.calorie_goal == null) {
    return (
      <div className="card p-4 mb-6 flex items-center gap-3 text-sm text-slate-500">
        <Target className="w-4 h-4 text-slate-400 shrink-0" />
        <span>
          Set a <strong className="text-slate-700 dark:text-slate-200">daily calorie goal</strong> in your
          profile to see how consistently you're hitting it.
        </span>
      </div>
    );
  }
  return (
    <div className="card p-4 mb-6">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Target className="w-4 h-4 text-brand-500" />
          <h3 className="font-semibold text-sm">
            Goal adherence · <span className="font-normal text-slate-500">{adherence.calorie_goal} kcal ± {adherence.tolerance_pct}%</span>
          </h3>
        </div>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <AdherenceStat label="On-target days" value={adherence.days_on_target} />
        <AdherenceStat label="Hit rate" value={`${adherence.on_target_pct}%`} />
        <AdherenceStat
          label="Current streak"
          value={adherence.current_streak_days}
          unit={adherence.current_streak_days === 1 ? "day" : "days"}
          highlight
        />
        <AdherenceStat
          label="Longest streak"
          value={adherence.longest_streak_days}
          unit={adherence.longest_streak_days === 1 ? "day" : "days"}
          icon={<Award className="w-3.5 h-3.5 text-amber-500" />}
        />
      </div>
    </div>
  );
}

function AdherenceStat({ label, value, unit, highlight, icon }) {
  // Palette note: slate-100 is "subtle fills / hovers" in both themes
  // (see index.css). Using bg-slate-800/60 here previously produced a pale
  // semi-transparent surface in dark mode because the scale is inverted.
  return (
    <div
      className={`rounded-lg p-3 border ${
        highlight
          ? "bg-brand-50 border-brand-200"
          : "bg-slate-100 border-slate-200"
      }`}
    >
      <div className="flex items-center gap-1 text-xs font-medium text-slate-600">
        {icon}{label}
      </div>
      <p
        className={`text-lg font-bold mt-0.5 ${
          highlight ? "text-brand-700" : "text-slate-900"
        }`}
      >
        {value}{" "}
        {unit && <span className="text-xs font-normal text-slate-500">{unit}</span>}
      </p>
    </div>
  );
}

// ── Calorie vs goal line chart ──────────────────────────────────────────────

function CalorieTrendCard({ buckets, goal, granularity }) {
  const rows = useMemo(
    () => buckets.map((b) => ({
      date: formatBucket(b.date, granularity),
      calories: b.calories,
    })),
    [buckets, granularity],
  );
  const hasData = rows.some((r) => r.calories > 0);
  return (
    <div className="card p-5">
      <h3 className="font-semibold mb-3">Calories over time</h3>
      {!hasData ? (
        <EmptyChart message="No meals logged in this range." />
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={rows} margin={CHART_MARGIN}>
            <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="opacity-10" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} interval="preserveStartEnd" />
            <YAxis tick={{ fontSize: 11 }} width={48} tickFormatter={(v) => `${Math.round(v)}`} />
            <Tooltip content={<ChartTooltip unit=" kcal" />} />
            {goal && (
              <ReferenceLine
                y={goal}
                stroke="#f43f5e"
                strokeDasharray="4 4"
                label={{ value: "Goal", position: "right", fontSize: 10, fill: "#f43f5e" }}
              />
            )}
            <Line type="monotone" dataKey="calories" name="Calories" stroke="#3b82f6" strokeWidth={2} dot={rows.length < 40 ? { r: 3 } : false} />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}

// ── Macro stacked-bar distribution ──────────────────────────────────────────

function MacroDistributionCard({ buckets, granularity }) {
  const rows = useMemo(
    () => buckets.map((b) => ({
      date: formatBucket(b.date, granularity),
      // Convert grams → kcal so the stacked bar reflects energy contribution,
      // not raw grams (fat is 9 kcal/g vs 4 kcal/g for the others — mixing
      // them by mass would visually understate fat's share).
      protein: Math.round(b.protein_g * 4),
      carbs:   Math.round(b.carbs_g * 4),
      fat:     Math.round(b.fat_g * 9),
    })),
    [buckets, granularity],
  );
  const hasData = rows.some((r) => r.protein + r.carbs + r.fat > 0);
  return (
    <div className="card p-5">
      <h3 className="font-semibold mb-3">Macro distribution</h3>
      {!hasData ? (
        <EmptyChart message="No meals logged in this range." />
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={rows} margin={CHART_MARGIN}>
            <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="opacity-10" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} interval="preserveStartEnd" />
            <YAxis tick={{ fontSize: 11 }} width={48} />
            <Tooltip content={<ChartTooltip unit=" kcal" />} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            <Bar dataKey="protein" name="Protein" stackId="m" fill={MACRO_COLORS.protein} />
            <Bar dataKey="carbs"   name="Carbs"   stackId="m" fill={MACRO_COLORS.carbs} />
            <Bar dataKey="fat"     name="Fat"     stackId="m" fill={MACRO_COLORS.fat} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}

// ── Macro split donut ───────────────────────────────────────────────────────

function MacroSplitCard({ split }) {
  const rows = [
    { name: "Protein", value: split.protein, color: MACRO_COLORS.protein },
    { name: "Carbs",   value: split.carbs,   color: MACRO_COLORS.carbs },
    { name: "Fat",     value: split.fat,     color: MACRO_COLORS.fat },
  ];
  const total = rows.reduce((a, r) => a + r.value, 0);
  return (
    <div className="card p-5">
      <h3 className="font-semibold mb-3">Macro split (calories)</h3>
      {total === 0 ? (
        <EmptyChart message="No meals logged in this range." />
      ) : (
        <div className="flex items-center gap-4">
          <ResponsiveContainer width="50%" height={180}>
            <PieChart>
              <Pie
                data={rows}
                dataKey="value"
                innerRadius={45}
                outerRadius={70}
                paddingAngle={2}
                stroke="none"
              >
                {rows.map((r) => <Cell key={r.name} fill={r.color} />)}
              </Pie>
              <Tooltip content={<ChartTooltip unit="%" />} />
            </PieChart>
          </ResponsiveContainer>
          <ul className="flex-1 space-y-2 text-sm">
            {rows.map((r) => (
              <li key={r.name} className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ background: r.color }} />
                  {r.name}
                </span>
                <span className="font-medium">{r.value}%</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

// ── Top foods list ──────────────────────────────────────────────────────────

function TopFoodsCard({ foods }) {
  return (
    <div className="card p-5">
      <h3 className="font-semibold mb-3">Most-logged foods</h3>
      {foods.length === 0 ? (
        <EmptyChart message="No foods logged in this range." />
      ) : (
        <ul className="divide-y divide-slate-200">
          {foods.map((f) => (
            <li key={f.food_id} className="flex items-center justify-between py-2 text-sm">
              <span className="truncate pr-2 text-slate-900">{f.name}</span>
              <span className="text-slate-600 shrink-0">
                {f.times_logged}× ·{" "}
                <span className="font-semibold text-slate-900">
                  {f.total_calories} kcal
                </span>
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// ── Shared ──────────────────────────────────────────────────────────────────

function formatBucket(iso, granularity) {
  const d = parseISO(iso);
  if (granularity === "month") return format(d, "MMM yyyy");
  if (granularity === "week")  return format(d, "MMM d");
  return format(d, "MMM d");
}

function ChartTooltip({ active, payload, label, unit = "" }) {
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

function EmptyChart({ message }) {
  return (
    <div className="h-48 flex items-center justify-center text-slate-400 text-sm text-center px-4">
      {message}
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="card p-4 animate-pulse">
            <div className="h-3 w-20 bg-slate-200 dark:bg-slate-700 rounded" />
            <div className="h-6 w-16 bg-slate-200 dark:bg-slate-700 rounded mt-2" />
          </div>
        ))}
      </div>
      <div className="card p-5 animate-pulse h-56" />
    </div>
  );
}
