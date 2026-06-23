/**
 * WorkoutSession — full-screen, distraction-free active workout mode.
 *
 * Route: /session/:routineId  (outside AppLayout, no sidebar)
 *
 * Flow:
 *   1. Load routine + exercise history in parallel
 *   2. Show "preview" screen (exercise overview, estimated duration)
 *   3. User taps "Begin" → state machine takes over
 *   4. For each exercise:  show set → user logs reps/weight → rest timer → next set
 *   5. After all exercises → summary screen → save as completed Workout
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import {
  ArrowLeft, CheckCircle2, ChevronRight, Clock,
  Dumbbell, RotateCcw, Trophy, X,
} from "lucide-react";
import toast from "react-hot-toast";

import RestTimer from "../components/RestTimer.jsx";
import ExerciseTutorialSheet, { TutorialTrigger } from "../components/ExerciseTutorialSheet.jsx";
import WorkoutProgressSidebar from "../components/WorkoutProgressSidebar.jsx";
import useWorkoutSession, { getProgressionSuggestion } from "../hooks/useWorkoutSession.js";
import { routinesApi, workoutsApi } from "../api/endpoints.js";
import { qk } from "../api/queryKeys.js";

// ── Stopwatch ─────────────────────────────────────────────────────────────────

/**
 * Live elapsed-time display.  Ticks every second from startedAt (ISO string).
 * Shows MM:SS for the first hour, then H:MM:SS.
 */
function Stopwatch({ startedAt, className = "" }) {
  const [elapsed, setElapsed] = useState(0); // seconds

  useEffect(() => {
    if (!startedAt) return;
    const origin = new Date(startedAt).getTime();

    const tick = () => setElapsed(Math.floor((Date.now() - origin) / 1000));
    tick();                                   // run immediately
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [startedAt]);

  const h  = Math.floor(elapsed / 3600);
  const m  = Math.floor((elapsed % 3600) / 60);
  const s  = elapsed % 60;
  const pad = (n) => String(n).padStart(2, "0");

  const display = h > 0
    ? `${h}:${pad(m)}:${pad(s)}`
    : `${pad(m)}:${pad(s)}`;

  return (
    <span className={`font-mono tabular-nums ${className}`}>{display}</span>
  );
}

// ── Small helpers ─────────────────────────────────────────────────────────────

function muscleLabel(m) {
  return (m || "").replace(/_/g, " ");
}

function fmtWeight(w) {
  if (!w && w !== 0) return "—";
  return `${w} kg`;
}

function totalVolume(logs, items) {
  let vol = 0;
  logs.forEach((exLogs, i) => {
    exLogs.forEach((s) => {
      if (s.reps && s.weight) vol += s.reps * s.weight;
    });
  });
  return Math.round(vol);
}

function elapsedMinutes(startedAt) {
  if (!startedAt) return 0;
  return Math.floor((Date.now() - new Date(startedAt).getTime()) / 60000);
}

// ── Previous-performance row ──────────────────────────────────────────────────

function PrevPerformance({ history, item }) {
  const suggestion = getProgressionSuggestion(history, item);
  const sets = history?.last_session?.sets ?? [];

  return (
    <div className="rounded-xl bg-slate-50 dark:bg-slate-100/5 border border-slate-200 p-3 space-y-2">
      {sets.length > 0 ? (
        <>
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">Last session</p>
          <div className="flex flex-wrap gap-2">
            {sets.map((s, i) => (
              <span key={i} className="text-xs font-mono bg-surface border border-slate-200 rounded-lg px-2 py-1 text-slate-700">
                {s.weight ? `${s.weight} kg` : "—"} × {s.reps ?? "—"}
                {s.rpe ? <span className="text-slate-400"> · RPE {s.rpe}</span> : null}
              </span>
            ))}
          </div>
          <p className={`text-xs font-medium flex items-center gap-1 ${
            suggestion.reason === "increase" ? "text-emerald-600 dark:text-emerald-400" : "text-slate-500"
          }`}>
            {suggestion.reason === "increase"
              ? `Progression: try ${suggestion.weight} kg × ${suggestion.reps}`
              : `Hold: ${suggestion.weight} kg × ${suggestion.reps}`}
          </p>
        </>
      ) : (
        <p className="text-xs text-slate-400">No history — first time doing this exercise.</p>
      )}
    </div>
  );
}

// ── Set dots ─────────────────────────────────────────────────────────────────

function SetDots({ total, completed, current }) {
  return (
    <div className="flex items-center gap-1.5">
      {Array.from({ length: total }, (_, i) => (
        <span
          key={i}
          className={`h-2.5 w-2.5 rounded-full transition-all ${
            i < completed
              ? "bg-emerald-500"
              : i === current
              ? "bg-brand-500 scale-125"
              : "bg-slate-200"
          }`}
        />
      ))}
    </div>
  );
}

// ── Number input (big tap-friendly) ──────────────────────────────────────────

function BigInput({ label, value, onChange, step = 1, min = 0 }) {
  return (
    <div className="flex flex-col items-center gap-1">
      <p className="text-xs text-slate-500 font-medium uppercase tracking-wide">{label}</p>
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => onChange(Math.max(min, Number(value) - step))}
          className="h-10 w-10 rounded-full border border-slate-200 text-xl font-bold text-slate-600 hover:bg-slate-50 flex items-center justify-center transition"
        >−</button>
        <input
          type="number"
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="w-20 text-center text-2xl font-bold input py-2"
          min={min}
          step={step}
        />
        <button
          type="button"
          onClick={() => onChange(Number(value) + step)}
          className="h-10 w-10 rounded-full border border-slate-200 text-xl font-bold text-slate-600 hover:bg-slate-50 flex items-center justify-center transition"
        >+</button>
      </div>
    </div>
  );
}

// ── RPE picker ────────────────────────────────────────────────────────────────

const RPE_LABELS = {
  6: "Very easy", 7: "Easy", 8: "Moderate", 9: "Hard", 10: "Max effort"
};

function RpePicker({ value, onChange }) {
  return (
    <div className="flex flex-col items-center gap-2">
      <p className="text-xs text-slate-500 font-medium uppercase tracking-wide">
        RPE {value ? `${value} — ${RPE_LABELS[value] || ""}` : "(optional)"}
      </p>
      <div className="flex gap-1.5">
        {[6, 7, 8, 9, 10].map((r) => (
          <button
            key={r}
            type="button"
            onClick={() => onChange(value === r ? null : r)}
            className={`h-9 w-9 rounded-lg text-sm font-semibold transition border ${
              value === r
                ? "bg-brand-600 text-white border-brand-600"
                : "border-slate-200 text-slate-600 hover:border-brand-400"
            }`}
          >
            {r}
          </button>
        ))}
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function WorkoutSession() {
  const { routineId } = useParams();
  const navigate = useNavigate();
  const [confirmAbandon, setConfirmAbandon] = useState(false);
  const [tutorialOpen, setTutorialOpen] = useState(false);

  const {
    session,
    initSession,
    beginSession,
    setCurrentReps,
    setCurrentWeight,
    setCurrentRpe,
    completeSet,
    skipRest,
    addRestTime,
    abandonSession,
    clearSession,
  } = useWorkoutSession();

  // Load routine and exercise history in parallel
  const { data: routine, isLoading: routineLoading } = useQuery({
    queryKey: qk.routines.detail(routineId),
    queryFn: () => routinesApi.retrieve(routineId),
    enabled: !session || session.routineId !== Number(routineId),
  });

  const exerciseIds = useMemo(() => {
    const r = routine || session?.routine;
    return r?.items?.map((it) => it.exercise) ?? [];
  }, [routine, session?.routine]);

  const { data: history = {} } = useQuery({
    queryKey: qk.workouts.exerciseHistory(exerciseIds),
    queryFn: () => workoutsApi.exerciseHistory(exerciseIds),
    enabled: exerciseIds.length > 0 && (!session || session.routineId !== Number(routineId)),
  });

  // Initialise session once both pieces of data are ready
  useEffect(() => {
    if (routine && history && (!session || session.routineId !== Number(routineId))) {
      initSession(routine, history);
    }
  }, [routine, history]);

  const saveWorkout = useMutation({
    mutationFn: () => {
      const { session: s } = { session };
      const items = (session.routine.items || []).map((item, i) => ({
        exercise: item.exercise,
        order: i,
        sets: (session.logs[i] || []).map((log, j) => ({
          set_number: j + 1,
          reps: log.reps,
          weight: log.weight || null,
          rpe: log.rpe || null,
          completed: true,
        })),
      }));

      const minutes = elapsedMinutes(session.startedAt);
      const vol = totalVolume(session.logs, session.routine.items);

      return workoutsApi.create({
        name: session.routineName,
        notes: `Active session via routine "${session.routineName}"`,
        started_at: session.startedAt,
        ended_at: new Date().toISOString(),
        duration_min: minutes,
        status: "completed",
        exercises: items.map((ex) => ({
          exercise: ex.exercise,
          order: ex.order,
          notes: "",
          sets: ex.sets,
        })),
      });
    },
    onSuccess: (data) => {
      toast.success("Workout saved!");
      clearSession();
      navigate(`/workouts/${data.id}`);
    },
    onError: () => toast.error("Could not save workout. Try again."),
  });

  // ── Loading ────────────────────────────────────────────────────────────────
  if (routineLoading || !session) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-50">
        <div className="text-center space-y-3">
          <Dumbbell className="w-10 h-10 text-brand-500 mx-auto animate-pulse" />
          <p className="text-slate-500">Loading session…</p>
        </div>
      </div>
    );
  }

  const { routine: r, status, currentExIdx, currentSetIdx } = session;
  const currentItem = r?.items?.[currentExIdx];
  const totalExercises = r?.items?.length ?? 0;

  // ── Preview screen ─────────────────────────────────────────────────────────
  if (status === "preview") {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-50 flex flex-col">
        {tutorialOpen && (
          <ExerciseTutorialSheet
            exercise={r?.items?.[tutorialOpen - 1]?.exercise_detail}
            isFirstSession={!session.history?.[String(r?.items?.[tutorialOpen - 1]?.exercise)]}
            onClose={() => setTutorialOpen(false)}
          />
        )}
        <div className="sticky top-0 bg-surface border-b border-slate-200 px-4 py-3 flex items-center gap-3">
          <button onClick={() => navigate(-1)} className="text-slate-500 hover:text-slate-700">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="font-semibold text-slate-900 flex-1 truncate">{r?.name}</h1>
          {r?.estimated_duration_min && (
            <span className="flex items-center gap-1 text-xs text-slate-500">
              <Clock className="w-3.5 h-3.5" />
              ~{r.estimated_duration_min} min
            </span>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3 max-w-lg mx-auto w-full">
          <p className="text-sm text-slate-500">{totalExercises} exercise{totalExercises !== 1 ? "s" : ""}</p>

          {r?.items?.map((item, i) => {
            const ex = item.exercise_detail;
            const h = session.history?.[String(item.exercise)];
            const sug = session.suggestions?.[i];
            const hasHistory = !!h?.last_session?.sets?.length;

            return (
              <div key={i} className="card p-4 flex items-center gap-3">
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-500 shrink-0">
                  {i + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-slate-900 truncate">{ex?.name}</p>
                  <p className="text-xs text-slate-500 capitalize">
                    {muscleLabel(ex?.primary_muscle)} · {item.target_sets} sets × {item.target_reps ?? "—"} reps
                  </p>
                  {hasHistory ? (
                    <p className={`text-xs mt-0.5 font-medium ${sug?.reason === "increase" ? "text-emerald-600" : "text-slate-400"}`}>
                      {sug?.reason === "increase"
                        ? `Suggest ${sug.weight} kg (+2.5 kg progression)`
                        : `Hold at ${sug?.weight} kg`}
                    </p>
                  ) : (
                    <p className="text-xs text-slate-400 mt-0.5">First session</p>
                  )}
                </div>
                {sug?.reason === "increase" && (
                  <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 dark:bg-emerald-500/15 px-1.5 py-0.5 rounded-full shrink-0">
                    ↑ PO
                  </span>
                )}
                <TutorialTrigger
                  onClick={() => setTutorialOpen(i + 1)}
                  isFirstSession={!hasHistory}
                />
              </div>
            );
          })}
        </div>

        <div className="sticky bottom-0 bg-surface border-t border-slate-200 p-4">
          <button onClick={beginSession} className="btn-primary w-full text-base py-3">
            Begin workout
          </button>
        </div>
      </div>
    );
  }

  // ── Done screen ────────────────────────────────────────────────────────────
  if (status === "done") {
    const mins = elapsedMinutes(session.startedAt);
    const vol = totalVolume(session.logs, r?.items ?? []);
    const totalSets = session.logs.reduce((acc, ex) => acc + ex.length, 0);

    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-50 flex flex-col items-center justify-center p-6 gap-8">
        <div className="text-center space-y-2">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-emerald-50 mx-auto">
            <Trophy className="w-10 h-10 text-emerald-500" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Session complete</h1>
          <p className="text-slate-500">{r?.name}</p>
        </div>

        <div className="grid grid-cols-3 gap-4 w-full max-w-sm">
          {[
            { label: "Duration", value: `${mins} min` },
            { label: "Sets done", value: totalSets },
            { label: "Volume", value: vol > 0 ? `${vol} kg` : "—" },
          ].map(({ label, value }) => (
            <div key={label} className="card p-4 text-center">
              <p className="text-xl font-bold text-slate-900">{value}</p>
              <p className="text-xs text-slate-500 mt-0.5">{label}</p>
            </div>
          ))}
        </div>

        <div className="space-y-3 w-full max-w-sm">
          <button
            onClick={() => saveWorkout.mutate()}
            disabled={saveWorkout.isPending}
            className="btn-primary w-full py-3 text-base"
          >
            {saveWorkout.isPending ? "Saving…" : "Save workout"}
          </button>
          <button
            onClick={() => { abandonSession(); navigate("/routines"); }}
            className="btn-ghost w-full text-sm text-slate-500"
          >
            Discard
          </button>
        </div>
      </div>
    );
  }

  // ── Rest timer ─────────────────────────────────────────────────────────────
  if (status === "resting") {
    const { currentExIdx: nextExIdx, currentSetIdx: nextSetIdx } = (() => {
      const item = r?.items?.[currentExIdx];
      const totalSets = item?.target_sets ?? 3;
      if (currentSetIdx + 1 >= totalSets) {
        return { currentExIdx: currentExIdx + 1, currentSetIdx: 0 };
      }
      return { currentExIdx, currentSetIdx: currentSetIdx + 1 };
    })();

    const nextItem = r?.items?.[nextExIdx];
    const nextLabel = nextItem
      ? `Set ${nextSetIdx + 1} of ${nextItem.target_sets} — ${nextItem.exercise_detail?.name}`
      : "Last set done!";

    // Rest screen is intentionally dark regardless of theme —
    // it's a focused, immersive pause between sets.
    return (
      <div className="h-screen flex flex-col" style={{ background: "#0f172a" }}>
        {/* Minimal header */}
        <div className="px-4 py-4 flex items-center justify-between shrink-0">
          <div>
            <p className="text-xs text-white/40 uppercase tracking-widest">Just completed</p>
            <p className="text-sm font-semibold text-white/80 truncate mt-0.5">
              {currentItem?.exercise_detail?.name}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Stopwatch startedAt={session.startedAt} className="text-xs text-white/40" />
            <ExerciseProgress currentIdx={currentExIdx} total={totalExercises} dark />
          </div>
        </div>

        <div className="flex-1 flex overflow-hidden">
          <div className="flex-1 flex items-center justify-center">
            <div className="w-full max-w-sm px-4">
              <RestTimer
                secondsLeft={session.restSecondsLeft}
                secondsTotal={session.restSecondsTotal}
                nextLabel={nextLabel}
                onSkip={skipRest}
                onAdd={addRestTime}
              />
            </div>
          </div>
          <WorkoutProgressSidebar session={session} />
        </div>
      </div>
    );
  }

  // ── Active set screen ──────────────────────────────────────────────────────
  const totalSets = currentItem?.target_sets ?? 3;
  const completedSetsForEx = session.logs[currentExIdx]?.length ?? 0;
  const exHistory = session.history?.[String(currentItem?.exercise)];

  return (
    <div className="h-screen bg-slate-50 dark:bg-slate-50 flex flex-col">

      {/* Header */}
      <div className="shrink-0 bg-surface border-b border-slate-200 px-4 py-3 flex items-center gap-3">
        <button
          onClick={() => setConfirmAbandon(true)}
          className="text-slate-400 hover:text-slate-600"
        >
          <X className="w-5 h-5" />
        </button>
        <div className="flex-1 min-w-0">
          <p className="text-xs text-slate-500 truncate">{r?.name}</p>
          <p className="font-semibold text-slate-900 truncate">{currentItem?.exercise_detail?.name}</p>
        </div>
        <Stopwatch
          startedAt={session.startedAt}
          className="text-sm font-semibold text-brand-600 dark:text-brand-400 shrink-0"
        />
        <TutorialTrigger
          onClick={() => setTutorialOpen(true)}
          isFirstSession={!exHistory?.last_session}
        />
        <ExerciseProgress currentIdx={currentExIdx} total={totalExercises} />
      </div>

      {/* Body: scrollable main content + sidebar */}
      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-sm mx-auto px-4 py-6 space-y-6">

            {/* Exercise info */}
            <div className="text-center space-y-1">
              <p className="text-xs text-slate-400 capitalize">
                {muscleLabel(currentItem?.exercise_detail?.primary_muscle)}
                {currentItem?.exercise_detail?.equipment && ` · ${currentItem.exercise_detail.equipment}`}
              </p>
              <div className="flex justify-center">
                <SetDots
                  total={totalSets}
                  completed={completedSetsForEx}
                  current={currentSetIdx}
                />
              </div>
              <p className="text-sm font-medium text-slate-700">
                Set {currentSetIdx + 1} of {totalSets}
              </p>
            </div>

            {/* Previous performance */}
            {exHistory && (
              <PrevPerformance history={exHistory} item={currentItem} />
            )}

            {/* Input controls */}
            <div className="card p-6 space-y-6">
              <BigInput
                label="Reps"
                value={session.currentReps}
                onChange={setCurrentReps}
                step={1}
                min={0}
              />
              <BigInput
                label="Weight (kg)"
                value={session.currentWeight}
                onChange={setCurrentWeight}
                step={2.5}
                min={0}
              />
              <RpePicker value={session.currentRpe} onChange={setCurrentRpe} />
            </div>

            {/* Up next preview */}
            {currentItem && (() => {
              const nextIsNextSet = currentSetIdx + 1 < totalSets;
              const nextEx = nextIsNextSet
                ? currentItem
                : r?.items?.[currentExIdx + 1];
              if (!nextEx) return null;
              return (
                <div className="flex items-center gap-2 text-xs text-slate-500 px-1">
                  <ChevronRight className="w-3.5 h-3.5 shrink-0" />
                  <span>
                    Next: {nextIsNextSet
                      ? `Set ${currentSetIdx + 2} of ${totalSets}`
                      : nextEx.exercise_detail?.name
                    }
                  </span>
                </div>
              );
            })()}
          </div>
        </div>

        {/* Progress sidebar — visible lg+ */}
        <WorkoutProgressSidebar session={session} />
      </div>

      {/* CTA */}
      <div className="shrink-0 bg-surface border-t border-slate-200 p-4">
        <button
          onClick={completeSet}
          className="btn-primary w-full py-3 text-base gap-2"
        >
          <CheckCircle2 className="w-5 h-5" />
          Complete set
        </button>
      </div>

      {/* Tutorial sheet */}
      {tutorialOpen === true && (
        <ExerciseTutorialSheet
          exercise={currentItem?.exercise_detail}
          isFirstSession={!exHistory}
          onClose={() => setTutorialOpen(false)}
        />
      )}

      {/* Abandon confirm */}
      {confirmAbandon && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-end sm:items-center justify-center p-4">
          <div className="bg-surface rounded-2xl shadow-xl w-full max-w-sm p-6 space-y-4">
            <h3 className="font-semibold text-slate-900 text-lg">End session?</h3>
            <p className="text-sm text-slate-500">
              Your progress will be lost. Save the session first if you want to keep it.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setConfirmAbandon(false)}
                className="btn-secondary flex-1"
              >
                Keep going
              </button>
              <button
                onClick={() => { abandonSession(); navigate("/routines"); }}
                className="flex-1 btn bg-rose-600 text-white hover:bg-rose-700 focus:ring-rose-500"
              >
                End session
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ExerciseProgress({ currentIdx, total, dark = false }) {
  return (
    <span className={`text-xs font-semibold shrink-0 ${dark ? "text-white/40" : "text-slate-500"}`}>
      {currentIdx + 1}/{total}
    </span>
  );
}
