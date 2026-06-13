import { useQuery } from "@tanstack/react-query";
import { Footprints, Heart, Zap, Moon, RefreshCw } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { wellnessApi } from "../api/endpoints.js";

const STEP_GOAL = 10_000;

// Circular SVG progress ring
function StepRing({ steps, goal }) {
  const pct = Math.min(1, (steps || 0) / goal);
  const r = 52;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - pct);
  const color = pct >= 1 ? "#10b981" : pct >= 0.6 ? "#0ea5e9" : "#f59e0b";

  return (
    <div className="relative flex items-center justify-center w-36 h-36">
      <svg className="absolute inset-0 -rotate-90" width="144" height="144" viewBox="0 0 144 144">
        {/* track */}
        <circle cx="72" cy="72" r={r} fill="none" stroke="currentColor"
          className="text-slate-100 dark:text-slate-100/10" strokeWidth="10" />
        {/* progress */}
        <circle cx="72" cy="72" r={r} fill="none" stroke={color} strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
      </svg>
      <div className="flex flex-col items-center z-10">
        <span className="text-2xl font-bold text-slate-900 leading-none">
          {steps != null ? steps.toLocaleString() : "—"}
        </span>
        <span className="text-xs text-slate-400 mt-0.5">steps</span>
      </div>
    </div>
  );
}

function WellnessStat({ icon: Icon, label, value, unit, color }) {
  if (value == null) return null;
  return (
    <div className="flex items-center gap-2">
      <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${color}`}>
        <Icon className="w-4 h-4" />
      </div>
      <div className="min-w-0">
        <p className="text-xs text-slate-500">{label}</p>
        <p className="text-sm font-semibold text-slate-900 leading-tight">
          {value} <span className="font-normal text-slate-400">{unit}</span>
        </p>
      </div>
    </div>
  );
}

export default function StepsCounter() {
  const { data, isLoading, dataUpdatedAt, refetch, isFetching } = useQuery({
    queryKey: ["todayWellness"],
    queryFn: wellnessApi.today,
    refetchInterval: 5 * 60 * 1000,   // poll every 5 minutes
    staleTime: 4 * 60 * 1000,
  });

  const steps = data?.steps ?? null;
  const goalPct = steps != null ? Math.min(100, Math.round((steps / STEP_GOAL) * 100)) : 0;
  const lastUpdated = dataUpdatedAt
    ? formatDistanceToNow(new Date(dataUpdatedAt), { addSuffix: true })
    : null;

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="font-semibold flex items-center gap-2">
          <Footprints className="w-4 h-4 text-brand-500" />
          Today's activity
        </h3>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          title="Refresh"
          className="text-slate-400 hover:text-slate-600 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? "animate-spin" : ""}`} />
        </button>
      </div>

      <div className="card-body">
        {isLoading ? (
          <div className="flex items-center justify-center h-32 text-slate-400 text-sm">
            Loading…
          </div>
        ) : steps == null && !data?.resting_hr_bpm && !data?.hrv_rmssd ? (
          <div className="flex flex-col items-center justify-center gap-2 py-4 text-center">
            <Footprints className="w-8 h-8 text-slate-300" />
            <p className="text-sm text-slate-500">No watch data for today yet.</p>
            <p className="text-xs text-slate-400">
              Sync your Amazfit watch via Intervals.icu to see live steps here.
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4">
            {/* Ring */}
            <StepRing steps={steps} goal={STEP_GOAL} />

            {/* Goal label */}
            <div className="text-center -mt-2">
              <p className="text-xs text-slate-400">
                {steps != null
                  ? goalPct >= 100
                    ? "🎉 Daily goal reached!"
                    : `${goalPct}% of ${STEP_GOAL.toLocaleString()} goal`
                  : "Goal: 10,000 steps"}
              </p>
            </div>

            {/* Only render the extra stats block if at least one value exists */}
            {(data?.resting_hr_bpm || data?.hrv_rmssd || data?.sleep_score) ? (
              <div className="w-full grid grid-cols-1 gap-2 pt-2 border-t border-slate-100">
                <WellnessStat
                  icon={Heart}
                  label="Resting HR"
                  value={data?.resting_hr_bpm}
                  unit="bpm"
                  color="bg-rose-50 text-rose-500 dark:bg-rose-500/15"
                />
                <WellnessStat
                  icon={Zap}
                  label="HRV"
                  value={data?.hrv_rmssd != null ? Number(data.hrv_rmssd).toFixed(1) : null}
                  unit="ms"
                  color="bg-violet-50 text-violet-500 dark:bg-violet-500/15"
                />
                <WellnessStat
                  icon={Moon}
                  label="Sleep score"
                  value={data?.sleep_score}
                  unit="/ 100"
                  color="bg-indigo-50 text-indigo-500 dark:bg-indigo-500/15"
                />
              </div>
            ) : (
              <p className="text-xs text-slate-400 text-center px-2 border-t border-slate-100 pt-3 w-full">
                HR, HRV &amp; sleep data not available — Amazfit only syncs step count to Intervals.icu.
              </p>
            )}

            {lastUpdated && (
              <p className="text-xs text-slate-400 self-start">
                Updated {lastUpdated}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
