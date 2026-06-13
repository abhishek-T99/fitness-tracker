import { useState } from "react";
import { useForm } from "react-hook-form";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Target, Trash2, Check } from "lucide-react";
import { format, parseISO } from "date-fns";
import toast from "react-hot-toast";

import PageHeader from "../components/PageHeader.jsx";
import EmptyState from "../components/EmptyState.jsx";
import SortableList, { DragHandle, SortableItem } from "../components/SortableList.jsx";
import { goalsApi } from "../api/endpoints.js";

const GOAL_TYPES = [
  { value: "weight_loss", label: "Weight loss" },
  { value: "weight_gain", label: "Weight gain" },
  { value: "strength", label: "Strength PR" },
  { value: "endurance", label: "Endurance" },
  { value: "workouts_per_week", label: "Workouts per week" },
  { value: "calories", label: "Daily calorie target" },
  { value: "custom", label: "Custom" },
];

export default function Goals() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [localItems, setLocalItems] = useState(null);

  const { data } = useQuery({ queryKey: ["goals"], queryFn: goalsApi.list });
  const serverItems = data?.results || data || [];
  const items = localItems ?? serverItems;

  const remove = useMutation({
    mutationFn: (id) => goalsApi.remove(id),
    onSuccess: () => {
      toast.success("Goal removed");
      queryClient.invalidateQueries({ queryKey: ["goals"] });
    },
  });

  const markAchieved = useMutation({
    mutationFn: (id) => goalsApi.update(id, { status: "achieved" }),
    onSuccess: () => {
      toast.success("Goal achieved!");
      queryClient.invalidateQueries({ queryKey: ["goals"] });
    },
  });

  const updateCurrent = useMutation({
    mutationFn: ({ id, current_value }) => goalsApi.update(id, { current_value }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["goals"] }),
  });

  function handleReorder(newIds) {
    const reordered = newIds.map((id) => items.find((g) => String(g.id) === String(id)));
    setLocalItems(reordered);
    const payload = newIds.map((id, i) => ({ id: Number(id), order: i }));
    goalsApi.reorder(payload).catch(() => {
      toast.error("Couldn't save order");
      setLocalItems(null);
    });
  }

  return (
    <div>
      <PageHeader
        title="Goals"
        subtitle="Targets keep you accountable"
        actions={
          <button className="btn-primary" onClick={() => setOpen(true)}>
            <Plus className="w-4 h-4" /> New goal
          </button>
        }
      />

      {items.length === 0 ? (
        <EmptyState
          icon={Target}
          title="No goals yet"
          description="Set a target — weight, strength PR, or weekly workouts."
          action={
            <button onClick={() => setOpen(true)} className="btn-primary">
              Set a goal
            </button>
          }
        />
      ) : (
        <SortableList
          ids={items.map((g) => String(g.id))}
          onReorder={handleReorder}
          strategy="grid"
          className="grid grid-cols-1 md:grid-cols-2 gap-4"
        >
          {items.map((g) => (
            <SortableItem key={g.id} id={String(g.id)}>
              {(dragHandleProps) => (
            <div className="card p-5">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <DragHandle dragHandleProps={dragHandleProps} className="shrink-0" />
                  <div className="min-w-0">
                    <span className={`badge ${badgeFor(g.status)}`}>{g.status}</span>
                    <h3 className="font-semibold mt-1">{g.title}</h3>
                    <p className="text-xs text-slate-500">
                      {GOAL_TYPES.find((t) => t.value === g.goal_type)?.label}
                    </p>
                  </div>
                </div>
                <div className="flex gap-1 shrink-0">
                  {g.status === "active" && (
                    <button
                      onClick={() => markAchieved.mutate(g.id)}
                      className="text-emerald-600 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-500/10 p-2 rounded"
                      title="Mark achieved"
                    >
                      <Check className="w-4 h-4" />
                    </button>
                  )}
                  <button
                    onClick={() => {
                      if (confirm("Delete this goal?")) remove.mutate(g.id);
                    }}
                    className="text-slate-400 hover:text-rose-500 p-2 rounded"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <div className="mb-2">
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-500">
                    {g.current_value} → {g.target_value} {g.unit}
                  </span>
                  <span className="font-semibold">{g.progress_percent}%</span>
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-brand-500"
                    style={{ width: `${g.progress_percent}%` }}
                  />
                </div>
              </div>
              {g.deadline && (
                <p className="text-xs text-slate-500">
                  Deadline: {format(parseISO(g.deadline), "MMM d, yyyy")}
                </p>
              )}
              {g.status === "active" && (
                <div className="mt-3 flex items-center gap-2">
                  <input
                    type="number"
                    step="0.1"
                    defaultValue={g.current_value}
                    className="input py-1 flex-1"
                    onBlur={(e) =>
                      e.target.value !== String(g.current_value) &&
                      updateCurrent.mutate({ id: g.id, current_value: e.target.value })
                    }
                  />
                  <span className="text-xs text-slate-500">update current</span>
                </div>
              )}
            </div>
              )}
            </SortableItem>
          ))}
        </SortableList>
      )}

      {open && (
        <GoalModal
          onClose={() => setOpen(false)}
          onSaved={() => {
            setOpen(false);
            queryClient.invalidateQueries({ queryKey: ["goals"] });
          }}
        />
      )}
    </div>
  );
}

function badgeFor(status) {
  return {
    active: "bg-brand-50 text-brand-700 dark:text-brand-300",
    achieved: "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300",
    abandoned: "bg-slate-100 text-slate-600",
  }[status];
}

function GoalModal({ onClose, onSaved }) {
  const { register, handleSubmit, formState: { errors } } = useForm();
  const save = useMutation({
    mutationFn: (data) => goalsApi.create(data),
    onSuccess: onSaved,
    onError: () => toast.error("Could not save goal"),
  });

  const onSubmit = (data) => {
    const payload = {
      ...data,
      target_value: Number(data.target_value),
      current_value: Number(data.current_value || 0),
      starting_value: Number(data.starting_value || data.current_value || 0),
    };
    if (!payload.deadline) delete payload.deadline;
    save.mutate(payload);
  };

  return (
    <div className="fixed inset-0 z-40 bg-black/60 flex items-center justify-center p-4">
      <form
        onSubmit={handleSubmit(onSubmit)}
        className="bg-surface rounded-2xl shadow-xl w-full max-w-md"
      >
        <div className="border-b border-slate-200 px-5 py-4 flex justify-between">
          <h3 className="font-semibold">New goal</h3>
          <button type="button" onClick={onClose}>✕</button>
        </div>
        <div className="p-5 grid grid-cols-2 gap-3">
          <div className="col-span-2">
            <label className="label">Title</label>
            <input className="input" {...register("title", { required: true })} />
          </div>
          <div className="col-span-2">
            <label className="label">Type</label>
            <select className="input" {...register("goal_type", { required: true })}>
              {GOAL_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Starting</label>
            <input type="number" step="0.1" className="input" {...register("starting_value")} />
          </div>
          <div>
            <label className="label">Current</label>
            <input type="number" step="0.1" className="input" {...register("current_value")} />
          </div>
          <div>
            <label className="label">Target *</label>
            <input
              type="number"
              step="0.1"
              className="input"
              {...register("target_value", { required: true })}
            />
            {errors.target_value && <p className="text-xs text-rose-500 mt-1">Required</p>}
          </div>
          <div>
            <label className="label">Unit</label>
            <input className="input" placeholder="kg, lb, reps…" {...register("unit")} />
          </div>
          <div className="col-span-2">
            <label className="label">Deadline (optional)</label>
            <input type="date" className="input" {...register("deadline")} />
          </div>
          <div className="col-span-2">
            <label className="label">Notes</label>
            <textarea rows={2} className="input" {...register("notes")} />
          </div>
        </div>
        <div className="border-t border-slate-200 px-5 py-4 flex justify-end gap-2">
          <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
          <button type="submit" className="btn-primary" disabled={save.isPending}>
            {save.isPending ? "Saving…" : "Save"}
          </button>
        </div>
      </form>
    </div>
  );
}
