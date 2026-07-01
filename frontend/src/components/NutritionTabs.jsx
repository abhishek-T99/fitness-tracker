import { useLocation, useNavigate } from "react-router-dom";
import { Apple, BarChart3 } from "lucide-react";

// Matches the segmented tab style used on the Progress page. The two views
// live at separate routes (/nutrition and /nutrition/insights) so each stays
// bookmarkable — the tab bar just picks its active state from the location.
const TABS = [
  { to: "/nutrition",          label: "Overview", icon: Apple },
  { to: "/nutrition/insights", label: "Insights", icon: BarChart3 },
];

export default function NutritionTabs() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  // Palette note: this theme inverts the slate scale in dark mode (see
  // index.css). Use `bg-slate-100` (semantic "subtle fill" in both themes)
  // for the container and `bg-surface` (the card-surface token) for the
  // active pill — no `dark:` overrides, or you'll invert the colors twice.
  return (
    <div className="flex gap-1 p-1 bg-slate-100 rounded-xl mb-6 border border-slate-200">
      {TABS.map(({ to, label, icon: Icon }) => {
        const active = pathname === to;
        return (
          <button
            key={to}
            onClick={() => navigate(to)}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all
              ${active
                ? "bg-surface text-brand-600 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
              }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        );
      })}
    </div>
  );
}
