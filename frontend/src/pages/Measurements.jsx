import { useState } from "react";
import { useForm } from "react-hook-form";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
} from "recharts";
import { format, parseISO } from "date-fns";
import { Plus, Trash2, Pencil, Lightbulb } from "lucide-react";
import toast from "react-hot-toast";

import PageHeader from "../components/PageHeader.jsx";
import { measurementsApi } from "../api/endpoints.js";
import { qk } from "../api/queryKeys.js";

export default function Measurements() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(null);

  const { data: list } = useQuery({ queryKey: qk.measurements.all(), queryFn: measurementsApi.list });
  const { data: history } = useQuery({
    queryKey: qk.measurements.weightHistory(),
    queryFn: () => measurementsApi.weightHistory(180),
  });
  const items = list?.results || list || [];

  const remove = useMutation({
    mutationFn: (id) => measurementsApi.remove(id),
    onSuccess: () => {
      toast.success("Deleted");
      queryClient.invalidateQueries({ queryKey: qk.measurements.all() });
      queryClient.invalidateQueries({ queryKey: qk.measurements.weightHistory() });
    },
  });

  const chartData = (history || []).map((r) => ({
    date: format(parseISO(r.recorded_at), "MMM d"),
    weight: parseFloat(r.weight_kg),
  }));

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: qk.measurements.all() });
    queryClient.invalidateQueries({ queryKey: qk.measurements.weightHistory() });
  };

  return (
    <div>
      <PageHeader
        title="Measurements"
        subtitle="Body weight, body fat, and circumference history"
        actions={
          <button className="btn-primary" onClick={() => setOpen(true)}>
            <Plus className="w-4 h-4" /> Add entry
          </button>
        }
      />

      {/* Weight chart */}
      <div className="card mb-6">
        <div className="card-header"><h3 className="font-semibold">Weight trend</h3></div>
        <div className="card-body h-48">
          {chartData.length === 0 ? (
            <div className="h-full flex items-center justify-center text-slate-400 text-sm">
              Log a measurement to see your trend.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis domain={["auto", "auto"]} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line type="monotone" dataKey="weight" stroke="#0ea5e9" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* History table */}
      <div className="card">
        <div className="card-header"><h3 className="font-semibold">History</h3></div>
        <div className="card-body overflow-x-auto">
          {items.length === 0 ? (
            <p className="text-sm text-slate-400 py-4">No entries yet.</p>
          ) : (
            <table className="w-full text-sm text-left">
              <thead>
                <tr className="text-xs text-slate-500 border-b border-slate-100">
                  <th className="pb-2 font-medium">Date</th>
                  <th className="pb-2 font-medium">Weight</th>
                  <th className="pb-2 font-medium">BMI</th>
                  <th className="pb-2 font-medium">Body fat</th>
                  <th className="pb-2 font-medium">Waist</th>
                  <th className="pb-2 font-medium">Resting HR</th>
                  <th className="pb-2 font-medium">Notes / Watch data</th>
                  <th className="pb-2 font-medium w-16"></th>
                </tr>
              </thead>
              <tbody>
                {items.map((m) => (
                  <tr key={m.id} className="border-t border-slate-100">
                    <td className="py-2 whitespace-nowrap">{format(parseISO(m.recorded_at), "MMM d, yyyy")}</td>
                    <td className="py-2">{m.weight_kg ? `${m.weight_kg} kg` : "—"}</td>
                    <td className="py-2">{m.bmi ?? "—"}</td>
                    <td className="py-2">
                      {m.body_fat_percent ? (
                        <span className="font-medium">{m.body_fat_percent}%</span>
                      ) : m.estimated_body_fat ? (
                        <span className="text-slate-400 italic" title={`Estimated via ${m.estimated_body_fat.formula}`}>
                          ~{m.estimated_body_fat.value}%
                        </span>
                      ) : "—"}
                    </td>
                    <td className="py-2">{m.waist_cm ? `${m.waist_cm} cm` : "—"}</td>
                    <td className="py-2">
                      {m.resting_hr_bpm ? (
                        <span className="text-rose-500 font-medium">{m.resting_hr_bpm} bpm</span>
                      ) : "—"}
                    </td>
                    <td className="py-2 text-slate-500 text-xs max-w-[200px]">
                      {m.notes
                        ? m.notes.startsWith("Synced from Intervals.icu")
                          ? <span className="inline-flex items-center gap-1">
                              <span className="inline-block w-2 h-2 rounded-full bg-rose-400 shrink-0" />
                              {m.notes.replace("Synced from Intervals.icu · ", "")}
                            </span>
                          : m.notes
                        : "—"}
                    </td>
                    <td className="py-2 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => setEditing(m)}
                          className="p-1 text-slate-400 hover:text-brand-600 rounded transition-colors"
                          title="Edit"
                        >
                          <Pencil className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => remove.mutate(m.id)}
                          className="p-1 text-slate-400 hover:text-rose-500 rounded transition-colors"
                          title="Delete"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {open && (
        <MeasurementModal
          onClose={() => setOpen(false)}
          onSaved={() => { setOpen(false); invalidate(); }}
        />
      )}
      {editing && (
        <MeasurementModal
          measurement={editing}
          onClose={() => setEditing(null)}
          onSaved={() => { setEditing(null); invalidate(); }}
        />
      )}
    </div>
  );
}

function MeasurementModal({ measurement = null, onClose, onSaved }) {
  const isEditing = !!measurement;
  const [bfEstimate, setBfEstimate] = useState(null);

  const { register, handleSubmit, watch, setValue } = useForm({
    defaultValues: {
      recorded_at:      measurement?.recorded_at      ?? format(new Date(), "yyyy-MM-dd"),
      weight_kg:        measurement?.weight_kg         ?? "",
      body_fat_percent: measurement?.body_fat_percent  ?? "",
      chest_cm:         measurement?.chest_cm          ?? "",
      waist_cm:         measurement?.waist_cm          ?? "",
      hips_cm:          measurement?.hips_cm           ?? "",
      neck_cm:          measurement?.neck_cm           ?? "",
      arm_cm:           measurement?.arm_cm            ?? "",
      thigh_cm:         measurement?.thigh_cm          ?? "",
      resting_hr_bpm:   measurement?.resting_hr_bpm    ?? "",
      notes:            measurement?.notes             ?? "",
    },
  });

  const save = useMutation({
    mutationFn: (data) =>
      isEditing
        ? measurementsApi.update(measurement.id, data)
        : measurementsApi.create(data),
    onSuccess: () => {
      toast.success(isEditing ? "Measurement updated" : "Measurement recorded");
      onSaved();
    },
    onError: (err) => toast.error(err?.response?.data?.detail || "Could not save"),
  });

  // Live BF estimate: re-compute whenever relevant fields change
  const [waist, neck, hips] = watch(["waist_cm", "neck_cm", "hips_cm"]);

  // We call the latest-endpoint to get user profile data for the estimate
  const { data: latestData } = useQuery({
    queryKey: qk.measurements.latest(),
    queryFn: measurementsApi.latest,
    staleTime: 60_000,
  });

  // We can't easily run the server-side formula in the browser without profile data,
  // so show the server's estimate once the entry exists (edit mode), or
  // show a prompt to save first (create mode).
  const serverEstimate = isEditing ? measurement?.estimated_body_fat : null;

  const onSubmit = (data) => {
    const payload = Object.fromEntries(
      Object.entries(data).filter(([, v]) => v !== "")
    );
    save.mutate(payload);
  };

  return (
    <div className="fixed inset-0 z-40 bg-black/60 flex items-center justify-center p-4 overflow-y-auto">
      <form
        onSubmit={handleSubmit(onSubmit)}
        className="bg-surface rounded-2xl shadow-xl w-full max-w-lg my-4"
      >
        <div className="border-b border-slate-200 px-5 py-4 flex justify-between items-center">
          <h3 className="font-semibold">{isEditing ? "Edit measurement" : "New measurement"}</h3>
          <button type="button" onClick={onClose} className="text-slate-400 hover:text-slate-600 text-lg leading-none">✕</button>
        </div>

        <div className="p-5 grid grid-cols-2 gap-3">
          <div className="col-span-2">
            <label className="label">Date</label>
            <input type="date" className="input" {...register("recorded_at", { required: true })} />
          </div>

          {/* Core measurements */}
          <div>
            <label className="label">Weight (kg)</label>
            <input type="number" step="0.1" className="input" {...register("weight_kg")} />
          </div>
          <div>
            <label className="label">
              Body fat (%)
              {serverEstimate && (
                <span className="ml-1 text-xs font-normal text-slate-400">
                  — estimated below
                </span>
              )}
            </label>
            <input type="number" step="0.1" className="input" {...register("body_fat_percent")} />
          </div>

          {/* Body fat estimate callout (edit mode only) */}
          {serverEstimate && (
            <div className="col-span-2 rounded-xl border border-amber-200 dark:border-amber-500/30 bg-amber-50 dark:bg-amber-500/10 p-3.5 flex items-start gap-3">
              <Lightbulb className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-amber-800 dark:text-amber-300">
                  Estimated body fat: <span className="font-bold">{serverEstimate.value}%</span>
                </p>
                <p className="text-xs text-amber-600 dark:text-amber-400 mt-0.5">
                  {serverEstimate.formula === "navy"
                    ? "U.S. Navy formula (waist + neck + height). Accuracy ±1–3%."
                    : "Deurenberg BMI formula (BMI + age + sex). Add neck_cm for higher accuracy (±1–3%)."}
                </p>
                <button
                  type="button"
                  onClick={() => setValue("body_fat_percent", serverEstimate.value)}
                  className="mt-2 text-xs font-semibold text-amber-700 dark:text-amber-300 underline hover:no-underline"
                >
                  Use this estimate →
                </button>
              </div>
            </div>
          )}

          {/* Circumferences */}
          <div>
            <label className="label">Chest (cm)</label>
            <input type="number" step="0.1" className="input" {...register("chest_cm")} />
          </div>
          <div>
            <label className="label">Waist (cm)</label>
            <input type="number" step="0.1" className="input" {...register("waist_cm")} />
          </div>
          <div>
            <label className="label">Hips (cm)</label>
            <input type="number" step="0.1" className="input" {...register("hips_cm")} />
          </div>
          <div>
            <label className="label">
              Neck (cm)
              <span className="ml-1 text-[10px] font-normal text-brand-500">used for BF estimate</span>
            </label>
            <input type="number" step="0.1" className="input" {...register("neck_cm")} />
          </div>
          <div>
            <label className="label">
              Upper arm (cm)
              <span className="block text-[10px] font-normal text-slate-400 mt-0.5">
                Flexed bicep at widest point
              </span>
            </label>
            <input type="number" step="0.1" className="input" {...register("arm_cm")} />
          </div>
          <div>
            <label className="label">Thigh (cm)</label>
            <input type="number" step="0.1" className="input" {...register("thigh_cm")} />
          </div>
          <div>
            <label className="label">Resting HR (bpm)</label>
            <input type="number" className="input" {...register("resting_hr_bpm")} />
          </div>
          <div className="col-span-2">
            <label className="label">Notes</label>
            <input className="input" {...register("notes")} />
          </div>
        </div>

        {/* Info about BF estimate availability */}
        {!isEditing && (
          <div className="px-5 pb-4">
            <p className="text-xs text-slate-400">
              Body fat % will be estimated automatically after saving if you provide neck + waist (+ hips for women).
            </p>
          </div>
        )}

        <div className="border-t border-slate-200 px-5 py-4 flex justify-end gap-2">
          <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
          <button type="submit" className="btn-primary" disabled={save.isPending}>
            {save.isPending ? "Saving…" : isEditing ? "Update" : "Save"}
          </button>
        </div>
      </form>
    </div>
  );
}
