import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Dumbbell, Plus } from "lucide-react";
import { format, parseISO } from "date-fns";

import PageHeader from "../components/PageHeader.jsx";
import EmptyState from "../components/EmptyState.jsx";
import { workoutsApi } from "../api/endpoints.js";

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
          description="Log your first session to start tracking progress."
          action={
            <Link to="/workouts/new" className="btn-primary">
              Log a workout
            </Link>
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((w) => (
            <Link
              key={w.id}
              to={`/workouts/${w.id}`}
              className="card p-5 hover:shadow-md transition"
            >
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs uppercase text-slate-400 tracking-wide">
                    {format(parseISO(w.started_at), "EEE, MMM d • h:mm a")}
                  </p>
                  <h3 className="font-semibold text-slate-900 mt-1">
                    {w.name || "Workout session"}
                  </h3>
                </div>
                <span
                  className={`badge ${
                    w.status === "completed"
                      ? "bg-emerald-50 text-emerald-700"
                      : "bg-amber-50 text-amber-700"
                  }`}
                >
                  {w.status}
                </span>
              </div>
              <div className="grid grid-cols-3 gap-2 mt-4 text-sm">
                <Stat label="Exercises" value={w.exercises?.length || 0} />
                <Stat label="Minutes" value={w.duration_min || 0} />
                <Stat label="Volume" value={`${Math.round(w.total_volume || 0)} kg`} />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="bg-slate-50 rounded-lg px-3 py-2">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="font-semibold text-slate-900">{value}</p>
    </div>
  );
}
