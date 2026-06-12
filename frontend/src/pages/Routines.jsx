import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, ListChecks, Trash2 } from "lucide-react";
import toast from "react-hot-toast";

import PageHeader from "../components/PageHeader.jsx";
import EmptyState from "../components/EmptyState.jsx";
import { routinesApi } from "../api/endpoints.js";

export default function Routines() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["routines"],
    queryFn: routinesApi.list,
  });
  const items = data?.results || data || [];

  const remove = useMutation({
    mutationFn: (id) => routinesApi.remove(id),
    onSuccess: () => {
      toast.success("Routine deleted");
      queryClient.invalidateQueries({ queryKey: ["routines"] });
    },
  });

  return (
    <div>
      <PageHeader
        title="Routines"
        subtitle="Reusable workout templates"
        actions={
          <Link to="/routines/new" className="btn-primary">
            <Plus className="w-4 h-4" /> New routine
          </Link>
        }
      />

      {isLoading ? (
        <p className="text-slate-500">Loading…</p>
      ) : items.length === 0 ? (
        <EmptyState
          icon={ListChecks}
          title="No routines yet"
          description="Save your favorite workouts as templates to reuse."
          action={
            <Link to="/routines/new" className="btn-primary">
              Create routine
            </Link>
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((r) => (
            <div key={r.id} className="card p-5">
              <div className="flex items-start justify-between">
                <Link to={`/routines/${r.id}`} className="flex-1">
                  <h3 className="font-semibold hover:text-brand-600">{r.name}</h3>
                  {r.description && (
                    <p className="text-sm text-slate-500 mt-1 line-clamp-2">
                      {r.description}
                    </p>
                  )}
                </Link>
                <button
                  onClick={() => {
                    if (confirm("Delete this routine?")) remove.mutate(r.id);
                  }}
                  className="text-slate-400 hover:text-rose-500"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
              <div className="mt-3 flex flex-wrap gap-2 text-xs">
                <span className="badge bg-brand-50 text-brand-700">
                  {r.items?.length || 0} exercises
                </span>
                {r.estimated_duration_min && (
                  <span className="badge bg-slate-100 text-slate-700">
                    ~{r.estimated_duration_min} min
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
