import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import {
  LayoutDashboard,
  Dumbbell,
  ListChecks,
  CalendarDays,
  Apple,
  Ruler,
  Target,
  Users,
  Trophy,
  Bell,
  UserCircle2,
  LogOut,
  Menu,
  X,
} from "lucide-react";
import clsx from "clsx";

import { useAuth } from "../contexts/AuthContext.jsx";

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/workouts", label: "Workouts", icon: Dumbbell },
  { to: "/routines", label: "Routines", icon: ListChecks },
  { to: "/exercises", label: "Exercise Library", icon: CalendarDays },
  { to: "/nutrition", label: "Nutrition", icon: Apple },
  { to: "/measurements", label: "Measurements", icon: Ruler },
  { to: "/goals", label: "Goals", icon: Target },
  { to: "/social", label: "Social", icon: Users },
  { to: "/achievements", label: "Achievements", icon: Trophy },
  { to: "/reminders", label: "Reminders", icon: Bell },
  { to: "/profile", label: "Profile", icon: UserCircle2 },
];

export default function AppLayout() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);

  return (
    <div className="min-h-screen flex bg-slate-50">
      {/* Sidebar */}
      <aside
        className={clsx(
          "fixed inset-y-0 left-0 z-30 w-64 transform bg-slate-900 text-slate-100 transition-transform lg:static lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-16 items-center justify-between px-6 border-b border-slate-800">
          <span className="text-xl font-bold text-white">
            Fit<span className="text-brand-400">Track</span>
          </span>
          <button
            className="lg:hidden text-slate-300"
            onClick={() => setOpen(false)}
            aria-label="Close menu"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition",
                  isActive
                    ? "bg-brand-600 text-white"
                    : "text-slate-300 hover:bg-slate-800 hover:text-white"
                )
              }
            >
              <Icon className="w-5 h-5" />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-slate-800 p-4">
          <button
            onClick={logout}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800 hover:text-white"
          >
            <LogOut className="w-5 h-5" /> Sign out
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-200 bg-white px-4 lg:px-8">
          <button
            className="lg:hidden text-slate-700"
            onClick={() => setOpen(true)}
            aria-label="Open menu"
          >
            <Menu className="w-6 h-6" />
          </button>
          <div className="ml-auto flex items-center gap-3">
            <div className="text-right hidden sm:block">
              <p className="text-sm font-semibold text-slate-900">
                {user?.first_name || user?.username}
              </p>
              <p className="text-xs text-slate-500">{user?.email}</p>
            </div>
            <div className="h-9 w-9 rounded-full bg-brand-600 text-white flex items-center justify-center font-semibold">
              {(user?.first_name?.[0] || user?.username?.[0] || "?").toUpperCase()}
            </div>
          </div>
        </header>
        <main className="flex-1 p-4 lg:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
