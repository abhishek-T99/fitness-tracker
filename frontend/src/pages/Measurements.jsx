import { useState } from "react";
import { useForm } from "react-hook-form";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import { format, parseISO } from "date-fns";
import { Plus, Trash2 } from "lucide-react";
import toast from "react-hot-toast";

import PageHeader from "../components/PageHeader.jsx";
import { measurementsApi } from "../api/endpoints.js";

export default function Measurements() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);

  const { data: list } = useQuery({
    queryKey: ["measurements"],
    queryFn: measurementsApi.list,
  });
  const { data: history } = useQuery({
    queryKey: ["weightHistory"],
    queryFn: () => measurementsApi.weightHistory(180),
  });
  const items = list?.results || list || [];

  const remove = useMutation({
    mutationFn: (id) => measurementsApi.remove(id),
    onSuccess: () => {
      toast.success("Deleted");
      queryClient.invalidateQueries({ queryKey: ["measurements"] });
      queryClient.invalidateQueries({ queryKey: ["weightHistory"] });
    },
  });

  const chartData = (history || []).map((r) => ({
    date: format(parseISO(r.recorded_at), "MMM d"),
    weight: parseFloat(r.weight_kg),
  }));

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

      <div className="card mb-6">
        <div className="card-header">
          <h3 className="font-semibold">Weight (last 6 months)</h3>
        </div>
        <div className="card-body h-72">
          {chartData.length === 0 ? (
            <div className="h-full flex items-center justify-center text-slate-400 text-sm">
              No entries yet.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis domain={["auto", "auto"]} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="weight"
                  stroke="#0ea5e9"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3 className="font-semibold">History</h3>
        </div>
        <div className="card-body overflow-x-auto">
          {items.length === 0 ? (
            <p className="text-slate-500 text-sm">No measurements yet.</p>
          ) : (
            <table className="w-full text-sm">
              <thead className="text-slate-500 text-xs">
                <tr className="text-left">
                  <th className="pb-2 font-medium">Date</th>
                  <th className="pb-2 font-medium">Weight</th>
                  <th className="pb-2 font-medium">BMI</th>
                  <th className="pb-2 font-medium">Body fat</th>
                  <th className="pb-2 font-medium">Waist</th>
                  <th className="pb-2 font-medium">Notes</th>
                  <th className="pb-2 font-medium w-10"></th>
                </tr>
              </thead>
              <tbody>
                {items.map((m) => (
                  <tr key={m.id} className="border-t border-slate-100">
                    <td className="py-2">{format(parseISO(m.recorded_at), "MMM d, yyyy")}</td>
                    <td className="py-2">{m.weight_kg ? `${m.weight_kg} kg` : "—"}</td>
                    <td className="py-2">{m.bmi ?? "—"}</td>
                    <td className="py-2">{m.body_fat_percent ? `${m.body_fat_percent}%` : "—"}</td>
                    <td className="py-2">{m.waist_cm ? `${m.waist_cm} cm` : "—"}</td>
                    <td className="py-2 text-slate-500">{m.notes}</td>
                    <td className="py-2 text-right">
                      <button
                        onClick={() => remove.mutate(m.id)}
                        className="text-slate-400 hover:text-rose-500"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
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
          onSaved={() => {
            setOpen(false);
            queryClient.invalidateQueries({ queryKey: ["measurements"] });
            queryClient.invalidateQueries({ queryKey: ["weightHistory"] });
          }}
        />
      )}
    </div>
  );
}

function MeasurementModal({ onClose, onSaved }) {
  const { register, handleSubmit } = useForm({
    defaultValues: { recorded_at: format(new Date(), "yyyy-MM-dd") },
  });
  const save = useMutation({
    mutationFn: (data) => measurementsApi.create(data),
    onSuccess: () => {
      toast.success("Recorded");
      onSaved();
    },
    onError: (err) => toast.error(err?.response?.data?.detail || "Could not save"),
  });

  const onSubmit = (data) => {
    const payload = Object.fromEntries(
      Object.entries(data).filter(([, v]) => v !== "")
    );
    save.mutate(payload);
  };

  return (
    <div className="fixed inset-0 z-40 bg-slate-900/40 flex items-center justify-center p-4">
      <form
        onSubmit={handleSubmit(onSubmit)}
        className="bg-white rounded-2xl shadow-xl w-full max-w-lg"
      >
        <div className="border-b border-slate-200 px-5 py-4 flex justify-between">
          <h3 className="font-semibold">New measurement</h3>
          <button type="button" onClick={onClose}>✕</button>
        </div>
        <div className="p-5 grid grid-cols-2 gap-3">
          <div className="col-span-2">
            <label className="label">Date</label>
            <input type="date" className="input" {...register("recorded_at", { required: true })} />
          </div>
          <div>
            <label className="label">Weight (kg)</label>
            <input type="number" step="0.1" className="input" {...register("weight_kg")} />
          </div>
          <div>
            <label className="label">Body fat (%)</label>
            <input type="number" step="0.1" className="input" {...register("body_fat_percent")} />
          </div>
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
            <label className="label">Arm (cm)</label>
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
