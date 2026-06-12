import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";

import PageHeader from "../components/PageHeader.jsx";
import { exercisesApi } from "../api/endpoints.js";

const MUSCLES = [
  "", "chest", "back", "shoulders", "biceps", "triceps", "core",
  "quads", "hamstrings", "glutes", "calves", "full_body", "cardio",
];

const CATEGORIES = ["", "strength", "cardio", "flexibility", "balance"];

export default function Exercises() {
  const [search, setSearch] = useState("");
  const [muscle, setMuscle] = useState("");
  const [category, setCategory] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["exercises", search, muscle, category],
    queryFn: () =>
      exercisesApi.list({
        search: search || undefined,
        primary_muscle: muscle || undefined,
        category: category || undefined,
        page_size: 100,
      }),
  });
  const items = data?.results || [];

  return (
    <div>
      <PageHeader
        title="Exercise library"
        subtitle="Browse exercises by muscle, equipment, or category"
      />

      <div className="card p-4 mb-6 flex flex-col md:flex-row gap-3">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            className="input pl-9"
            placeholder="Search exercises…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <select
          className="input md:w-48"
          value={muscle}
          onChange={(e) => setMuscle(e.target.value)}
        >
          {MUSCLES.map((m) => (
            <option key={m} value={m}>
              {m ? m.replace("_", " ") : "All muscles"}
            </option>
          ))}
        </select>
        <select
          className="input md:w-48"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c || "All categories"}
            </option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <p className="text-slate-500">Loading…</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((ex) => (
            <div key={ex.id} className="card p-5">
              <div className="flex items-start justify-between mb-2">
                <h3 className="font-semibold">{ex.name}</h3>
                {ex.is_compound && (
                  <span className="badge bg-brand-50 text-brand-700 dark:text-brand-300">compound</span>
                )}
              </div>
              <div className="flex flex-wrap gap-2 mb-3">
                <span className="badge bg-slate-100 text-slate-700 capitalize">
                  {ex.primary_muscle.replace("_", " ")}
                </span>
                <span className="badge bg-slate-100 text-slate-700 capitalize">
                  {ex.equipment}
                </span>
                <span className="badge bg-slate-100 text-slate-700 capitalize">
                  {ex.category}
                </span>
              </div>
              {ex.instructions && (
                <p className="text-sm text-slate-600">{ex.instructions}</p>
              )}
            </div>
          ))}
          {items.length === 0 && (
            <p className="col-span-full text-center text-slate-500 py-12">
              No exercises match those filters.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
