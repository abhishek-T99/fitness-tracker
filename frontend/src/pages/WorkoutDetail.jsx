import { Link, useNavigate, useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { format, parseISO } from "date-fns";
import { Pencil, Trash2 } from "lucide-react";
import toast from "react-hot-toast";

import PageHeader from "../components/PageHeader.jsx";
import { workoutsApi } from "../api/endpoints.js";
import { qk } from "../api/queryKeys.js";

export default function WorkoutDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: w, isLoading } = useQuery({
    queryKey: qk.workouts.detail(id),
    queryFn: () => workoutsApi.retrieve(id),
  });

  const remove = useMutation({
    mutationFn: () => workoutsApi.remove(id),
    onSuccess: () => {
      toast.success("Workout deleted");
      queryClient.invalidateQueries({ queryKey: qk.workouts.all() });
      navigate("/workouts");
    },
  });

if (isLoading || !w) return <p className="text-slate-500">Loading…</p>;

  return (
    <div>
      <PageHeader
        title={w.name || "Workout"}
        subtitle={format(parseISO(w.started_at), "EEEE, MMM d, yyyy • h:mm a")}
        actions={
          <>
            <Link to={`/workouts/${id}/edit`} className="btn-secondary">
              <Pencil className="w-4 h-4" /> Edit
            </Link>
            <button
              onClick={() => {
                if (confirm("Delete this workout?")) remove.mutate();
              }}
              className="btn-danger"
            >
              <Trash2 className="w-4 h-4" /> Delete
            </button>
          </>
        }
      />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Metric label="Duration" value={`${w.duration_min || 0} min`} />
        <div className="card p-4">
          <p className="text-xs text-slate-500">Calories</p>
          <p className="text-xl font-bold mt-1">
            {w.calories_burned ?? (
              <span className="text-slate-400 text-base font-normal">—</span>
            )}
          </p>
        </div>
        <Metric label="RPE" value={w.perceived_exertion || "—"} />
        <Metric label="Total volume" value={`${Math.round(w.total_volume || 0)} kg`} />
      </div>

      {w.notes && (
        <div className="card mb-6 p-5">
          <h4 className="font-semibold mb-2">Notes</h4>
          <p className="text-slate-600 text-sm whitespace-pre-wrap">{w.notes}</p>
        </div>
      )}

      <div className="space-y-4">
        {w.exercises.map((we) => (
          <div key={we.id} className="card">
            <div className="card-header">
              <div>
                <h4 className="font-semibold">{we.exercise_detail?.name}</h4>
                <p className="text-xs text-slate-500 capitalize">
                  {we.exercise_detail?.primary_muscle} · {we.exercise_detail?.equipment}
                </p>
              </div>
            </div>
            <div className="card-body overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-slate-500 text-xs">
                  <tr className="text-left">
                    <th className="pb-2 font-medium">Set</th>
                    <th className="pb-2 font-medium">Reps</th>
                    <th className="pb-2 font-medium">Weight</th>
                    <th className="pb-2 font-medium">RPE</th>
                  </tr>
                </thead>
                <tbody>
                  {we.sets.map((s) => (
                    <tr key={s.id} className="border-t border-slate-100">
                      <td className="py-2">
                        {s.is_warmup ? <span className="badge bg-amber-50 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300">W</span> : s.set_number}
                      </td>
                      <td className="py-2">{s.reps ?? "—"}</td>
                      <td className="py-2">{s.weight ? `${s.weight} kg` : "—"}</td>
                      <td className="py-2">{s.rpe ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {we.notes && <p className="text-xs text-slate-500 mt-3">{we.notes}</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="card p-4">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-xl font-bold text-slate-900">{value}</p>
    </div>
  );
}
