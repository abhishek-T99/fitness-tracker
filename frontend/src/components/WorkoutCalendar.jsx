/**
 * WorkoutCalendar — GitHub-style contribution heatmap.
 *
 * Props
 * ─────
 *  data      Array of { date: "YYYY-MM-DD", workout_count, total_volume_kg, total_duration_min }
 *            Only days with workouts are present; missing days = rest days.
 *  days      Max days to look back (default 365).
 *  minWeeks  Minimum weeks to always display (default 16) so new users
 *            never see a tiny cluster in a huge empty card.
 */
import { useMemo, useState } from "react";
import { format, parseISO, subDays, startOfWeek, addDays, differenceInCalendarDays } from "date-fns";

const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTHS   = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

function intensityClass(volume) {
  if (!volume) return "rest-cell";
  if (volume < 500)  return "active-cell-1";
  if (volume < 1500) return "active-cell-2";
  if (volume < 3000) return "active-cell-3";
  return "active-cell-4";
}

// Separate intensity → Tailwind classes so JIT scanner sees full strings
const CELL_CLASSES = {
  "rest-cell":    "bg-slate-200/60 dark:bg-ink-700/50",
  "active-cell-1":"bg-brand-200 dark:bg-brand-900",
  "active-cell-2":"bg-brand-400 dark:bg-brand-700",
  "active-cell-3":"bg-brand-500 dark:bg-brand-500",
  "active-cell-4":"bg-brand-700 dark:bg-brand-400",
};

const LEGEND_CLASSES = [
  "bg-slate-200/60 dark:bg-ink-700/50",
  "bg-brand-200 dark:bg-brand-900",
  "bg-brand-400 dark:bg-brand-700",
  "bg-brand-500 dark:bg-brand-500",
  "bg-brand-700 dark:bg-brand-400",
];

export default function WorkoutCalendar({ data = [], days = 365, minWeeks = 16 }) {
  const [tooltip, setTooltip] = useState(null);

  const byDate = useMemo(() => {
    const map = {};
    for (const d of data) map[d.date] = d;
    return map;
  }, [data]);

  const today      = new Date();
  const maxOrigin  = subDays(today, days - 1);           // furthest back (365 d)
  const minOrigin  = subDays(today, minWeeks * 7 - 1);   // minimum grid width

  // Find earliest workout date
  const firstEntryStr = data.length > 0
    ? data.reduce((min, d) => d.date < min ? d.date : min, data[0].date)
    : null;
  const firstEntryDate = firstEntryStr ? parseISO(firstEntryStr) : null;

  // Origin rules:
  //  - New user (first workout < minWeeks ago) → show minWeeks so grid isn't tiny
  //  - Established user → show from first workout (up to maxOrigin)
  //  - Very old user (first workout > 365 d ago) → show full year
  let origin;
  if (!firstEntryDate || firstEntryDate > minOrigin) {
    origin = minOrigin;      // new user: always show at least minWeeks
  } else if (firstEntryDate < maxOrigin) {
    origin = maxOrigin;      // > 365 d of history: cap at 1 year
  } else {
    origin = firstEntryDate; // show from first workout
  }

  const gridStart  = startOfWeek(origin, { weekStartsOn: 0 });
  const totalDays  = differenceInCalendarDays(today, gridStart) + 1;
  const totalWeeks = Math.ceil(totalDays / 7);

  const grid = useMemo(() => {
    const cols = [];
    for (let w = 0; w < totalWeeks; w++) {
      const col = [];
      for (let d = 0; d < 7; d++) {
        const cellDate = addDays(gridStart, w * 7 + d);
        const iso = format(cellDate, "yyyy-MM-dd");
        const inRange = cellDate >= origin && cellDate <= today;
        col.push({ date: cellDate, iso, inRange, entry: byDate[iso] || null });
      }
      cols.push(col);
    }
    return cols;
  }, [byDate, gridStart, origin, totalWeeks]);

  const monthLabels = useMemo(() => {
    const labels = [];
    let lastMonth = -1;
    grid.forEach((col, wi) => {
      const firstInRange = col.find((c) => c.inRange);
      if (!firstInRange) return;
      const m = firstInRange.date.getMonth();
      if (m !== lastMonth) {
        labels.push({ wi, label: MONTHS[m] });
        lastMonth = m;
      }
    });
    return labels;
  }, [grid]);

  const totalWorkouts = data.reduce((s, d) => s + d.workout_count, 0);
  const activeDays    = data.length;

  // Cell + gap size (px) — used for month label positioning
  const CELL = 12;
  const GAP  = 3;
  const COL_STEP = CELL + GAP;

  return (
    <div className="select-none">
      {/* Month labels */}
      <div className="relative h-5 mb-1">
        {monthLabels.map(({ wi, label }) => (
          <span
            key={wi}
            className="absolute text-[10px] text-slate-400"
            style={{ left: wi * COL_STEP }}
          >
            {label}
          </span>
        ))}
      </div>

      <div className="flex" style={{ gap: GAP }}>
        {/* Day-of-week labels */}
        <div className="flex flex-col mr-1 pt-0.5" style={{ gap: GAP }}>
          {WEEKDAYS.map((d, i) => (
            <div
              key={d}
              className="text-[9px] text-slate-400 leading-none flex items-center"
              style={{ height: CELL, width: 20 }}
            >
              {i % 2 === 1 ? d : ""}
            </div>
          ))}
        </div>

        {/* Grid */}
        <div className="flex" style={{ gap: GAP }}>
          {grid.map((col, wi) => (
            <div key={wi} className="flex flex-col" style={{ gap: GAP }}>
              {col.map((cell) => {
                if (!cell.inRange) {
                  return (
                    <div
                      key={cell.iso}
                      style={{ width: CELL, height: CELL }}
                    />
                  );
                }
                const cls = cell.entry
                  ? CELL_CLASSES[intensityClass(cell.entry.total_volume_kg)]
                  : CELL_CLASSES["rest-cell"];
                return (
                  <div
                    key={cell.iso}
                    className={`rounded-sm cursor-default transition-all duration-100 ${cls} ${tooltip?.iso === cell.iso ? "ring-1 ring-brand-500 scale-110" : "hover:scale-110"}`}
                    style={{ width: CELL, height: CELL }}
                    onMouseEnter={() => setTooltip({ ...cell })}
                    onMouseLeave={() => setTooltip(null)}
                  />
                );
              })}
            </div>
          ))}
        </div>
      </div>

      {/* Tooltip */}
      {tooltip && (
        <div className="mt-2 text-xs text-ink-900 bg-white border border-slate-200 rounded-lg px-3 py-2 shadow-lg inline-block">
          <span className="font-semibold">{format(tooltip.date, "EEE, MMM d yyyy")}</span>
          {tooltip.entry ? (
            <span className="ml-2 text-ink-500">
              {tooltip.entry.workout_count} workout{tooltip.entry.workout_count !== 1 ? "s" : ""}
              {" · "}
              {Math.round(tooltip.entry.total_volume_kg).toLocaleString()} kg
              {tooltip.entry.total_duration_min
                ? ` · ${tooltip.entry.total_duration_min} min`
                : ""}
            </span>
          ) : (
            <span className="ml-2 text-ink-400">Rest day</span>
          )}
        </div>
      )}

      {/* Legend + summary */}
      <div className="flex items-center justify-between mt-3">
        <p className="text-[11px] text-slate-400">
          {totalWorkouts} workout{totalWorkouts !== 1 ? "s" : ""} · {activeDays} active day{activeDays !== 1 ? "s" : ""}
        </p>
        <div className="flex items-center gap-1.5 text-[10px] text-slate-400">
          <span>Less</span>
          {LEGEND_CLASSES.map((cls, i) => (
            <div key={i} className={`rounded-sm ${cls}`} style={{ width: CELL, height: CELL }} />
          ))}
          <span>More</span>
        </div>
      </div>
    </div>
  );
}
