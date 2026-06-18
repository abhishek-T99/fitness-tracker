import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Dumbbell, Plus } from "lucide-react";
import { format, parseISO } from "date-fns";

import PageHeader from "../components/PageHeader.jsx";
import EmptyState from "../components/EmptyState.jsx";
import Pagination from "../components/Pagination.jsx";
import { workoutsApi } from "../api/endpoints.js";

const PAGE_SIZE = 12;

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

function SkeletonPulse({ className = "" }) {
  return <div className={`animate-pulse rounded-lg bg-slate-200 dark:bg-slate-700/50 ${className}`} />;
}

function WorkoutsSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="card p-5 space-y-4">
          <div className="flex items-start justify-between gap-2">
            <div className="space-y-2 flex-1">
              <SkeletonPulse className="h-3 w-28" />
              <SkeletonPulse className="h-4 w-40" />
            </div>
            <SkeletonPulse className="h-5 w-16 rounded-full" />
          </div>
          <div className="grid grid-cols-3 gap-2">
            {[1, 2, 3].map((j) => (
              <div key={j} className="bg-slate-50 dark:bg-slate-100/5 rounded-lg px-3 py-2 space-y-1.5">
                <SkeletonPulse className="h-2.5 w-12" />
                <SkeletonPulse className="h-4 w-8" />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function Workouts() {
  const [page, setPage] = useState(1);

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ["workouts", page],
    queryFn: () => workoutsApi.list({ page, page_size: PAGE_SIZE }),
    keepPreviousData: true,
  });

  const items      = data?.results ?? [];
  const totalCount = data?.count   ?? 0;

  return (
    <div>
      <PageHeader
        title="Workouts"
        subtitle={totalCount > 0 ? `${totalCount} sessions in your history` : "Your training history"}
        actions={
          <Link to="/workouts/new" className="btn-primary">
            <Plus className="w-4 h-4" /> Log workout
          </Link>
        }
      />

      {isLoading ? (
        <WorkoutsSkeleton />
      ) : items.length === 0 && page === 1 ? (
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
        <>
          <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 transition-opacity ${isFetching ? "opacity-60" : ""}`}>
            {items.map((w) => <WorkoutCard key={w.id} w={w} />)}
          </div>
          <Pagination
            page={page}
            pageSize={PAGE_SIZE}
            totalCount={totalCount}
            onChange={setPage}
          />
        </>
      )}
    </div>
  );
}
