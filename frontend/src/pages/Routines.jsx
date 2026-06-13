import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Plus, ListChecks, Trash2, Clock, ChevronDown, ChevronUp,
  Pencil, Dumbbell, Repeat2,
} from "lucide-react";
import toast from "react-hot-toast";

import PageHeader from "../components/PageHeader.jsx";
import EmptyState from "../components/EmptyState.jsx";
import SortableList, { DragHandle, SortableItem } from "../components/SortableList.jsx";
import { routinesApi } from "../api/endpoints.js";

// Colour a muscle-group badge
const MUSCLE_COLORS = {
  chest:      "bg-rose-50   text-rose-700   dark:bg-rose-500/15   dark:text-rose-300",
  back:       "bg-blue-50   text-blue-700   dark:bg-blue-500/15   dark:text-blue-300",
  shoulders:  "bg-violet-50 text-violet-700 dark:bg-violet-500/15 dark:text-violet-300",
  biceps:     "bg-indigo-50 text-indigo-700 dark:bg-indigo-500/15 dark:text-indigo-300",
  triceps:    "bg-purple-50 text-purple-700 dark:bg-purple-500/15 dark:text-purple-300",
  quads:      "bg-amber-50  text-amber-700  dark:bg-amber-500/15  dark:text-amber-300",
  hamstrings: "bg-orange-50 text-orange-700 dark:bg-orange-500/15 dark:text-orange-300",
  glutes:     "bg-pink-50   text-pink-700   dark:bg-pink-500/15   dark:text-pink-300",
  calves:     "bg-yellow-50 text-yellow-700 dark:bg-yellow-500/15 dark:text-yellow-300",
  core:       "bg-teal-50   text-teal-700   dark:bg-teal-500/15   dark:text-teal-300",
  full_body:  "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300",
  cardio:     "bg-sky-50    text-sky-700    dark:bg-sky-500/15    dark:text-sky-300",
  forearms:   "bg-slate-100 text-slate-700",
};

function muscleBadgeClass(muscle) {
  return MUSCLE_COLORS[muscle] || "bg-slate-100 text-slate-700";
}

// Summarise the unique muscles targeted by a routine
function musclesSummary(items) {
  const seen = new Set();
  const out = [];
  for (const item of items) {
    const m = item.exercise_detail?.primary_muscle;
    if (m && !seen.has(m)) { seen.add(m); out.push(m); }
  }
  return out;
}

function ExerciseRow({ item }) {
  const ex = item.exercise_detail;
  if (!ex) return null;

  const repsLabel = item.target_reps
    ? `${item.target_sets} × ${item.target_reps}`
    : item.target_duration_sec
    ? `${item.target_sets} × ${item.target_duration_sec}s`
    : `${item.target_sets} sets`;

  return (
    <div className="flex items-center gap-3 py-2 border-b border-slate-100 last:border-0">
      {/* order dot */}
      <span className="flex-shrink-0 flex h-6 w-6 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-500">
        {item.order + 1}
      </span>

      {/* name + muscle */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-slate-900 truncate">{ex.name}</p>
        <div className="flex items-center gap-1.5 mt-0.5 flex-wrap">
          <span className={`badge text-[10px] capitalize ${muscleBadgeClass(ex.primary_muscle)}`}>
            {ex.primary_muscle?.replace(/_/g, " ")}
          </span>
          <span className="text-[10px] text-slate-400 capitalize">{ex.equipment}</span>
        </div>
      </div>

      {/* sets × reps */}
      <div className="flex-shrink-0 text-right">
        <p className="text-sm font-semibold text-slate-800">{repsLabel}</p>
        {item.target_weight && (
          <p className="text-[10px] text-slate-400">{item.target_weight} kg</p>
        )}
        {item.rest_sec && (
          <p className="text-[10px] text-slate-400">{item.rest_sec}s rest</p>
        )}
      </div>
    </div>
  );
}

function RoutineCard({ r, onDelete, dragHandleProps }) {
  const [expanded, setExpanded] = useState(false);

  const items = r.items || [];
  const muscles = musclesSummary(items);
  // Show first 3 exercises collapsed, rest on expand
  const preview = items.slice(0, 3);
  const hasMore = items.length > 3;

  return (
    <div className="card flex flex-col">
      {/* ── Header ── */}
      <div className="p-5 flex items-start justify-between gap-3">
        <DragHandle dragHandleProps={dragHandleProps} className="mt-0.5 shrink-0" />
        <Link to={`/routines/${r.id}`} className="flex-1 min-w-0 group">
          <h3 className="font-semibold text-slate-900 group-hover:text-brand-600 truncate">
            {r.name}
          </h3>
          {r.description && (
            <p className="text-sm text-slate-500 mt-0.5 line-clamp-2">{r.description}</p>
          )}
        </Link>
        <div className="flex items-center gap-1 shrink-0">
          <Link
            to={`/routines/${r.id}`}
            className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100 hover:text-brand-600 transition-colors"
            title="Edit routine"
          >
            <Pencil className="w-3.5 h-3.5" />
          </Link>
          <button
            onClick={onDelete}
            className="p-1.5 rounded-lg text-slate-400 hover:bg-rose-50 hover:text-rose-500 transition-colors"
            title="Delete routine"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* ── Stats row ── */}
      <div className="px-5 pb-3 flex items-center gap-3 text-xs text-slate-500 border-b border-slate-100">
        <span className="flex items-center gap-1">
          <Dumbbell className="w-3.5 h-3.5" />
          {items.length} exercise{items.length !== 1 ? "s" : ""}
        </span>
        {r.estimated_duration_min && (
          <span className="flex items-center gap-1">
            <Clock className="w-3.5 h-3.5" />
            ~{r.estimated_duration_min} min
          </span>
        )}
        {r.is_public && (
          <span className="badge bg-emerald-50 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300 ml-auto">
            public
          </span>
        )}
      </div>

      {/* ── Muscles targeted ── */}
      {muscles.length > 0 && (
        <div className="px-5 py-2.5 flex flex-wrap gap-1.5 border-b border-slate-100">
          {muscles.map((m) => (
            <span key={m} className={`badge text-[10px] capitalize ${muscleBadgeClass(m)}`}>
              {m.replace(/_/g, " ")}
            </span>
          ))}
        </div>
      )}

      {/* ── Exercise list ── */}
      {items.length > 0 && (
        <div className="px-5 pt-2 pb-1">
          {(expanded ? items : preview).map((item) => (
            <ExerciseRow key={item.id} item={item} />
          ))}
        </div>
      )}

      {/* ── Expand / collapse ── */}
      {hasMore && (
        <button
          onClick={() => setExpanded((v) => !v)}
          className="flex items-center justify-center gap-1.5 py-2.5 text-xs text-slate-500 hover:text-brand-600 hover:bg-slate-50 rounded-b-xl transition-colors border-t border-slate-100"
        >
          {expanded ? (
            <><ChevronUp className="w-3.5 h-3.5" /> Show less</>
          ) : (
            <><ChevronDown className="w-3.5 h-3.5" /> Show {items.length - 3} more exercise{items.length - 3 !== 1 ? "s" : ""}</>
          )}
        </button>
      )}

      {/* Use routine CTA */}
      <div className="px-5 pb-4 pt-3 mt-auto">
        <Link
          to={`/workouts/new?routine=${r.id}`}
          className="btn-primary w-full text-sm"
        >
          <Repeat2 className="w-4 h-4" />
          Start workout
        </Link>
      </div>
    </div>
  );
}

export default function Routines() {
  const queryClient = useQueryClient();
  const [localItems, setLocalItems] = useState(null);

  const { data, isLoading } = useQuery({
    queryKey: ["routines"],
    queryFn: routinesApi.list,
  });
  const serverItems = data?.results || data || [];
  const items = localItems ?? serverItems;

  const remove = useMutation({
    mutationFn: (id) => routinesApi.remove(id),
    onSuccess: () => {
      toast.success("Routine deleted");
      queryClient.invalidateQueries({ queryKey: ["routines"] });
    },
  });

  function handleReorder(newIds) {
    const reordered = newIds.map((id) => items.find((r) => String(r.id) === id));
    setLocalItems(reordered);
    const payload = newIds.map((id, i) => ({ id: Number(id), order: i }));
    routinesApi.reorder(payload).catch(() => {
      toast.error("Couldn't save order");
      setLocalItems(null);
    });
  }

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
          description="Save your favourite workouts as templates to reuse."
          action={
            <Link to="/routines/new" className="btn-primary">
              Create routine
            </Link>
          }
        />
      ) : (
        <SortableList
          ids={items.map((r) => String(r.id))}
          onReorder={handleReorder}
          strategy="grid"
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
        >
          {items.map((r) => (
            <SortableItem key={r.id} id={String(r.id)}>
              {(dragHandleProps) => (
                <RoutineCard
                  r={r}
                  dragHandleProps={dragHandleProps}
                  onDelete={() => {
                    if (confirm("Delete this routine?")) remove.mutate(r.id);
                  }}
                />
              )}
            </SortableItem>
          ))}
        </SortableList>
      )}
    </div>
  );
}
