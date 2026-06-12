import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2, Droplets } from "lucide-react";
import { format } from "date-fns";
import toast from "react-hot-toast";

import PageHeader from "../components/PageHeader.jsx";
import { foodsApi, mealsApi, waterApi } from "../api/endpoints.js";

const MEAL_TYPES = [
  { value: "breakfast", label: "Breakfast" },
  { value: "lunch", label: "Lunch" },
  { value: "dinner", label: "Dinner" },
  { value: "snack", label: "Snack" },
];

export default function Nutrition() {
  const queryClient = useQueryClient();
  const today = format(new Date(), "yyyy-MM-dd");
  const [date, setDate] = useState(today);
  const [adding, setAdding] = useState(false);

  const { data: summary } = useQuery({
    queryKey: ["dailyNutrition", date],
    queryFn: () => mealsApi.dailySummary(date),
  });
  const { data: meals } = useQuery({
    queryKey: ["meals", date],
    queryFn: () => mealsApi.list({ date }),
  });

  const removeMeal = useMutation({
    mutationFn: (id) => mealsApi.remove(id),
    onSuccess: () => {
      toast.success("Meal removed");
      queryClient.invalidateQueries({ queryKey: ["meals"] });
      queryClient.invalidateQueries({ queryKey: ["dailyNutrition"] });
    },
  });

  const addWater = useMutation({
    mutationFn: (ml) =>
      waterApi.create({ amount_ml: ml, logged_at: new Date().toISOString() }),
    onSuccess: () => {
      toast.success("Water logged");
      queryClient.invalidateQueries({ queryKey: ["dailyNutrition"] });
    },
  });

  const items = meals?.results || meals || [];

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

      <div className="card p-4 mb-6 flex items-center justify-between">
        <input
          type="date"
          className="input w-auto"
          value={date}
          onChange={(e) => setDate(e.target.value)}
        />
        <div className="flex gap-2">
          {[250, 500, 750].map((ml) => (
            <button
              key={ml}
              onClick={() => addWater.mutate(ml)}
              className="btn-secondary"
            >
              <Droplets className="w-4 h-4" /> +{ml} ml
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
        <MacroCard
          label="Calories"
          value={summary?.totals?.calories ?? 0}
          goal={summary?.calorie_goal}
          unit="kcal"
          color="bg-rose-500"
        />
        <MacroCard label="Protein" value={summary?.totals?.protein_g ?? 0} unit="g" color="bg-emerald-500" />
        <MacroCard label="Carbs" value={summary?.totals?.carbs_g ?? 0} unit="g" color="bg-amber-500" />
        <MacroCard label="Fat" value={summary?.totals?.fat_g ?? 0} unit="g" color="bg-indigo-500" />
        <MacroCard label="Water" value={summary?.water_ml ?? 0} unit="ml" color="bg-brand-500" />
      </div>

      <div className="space-y-4">
        {MEAL_TYPES.map(({ value, label }) => {
          const mealsForType = items.filter((m) => m.meal_type === value);
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
                    <div
                      key={meal.id}
                      className="border border-slate-100 rounded-lg p-3"
                    >
                      <div className="flex justify-between items-center mb-2">
                        <div>
                          <p className="text-xs text-slate-500">
                            {format(new Date(meal.consumed_at), "h:mm a")}
                          </p>
                          <p className="text-sm font-medium">
                            {meal.totals.calories} kcal · {meal.totals.protein_g}g P
                          </p>
                        </div>
                        <button
                          onClick={() => removeMeal.mutate(meal.id)}
                          className="text-slate-400 hover:text-rose-500"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                      <ul className="text-sm text-slate-600 space-y-1">
                        {meal.items.map((it) => (
                          <li key={it.id}>
                            • {it.food_detail.name} ×{it.servings} ({it.calories} kcal)
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>

      {adding && (
        <MealModal
          date={date}
          onClose={() => setAdding(false)}
          onSaved={() => {
            setAdding(false);
            queryClient.invalidateQueries({ queryKey: ["meals"] });
            queryClient.invalidateQueries({ queryKey: ["dailyNutrition"] });
          }}
        />
      )}
    </div>
  );
}

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

function MealModal({ date, onClose, onSaved }) {
  const [mealType, setMealType] = useState("breakfast");
  const [time, setTime] = useState(() => format(new Date(), "HH:mm"));
  const [items, setItems] = useState([]);
  const [search, setSearch] = useState("");

  const { data } = useQuery({
    queryKey: ["foodSearch", search],
    queryFn: () => foodsApi.list({ search, page_size: 30 }),
    enabled: search.length > 0,
  });
  const foods = data?.results || [];

  const save = useMutation({
    mutationFn: (payload) => mealsApi.create(payload),
    onSuccess: () => {
      toast.success("Meal logged");
      onSaved();
    },
    onError: () => toast.error("Could not save meal"),
  });

  const addFood = (food) => {
    setItems([...items, { food, servings: 1 }]);
    setSearch("");
  };

  const totals = items.reduce(
    (acc, it) => ({
      calories: acc.calories + parseFloat(it.food.calories) * it.servings,
      protein: acc.protein + parseFloat(it.food.protein_g) * it.servings,
    }),
    { calories: 0, protein: 0 }
  );

  const submit = () => {
    if (items.length === 0) {
      toast.error("Add at least one food");
      return;
    }
    const consumedAt = new Date(`${date}T${time}:00`).toISOString();
    save.mutate({
      meal_type: mealType,
      consumed_at: consumedAt,
      items: items.map((it) => ({ food: it.food.id, servings: Number(it.servings) })),
    });
  };

  return (
    <div className="fixed inset-0 z-40 bg-black/60 flex items-center justify-center p-4">
      <div className="bg-surface rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="border-b border-slate-200 px-5 py-4 flex items-center justify-between">
          <h3 className="font-semibold">Log a meal</h3>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-900">
            ✕
          </button>
        </div>
        <div className="p-5 space-y-4 overflow-y-auto">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Meal</label>
              <select
                className="input"
                value={mealType}
                onChange={(e) => setMealType(e.target.value)}
              >
                {MEAL_TYPES.map((m) => (
                  <option key={m.value} value={m.value}>{m.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Time</label>
              <input
                type="time"
                className="input"
                value={time}
                onChange={(e) => setTime(e.target.value)}
              />
            </div>
          </div>

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
                    className="w-full text-left p-2 hover:bg-slate-50 text-sm flex justify-between"
                  >
                    <span>{f.name}</span>
                    <span className="text-slate-500">{f.calories} kcal</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {items.length > 0 && (
            <div>
              <p className="text-sm font-medium text-slate-700 mb-2">Items</p>
              <div className="space-y-2">
                {items.map((it, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <span className="flex-1 text-sm">{it.food.name}</span>
                    <input
                      type="number"
                      step="0.25"
                      className="input w-20 py-1"
                      value={it.servings}
                      onChange={(e) => {
                        const copy = [...items];
                        copy[idx].servings = e.target.value;
                        setItems(copy);
                      }}
                    />
                    <span className="text-xs text-slate-500">servings</span>
                    <button
                      onClick={() => setItems(items.filter((_, i) => i !== idx))}
                      className="text-slate-400 hover:text-rose-500"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
              <p className="mt-3 text-sm text-slate-500">
                Total: {Math.round(totals.calories)} kcal · {Math.round(totals.protein)}g protein
              </p>
            </div>
          )}
        </div>
        <div className="border-t border-slate-200 px-5 py-4 flex justify-end gap-2">
          <button onClick={onClose} className="btn-secondary">Cancel</button>
          <button onClick={submit} className="btn-primary" disabled={save.isPending}>
            {save.isPending ? "Saving…" : "Save meal"}
          </button>
        </div>
      </div>
    </div>
  );
}
