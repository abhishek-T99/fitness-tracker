import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2, Droplets, Pencil, Sparkles, Send } from "lucide-react";
import { format } from "date-fns";
import toast from "react-hot-toast";

import PageHeader from "../components/PageHeader.jsx";
import NutritionTabs from "../components/NutritionTabs.jsx";
import { aiApi, foodsApi, mealsApi, waterApi } from "../api/endpoints.js";
import { qk } from "../api/queryKeys.js";

const MEAL_TYPES = [
  { value: "breakfast", label: "Breakfast" },
  { value: "lunch",     label: "Lunch" },
  { value: "dinner",    label: "Dinner" },
  { value: "snack",     label: "Snack" },
];

const WATER_PRESETS = [250, 500, 750];

export default function Nutrition() {
  const queryClient = useQueryClient();
  const today = format(new Date(), "yyyy-MM-dd");
  const [date, setDate] = useState(today);
  const [adding, setAdding] = useState(false);
  const [editingMeal, setEditingMeal] = useState(null);
  const [editingWater, setEditingWater] = useState(null);

  const { data: summary } = useQuery({
    queryKey: qk.nutrition.dailySummary(date),
    queryFn: () => mealsApi.dailySummary(date),
  });
  const { data: meals } = useQuery({
    queryKey: qk.nutrition.meals(date),
    queryFn: () => mealsApi.list({ date }),
  });
  const { data: waterData } = useQuery({
    queryKey: qk.nutrition.water(date),
    queryFn: () => waterApi.list({ date }),
  });

  const invalidateNutrition = () => {
    queryClient.invalidateQueries({ queryKey: qk.nutrition.meals() });
    queryClient.invalidateQueries({ queryKey: qk.nutrition.dailySummary() });
    queryClient.invalidateQueries({ queryKey: qk.nutrition.rangeSummary() });
  };
  const invalidateWater = () => {
    queryClient.invalidateQueries({ queryKey: qk.nutrition.water() });
    queryClient.invalidateQueries({ queryKey: qk.nutrition.dailySummary() });
    queryClient.invalidateQueries({ queryKey: qk.nutrition.rangeSummary() });
  };

  const removeMeal = useMutation({
    mutationFn: (id) => mealsApi.remove(id),
    onSuccess: () => { toast.success("Meal removed"); invalidateNutrition(); },
  });

  const addWater = useMutation({
    mutationFn: (ml) => {
      const now = new Date();
      // When viewing a past/future date, anchor the log to that date at the
      // current time-of-day so it lands on the day the user is actually
      // looking at, instead of always defaulting to "right now".
      const loggedAt = date === today
        ? now.toISOString()
        : new Date(`${date}T${format(now, "HH:mm:ss")}`).toISOString();
      return waterApi.create({ amount_ml: ml, logged_at: loggedAt });
    },
    onSuccess: () => { toast.success("Water logged"); invalidateWater(); },
  });

  const removeWater = useMutation({
    mutationFn: (id) => waterApi.remove(id),
    onSuccess: () => { toast.success("Water entry deleted"); invalidateWater(); },
  });

  const undoAiBatch = async (created) => {
    const tasks = [
      ...(created.meal_ids ?? []).map((id) => mealsApi.remove(id).catch(() => {})),
      ...(created.water_log_ids ?? []).map((id) => waterApi.remove(id).catch(() => {})),
    ];
    await Promise.all(tasks);
    invalidateNutrition();
    invalidateWater();
    toast.success("Undone");
  };

  const aiParse = useMutation({
    mutationFn: (text) => aiApi.nutritionParse({ text, date }),
    onSuccess: (data) => {
      invalidateNutrition();
      invalidateWater();
      const created = data.created || { meal_ids: [], water_log_ids: [], food_ids: [] };
      const total = created.meal_ids.length + created.water_log_ids.length;
      toast.success(
        (t) => (
          <span className="flex items-center gap-2">
            <span>{data.summary || "Logged."}</span>
            {total > 0 && (
              <button
                onClick={() => { toast.dismiss(t.id); undoAiBatch(created); }}
                className="text-xs underline text-brand-600 hover:text-brand-700"
              >
                Undo
              </button>
            )}
          </span>
        ),
        { duration: 8000 },
      );
    },
    onError: (err) => {
      const msg = err?.response?.data?.detail || "Couldn't parse that — try rephrasing.";
      toast.error(msg);
    },
  });

  const mealItems = meals?.results || meals || [];
  const waterLogs = waterData?.results || waterData || [];

  return (
    <div>
      <PageHeader
        title="Nutrition"
        subtitle="Track meals, calories, and macros"
        actions={
          <button onClick={() => setAdding(true)} className="btn-primary">
            <Plus className="w-4 h-4" /> Log meal
          </button>
        }
      />

      <NutritionTabs />

      {/* AI quick-log */}
      <AiQuickLog
        onSubmit={(text) => aiParse.mutate(text)}
        pending={aiParse.isPending}
      />

      {/* Date + water controls */}
      <div className="card p-4 mb-6 flex flex-wrap items-center gap-3 justify-between">
        <input
          type="date"
          className="input w-auto"
          value={date}
          onChange={(e) => setDate(e.target.value)}
        />
        <div className="flex gap-2 flex-wrap">
          {WATER_PRESETS.map((ml) => (
            <button key={ml} onClick={() => addWater.mutate(ml)} className="btn-secondary">
              <Droplets className="w-4 h-4" /> +{ml} ml
            </button>
          ))}
        </div>
      </div>

      {/* Macro summary */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
        <MacroCard label="Calories" value={summary?.totals?.calories ?? 0} goal={summary?.calorie_goal} unit="kcal" color="bg-rose-500" />
        <MacroCard label="Protein"  value={summary?.totals?.protein_g ?? 0} unit="g" color="bg-emerald-500" />
        <MacroCard label="Carbs"    value={summary?.totals?.carbs_g ?? 0} unit="g" color="bg-amber-500" />
        <MacroCard label="Fat"      value={summary?.totals?.fat_g ?? 0} unit="g" color="bg-indigo-500" />
        <MacroCard label="Water"    value={summary?.water_ml ?? 0} unit="ml" color="bg-brand-500" />
      </div>

      {/* Water log entries */}
      {waterLogs.length > 0 && (
        <div className="card mb-4">
          <div className="card-header">
            <h3 className="font-semibold flex items-center gap-2">
              <Droplets className="w-4 h-4 text-brand-500" /> Water log
            </h3>
          </div>
          <div className="card-body">
            <div className="space-y-1.5">
              {waterLogs.map((w) => (
                <div key={w.id} className="flex items-center justify-between text-sm">
                  <span className="text-slate-500">{format(new Date(w.logged_at), "h:mm a")}</span>
                  <span className="font-medium text-brand-600">{w.amount_ml} ml</span>
                  <div className="flex gap-1">
                    <button
                      onClick={() => setEditingWater(w)}
                      className="p-1 text-slate-400 hover:text-brand-600 rounded transition-colors"
                      title="Edit"
                    >
                      <Pencil className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => removeWater.mutate(w.id)}
                      className="p-1 text-slate-400 hover:text-rose-500 rounded transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Meal sections by type */}
      <div className="space-y-4">
        {MEAL_TYPES.map(({ value, label }) => {
          const mealsForType = mealItems.filter((m) => m.meal_type === value);
          return (
            <div key={value} className="card">
              <div className="card-header">
                <h3 className="font-semibold">{label}</h3>
              </div>
              <div className="card-body space-y-3">
                {mealsForType.length === 0 ? (
                  <p className="text-sm text-slate-400">Nothing logged.</p>
                ) : (
                  mealsForType.map((meal) => (
                    <div key={meal.id} className="border border-slate-100 rounded-lg p-3">
                      <div className="flex justify-between items-center mb-2">
                        <div>
                          <p className="text-xs text-slate-500">
                            {format(new Date(meal.consumed_at), "h:mm a")}
                          </p>
                          <p className="text-sm font-medium">
                            {meal.totals.calories} kcal · {meal.totals.protein_g}g protein
                          </p>
                        </div>
                        <div className="flex gap-1">
                          <button
                            onClick={() => setEditingMeal(meal)}
                            className="p-1.5 text-slate-400 hover:text-brand-600 hover:bg-brand-50 dark:hover:bg-brand-500/10 rounded-lg transition-colors"
                            title="Edit meal"
                          >
                            <Pencil className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => removeMeal.mutate(meal.id)}
                            className="p-1.5 text-slate-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-500/10 rounded-lg transition-colors"
                            title="Delete meal"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                      <ul className="text-sm text-slate-600 space-y-0.5">
                        {meal.items.map((it) => {
                          const su = it.food_detail?.serving_unit || "g";
                          const ss = parseFloat(it.food_detail?.serving_size || 0);
                          const grams = Math.round(ss * parseFloat(it.servings));
                          return (
                            <li key={it.id} className="flex items-center justify-between gap-2">
                              <span>• {it.food_detail.name}</span>
                              <span className="text-slate-400 text-xs shrink-0">
                                {it.servings} serving{parseFloat(it.servings) !== 1 ? "s" : ""}
                                {ss > 0 ? ` (${grams} ${su})` : ""} · {it.calories} kcal
                              </span>
                            </li>
                          );
                        })}
                      </ul>
                    </div>
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Modals */}
      {adding && (
        <MealModal
          date={date}
          onClose={() => setAdding(false)}
          onSaved={() => { setAdding(false); invalidateNutrition(); }}
        />
      )}
      {editingMeal && (
        <MealModal
          date={date}
          meal={editingMeal}
          onClose={() => setEditingMeal(null)}
          onSaved={() => { setEditingMeal(null); invalidateNutrition(); }}
        />
      )}
      {editingWater && (
        <WaterEditModal
          water={editingWater}
          onClose={() => setEditingWater(null)}
          onSaved={() => { setEditingWater(null); invalidateWater(); }}
        />
      )}
    </div>
  );
}

// ── MacroCard ──────────────────────────────────────────────────────────────

function MacroCard({ label, value, goal, unit, color }) {
  const pct = goal ? Math.min(100, Math.round((value / goal) * 100)) : null;
  return (
    <div className="card p-4">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-xl font-bold mt-1">
        {value} <span className="text-sm font-normal text-slate-400">{unit}</span>
      </p>
      {goal && (
        <>
          <div className="h-1.5 bg-slate-100 rounded-full mt-2 overflow-hidden">
            <div className={`h-full ${color}`} style={{ width: `${pct}%` }} />
          </div>
          <p className="text-xs text-slate-400 mt-1">Goal: {goal}</p>
        </>
      )}
    </div>
  );
}

// ── AI quick-log ───────────────────────────────────────────────────────────

function AiQuickLog({ onSubmit, pending }) {
  const [text, setText] = useState("");
  const submit = () => {
    const trimmed = text.trim();
    if (!trimmed || pending) return;
    onSubmit(trimmed);
    setText("");
  };
  return (
    <div className="card p-4 mb-4">
      <label className="flex items-center gap-2 text-xs font-medium text-slate-500 mb-2">
        <Sparkles className="w-3.5 h-3.5 text-brand-500" />
        Quick log with AI
      </label>
      <div className="flex gap-2">
        <input
          className="input flex-1"
          placeholder='Try "two boiled eggs and 500 ml of water"'
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          disabled={pending}
        />
        <button
          onClick={submit}
          disabled={pending || !text.trim()}
          className="btn-primary"
          title="Parse and log"
        >
          {pending ? (
            <span className="inline-block w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </button>
      </div>
      <p className="text-xs text-slate-400 mt-2">
        Describe what you ate or drank. The agent will look up the foods and log them
        for {/* current date hint comes from the page */}the selected date.
      </p>
    </div>
  );
}

// ── Water edit modal ───────────────────────────────────────────────────────

function WaterEditModal({ water, onClose, onSaved }) {
  const [amount, setAmount] = useState(water.amount_ml);

  const save = useMutation({
    mutationFn: () => waterApi.update(water.id, { amount_ml: Number(amount) }),
    onSuccess: () => { toast.success("Water updated"); onSaved(); },
    onError: () => toast.error("Could not update"),
  });

  return (
    <div className="fixed inset-0 z-40 bg-black/60 flex items-center justify-center p-4">
      <div className="bg-surface rounded-2xl shadow-xl w-full max-w-xs p-6 space-y-4">
        <h3 className="font-semibold text-slate-900">Edit water entry</h3>
        <p className="text-xs text-slate-500">{format(new Date(water.logged_at), "MMM d, h:mm a")}</p>
        <div>
          <label className="label">Amount (ml)</label>
          <input
            type="number"
            min="1"
            step="50"
            className="input"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            autoFocus
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          {[150, 200, 250, 330, 500, 750].map((ml) => (
            <button
              key={ml}
              type="button"
              onClick={() => setAmount(ml)}
              className={`px-2.5 py-1 text-xs rounded-lg border transition ${
                Number(amount) === ml
                  ? "border-brand-500 bg-brand-50 text-brand-700"
                  : "border-slate-200 text-slate-600 hover:border-brand-300"
              }`}
            >
              {ml} ml
            </button>
          ))}
        </div>
        <div className="flex gap-2 pt-1">
          <button onClick={onClose} className="btn-secondary flex-1">Cancel</button>
          <button onClick={() => save.mutate()} disabled={save.isPending} className="btn-primary flex-1">
            {save.isPending ? "Saving…" : "Update"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Meal modal (create + edit) ─────────────────────────────────────────────

function MealModal({ date, meal = null, onClose, onSaved }) {
  const isEditing = !!meal;

  const [mealType, setMealType] = useState(
    meal?.meal_type ?? "breakfast"
  );
  const [time, setTime] = useState(() => {
    if (meal?.consumed_at) return format(new Date(meal.consumed_at), "HH:mm");
    return format(new Date(), "HH:mm");
  });
  const [items, setItems] = useState(() => {
    if (!meal?.items) return [];
    return meal.items.map((it) => ({
      food: it.food_detail,
      servings: parseFloat(it.servings),
    }));
  });
  const [search, setSearch] = useState("");

  const { data } = useQuery({
    queryKey: qk.nutrition.foodSearch(search),
    queryFn: () => foodsApi.list({ search, page_size: 30 }),
    enabled: search.length > 0,
  });
  const foods = data?.results || [];

  const save = useMutation({
    mutationFn: (payload) =>
      isEditing ? mealsApi.update(meal.id, payload) : mealsApi.create(payload),
    onSuccess: () => { toast.success(isEditing ? "Meal updated" : "Meal logged"); onSaved(); },
    onError: () => toast.error("Could not save meal"),
  });

  const addFood = (food) => {
    setItems((prev) => [...prev, { food, servings: 1 }]);
    setSearch("");
  };

  const totals = items.reduce(
    (acc, it) => ({
      calories: acc.calories + parseFloat(it.food.calories) * it.servings,
      protein:  acc.protein  + parseFloat(it.food.protein_g) * it.servings,
    }),
    { calories: 0, protein: 0 }
  );

  const submit = () => {
    if (items.length === 0) { toast.error("Add at least one food"); return; }
    const consumedAt = new Date(`${date}T${time}:00`).toISOString();
    save.mutate({
      meal_type:   mealType,
      consumed_at: consumedAt,
      items:       items.map((it) => ({ food: it.food.id, servings: Number(it.servings) })),
    });
  };

  return (
    <div className="fixed inset-0 z-40 bg-black/60 flex items-center justify-center p-4">
      <div className="bg-surface rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="border-b border-slate-200 px-5 py-4 flex items-center justify-between">
          <h3 className="font-semibold">{isEditing ? "Edit meal" : "Log a meal"}</h3>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-900 text-lg leading-none">✕</button>
        </div>

        <div className="p-5 space-y-4 overflow-y-auto">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Meal</label>
              <select className="input" value={mealType} onChange={(e) => setMealType(e.target.value)}>
                {MEAL_TYPES.map((m) => (
                  <option key={m.value} value={m.value}>{m.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Time</label>
              <input type="time" className="input" value={time} onChange={(e) => setTime(e.target.value)} />
            </div>
          </div>

          {/* Food search */}
          <div>
            <label className="label">Search foods</label>
            <input
              className="input"
              placeholder="Chicken, banana, oats…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            {search && foods.length > 0 && (
              <div className="mt-2 border border-slate-200 rounded-lg max-h-48 overflow-y-auto">
                {foods.map((f) => (
                  <button
                    key={f.id}
                    onClick={() => addFood(f)}
                    className="w-full text-left px-3 py-2 hover:bg-slate-50 text-sm flex items-center justify-between gap-2"
                  >
                    <div className="min-w-0">
                      <span className="font-medium text-slate-900">{f.name}</span>
                      <span className="ml-2 text-xs text-slate-400">per {f.serving_size} {f.serving_unit}</span>
                    </div>
                    <span className="text-slate-500 shrink-0 text-xs">{f.calories} kcal</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Items list */}
          {items.length > 0 && (
            <div>
              <p className="text-sm font-medium text-slate-700 mb-2">Items</p>
              <div className="space-y-2">
                {items.map((it, idx) => {
                  const ss = parseFloat(it.food.serving_size) || 0;
                  const unit = it.food.serving_unit || "g";
                  const totalGrams = Math.round(ss * parseFloat(it.servings || 0));

                  return (
                    <div key={idx} className="rounded-xl border border-slate-200 p-3 space-y-2">
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-slate-900 truncate">{it.food.name}</p>
                          <p className="text-xs text-slate-400 mt-0.5">
                            {it.food.calories} kcal · {it.food.protein_g}g protein per {it.food.serving_size} {unit}
                          </p>
                        </div>
                        <button
                          onClick={() => setItems(items.filter((_, i) => i !== idx))}
                          className="text-slate-400 hover:text-rose-500 shrink-0 p-0.5"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="flex items-center gap-2">
                          <input
                            type="number"
                            step="0.25"
                            min="0.25"
                            className="input w-20 py-1.5 text-center"
                            value={it.servings}
                            onChange={(e) => {
                              const copy = [...items];
                              copy[idx].servings = e.target.value;
                              setItems(copy);
                            }}
                          />
                          <span className="text-sm text-slate-500 whitespace-nowrap">
                            serving{parseFloat(it.servings) !== 1 ? "s" : ""}
                          </span>
                        </div>
                        {ss > 0 && (
                          <span className="text-xs text-slate-400 bg-slate-50 dark:bg-slate-100/5 border border-slate-200 rounded-lg px-2 py-1 whitespace-nowrap">
                            = {totalGrams} {unit}
                          </span>
                        )}
                        <span className="ml-auto text-sm font-semibold text-slate-700">
                          {Math.round(parseFloat(it.food.calories) * parseFloat(it.servings || 0))} kcal
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
              <p className="mt-3 text-sm text-slate-500">
                Total: <span className="font-medium">{Math.round(totals.calories)} kcal</span> · <span className="font-medium">{Math.round(totals.protein)}g</span> protein
              </p>
            </div>
          )}
        </div>

        <div className="border-t border-slate-200 px-5 py-4 flex justify-end gap-2 shrink-0">
          <button onClick={onClose} className="btn-secondary">Cancel</button>
          <button onClick={submit} className="btn-primary" disabled={save.isPending}>
            {save.isPending ? "Saving…" : isEditing ? "Update meal" : "Save meal"}
          </button>
        </div>
      </div>
    </div>
  );
}
