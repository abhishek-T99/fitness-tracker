import clsx from "clsx";

export default function StatCard({ icon: Icon, label, value, hint, accent = "brand" }) {
  const accentColor =
    {
      brand: "bg-brand-50 text-brand-600",
      emerald: "bg-emerald-50 text-emerald-600",
      amber: "bg-amber-50 text-amber-600",
      rose: "bg-rose-50 text-rose-600",
      indigo: "bg-indigo-50 text-indigo-600",
    }[accent] || "bg-brand-50 text-brand-600";

  return (
    <div className="card p-5 flex items-center gap-4">
      {Icon && (
        <div className={clsx("h-12 w-12 rounded-lg flex items-center justify-center", accentColor)}>
          <Icon className="w-6 h-6" />
        </div>
      )}
      <div>
        <p className="text-sm text-slate-500">{label}</p>
        <p className="text-2xl font-bold text-slate-900">{value}</p>
        {hint && <p className="text-xs text-slate-400 mt-0.5">{hint}</p>}
      </div>
    </div>
  );
}
