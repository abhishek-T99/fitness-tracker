/**
 * WorkoutCalendar — GitHub-style contribution heatmap.
 *
 * Props
 * ─────
 *  data  Array of { date: "YYYY-MM-DD", workout_count, total_volume_kg, total_duration_min }
 *        Only days with workouts are present; missing days = rest days.
 *  days  Number of days to display (default 365).
 */
import { useMemo, useState } from "react";
import { format, parseISO, subDays, startOfWeek, addDays, differenceInCalendarDays } from "date-fns";

const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTHS   = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

function intensityClass(volume) {
  if (!volume) return "bg-slate-100 dark:bg-slate-800";
  if (volume < 500)  return "bg-brand-200 dark:bg-brand-900";
  if (volume < 1500) return "bg-brand-400 dark:bg-brand-700";
  if (volume < 3000) return "bg-brand-500 dark:bg-brand-500";
  return "bg-brand-700 dark:bg-brand-400";
}

export default function WorkoutCalendar({ data = [], days = 365 }) {
  const [tooltip, setTooltip] = useState(null);

  // Build a lookup from date-string → data
  const byDate = useMemo(() => {
    const map = {};
    for (const d of data) map[d.date] = d;
    return map;
  }, [data]);

  // Build the grid: columns = weeks (left→right), rows = day-of-week (Sun=0)
  const today  = new Date();
  const origin = subDays(today, days - 1);
  // Align to the Sunday of the week containing origin
  const gridStart = startOfWeek(origin, { weekStartsOn: 0 });
  const totalDays = differenceInCalendarDays(today, gridStart) + 1;
  const totalWeeks = Math.ceil(totalDays / 7);

  // Cells: [week][dow] = { date, inRange, entry }
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

  // Month labels: one per month change along the top
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

  return (
    <div className="select-none">
      {/* Month labels */}
      <div className="relative h-5 mb-1">
        {monthLabels.map(({ wi, label }) => (
          <span
            key={wi}
            className="absolute text-[10px] text-slate-400"
            style={{ left: wi * 13 }}
          >
            {label}
          </span>
        ))}
      </div>

      <div className="flex gap-0.5">
        {/* Day-of-week labels */}
        <div className="flex flex-col gap-0.5 mr-1 pt-0.5">
          {WEEKDAYS.map((d, i) => (
            <div key={d} className="w-5 h-2.5 text-[9px] text-slate-400 leading-none">
              {i % 2 === 1 ? d : ""}
            </div>
          ))}
        </div>

        {/* Grid */}
        <div className="flex gap-0.5">
          {grid.map((col, wi) => (
            <div key={wi} className="flex flex-col gap-0.5">
              {col.map((cell) => {
                if (!cell.inRange) {
                  return <div key={cell.iso} className="w-2.5 h-2.5" />;
                }
                return (
                  <div
                    key={cell.iso}
                    className={`w-2.5 h-2.5 rounded-sm cursor-default transition-opacity
                      ${cell.entry ? intensityClass(cell.entry.total_volume_kg) : "bg-slate-100 dark:bg-slate-800"}
                      ${tooltip?.iso === cell.iso ? "ring-1 ring-brand-500" : ""}
                    `}
                    onMouseEnter={() => setTooltip({ ...cell, x: wi, y: wi })}
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
        <div className="mt-2 text-xs text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2 shadow-md inline-block">
          <span className="font-semibold">{format(tooltip.date, "EEE, MMM d yyyy")}</span>
          {tooltip.entry ? (
            <span className="ml-2 text-slate-500">
              {tooltip.entry.workout_count} workout{tooltip.entry.workout_count !== 1 ? "s" : ""}
              {" · "}
              {Math.round(tooltip.entry.total_volume_kg).toLocaleString()} kg
              {tooltip.entry.total_duration_min
                ? ` · ${tooltip.entry.total_duration_min} min`
                : ""}
            </span>
          ) : (
            <span className="ml-2 text-slate-400">Rest day</span>
          )}
        </div>
      )}

      {/* Legend + summary */}
      <div className="flex items-center justify-between mt-3">
        <p className="text-[11px] text-slate-400">
          {totalWorkouts} workout{totalWorkouts !== 1 ? "s" : ""} across {activeDays} active day{activeDays !== 1 ? "s" : ""}
        </p>
        <div className="flex items-center gap-1 text-[10px] text-slate-400">
          <span>Less</span>
          {["bg-slate-100 dark:bg-slate-800","bg-brand-200 dark:bg-brand-900","bg-brand-400 dark:bg-brand-700","bg-brand-500 dark:bg-brand-500","bg-brand-700 dark:bg-brand-400"].map((cls, i) => (
            <div key={i} className={`w-2.5 h-2.5 rounded-sm ${cls}`} />
          ))}
          <span>More</span>
        </div>
      </div>
    </div>
  );
}
