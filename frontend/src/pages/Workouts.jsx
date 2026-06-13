import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Dumbbell, Plus } from "lucide-react";
import { format, parseISO } from "date-fns";

import PageHeader from "../components/PageHeader.jsx";
import EmptyState from "../components/EmptyState.jsx";
import { workoutsApi } from "../api/endpoints.js";

const SOURCE_META = {
  intervals: { label: "Intervals.icu", color: "bg-rose-50 text-rose-600 dark:bg-rose-500/15 dark:text-rose-400" },
  strava:    { label: "Strava",        color: "bg-orange-50 text-orange-600 dark:bg-orange-500/15 dark:text-orange-400" },
};

function SourceBadge({ source }) {
  const meta = SOURCE_META[source];
  if (!meta) return null;
  return (
    <span className={`badge ${meta.color}`}>
      {meta.label}
    </span>
  );
}

function Stat({ label, value }) {
  return (
    <div className="bg-slate-50 dark:bg-slate-100/5 rounded-lg px-3 py-2">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="font-semibold text-slate-900">{value}</p>
    </div>
  );
}

function WorkoutCard({ w }) {
  const isSynced = !!w.source;

  // For synced workouts show distance + HR; for manual show exercises + volume
  const stats = isSynced ? [
    { label: "Duration", value: w.duration_min ? `${w.duration_min} min` : "—" },
    { label: "Distance", value: w.distance_km ? `${Number(w.distance_km).toFixed(2)} km` : "—" },
    { label: "Avg HR", value: w.avg_hr_bpm ? `${w.avg_hr_bpm} bpm` : "—" },
  ] : [
    { label: "Exercises", value: w.exercises?.length || 0 },
    { label: "Minutes", value: w.duration_min || 0 },
    { label: "Volume", value: `${Math.round(w.total_volume || 0)} kg` },
  ];

  return (
    <Link
      key={w.id}
      to={`/workouts/${w.id}`}
      className="card p-5 hover:shadow-md transition"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-xs uppercase text-slate-400 tracking-wide">
            {format(parseISO(w.started_at), "EEE, MMM d • h:mm a")}
          </p>
          <h3 className="font-semibold text-slate-900 mt-1 truncate">
            {w.name || "Workout session"}
          </h3>
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          {w.source ? (
            <SourceBadge source={w.source} />
          ) : (
            <span className={`badge ${
              w.status === "completed"
                ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300"
                : "bg-amber-50 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300"
            }`}>
              {w.status}
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2 mt-4 text-sm">
        {stats.map((s) => <Stat key={s.label} label={s.label} value={s.value} />)}
      </div>

      {w.calories_burned > 0 && (
        <p className="mt-2 text-xs text-slate-400">
          {w.calories_burned} kcal burned
        </p>
      )}
    </Link>
  );
}

export default function Workouts() {
  const { data, isLoading } = useQuery({
    queryKey: ["workouts"],
    queryFn: () => workoutsApi.list(),
  });
  const items = data?.results || data || [];

  return (
    <div>
      <PageHeader
        title="Workouts"
        subtitle="Your training history"
        actions={
          <Link to="/workouts/new" className="btn-primary">
            <Plus className="w-4 h-4" /> Log workout
          </Link>
        }
      />

      {isLoading ? (
        <p className="text-slate-500">Loading…</p>
      ) : items.length === 0 ? (
        <EmptyState
          icon={Dumbbell}
          title="No workouts yet"
          description="Log your first session or connect your watch to start tracking."
          action={
            <Link to="/workouts/new" className="btn-primary">
              Log a workout
            </Link>
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((w) => <WorkoutCard key={w.id} w={w} />)}
        </div>
      )}
    </div>
  );
}
