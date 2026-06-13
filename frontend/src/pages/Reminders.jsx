import { useState } from "react";
import { useForm, Controller } from "react-hook-form";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Bell, Plus, Trash2, Repeat, Clock,
  Dumbbell, Droplets, Apple, Ruler, PersonStanding, Settings,
} from "lucide-react";
import toast from "react-hot-toast";

import PageHeader from "../components/PageHeader.jsx";
import EmptyState from "../components/EmptyState.jsx";
import SortableList, { DragHandle, SortableItem } from "../components/SortableList.jsx";
import { remindersApi } from "../api/endpoints.js";

const DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];

const TYPES = [
  { value: "workout",     label: "Workout",             Icon: Dumbbell },
  { value: "water",       label: "Water / Hydration",   Icon: Droplets },
  { value: "meal",        label: "Meal / Nutrition",    Icon: Apple },
  { value: "measurement", label: "Measurement",         Icon: Ruler },
  { value: "movement",    label: "Movement / Stretch",  Icon: PersonStanding },
  { value: "custom",      label: "Custom",              Icon: Settings },
];

const INTERVAL_PRESETS = [
  { value: 30,  label: "Every 30 min" },
  { value: 45,  label: "Every 45 min" },
  { value: 60,  label: "Every hour" },
  { value: 90,  label: "Every 1.5 hrs" },
  { value: 120, label: "Every 2 hrs" },
  { value: 180, label: "Every 3 hrs" },
  { value: 240, label: "Every 4 hrs" },
  { value: 0,   label: "Custom…" },
];

function fmt(timeStr) {
  if (!timeStr) return "";
  const [h, m] = timeStr.split(":").map(Number);
  const ampm = h >= 12 ? "PM" : "AM";
  const hh = h % 12 || 12;
  return `${hh}:${String(m).padStart(2, "0")} ${ampm}`;
}

function intervalLabel(mins) {
  if (!mins) return "";
  if (mins < 60) return `${mins} min`;
  if (mins % 60 === 0) return `${mins / 60}h`;
  return `${Math.floor(mins / 60)}h ${mins % 60}m`;
}

// ── Reminder row in the list ───────────────────────────────────────────────

function ReminderRow({ r, onToggle, onDelete, dragHandleProps }) {
  const typeInfo = TYPES.find((t) => t.value === r.reminder_type) || TYPES[TYPES.length - 1];
  const TypeIcon = typeInfo.Icon;
  const isInterval = r.recurrence_type === "interval";

  return (
    <div className="card p-4 flex items-center gap-3">
      <DragHandle dragHandleProps={dragHandleProps} />

      {/* Type icon */}
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-slate-100 dark:bg-slate-100/10">
        <TypeIcon className="w-4 h-4 text-slate-600" />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <p className="font-semibold truncate">{r.title}</p>
        <div className="flex items-center gap-2 mt-0.5 flex-wrap">
          {isInterval ? (
            <span className="flex items-center gap-1 text-xs text-brand-600 dark:text-brand-400 font-medium">
              <Repeat className="w-3 h-3" />
              Every {intervalLabel(r.interval_minutes)} · {fmt(r.start_time)} – {fmt(r.end_time)}
            </span>
          ) : (
            <span className="flex items-center gap-1 text-xs text-slate-500">
              <Clock className="w-3 h-3" />
              {fmt(r.time_of_day)}
            </span>
          )}
          <span className="text-xs text-slate-400">
            {(r.days_of_week || []).length === 7 || (r.days_of_week || []).length === 0
              ? "every day"
              : (r.days_of_week || []).join(", ")}
          </span>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-2 shrink-0">
        <label className="inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            className="sr-only peer"
            checked={r.is_active}
            onChange={onToggle}
          />
          <div className="relative w-10 h-5 bg-slate-200 peer-checked:bg-brand-500 rounded-full transition">
            <span
              className={`absolute top-0.5 left-0.5 h-4 w-4 bg-white rounded-full transition ${
                r.is_active ? "translate-x-5" : ""
              }`}
            />
          </div>
        </label>
        <button onClick={onDelete} className="text-slate-400 hover:text-rose-500 p-1">
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────

export default function Reminders() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [localItems, setLocalItems] = useState(null);

  const { data } = useQuery({ queryKey: ["reminders"], queryFn: remindersApi.list });
  const serverItems = data?.results || data || [];
  const items = localItems ?? serverItems;

  function handleReorder(newIds) {
    const reordered = newIds.map((id) => items.find((r) => String(r.id) === id));
    setLocalItems(reordered);
    const payload = newIds.map((id, i) => ({ id: Number(id), order: i }));
    remindersApi.reorder(payload).catch(() => {
      toast.error("Couldn't save order");
      setLocalItems(null);
    });
  }

  const toggleActive = useMutation({
    mutationFn: ({ id, is_active }) => remindersApi.update(id, { is_active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["reminders"] }),
  });

  const remove = useMutation({
    mutationFn: (id) => remindersApi.remove(id),
    onSuccess: () => {
      toast.success("Reminder deleted");
      queryClient.invalidateQueries({ queryKey: ["reminders"] });
    },
  });

  return (
    <div>
      <PageHeader
        title="Reminders"
        subtitle="Stay on track throughout the day"
        actions={
          <button onClick={() => setOpen(true)} className="btn-primary">
            <Plus className="w-4 h-4" /> New reminder
          </button>
        }
      />

      {items.length === 0 ? (
        <EmptyState
          icon={Bell}
          title="No reminders yet"
          description="Set once-daily or repeating nudges for workouts, water, meals, and more."
          action={
            <button onClick={() => setOpen(true)} className="btn-primary">
              Add reminder
            </button>
          }
        />
      ) : (
        <SortableList
          ids={items.map((r) => String(r.id))}
          onReorder={handleReorder}
          className="space-y-3"
        >
          {items.map((r) => (
            <SortableItem key={r.id} id={String(r.id)}>
              {(dragHandleProps) => (
                <ReminderRow
                  r={r}
                  dragHandleProps={dragHandleProps}
                  onToggle={() => toggleActive.mutate({ id: r.id, is_active: !r.is_active })}
                  onDelete={() => remove.mutate(r.id)}
                />
              )}
            </SortableItem>
          ))}
        </SortableList>
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

// ── New reminder modal ─────────────────────────────────────────────────────

function ReminderModal({ onClose, onSaved }) {
  const [recurrence, setRecurrence] = useState("once");
  const [days, setDays] = useState(["mon", "tue", "wed", "thu", "fri", "sat", "sun"]);
  const [intervalPreset, setIntervalPreset] = useState(60);
  const [customInterval, setCustomInterval] = useState(45);

  const { register, handleSubmit, formState: { errors }, watch } = useForm({
    defaultValues: {
      reminder_type: "water",
      time_of_day: "08:00",
      start_time: "08:00",
      end_time: "20:00",
      title: "",
      notes: "",
    },
  });

  const save = useMutation({
    mutationFn: (data) => remindersApi.create(data),
    onSuccess: onSaved,
    onError: (err) => {
      const detail = err?.response?.data;
      toast.error(
        typeof detail === "string"
          ? detail
          : Object.values(detail || {}).flat().join(" ") || "Could not save reminder"
      );
    },
  });

  function onSubmit(data) {
    const effectiveInterval = intervalPreset === 0 ? customInterval : intervalPreset;

    const payload = {
      title: data.title,
      reminder_type: data.reminder_type,
      recurrence_type: recurrence,
      days_of_week: days,
      notes: data.notes,
      is_active: true,
    };

    if (recurrence === "once") {
      payload.time_of_day = data.time_of_day;
    } else {
      payload.start_time = data.start_time;
      payload.end_time = data.end_time;
      payload.interval_minutes = Number(effectiveInterval);
    }

    save.mutate(payload);
  }

  const reminderType = watch("reminder_type");
  const typeInfo = TYPES.find((t) => t.value === reminderType);

  // Suggested titles by type
  const suggestions = {
    water:       ["Drink water", "Stay hydrated", "Water break"],
    workout:     ["Morning workout", "Training session", "Gym time"],
    meal:        ["Breakfast", "Lunch", "Dinner", "Log your meal"],
    measurement: ["Weigh in", "Body measurements", "Track progress"],
    movement:    ["Stand up & stretch", "Quick walk", "Movement break"],
    custom:      [],
  };
  const typeSuggestions = suggestions[reminderType] || [];

  return (
    <div className="fixed inset-0 z-40 bg-black/60 flex items-center justify-center p-4 overflow-y-auto">
      <form
        onSubmit={handleSubmit(onSubmit)}
        className="bg-surface rounded-2xl shadow-xl w-full max-w-md my-4"
      >
        {/* Header */}
        <div className="border-b border-slate-200 px-5 py-4 flex justify-between items-center">
          <h3 className="font-semibold text-slate-900">New reminder</h3>
          <button type="button" onClick={onClose} className="text-slate-400 hover:text-slate-600 text-lg leading-none">✕</button>
        </div>

        <div className="p-5 space-y-4">

          {/* Reminder type */}
          <div>
            <label className="label">Type</label>
            <div className="grid grid-cols-3 gap-2">
              {TYPES.map((t) => {
                const TIcon = t.Icon;
                return (
                  <label
                    key={t.value}
                    className={`flex flex-col items-center gap-1.5 p-2.5 rounded-xl border cursor-pointer text-center transition ${
                      reminderType === t.value
                        ? "border-brand-500 bg-brand-50 dark:bg-brand-500/10"
                        : "border-slate-200 hover:border-slate-300"
                    }`}
                  >
                    <input type="radio" className="sr-only" value={t.value} {...register("reminder_type")} />
                    <TIcon className={`w-5 h-5 ${reminderType === t.value ? "text-brand-600" : "text-slate-500"}`} />
                    <span className="text-[10px] font-medium leading-tight text-slate-700">{t.label}</span>
                  </label>
                );
              })}
            </div>
          </div>

          {/* Title */}
          <div>
            <label className="label">Title</label>
            <input
              className="input"
              placeholder={typeSuggestions[0] || "My reminder"}
              {...register("title", { required: "Title is required" })}
            />
            {errors.title && <p className="text-xs text-rose-500 mt-1">{errors.title.message}</p>}
            {typeSuggestions.length > 0 && (
              <div className="flex gap-1.5 mt-1.5 flex-wrap">
                {typeSuggestions.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={(e) => {
                      e.preventDefault();
                      document.querySelector('input[name="title"]').value = s;
                      document.querySelector('input[name="title"]').dispatchEvent(new Event("input", { bubbles: true }));
                    }}
                    className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 hover:bg-brand-50 hover:text-brand-700 transition"
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Recurrence type toggle */}
          <div>
            <label className="label">Schedule</label>
            <div className="flex rounded-xl border border-slate-200 overflow-hidden">
              <button
                type="button"
                onClick={() => setRecurrence("once")}
                className={`flex-1 py-2.5 text-sm font-medium transition ${
                  recurrence === "once"
                    ? "bg-brand-600 text-white"
                    : "text-slate-600 hover:bg-slate-50"
                }`}
              >
                <Clock className="w-3.5 h-3.5 inline mr-1.5" />
                Once per day
              </button>
              <button
                type="button"
                onClick={() => setRecurrence("interval")}
                className={`flex-1 py-2.5 text-sm font-medium transition border-l border-slate-200 ${
                  recurrence === "interval"
                    ? "bg-brand-600 text-white"
                    : "text-slate-600 hover:bg-slate-50"
                }`}
              >
                <Repeat className="w-3.5 h-3.5 inline mr-1.5" />
                Repeat throughout day
              </button>
            </div>
          </div>

          {/* Once-per-day config */}
          {recurrence === "once" && (
            <div>
              <label className="label">Time</label>
              <input type="time" className="input" {...register("time_of_day", { required: recurrence === "once" })} />
            </div>
          )}

          {/* Interval config */}
          {recurrence === "interval" && (
            <div className="space-y-3 rounded-xl border border-brand-200 dark:border-brand-500/20 bg-brand-50 dark:bg-brand-500/5 p-4">
              <p className="text-xs text-brand-700 dark:text-brand-300 font-medium">
                Triggers at regular intervals between your start and end time.
              </p>

              {/* Interval presets */}
              <div>
                <label className="label">Repeat every</label>
                <div className="grid grid-cols-4 gap-1.5">
                  {INTERVAL_PRESETS.map((p) => (
                    <button
                      key={p.value}
                      type="button"
                      onClick={() => setIntervalPreset(p.value)}
                      className={`py-1.5 text-xs font-medium rounded-lg border transition ${
                        intervalPreset === p.value
                          ? "border-brand-500 bg-brand-600 text-white"
                          : "border-slate-200 bg-surface text-slate-600 hover:border-brand-300"
                      }`}
                    >
                      {p.label}
                    </button>
                  ))}
                </div>
                {intervalPreset === 0 && (
                  <div className="mt-2 flex items-center gap-2">
                    <input
                      type="number"
                      min="5"
                      max="480"
                      className="input w-24"
                      value={customInterval}
                      onChange={(e) => setCustomInterval(Number(e.target.value))}
                    />
                    <span className="text-sm text-slate-500">minutes</span>
                  </div>
                )}
              </div>

              {/* Time window */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">Start time</label>
                  <input type="time" className="input" {...register("start_time")} />
                </div>
                <div>
                  <label className="label">End time</label>
                  <input type="time" className="input" {...register("end_time")} />
                </div>
              </div>

              {/* Preview */}
              {(() => {
                const interval = intervalPreset === 0 ? customInterval : intervalPreset;
                const startVal = watch("start_time");
                const endVal   = watch("end_time");
                if (!startVal || !endVal || !interval) return null;
                const [sh, sm] = startVal.split(":").map(Number);
                const [eh, em] = endVal.split(":").map(Number);
                const startMins = sh * 60 + sm;
                const endMins   = eh * 60 + em;
                if (endMins <= startMins) return null;
                const count = Math.floor((endMins - startMins) / interval) + 1;
                return (
                  <p className="text-xs text-brand-600 dark:text-brand-300">
                    ↳ {count} reminder{count !== 1 ? "s" : ""} per day · first at {fmt(startVal)}, last at or before {fmt(endVal)}
                  </p>
                );
              })()}
            </div>
          )}

          {/* Days of week */}
          <div>
            <label className="label">Days</label>
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
                  className={`flex-1 py-1.5 text-xs uppercase font-semibold rounded-lg transition ${
                    days.includes(d)
                      ? "bg-brand-600 text-white"
                      : "bg-slate-100 text-slate-500 hover:bg-slate-200"
                  }`}
                >
                  {d.slice(0, 1).toUpperCase() + d.slice(1)}
                </button>
              ))}
            </div>
            <div className="flex gap-2 mt-1.5">
              {[
                { label: "Weekdays", days: ["mon","tue","wed","thu","fri"] },
                { label: "Weekends", days: ["sat","sun"] },
                { label: "Every day", days: DAYS },
              ].map(({ label, days: preset }) => (
                <button
                  key={label}
                  type="button"
                  onClick={() => setDays(preset)}
                  className="text-[10px] text-slate-500 hover:text-brand-600 underline"
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className="label">Notes <span className="text-slate-400 font-normal">(optional)</span></label>
            <input className="input" placeholder="Any extra context…" {...register("notes")} />
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-slate-200 px-5 py-4 flex justify-end gap-2">
          <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
          <button type="submit" className="btn-primary" disabled={save.isPending}>
            {save.isPending ? "Saving…" : "Save reminder"}
          </button>
        </div>
      </form>
    </div>
  );
}
