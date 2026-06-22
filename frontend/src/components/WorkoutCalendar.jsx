/**
 * WorkoutCalendar — GitHub-style activity heatmap.
 *
 * Props
 * ─────
 *  data          Array of { date: "YYYY-MM-DD", workout_count, total_volume_kg, total_duration_min }
 *  gridStartDate Date — first day of the grid (snapped to its Sunday). Defaults to start of current week.
 *  gridEndDate   Date — last day to show (inclusive). Defaults to 52 weeks after gridStartDate.
 */
import { useMemo, useState } from "react";
import { format, isSameDay, startOfWeek, addDays } from "date-fns";

const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTHS   = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

const MS_PER_WEEK = 7 * 24 * 60 * 60 * 1000;

function intensityClass(volume) {
  if (!volume) return "rest-cell";
  if (volume < 500)  return "active-cell-1";
  if (volume < 1500) return "active-cell-2";
  if (volume < 3000) return "active-cell-3";
  return "active-cell-4";
}

const CELL_CLASSES = {
  "rest-cell":     "bg-slate-200/60 dark:bg-ink-700/50",
  "active-cell-1": "bg-brand-200 dark:bg-brand-900",
  "active-cell-2": "bg-brand-400 dark:bg-brand-700",
  "active-cell-3": "bg-brand-500 dark:bg-brand-500",
  "active-cell-4": "bg-brand-700 dark:bg-brand-400",
};

const LEGEND_CLASSES = [
  "bg-slate-200/60 dark:bg-ink-700/50",
  "bg-brand-200 dark:bg-brand-900",
  "bg-brand-400 dark:bg-brand-700",
  "bg-brand-500 dark:bg-brand-500",
  "bg-brand-700 dark:bg-brand-400",
];

const CELL     = 12;
const GAP      = 3;
const COL_STEP = CELL + GAP;

export default function WorkoutCalendar({ data = [], gridStartDate = null, gridEndDate = null }) {
  const [tooltip, setTooltip] = useState(null);

  const byDate = useMemo(() => {
    const map = {};
    for (const d of data) map[d.date] = d;
    return map;
  }, [data]);

  const today      = new Date();
  const gridStart  = startOfWeek(gridStartDate ?? today, { weekStartsOn: 0 });
  const gridEnd    = gridEndDate ?? addDays(gridStart, 52 * 7);

  // Number of Sunday-aligned columns needed to cover gridStart → gridEnd
  const totalWeeks = Math.ceil(Math.max(1, (gridEnd - gridStart) / MS_PER_WEEK));

  const grid = useMemo(() => {
    const cols = [];
    for (let w = 0; w < totalWeeks; w++) {
      const col = [];
      for (let d = 0; d < 7; d++) {
        const cellDate   = addDays(gridStart, w * 7 + d);
        const iso        = format(cellDate, "yyyy-MM-dd");
        const isFuture   = cellDate > today;
        const isAfterEnd = cellDate > gridEnd;
        const isToday    = isSameDay(cellDate, today);
        col.push({ date: cellDate, iso, isFuture, isAfterEnd, isToday, entry: byDate[iso] || null });
      }
      cols.push(col);
    }
    return cols;
  }, [byDate, gridStart, gridEnd, totalWeeks]);

  const monthLabels = useMemo(() => {
    const labels = [];
    let lastMonth = -1;
    let lastWi    = -4;
    grid.forEach((col, wi) => {
      const m = col[0].date.getMonth();
      if (m !== lastMonth && wi - lastWi >= 3) {
        labels.push({ wi, label: MONTHS[m] });
        lastMonth = m;
        lastWi    = wi;
      }
    });
    return labels;
  }, [grid]);

  const totalWorkouts = data.reduce((s, d) => s + d.workout_count, 0);
  const activeDays    = data.length;

  return (
    <div className="select-none overflow-x-auto">
      {/* Month labels */}
      <div className="relative h-5 mb-1" style={{ minWidth: totalWeeks * COL_STEP + 24 }}>
        {monthLabels.map(({ wi, label }) => (
          <span
            key={wi}
            className="absolute text-[10px] text-slate-400 whitespace-nowrap"
            style={{ left: wi * COL_STEP + 24 }}
          >
            {label}
          </span>
        ))}
      </div>

      <div className="flex" style={{ gap: GAP }}>
        {/* Day-of-week labels */}
        <div className="flex flex-col shrink-0 mr-1 pt-0.5" style={{ gap: GAP, width: 20 }}>
          {WEEKDAYS.map((d, i) => (
            <div
              key={d}
              className="text-[9px] text-slate-400 leading-none flex items-center"
              style={{ height: CELL }}
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
                // Days past the end date: invisible placeholder keeps column width stable
                if (cell.isAfterEnd) {
                  return <div key={cell.iso} style={{ width: CELL, height: CELL }} />;
                }

                let cls;
                if (cell.isFuture) {
                  cls = "bg-slate-200/50 dark:bg-ink-600/50";
                } else if (cell.entry) {
                  cls = CELL_CLASSES[intensityClass(cell.entry.total_volume_kg)];
                } else {
                  cls = CELL_CLASSES["rest-cell"];
                }

                const ring = cell.isToday
                  ? "ring-1 ring-brand-500 ring-offset-1 ring-offset-surface"
                  : tooltip?.iso === cell.iso
                    ? "ring-1 ring-brand-400 scale-110"
                    : "hover:scale-110";

                return (
                  <div
                    key={cell.iso}
                    className={`rounded-sm transition-all duration-100 ${cls} ${
                      cell.isFuture
                        ? "opacity-40"
                        : `cursor-default ${ring}`
                    }`}
                    style={{ width: CELL, height: CELL }}
                    onMouseEnter={() => !cell.isFuture && setTooltip({ ...cell })}
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
        <div className="mt-2 text-xs text-ink-900 bg-white border border-slate-200 rounded-lg px-3 py-2 shadow-lg inline-block dark:bg-ink-800 dark:border-ink-600 dark:text-ink-100">
          <span className="font-semibold">{format(tooltip.date, "EEE, MMM d yyyy")}</span>
          {tooltip.entry ? (
            <span className="ml-2 text-ink-500 dark:text-ink-300">
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
