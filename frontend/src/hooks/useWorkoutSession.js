/**
 * useWorkoutSession — manages the full lifecycle of an active workout session.
 *
 * State machine
 * ─────────────
 *  preview  → active  (user taps "Begin")
 *  active   → resting (user completes a set)
 *  resting  → active  (timer expires or user skips)
 *  active   → done    (all sets in all exercises completed)
 *  done     → (gone)  (user saves or abandons)
 *
 * Persistence
 * ───────────
 * The full session state is written to localStorage after every mutation.
 * On mount the hook reads it back, so a page refresh mid-session restores
 * exactly where the user was.
 */
import { useCallback, useEffect, useRef, useState } from "react";

const STORAGE_KEY = "fittrack_active_session";

// ── Progressive overload ────────────────────────────────────────────────────

/**
 * Double-progression algorithm:
 *  - If the user hit ≥ target_reps on ALL completed sets last time → suggest
 *    adding 2.5 kg (nearest 2.5 kg increment).
 *  - Otherwise → hold the same weight and keep chasing the rep target.
 *
 * Returns { weight, reps, reason: 'first_session' | 'increase' | 'maintain' }
 */
export function getProgressionSuggestion(history, routineItem) {
  const targetReps = routineItem?.target_reps ?? 8;
  const defaultWeight = parseFloat(routineItem?.target_weight) || 0;

  if (!history?.last_session?.sets?.length) {
    return { weight: defaultWeight, reps: targetReps, reason: "first_session" };
  }

  const sets = history.last_session.sets.filter((s) => s.reps > 0);
  if (!sets.length) {
    return { weight: defaultWeight, reps: targetReps, reason: "first_session" };
  }

  const lastWeight = parseFloat(sets[0]?.weight) || 0;
  const allHitTarget = sets.every((s) => s.reps >= targetReps);

  if (allHitTarget) {
    // Round up to the nearest 2.5 kg increment
    const bumped = lastWeight + 2.5;
    const rounded = Math.round(bumped / 2.5) * 2.5;
    return { weight: rounded, reps: targetReps, reason: "increase" };
  }

  return { weight: lastWeight, reps: targetReps, reason: "maintain" };
}

// ── Local storage helpers ────────────────────────────────────────────────────

function loadSession() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function saveSession(session) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
  } catch {
    // localStorage full / unavailable — continue in-memory
  }
}

function clearSession() {
  localStorage.removeItem(STORAGE_KEY);
}

// ── Initial session builder ──────────────────────────────────────────────────

function buildInitialSession(routine, history) {
  return {
    routineId: routine.id,
    routineName: routine.name,
    startedAt: new Date().toISOString(),
    status: "preview",          // preview | active | resting | done
    currentExIdx: 0,
    currentSetIdx: 0,
    // logs[exerciseIdx] = array of {reps, weight, rpe, completedAt}
    logs: routine.items.map(() => []),
    // pre-compute per-exercise suggestion from history
    suggestions: routine.items.map((item) => {
      const h = history?.[String(item.exercise)];
      return getProgressionSuggestion(h, item);
    }),
    // live editable values for the current set (pre-filled from suggestion)
    currentReps: routine.items[0]
      ? (routine.items[0].target_reps ?? 8)
      : 8,
    currentWeight: routine.items[0]
      ? (parseFloat(routine.items[0].target_weight) || 0)
      : 0,
    currentRpe: null,
    restSecondsTotal: 0,
    restSecondsLeft: 0,
    history,                    // raw exercise history for display
    routine,                    // full routine for reference
  };
}

// ── Hook ─────────────────────────────────────────────────────────────────────

export default function useWorkoutSession() {
  const [session, setSession] = useState(() => loadSession());
  const timerRef = useRef(null);

  // Persist to localStorage on every change
  useEffect(() => {
    if (session) {
      saveSession(session);
    }
  }, [session]);

  // Countdown tick
  useEffect(() => {
    if (session?.status !== "resting") {
      clearInterval(timerRef.current);
      return;
    }
    timerRef.current = setInterval(() => {
      setSession((prev) => {
        if (!prev || prev.status !== "resting") return prev;
        const next = prev.restSecondsLeft - 1;
        if (next <= 0) {
          return _advanceAfterRest(prev);
        }
        return { ...prev, restSecondsLeft: next };
      });
    }, 1000);
    return () => clearInterval(timerRef.current);
  }, [session?.status]);

  // ── Public actions ─────────────────────────────────────────────────────────

  /** Initialise a brand-new session from a routine + exercise history. */
  const initSession = useCallback((routine, history) => {
    const s = buildInitialSession(routine, history);
    setSession(s);
  }, []);

  /** Transition preview → active. */
  const beginSession = useCallback(() => {
    setSession((prev) => {
      if (!prev) return prev;
      const s = { ...prev, status: "active" };
      return _prefillCurrentSet(s);
    });
  }, []);

  /** Update the in-progress reps/weight/rpe before logging the set. */
  const setCurrentReps   = useCallback((v) => setSession((p) => p && ({ ...p, currentReps: v })), []);
  const setCurrentWeight = useCallback((v) => setSession((p) => p && ({ ...p, currentWeight: v })), []);
  const setCurrentRpe    = useCallback((v) => setSession((p) => p && ({ ...p, currentRpe: v })), []);

  /** Log the current set as completed, start the rest timer. */
  const completeSet = useCallback(() => {
    setSession((prev) => {
      if (!prev || prev.status !== "active") return prev;

      const { currentExIdx, currentSetIdx, logs, routine } = prev;
      const item = routine.items[currentExIdx];
      const totalSets = item?.target_sets ?? 3;

      // Append the logged set
      const updatedLogs = logs.map((exLog, i) =>
        i === currentExIdx
          ? [...exLog, {
              reps: prev.currentReps,
              weight: prev.currentWeight,
              rpe: prev.currentRpe,
              completedAt: new Date().toISOString(),
            }]
          : exLog
      );

      // Is this the last set of this exercise?
      const isLastSet = currentSetIdx + 1 >= totalSets;
      // Is this the last exercise?
      const isLastExercise = currentExIdx + 1 >= routine.items.length;

      if (isLastSet && isLastExercise) {
        return { ...prev, logs: updatedLogs, status: "done" };
      }

      // Start rest timer
      const restSec = item?.rest_sec ?? 60;
      return {
        ...prev,
        logs: updatedLogs,
        status: "resting",
        restSecondsTotal: restSec,
        restSecondsLeft: restSec,
      };
    });
  }, []);

  /** Skip the rest timer early. */
  const skipRest = useCallback(() => {
    setSession((prev) => {
      if (!prev || prev.status !== "resting") return prev;
      return _advanceAfterRest(prev);
    });
  }, []);

  /** Add seconds to the current rest timer. */
  const addRestTime = useCallback((seconds) => {
    setSession((prev) => {
      if (!prev || prev.status !== "resting") return prev;
      return { ...prev, restSecondsLeft: prev.restSecondsLeft + seconds };
    });
  }, []);

  /** Abandon without saving. */
  const abandonSession = useCallback(() => {
    clearSession();
    setSession(null);
  }, []);

  return {
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
    clearSession: () => { clearSession(); setSession(null); },
  };
}

// ── Private helpers ──────────────────────────────────────────────────────────

/** After rest ends, advance to the next set (or next exercise). */
function _advanceAfterRest(prev) {
  const { currentExIdx, currentSetIdx, logs, routine } = prev;
  const item = routine.items[currentExIdx];
  const totalSets = item?.target_sets ?? 3;

  let nextExIdx = currentExIdx;
  let nextSetIdx = currentSetIdx + 1;

  if (nextSetIdx >= totalSets) {
    nextExIdx += 1;
    nextSetIdx = 0;
  }

  const next = {
    ...prev,
    status: "active",
    currentExIdx: nextExIdx,
    currentSetIdx: nextSetIdx,
    restSecondsLeft: 0,
  };
  return _prefillCurrentSet(next);
}

/** Pre-fill currentReps/currentWeight from the suggestion for the upcoming set. */
function _prefillCurrentSet(session) {
  const { currentExIdx, currentSetIdx, suggestions, routine, logs } = session;
  const item = routine.items[currentExIdx];
  const suggestion = suggestions?.[currentExIdx];

  // If there's already a log entry for a previous set of this exercise,
  // use that weight as the default (the user may have changed it).
  const prevLog = logs[currentExIdx];
  const lastLoggedWeight =
    prevLog?.length > 0 ? prevLog[prevLog.length - 1].weight : null;
  const lastLoggedReps =
    prevLog?.length > 0 ? prevLog[prevLog.length - 1].reps : null;

  return {
    ...session,
    currentReps: lastLoggedReps ?? suggestion?.reps ?? item?.target_reps ?? 8,
    currentWeight: lastLoggedWeight ?? suggestion?.weight ?? parseFloat(item?.target_weight) ?? 0,
    currentRpe: null,
  };
}
