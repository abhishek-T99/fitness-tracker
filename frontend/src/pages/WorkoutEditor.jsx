import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2, GripVertical } from "lucide-react";
import toast from "react-hot-toast";

import PageHeader from "../components/PageHeader.jsx";
import { exercisesApi, workoutsApi } from "../api/endpoints.js";

function blankSet(n) {
  return { set_number: n, reps: "", weight: "", rpe: "", is_warmup: false, completed: true };
}

export default function WorkoutEditor() {
  const { id } = useParams();
  const editing = !!id;
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [name, setName] = useState("");
  const [notes, setNotes] = useState("");
  const [startedAt, setStartedAt] = useState(new Date().toISOString().slice(0, 16));
  const [duration, setDuration] = useState("");
  const [calories, setCalories] = useState("");
  const [rpe, setRpe] = useState("");
  const [items, setItems] = useState([]);
  const [pickerOpen, setPickerOpen] = useState(false);

  const { data: existing } = useQuery({
    queryKey: ["workout", id],
    queryFn: () => workoutsApi.retrieve(id),
    enabled: editing,
  });

  useEffect(() => {
    if (existing) {
      setName(existing.name || "");
      setNotes(existing.notes || "");
      setStartedAt(existing.started_at.slice(0, 16));
      setDuration(existing.duration_min || "");
      setCalories(existing.calories_burned || "");
      setRpe(existing.perceived_exertion || "");
      setItems(
        existing.exercises.map((we) => ({
          exercise: we.exercise,
          exercise_detail: we.exercise_detail,
          order: we.order,
          notes: we.notes,
          sets: we.sets.map((s, idx) => ({
            set_number: s.set_number || idx + 1,
            reps: s.reps || "",
            weight: s.weight || "",
            rpe: s.rpe || "",
            is_warmup: s.is_warmup,
            completed: s.completed,
          })),
        }))
      );
    }
  }, [existing]);

  const save = useMutation({
    mutationFn: (payload) =>
      editing ? workoutsApi.update(id, payload) : workoutsApi.create(payload),
    onSuccess: (res) => {
      toast.success(editing ? "Workout updated" : "Workout saved");
      queryClient.invalidateQueries({ queryKey: ["workouts"] });
      queryClient.invalidateQueries({ queryKey: ["workoutStats"] });
      queryClient.invalidateQueries({ queryKey: ["streak"] });
      navigate(`/workouts/${res.id}`);
    },
    onError: (err) => {
      toast.error(err?.response?.data?.detail || "Could not save workout");
    },
  });

  const addExercise = (ex) => {
    setItems([
      ...items,
      {
        exercise: ex.id,
        exercise_detail: ex,
        order: items.length,
        notes: "",
        sets: [blankSet(1), blankSet(2), blankSet(3)],
      },
    ]);
    setPickerOpen(false);
  };

  const removeExercise = (idx) => setItems(items.filter((_, i) => i !== idx));

  const updateSet = (exIdx, setIdx, field, value) => {
    const copy = [...items];
    copy[exIdx].sets[setIdx][field] = value;
    setItems(copy);
  };

  const addSet = (exIdx) => {
    const copy = [...items];
    copy[exIdx].sets.push(blankSet(copy[exIdx].sets.length + 1));
    setItems(copy);
  };

  const removeSet = (exIdx, setIdx) => {
    const copy = [...items];
    copy[exIdx].sets = copy[exIdx].sets.filter((_, i) => i !== setIdx);
    setItems(copy);
  };

  const onSubmit = (e) => {
    e.preventDefault();
    if (items.length === 0) {
      toast.error("Add at least one exercise");
      return;
    }
    const payload = {
      name,
      notes,
      started_at: new Date(startedAt).toISOString(),
      duration_min: duration ? Number(duration) : null,
      calories_burned: calories ? Number(calories) : null,
      perceived_exertion: rpe ? Number(rpe) : null,
      status: "completed",
      exercises: items.map((it, idx) => ({
        exercise: it.exercise,
        order: idx,
        notes: it.notes,
        sets: it.sets.map((s, sIdx) => ({
          set_number: sIdx + 1,
          reps: s.reps ? Number(s.reps) : null,
          weight: s.weight !== "" ? Number(s.weight) : null,
          rpe: s.rpe ? Number(s.rpe) : null,
          is_warmup: !!s.is_warmup,
          completed: s.completed !== false,
        })),
      })),
    };
    save.mutate(payload);
  };

  return (
    <div>
      <PageHeader
        title={editing ? "Edit workout" : "Log a workout"}
        subtitle="Add exercises and track each set"
      />

      <form onSubmit={onSubmit} className="space-y-6">
        <div className="card p-5 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="label">Name</label>
            <input
              className="input"
              placeholder="Push day"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div>
            <label className="label">Started at</label>
            <input
              type="datetime-local"
              className="input"
              value={startedAt}
              onChange={(e) => setStartedAt(e.target.value)}
            />
          </div>
          <div>
            <label className="label">Duration (min)</label>
            <input
              type="number"
              className="input"
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
            />
          </div>
          <div>
            <label className="label">Calories burned</label>
            <input
              type="number"
              className="input"
              value={calories}
              onChange={(e) => setCalories(e.target.value)}
            />
          </div>
          <div>
            <label className="label">Perceived effort (1-10)</label>
            <input
              type="number"
              min="1"
              max="10"
              className="input"
              value={rpe}
              onChange={(e) => setRpe(e.target.value)}
            />
          </div>
          <div className="md:col-span-2">
            <label className="label">Notes</label>
            <textarea
              rows={2}
              className="input"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>
        </div>

        <div className="space-y-4">
          {items.map((it, exIdx) => (
            <div key={exIdx} className="card">
              <div className="card-header">
                <div className="flex items-center gap-2">
                  <GripVertical className="w-4 h-4 text-slate-400" />
                  <div>
                    <h4 className="font-semibold">{it.exercise_detail?.name}</h4>
                    <p className="text-xs text-slate-500 capitalize">
                      {it.exercise_detail?.primary_muscle} ·{" "}
                      {it.exercise_detail?.equipment}
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => removeExercise(exIdx)}
                  className="text-rose-500 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-500/10 p-2 rounded"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
              <div className="card-body">
                <table className="w-full text-sm">
                  <thead className="text-slate-500 text-xs">
                    <tr className="text-left">
                      <th className="pb-2 font-medium w-12">Set</th>
                      <th className="pb-2 font-medium">Reps</th>
                      {!["bodyweight", "cardio"].includes(it.exercise_detail?.equipment) && (
                        <th className="pb-2 font-medium">Weight (kg)</th>
                      )}
                      <th className="pb-2 font-medium">RPE</th>
                      <th className="pb-2 font-medium">Warmup</th>
                      <th className="pb-2 font-medium w-10"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {it.sets.map((s, sIdx) => (
                      <tr key={sIdx} className="border-t border-slate-100">
                        <td className="py-1">{sIdx + 1}</td>
                        <td className="py-1 pr-2">
                          <input
                            className="input py-1"
                            type="number"
                            value={s.reps}
                            onChange={(e) =>
                              updateSet(exIdx, sIdx, "reps", e.target.value)
                            }
                          />
                        </td>
                        {!["bodyweight", "cardio"].includes(it.exercise_detail?.equipment) && (
                        <td className="py-1 pr-2">
                          <input
                            className="input py-1"
                            type="number"
                            step="0.5"
                            value={s.weight}
                            onChange={(e) =>
                              updateSet(exIdx, sIdx, "weight", e.target.value)
                            }
                          />
                        </td>
                        )}
                        <td className="py-1 pr-2">
                          <input
                            className="input py-1"
                            type="number"
                            min="1"
                            max="10"
                            value={s.rpe}
                            onChange={(e) =>
                              updateSet(exIdx, sIdx, "rpe", e.target.value)
                            }
                          />
                        </td>
                        <td className="py-1">
                          <input
                            type="checkbox"
                            checked={s.is_warmup}
                            onChange={(e) =>
                              updateSet(exIdx, sIdx, "is_warmup", e.target.checked)
                            }
                          />
                        </td>
                        <td className="py-1 text-right">
                          <button
                            type="button"
                            onClick={() => removeSet(exIdx, sIdx)}
                            className="text-slate-400 hover:text-rose-500"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <button
                  type="button"
                  onClick={() => addSet(exIdx)}
                  className="btn-ghost mt-3"
                >
                  <Plus className="w-4 h-4" /> Add set
                </button>
              </div>
            </div>
          ))}
        </div>

        <button
          type="button"
          onClick={() => setPickerOpen(true)}
          className="btn-secondary w-full"
        >
          <Plus className="w-4 h-4" /> Add exercise
        </button>

        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="btn-secondary"
          >
            Cancel
          </button>
          <button type="submit" className="btn-primary" disabled={save.isPending}>
            {save.isPending ? "Saving…" : editing ? "Update workout" : "Save workout"}
          </button>
        </div>
      </form>

      {pickerOpen && (
        <ExercisePicker onPick={addExercise} onClose={() => setPickerOpen(false)} />
      )}
    </div>
  );
}

function ExercisePicker({ onPick, onClose }) {
  const [search, setSearch] = useState("");
  const { data } = useQuery({
    queryKey: ["exercisePicker", search],
    queryFn: () => exercisesApi.list({ search, page_size: 50 }),
  });
  const items = data?.results || [];

  return (
    <div className="fixed inset-0 z-40 bg-black/60 flex items-center justify-center p-4">
      <div className="bg-surface rounded-2xl shadow-xl w-full max-w-2xl max-h-[80vh] flex flex-col">
        <div className="border-b border-slate-200 px-5 py-4 flex items-center justify-between">
          <h3 className="font-semibold">Add exercise</h3>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-900">
            ✕
          </button>
        </div>
        <div className="p-4 border-b border-slate-100">
          <input
            autoFocus
            className="input"
            placeholder="Search exercises…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="overflow-y-auto p-2">
          {items.map((ex) => (
            <button
              key={ex.id}
              type="button"
              onClick={() => onPick(ex)}
              className="w-full text-left p-3 rounded-lg hover:bg-slate-50 flex justify-between items-center"
            >
              <div>
                <p className="font-medium">{ex.name}</p>
                <p className="text-xs text-slate-500 capitalize">
                  {ex.primary_muscle} · {ex.equipment}
                </p>
              </div>
              <span className="text-xs text-brand-600 font-medium">Add →</span>
            </button>
          ))}
          {items.length === 0 && (
            <p className="text-sm text-slate-500 text-center py-6">No matches</p>
          )}
        </div>
      </div>
    </div>
  );
}
