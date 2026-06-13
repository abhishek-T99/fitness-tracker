import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";

import PageHeader from "../components/PageHeader.jsx";
import Pagination from "../components/Pagination.jsx";
import { exercisesApi } from "../api/endpoints.js";

const PAGE_SIZE = 24;

const MUSCLES = [
  "", "chest", "back", "shoulders", "biceps", "triceps", "forearms",
  "core", "quads", "hamstrings", "glutes", "calves", "full_body", "cardio",
];

const CATEGORIES = ["", "strength", "cardio", "flexibility", "balance"];

const EQUIPMENT = [
  "", "barbell", "dumbbell", "bodyweight", "cable", "machine",
  "kettlebell", "band", "cardio", "other",
];

export default function Exercises() {
  const [search,   setSearch]   = useState("");
  const [muscle,   setMuscle]   = useState("");
  const [category, setCategory] = useState("");
  const [equipment,setEquipment]= useState("");
  const [page,     setPage]     = useState(1);

  // Reset to page 1 whenever any filter changes
  useEffect(() => { setPage(1); }, [search, muscle, category, equipment]);

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ["exercises", search, muscle, category, equipment, page],
    queryFn: () =>
      exercisesApi.list({
        search:         search    || undefined,
        primary_muscle: muscle    || undefined,
        category:       category  || undefined,
        equipment:      equipment || undefined,
        page,
        page_size: PAGE_SIZE,
      }),
    keepPreviousData: true,   // keeps old items visible while next page loads
  });

  const items      = data?.results    || [];
  const totalCount = data?.count      ?? 0;

  return (
    <div>
      <PageHeader
        title="Exercise library"
        subtitle={`${totalCount} exercises — browse by muscle, equipment, or category`}
      />

      {/* Filter bar */}
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
        <select className="input md:w-44" value={muscle} onChange={(e) => setMuscle(e.target.value)}>
          {MUSCLES.map((m) => (
            <option key={m} value={m}>{m ? m.replace("_", " ") : "All muscles"}</option>
          ))}
        </select>
        <select className="input md:w-44" value={category} onChange={(e) => setCategory(e.target.value)}>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>{c || "All categories"}</option>
          ))}
        </select>
        <select className="input md:w-44" value={equipment} onChange={(e) => setEquipment(e.target.value)}>
          {EQUIPMENT.map((e) => (
            <option key={e} value={e}>{e || "All equipment"}</option>
          ))}
        </select>
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: PAGE_SIZE }).map((_, i) => (
            <div key={i} className="card p-5 animate-pulse">
              <div className="h-4 bg-slate-100 rounded w-2/3 mb-3" />
              <div className="flex gap-2 mb-3">
                <div className="h-5 bg-slate-100 rounded-full w-16" />
                <div className="h-5 bg-slate-100 rounded-full w-14" />
              </div>
              <div className="h-3 bg-slate-100 rounded w-full mb-1" />
              <div className="h-3 bg-slate-100 rounded w-4/5" />
            </div>
          ))}
        </div>
      ) : (
        <>
          <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 transition-opacity ${isFetching ? "opacity-60" : "opacity-100"}`}>
            {items.map((ex) => (
              <ExerciseCard key={ex.id} ex={ex} />
            ))}
            {items.length === 0 && (
              <p className="col-span-full text-center text-slate-500 py-16">
                No exercises match those filters.
              </p>
            )}
          </div>

          <Pagination
            page={page}
            pageSize={PAGE_SIZE}
            totalCount={totalCount}
            onChange={setPage}
          />
        </>
      )}
    </div>
  );
}

function ExerciseCard({ ex }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="card p-5">
      <div className="flex items-start justify-between mb-2 gap-2">
        <h3 className="font-semibold leading-snug">{ex.name}</h3>
        {ex.is_compound && (
          <span className="badge bg-brand-50 text-brand-700 dark:text-brand-300 shrink-0">
            compound
          </span>
        )}
      </div>
      <div className="flex flex-wrap gap-1.5 mb-3">
        <span className="badge bg-slate-100 text-slate-700 capitalize">
          {ex.primary_muscle.replace(/_/g, " ")}
        </span>
        <span className="badge bg-slate-100 text-slate-700 capitalize">
          {ex.equipment}
        </span>
        <span className="badge bg-slate-100 text-slate-700 capitalize">
          {ex.category}
        </span>
      </div>
      {ex.instructions && (
        <div>
          <p className={`text-sm text-slate-600 leading-relaxed ${expanded ? "" : "line-clamp-3"}`}>
            {ex.instructions}
          </p>
          {ex.instructions.length > 140 && (
            <button
              onClick={() => setExpanded((v) => !v)}
              className="text-xs text-brand-600 hover:underline mt-1"
            >
              {expanded ? "Show less" : "Show more"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
