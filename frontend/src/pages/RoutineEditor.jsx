import { useEffect, useId, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2 } from "lucide-react";
import toast from "react-hot-toast";
import { arrayMove } from "@dnd-kit/sortable";

import PageHeader from "../components/PageHeader.jsx";
import SortableList, { DragHandle, SortableItem } from "../components/SortableList.jsx";
import { exercisesApi, routinesApi } from "../api/endpoints.js";
import { qk } from "../api/queryKeys.js";

let _keySeq = 0;
const makeKey = () => String(++_keySeq);

export default function RoutineEditor() {
  const { id } = useParams();
  const editing = !!id;
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [duration, setDuration] = useState("");
  const [isPublic, setIsPublic] = useState(false);
  const [items, setItems] = useState([]);
  const [pickerOpen, setPickerOpen] = useState(false);

  const { data: existing } = useQuery({
    queryKey: qk.routines.detail(id),
    queryFn: () => routinesApi.retrieve(id),
    enabled: editing,
  });

  useEffect(() => {
    if (existing) {
      setName(existing.name);
      setDescription(existing.description || "");
      setDuration(existing.estimated_duration_min || "");
      setIsPublic(existing.is_public);
      setItems(
        existing.items.map((it) => ({
          _key: makeKey(),
          exercise: it.exercise,
          exercise_detail: it.exercise_detail,
          target_sets: it.target_sets,
          target_reps: it.target_reps || "",
          target_weight: it.target_weight || "",
          rest_sec: it.rest_sec,
          notes: it.notes || "",
        }))
      );
    }
  }, [existing]);

  const save = useMutation({
    mutationFn: (payload) =>
      editing ? routinesApi.update(id, payload) : routinesApi.create(payload),
    onSuccess: () => {
      toast.success("Routine saved");
      queryClient.invalidateQueries({ queryKey: qk.routines.all() });
      navigate("/routines");
    },
    onError: () => toast.error("Could not save routine"),
  });

  const addExercise = (ex) => {
    setItems((prev) => [
      ...prev,
      {
        _key: makeKey(),
        exercise: ex.id,
        exercise_detail: ex,
        target_sets: 3,
        target_reps: 10,
        target_weight: "",
        rest_sec: 60,
        notes: "",
      },
    ]);
    setPickerOpen(false);
  };

  const handleReorder = (newKeys) => {
    setItems((prev) => newKeys.map((k) => prev.find((it) => it._key === k)));
  };

  const updateItem = (idx, field, value) => {
    const copy = [...items];
    copy[idx][field] = value;
    setItems(copy);
  };

  const removeItem = (idx) => setItems(items.filter((_, i) => i !== idx));

  const onSubmit = (e) => {
    e.preventDefault();
    if (!name.trim()) {
      toast.error("Name is required");
      return;
    }
    save.mutate({
      name,
      description,
      estimated_duration_min: duration ? Number(duration) : null,
      is_public: isPublic,
      items: items.map((it, idx) => ({
        exercise: it.exercise,
        order: idx,
        target_sets: Number(it.target_sets) || 3,
        target_reps: it.target_reps ? Number(it.target_reps) : null,
        target_weight: it.target_weight !== "" ? Number(it.target_weight) : null,
        rest_sec: Number(it.rest_sec) || 60,
        notes: it.notes,
      })),
    });
  };

  return (
    <div>
      <PageHeader
        title={editing ? "Edit routine" : "New routine"}
        subtitle="Save a reusable workout template"
      />
      <form onSubmit={onSubmit} className="space-y-6">
        <div className="card p-5 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="label">Name</label>
            <input
              className="input"
              placeholder="Upper body strength"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="md:col-span-2">
            <label className="label">Description</label>
            <textarea
              rows={2}
              className="input"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
          <div>
            <label className="label">Estimated duration (min)</label>
            <input
              type="number"
              className="input"
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
            />
          </div>
          <div className="flex items-end">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={isPublic}
                onChange={(e) => setIsPublic(e.target.checked)}
              />
              <span className="text-sm">Share with friends</span>
            </label>
          </div>
        </div>

        <SortableList
          ids={items.map((it) => it._key)}
          onReorder={handleReorder}
          className="space-y-3"
        >
          {items.map((it, idx) => (
            <SortableItem key={it._key} id={it._key}>
              {(dragHandleProps) => (
                <div className="card p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <DragHandle dragHandleProps={dragHandleProps} />
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-500 shrink-0">
                      {idx + 1}
                    </span>
                    <div className="flex-1 min-w-0">
                      <h4 className="font-semibold leading-snug">{it.exercise_detail?.name}</h4>
                      <p className="text-xs text-slate-500 capitalize">
                        {it.exercise_detail?.primary_muscle?.replace(/_/g, " ")}
                        {it.exercise_detail?.equipment && ` · ${it.exercise_detail.equipment}`}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeItem(idx)}
                      className="text-rose-500 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-500/10 p-2 rounded shrink-0"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <div>
                      <label className="label">Sets</label>
                      <input
                        type="number"
                        className="input"
                        value={it.target_sets}
                        onChange={(e) => updateItem(idx, "target_sets", e.target.value)}
                      />
                    </div>
                    <div>
                      <label className="label">Reps</label>
                      <input
                        type="number"
                        className="input"
                        value={it.target_reps}
                        onChange={(e) => updateItem(idx, "target_reps", e.target.value)}
                      />
                    </div>
                    <div>
                      <label className="label">Weight (kg)</label>
                      <input
                        type="number"
                        step="0.5"
                        className="input"
                        value={it.target_weight}
                        onChange={(e) => updateItem(idx, "target_weight", e.target.value)}
                      />
                    </div>
                    <div>
                      <label className="label">Rest (sec)</label>
                      <input
                        type="number"
                        className="input"
                        value={it.rest_sec}
                        onChange={(e) => updateItem(idx, "rest_sec", e.target.value)}
                      />
                    </div>
                  </div>
                  <div className="mt-3">
                    <input
                      className="input"
                      placeholder="Notes (tempo, cue, etc.)"
                      value={it.notes}
                      onChange={(e) => updateItem(idx, "notes", e.target.value)}
                    />
                  </div>
                </div>
              )}
            </SortableItem>
          ))}
        </SortableList>

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
            {save.isPending ? "Saving…" : "Save routine"}
          </button>
        </div>
      </form>

      {pickerOpen && <ExercisePickerModal onPick={addExercise} onClose={() => setPickerOpen(false)} />}
    </div>
  );
}

function ExercisePickerModal({ onPick, onClose }) {
  const [search, setSearch] = useState("");
  const { data } = useQuery({
    queryKey: qk.routines.picker(search),
    queryFn: () => exercisesApi.list({ search, page_size: 50 }),
  });
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
            placeholder="Search…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="overflow-y-auto p-2">
          {(data?.results || []).map((ex) => (
            <button
              key={ex.id}
              type="button"
              onClick={() => onPick(ex)}
              className="w-full text-left p-3 rounded-lg hover:bg-slate-50 flex justify-between"
            >
              <div>
                <p className="font-medium">{ex.name}</p>
                <p className="text-xs text-slate-500 capitalize">{ex.primary_muscle}</p>
              </div>
              <span className="text-xs text-brand-600">Add →</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
