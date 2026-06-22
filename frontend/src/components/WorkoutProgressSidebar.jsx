import { useEffect, useRef } from "react";
import { Check, ChevronRight } from "lucide-react";

function ExerciseRow({ item, idx, state, setsCompleted, rowRef }) {
  const totalSets = item.target_sets ?? 3;
  const name = item.exercise_detail?.name ?? "Exercise";

  return (
    <div
      ref={rowRef ?? null}
      className={`flex items-center gap-3 px-4 py-2.5 transition-colors ${
        state === "active"
          ? "bg-brand-50 border-l-[3px] border-brand-500"
          : "border-l-[3px] border-transparent"
      }`}
    >
      <div className="shrink-0">
        {state === "done" ? (
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500/15">
            <Check className="w-3 h-3 text-emerald-500 stroke-[2.5]" />
          </span>
        ) : state === "active" ? (
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-brand-500/20">
            <ChevronRight className="w-3 h-3 text-brand-500 stroke-[2.5]" />
          </span>
        ) : (
          <span className="flex h-5 w-5 items-center justify-center rounded-full border border-slate-200">
            <span className="text-[9px] font-semibold text-slate-400">{idx + 1}</span>
          </span>
        )}
      </div>

      <div className="flex-1 min-w-0">
        <p
          className={`text-xs font-medium truncate leading-tight ${
            state === "done"
              ? "line-through text-slate-400"
              : state === "active"
              ? "text-brand-600"
              : "text-slate-600"
          }`}
        >
          {name}
        </p>
        <p
          className={`text-[10px] leading-tight mt-0.5 ${
            state === "done"
              ? "text-emerald-500"
              : state === "active"
              ? "text-slate-500"
              : "text-slate-400"
          }`}
        >
          {state === "done"
            ? `Done · ${totalSets} sets`
            : state === "active"
            ? `${setsCompleted} / ${totalSets} sets`
            : `${totalSets} sets`}
        </p>
      </div>
    </div>
  );
}

/**
 * Side panel showing completed / current / upcoming exercises for an active
 * workout session.  Hidden on screens narrower than lg (1024 px).
 */
export default function WorkoutProgressSidebar({ session }) {
  const { routine, currentExIdx, logs } = session;
  const items = routine?.items ?? [];
  const currentRowRef = useRef(null);

  // Keep the active exercise row visible when it changes
  useEffect(() => {
    currentRowRef.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [currentExIdx]);

  if (items.length === 0) return null;

  const doneCount = items.filter((_, i) => i < currentExIdx).length;
  const progressPct = Math.round((doneCount / items.length) * 100);

  const completedItems  = items.slice(0, currentExIdx);
  const currentItem     = items[currentExIdx];
  const upcomingItems   = items.slice(currentExIdx + 1);

  return (
    <aside className="hidden lg:flex flex-col w-60 xl:w-64 shrink-0 border-l border-slate-200 bg-surface overflow-hidden">
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div className="px-4 pt-4 pb-3 border-b border-slate-200 shrink-0">
        <p className="text-[10px] font-semibold uppercase tracking-widest text-slate-400">
          Workout Progress
        </p>
        <div className="flex items-baseline gap-1.5 mt-1">
          <span className="text-lg font-bold text-slate-900 tabular-nums">
            {doneCount}
          </span>
          <span className="text-xs text-slate-400">/ {items.length} exercises</span>
        </div>
        <div className="mt-2.5 h-1.5 bg-slate-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-brand-500 rounded-full transition-[width] duration-500"
            style={{ width: `${progressPct}%` }}
          />
        </div>
      </div>

      {/* ── Exercise list ───────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto">
        {/* Completed */}
        {completedItems.length > 0 && (
          <section className="py-1">
            <p className="px-4 pt-3 pb-1 text-[10px] font-semibold uppercase tracking-widest text-slate-400">
              Completed
            </p>
            {completedItems.map((item, idx) => (
              <ExerciseRow
                key={idx}
                item={item}
                idx={idx}
                state="done"
                setsCompleted={logs[idx]?.length ?? 0}
              />
            ))}
          </section>
        )}

        {/* Current */}
        {currentItem && (
          <section className="py-1">
            <p className="px-4 pt-3 pb-1 text-[10px] font-semibold uppercase tracking-widest text-slate-400">
              Current
            </p>
            <ExerciseRow
              item={currentItem}
              idx={currentExIdx}
              state="active"
              setsCompleted={logs[currentExIdx]?.length ?? 0}
              rowRef={currentRowRef}
            />
          </section>
        )}

        {/* Upcoming */}
        {upcomingItems.length > 0 && (
          <section className="py-1">
            <p className="px-4 pt-3 pb-1 text-[10px] font-semibold uppercase tracking-widest text-slate-400">
              Up Next
            </p>
            {upcomingItems.map((item, relIdx) => {
              const idx = currentExIdx + 1 + relIdx;
              return (
                <ExerciseRow
                  key={idx}
                  item={item}
                  idx={idx}
                  state="upcoming"
                  setsCompleted={0}
                />
              );
            })}
          </section>
        )}
      </div>
    </aside>
  );
}
