import { useState } from "react";
import { useForm } from "react-hook-form";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, Plus, Trash2 } from "lucide-react";
import toast from "react-hot-toast";

import PageHeader from "../components/PageHeader.jsx";
import EmptyState from "../components/EmptyState.jsx";
import { remindersApi } from "../api/endpoints.js";

const DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];
const TYPES = [
  { value: "workout", label: "Workout" },
  { value: "water", label: "Water" },
  { value: "meal", label: "Meal" },
  { value: "measurement", label: "Measurement" },
  { value: "custom", label: "Custom" },
];

export default function Reminders() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);

  const { data } = useQuery({ queryKey: ["reminders"], queryFn: remindersApi.list });
  const items = data?.results || data || [];

  const toggleActive = useMutation({
    mutationFn: ({ id, is_active }) => remindersApi.update(id, { is_active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["reminders"] }),
  });
  const remove = useMutation({
    mutationFn: (id) => remindersApi.remove(id),
    onSuccess: () => {
      toast.success("Removed");
      queryClient.invalidateQueries({ queryKey: ["reminders"] });
    },
  });

  return (
    <div>
      <PageHeader
        title="Reminders"
        subtitle="Schedule prompts to stay consistent"
        actions={
          <button onClick={() => setOpen(true)} className="btn-primary">
            <Plus className="w-4 h-4" /> New reminder
          </button>
        }
      />

      <p className="text-xs text-slate-500 mb-4">
        ⓘ Reminders are saved on the server. To receive push notifications, integrate a
        notifications service (e.g. web-push or a mobile client).
      </p>

      {items.length === 0 ? (
        <EmptyState
          icon={Bell}
          title="No reminders yet"
          description="Set up nudges for workouts, hydration, or meals."
          action={
            <button onClick={() => setOpen(true)} className="btn-primary">
              Add reminder
            </button>
          }
        />
      ) : (
        <div className="space-y-3">
          {items.map((r) => (
            <div key={r.id} className="card p-4 flex items-center justify-between">
              <div>
                <p className="font-semibold">{r.title}</p>
                <p className="text-xs text-slate-500 capitalize">
                  {r.reminder_type} · {r.time_of_day?.slice(0, 5)} ·{" "}
                  {(r.days_of_week || []).join(", ") || "every day"}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <label className="inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    className="sr-only peer"
                    checked={r.is_active}
                    onChange={() =>
                      toggleActive.mutate({ id: r.id, is_active: !r.is_active })
                    }
                  />
                  <div className="relative w-10 h-5 bg-slate-200 peer-checked:bg-brand-500 rounded-full transition">
                    <span
                      className={`absolute top-0.5 left-0.5 h-4 w-4 bg-white rounded-full transition ${
                        r.is_active ? "translate-x-5" : ""
                      }`}
                    />
                  </div>
                </label>
                <button
                  onClick={() => remove.mutate(r.id)}
                  className="text-slate-400 hover:text-rose-500"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {open && (
        <ReminderModal
          onClose={() => setOpen(false)}
          onSaved={() => {
            setOpen(false);
            queryClient.invalidateQueries({ queryKey: ["reminders"] });
          }}
        />
      )}
    </div>
  );
}

function ReminderModal({ onClose, onSaved }) {
  const { register, handleSubmit } = useForm({
    defaultValues: { reminder_type: "workout", time_of_day: "07:00" },
  });
  const [days, setDays] = useState(["mon", "wed", "fri"]);

  const save = useMutation({
    mutationFn: (data) =>
      remindersApi.create({
        ...data,
        days_of_week: days,
      }),
    onSuccess: onSaved,
    onError: () => toast.error("Could not save"),
  });

  return (
    <div className="fixed inset-0 z-40 bg-slate-900/40 flex items-center justify-center p-4">
      <form
        onSubmit={handleSubmit((d) => save.mutate(d))}
        className="bg-white rounded-2xl shadow-xl w-full max-w-md"
      >
        <div className="border-b border-slate-200 px-5 py-4 flex justify-between">
          <h3 className="font-semibold">New reminder</h3>
          <button type="button" onClick={onClose}>✕</button>
        </div>
        <div className="p-5 grid grid-cols-2 gap-3">
          <div className="col-span-2">
            <label className="label">Title</label>
            <input className="input" {...register("title", { required: true })} />
          </div>
          <div>
            <label className="label">Type</label>
            <select className="input" {...register("reminder_type")}>
              {TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Time</label>
            <input type="time" className="input" {...register("time_of_day", { required: true })} />
          </div>
          <div className="col-span-2">
            <label className="label">Days of week</label>
            <div className="flex gap-1">
              {DAYS.map((d) => (
                <button
                  type="button"
                  key={d}
                  onClick={() =>
                    setDays((prev) =>
                      prev.includes(d) ? prev.filter((x) => x !== d) : [...prev, d]
                    )
                  }
                  className={`flex-1 py-1 text-xs uppercase font-medium rounded ${
                    days.includes(d)
                      ? "bg-brand-600 text-white"
                      : "bg-slate-100 text-slate-600"
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>
          </div>
          <div className="col-span-2">
            <label className="label">Notes</label>
            <input className="input" {...register("notes")} />
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
