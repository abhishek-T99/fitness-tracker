/**
 * MealPlan — weekly meal planner
 *
 * Layout:
 *   Week navigator (← Mon dd MMM – Sun dd MMM →)
 *   [Generate week]  [New plan]
 *
 *   7-column grid, one column per day:
 *     Day label + date
 *     Macro heatmap bar (green/yellow/red based on calorie % of target)
 *     Daily calorie total
 *     4 meal sections (Breakfast / Lunch / Dinner / Snack)
 *       Each food item row: name, servings, kcal, remove
 *       [+ Add food] button per slot
 *
 *   On the current day: [Log today to tracker] button
 */
import { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ChevronLeft, ChevronRight, Plus, Trash2, Sparkles,
  CalendarCheck, Loader2, UtensilsCrossed,
} from "lucide-react";
import { format, addDays, startOfWeek, addWeeks, subWeeks, isToday, parseISO } from "date-fns";
import toast from "react-hot-toast";

import PageHeader from "../components/PageHeader.jsx";
import { foodsApi, mealPlanApi } from "../api/endpoints.js";

const DAYS        = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const MEAL_TYPES  = ["breakfast", "lunch", "dinner", "snack"];
const MEAL_LABELS = { breakfast: "Breakfast", lunch: "Lunch", dinner: "Dinner", snack: "Snack" };

// ── Helpers ───────────────────────────────────────────────────────────────────

function toMonday(date) {
  return startOfWeek(date, { weekStartsOn: 1 });
}

function heatColor(pct) {
  if (pct === 0)          return "bg-slate-100 dark:bg-slate-100/10";
  if (pct < 70)           return "bg-rose-400";
  if (pct < 90)           return "bg-amber-400";
  if (pct <= 110)         return "bg-emerald-500";
  if (pct <= 130)         return "bg-amber-400";
  return "bg-rose-400";
}

function heatLabel(pct) {
  if (pct === 0)   return "—";
  if (pct < 70)    return "Low";
  if (pct <= 110)  return "On target";
  return "Over";
}

// ── Food search picker ────────────────────────────────────────────────────────

function FoodPicker({ onPick, onClose }) {
  const [search, setSearch] = useState("");
  const [servings, setServings] = useState(1);
  const [selected, setSelected] = useState(null);

  const { data } = useQuery({
    queryKey: ["foodPicker", search],
    queryFn: () => foodsApi.list({ search, page_size: 20 }),
    enabled: search.length > 0,
  });
  const foods = data?.results || [];

  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex items-end sm:items-center justify-center p-4">
      <div className="bg-surface rounded-2xl shadow-xl w-full max-w-md flex flex-col max-h-[80vh]">
        <div className="border-b border-slate-200 px-5 py-4 flex items-center justify-between">
          <h3 className="font-semibold">Add food</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-lg leading-none">✕</button>
        </div>

        <div className="p-4 border-b border-slate-100">
          <input
            autoFocus
            className="input"
            placeholder="Search foods…"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setSelected(null); }}
          />
        </div>

        <div className="overflow-y-auto flex-1">
          {foods.map((f) => (
            <button
              key={f.id}
              onClick={() => setSelected(f)}
              className={`w-full text-left px-4 py-2.5 flex items-center justify-between text-sm border-b border-slate-50 transition ${
                selected?.id === f.id ? "bg-brand-50 dark:bg-brand-500/10" : "hover:bg-slate-50"
              }`}
            >
              <div>
                <p className="font-medium text-slate-900">{f.name}</p>
                <p className="text-xs text-slate-400">per {f.serving_size} {f.serving_unit}</p>
              </div>
              <span className="text-xs text-slate-500 shrink-0 ml-2">{f.calories} kcal</span>
            </button>
          ))}
          {search && foods.length === 0 && (
            <p className="p-4 text-sm text-slate-400 text-center">No results</p>
          )}
        </div>

        {selected && (
          <div className="border-t border-slate-200 p-4 space-y-3">
            <p className="text-sm font-medium text-slate-900">{selected.name}</p>
            <div className="flex items-center gap-3">
              <label className="text-sm text-slate-500 shrink-0">Servings</label>
              <input
                type="number" step="0.25" min="0.25"
                className="input w-24 text-center py-1.5"
                value={servings}
                onChange={(e) => setServings(Number(e.target.value))}
              />
              <span className="text-xs text-slate-400">
                = {Math.round(parseFloat(selected.serving_size) * servings)} {selected.serving_unit} ·{" "}
                {Math.round(parseFloat(selected.calories) * servings)} kcal
              </span>
            </div>
            <button
              onClick={() => onPick(selected, servings)}
              className="btn-primary w-full"
            >
              Add to plan
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Meal slot ─────────────────────────────────────────────────────────────────

function MealSlot({ planId, dayIdx, mealType, items, onMutated }) {
  const [picking, setPicking] = useState(false);
  const queryClient = useQueryClient();

  const addItem = useMutation({
    mutationFn: ({ food, servings }) =>
      mealPlanApi.addItem(planId, { day: dayIdx, meal_type: mealType, food: food.id, servings }),
    onSuccess: () => { onMutated(); setPicking(false); },
    onError: () => toast.error("Could not add food"),
  });

  const removeItem = useMutation({
    mutationFn: (itemId) => mealPlanApi.removeItem(itemId),
    onSuccess: onMutated,
    onError: () => toast.error("Could not remove"),
  });

  return (
    <div className="space-y-1">
      {items.map((it) => (
        <div key={it.id} className="flex items-center gap-1.5 group">
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-slate-800 truncate leading-snug">
              {it.food_detail?.name}
            </p>
            <p className="text-[10px] text-slate-400">
              {it.servings}× · {it.calories} kcal
            </p>
          </div>
          <button
            onClick={() => removeItem.mutate(it.id)}
            className="opacity-0 group-hover:opacity-100 text-slate-300 hover:text-rose-400 transition-opacity shrink-0"
          >
            <Trash2 className="w-3 h-3" />
          </button>
        </div>
      ))}

      <button
        onClick={() => setPicking(true)}
        className="flex items-center gap-1 text-[10px] text-slate-400 hover:text-brand-600 transition-colors"
      >
        <Plus className="w-3 h-3" /> Add
      </button>

      {picking && (
        <FoodPicker
          onPick={(food, servings) => addItem.mutate({ food, servings })}
          onClose={() => setPicking(false)}
        />
      )}
    </div>
  );
}

// ── Day column ─────────────────────────────────────────────────────────────────

function DayColumn({ planId, dayIdx, date, items, summary, calTarget, onMutated, onLogDay }) {
  const dayLabel = DAYS[dayIdx];
  const isCurrentDay = isToday(date);
  const dayData  = summary?.days?.[dayIdx];
  const pct      = dayData?.calorie_pct ?? 0;
  const cal      = dayData?.calories ?? 0;

  return (
    <div className={`flex flex-col rounded-xl border min-w-[140px] overflow-hidden ${
      isCurrentDay ? "border-brand-400 shadow-sm shadow-brand-500/20" : "border-slate-200"
    }`}>
      {/* Header */}
      <div className={`px-2.5 py-2 text-center ${isCurrentDay ? "bg-brand-600" : "bg-slate-50 dark:bg-slate-100/5"}`}>
        <p className={`text-xs font-bold uppercase tracking-wide ${isCurrentDay ? "text-white" : "text-slate-500"}`}>
          {dayLabel}
        </p>
        <p className={`text-[10px] ${isCurrentDay ? "text-brand-100" : "text-slate-400"}`}>
          {format(date, "MMM d")}
        </p>
      </div>

      {/* Heatmap bar */}
      <div className="px-2.5 py-2 border-b border-slate-100 dark:border-slate-100/10">
        <div className="h-1.5 rounded-full bg-slate-100 overflow-hidden mb-1">
          <div
            className={`h-full rounded-full transition-all ${heatColor(pct)}`}
            style={{ width: `${Math.min(pct, 100)}%` }}
          />
        </div>
        <p className="text-[10px] text-center text-slate-400">
          {cal > 0 ? `${Math.round(cal)} kcal` : "—"}
        </p>
      </div>

      {/* Meal sections */}
      <div className="flex-1 divide-y divide-slate-100 dark:divide-slate-100/10">
        {MEAL_TYPES.map((mt) => {
          const slotItems = items.filter((it) => it.meal_type === mt);
          return (
            <div key={mt} className="px-2.5 py-2">
              <p className="text-[9px] font-bold uppercase tracking-widest text-slate-400 mb-1.5">
                {MEAL_LABELS[mt]}
              </p>
              <MealSlot
                planId={planId}
                dayIdx={dayIdx}
                mealType={mt}
                items={slotItems}
                onMutated={onMutated}
              />
            </div>
          );
        })}
      </div>

      {/* Log today */}
      {isCurrentDay && (
        <div className="p-2 border-t border-slate-100">
          <button
            onClick={() => onLogDay(dayIdx)}
            className="btn-primary w-full text-[10px] py-1.5 gap-1"
          >
            <CalendarCheck className="w-3 h-3" />
            Log to tracker
          </button>
        </div>
      )}
    </div>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────────

export default function MealPlan() {
  const queryClient = useQueryClient();
  const [weekStart, setWeekStart] = useState(() => toMonday(new Date()));
  const weekStartStr = format(weekStart, "yyyy-MM-dd");

  // Fetch or create plan for this week
  const { data: plans, isLoading } = useQuery({
    queryKey: ["mealPlans", weekStartStr],
    queryFn: () => mealPlanApi.list({ week_start: weekStartStr }),
  });

  const planList = plans?.results || plans || [];
  const plan     = planList[0] ?? null;

  const { data: summary } = useQuery({
    queryKey: ["mealPlanSummary", plan?.id],
    queryFn: () => mealPlanApi.summary(plan.id),
    enabled: !!plan?.id,
  });

  const createPlan = useMutation({
    mutationFn: () => mealPlanApi.create({ name: `Week of ${weekStartStr}`, week_start: weekStartStr }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["mealPlans", weekStartStr] }),
    onError: () => toast.error("Could not create plan"),
  });

  const generate = useMutation({
    mutationFn: () => mealPlanApi.generate(plan.id),
    onSuccess: () => {
      toast.success("Plan generated from your food history!");
      invalidate();
    },
    onError: () => toast.error("Could not generate plan"),
  });

  const logDay = useMutation({
    mutationFn: (day) => mealPlanApi.logDay(plan.id, { day }),
    onSuccess: () => {
      toast.success("Today's meals logged to the nutrition tracker!");
      queryClient.invalidateQueries({ queryKey: ["meals"] });
      queryClient.invalidateQueries({ queryKey: ["dailyNutrition"] });
    },
    onError: (err) => {
      const msg = err?.response?.data?.detail || "Could not log day";
      toast.error(msg);
    },
  });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["mealPlans", weekStartStr] });
    queryClient.invalidateQueries({ queryKey: ["mealPlanSummary", plan?.id] });
  }

  const weekDates = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));

  return (
    <div>
      <PageHeader
        title="Meal Plan"
        subtitle="Plan your week, hit your targets"
        actions={
          <div className="flex gap-2">
            {plan && (
              <button
                onClick={() => generate.mutate()}
                disabled={generate.isPending}
                className="btn-secondary gap-1.5"
              >
                {generate.isPending
                  ? <Loader2 className="w-4 h-4 animate-spin" />
                  : <Sparkles className="w-4 h-4" />}
                Generate week
              </button>
            )}
            {!plan && (
              <button
                onClick={() => createPlan.mutate()}
                disabled={createPlan.isPending}
                className="btn-primary gap-1.5"
              >
                <Plus className="w-4 h-4" />
                {createPlan.isPending ? "Creating…" : "New plan"}
              </button>
            )}
          </div>
        }
      />

      {/* Week navigator */}
      <div className="flex items-center gap-3 mb-6">
        <button
          onClick={() => setWeekStart((w) => toMonday(subWeeks(w, 1)))}
          className="btn-ghost p-2"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        <span className="text-sm font-medium text-slate-700 flex-1 text-center">
          {format(weekStart, "MMM d")} – {format(addDays(weekStart, 6), "MMM d, yyyy")}
        </span>
        <button
          onClick={() => setWeekStart((w) => toMonday(addWeeks(w, 1)))}
          className="btn-ghost p-2"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>

      {/* Calorie target hint */}
      {summary && (
        <div className="flex items-center gap-4 mb-4 text-xs text-slate-500 flex-wrap">
          <span>Daily target: <strong className="text-slate-700">{Math.round(summary.cal_target)} kcal</strong></span>
          <span>Protein target: <strong className="text-slate-700">{Math.round(summary.protein_target)}g</strong></span>
          <span className="flex items-center gap-2 ml-auto">
            <span className="inline-block w-3 h-3 rounded-sm bg-emerald-500"></span> On target (90–110%)
            <span className="inline-block w-3 h-3 rounded-sm bg-amber-400"></span> Low/High
            <span className="inline-block w-3 h-3 rounded-sm bg-rose-400"></span> Off
          </span>
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center h-40 text-slate-400">
          <Loader2 className="w-6 h-6 animate-spin" />
        </div>
      ) : !plan ? (
        <div className="card p-12 flex flex-col items-center gap-4 text-center">
          <UtensilsCrossed className="w-12 h-12 text-slate-300" />
          <div>
            <p className="font-semibold text-slate-700">No plan for this week yet</p>
            <p className="text-sm text-slate-400 mt-1">
              Create a plan and then hit "Generate week" to auto-fill it from your food history.
            </p>
          </div>
          <button onClick={() => createPlan.mutate()} disabled={createPlan.isPending} className="btn-primary">
            <Plus className="w-4 h-4" /> Create plan
          </button>
        </div>
      ) : (
        <div className="overflow-x-auto pb-4">
          <div className="flex gap-3 min-w-max">
            {weekDates.map((date, dayIdx) => (
              <DayColumn
                key={dayIdx}
                planId={plan.id}
                dayIdx={dayIdx}
                date={date}
                items={plan.items?.filter((it) => it.day === dayIdx) ?? []}
                summary={summary}
                calTarget={summary?.cal_target}
                onMutated={invalidate}
                onLogDay={(d) => logDay.mutate(d)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
