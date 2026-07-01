import { useEffect, useRef, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Dumbbell,
  ListChecks,
  CalendarDays,
  Apple,
  UtensilsCrossed,
  BarChart3,
  TrendingUp,
  Ruler,
  Target,
  Users,
  Trophy,
  Bell,
  UserCircle2,
  LogOut,
  Menu,
  X,
  Settings,
  ChevronLeft,
  ChevronRight,
  Sun,
  Moon,
  Medal,
} from "lucide-react";
import clsx from "clsx";

import { useAuth } from "../contexts/AuthContext.jsx";
import { useTheme } from "../contexts/ThemeContext.jsx";
import { useLevelContext } from "../contexts/LevelContext.jsx";
import NotificationBell from "./NotificationBell.jsx";
import LevelBadge from "./LevelBadge.jsx";
import XPBar from "./XPBar.jsx";
import LevelUpModal from "./LevelUpModal.jsx";

const navItems = [
  { to: "/dashboard",    label: "Dashboard",       icon: LayoutDashboard },
  { to: "/workouts",     label: "Workouts",         icon: Dumbbell },
  { to: "/routines",     label: "Routines",         icon: ListChecks },
  { to: "/exercises",    label: "Exercise Library", icon: CalendarDays },
  { to: "/nutrition",           label: "Nutrition",         icon: Apple, end: true },
  { to: "/nutrition/insights",  label: "Nutrition Insights", icon: BarChart3 },
  { to: "/meal-plan",           label: "Meal Plan",         icon: UtensilsCrossed },
  { to: "/progress",    label: "Progress",         icon: TrendingUp },
  { to: "/measurements", label: "Measurements",     icon: Ruler },
  { to: "/goals",        label: "Goals",            icon: Target },
  { to: "/social",       label: "Social",           icon: Users },
  { to: "/achievements", label: "Achievements",     icon: Trophy },
  { to: "/leaderboard",  label: "Leaderboard",      icon: Medal },
  { to: "/reminders",    label: "Reminders",        icon: Bell },
];

function UserAvatar({ user, size = "md" }) {
  const sizeClass = size === "sm" ? "h-8 w-8 text-sm" : "h-10 w-10 text-base";
  if (user?.avatar) {
    return (
      <img
        src={user.avatar}
        alt={user.first_name || user.username}
        className={clsx("rounded-full object-cover ring-2 ring-surface", sizeClass)}
      />
    );
  }
  return (
    <div
      className={clsx(
        "rounded-full bg-brand-600 text-white flex items-center justify-center font-semibold ring-2 ring-surface",
        sizeClass
      )}
    >
      {(user?.first_name?.[0] || user?.username?.[0] || "?").toUpperCase()}
    </div>
  );
}

function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  return (
    <button
      onClick={toggleTheme}
      aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
      className="flex h-9 w-9 items-center justify-center rounded-full text-slate-500 hover:bg-slate-100 hover:text-slate-700 transition-colors"
    >
      {theme === "dark" ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
    </button>
  );
}

function SidebarXP({ collapsed }) {
  const ctx = useLevelContext();
  const profile = ctx?.profile;
  if (!profile) return null;

  // Collapsed desktop: show just the level number as a compact badge
  if (collapsed) {
    return (
      <div className="hidden lg:flex shrink-0 border-t border-ink-800 py-3 justify-center">
        <div
          className="h-8 w-8 rounded-full bg-brand-500/20 ring-1 ring-brand-500/40 flex items-center justify-center"
          title={`Level ${profile.level} ${profile.tier}`}
        >
          <span className="text-xs font-bold text-brand-400">{profile.level}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="shrink-0 border-t border-ink-800 px-3 py-3 space-y-2">
      <div className="flex items-center justify-between">
        <LevelBadge tier={profile.tier} level={profile.level} />
        {profile.prestige_count > 0 && (
          <span className="text-xs text-yellow-400 font-bold">✦{profile.prestige_count}</span>
        )}
      </div>
      <XPBar compact />
    </div>
  );
}

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [sidebarOpen, setSidebarOpen] = useState(false);   // mobile overlay
  const [collapsed, setCollapsed] = useState(              // desktop collapse
    () => localStorage.getItem("sidebar-collapsed") === "true"
  );
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  function toggleCollapsed() {
    setCollapsed((v) => {
      localStorage.setItem("sidebar-collapsed", String(!v));
      return !v;
    });
  }

  useEffect(() => {
    function handleClickOutside(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function handleLogout() {
    setDropdownOpen(false);
    logout();
  }

  return (
    <>
    <LevelUpModal />
    <div className="min-h-screen flex bg-slate-50">

      {/* Mobile overlay backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* ── Sidebar ── */}
      <aside
        className={clsx(
          "fixed inset-y-0 left-0 z-30 flex flex-col bg-ink-900 text-ink-100 overflow-x-hidden",
          "dark:border-r dark:border-white/5",
          "transform transition-[width,transform] duration-300 ease-in-out",
          "lg:sticky lg:top-0 lg:h-screen lg:translate-x-0",
          // mobile: always full width, slides in/out
          sidebarOpen ? "translate-x-0 w-64" : "-translate-x-full w-64",
          // desktop: full or icon-only width
          collapsed ? "lg:w-16" : "lg:w-64"
        )}
      >
        {/* Logo row */}
        <div
          className={clsx(
            "flex h-16 shrink-0 items-center border-b border-ink-800",
            "transition-all duration-300",
            collapsed ? "lg:justify-center px-0" : "justify-between px-4"
          )}
        >
          {/* Logo mark + wordmark */}
          <div className={clsx("flex items-center gap-2.5 overflow-hidden")}>
            <img
              src="/favicon.svg"
              alt="FitTrack"
              className="h-8 w-8 rounded-lg shrink-0"
            />
            <span
              className={clsx(
                "text-xl font-bold text-white tracking-tight whitespace-nowrap",
                "transition-all duration-300 overflow-hidden",
                collapsed ? "lg:w-0 lg:opacity-0" : "w-auto opacity-100"
              )}
            >
              Fit<span className="text-brand-400">Track</span>
            </span>
          </div>

          {/* Mobile close */}
          <button
            className="lg:hidden text-ink-400 hover:text-white ml-auto"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close menu"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Nav items */}
        <nav className="flex-1 overflow-y-auto overflow-x-visible py-4 space-y-0.5 px-2">
          {navItems.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              title={collapsed ? label : undefined}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                clsx(
                  "flex items-center rounded-lg py-2 text-sm font-medium transition-colors duration-150",
                  collapsed ? "lg:justify-center lg:px-0 px-3 gap-3" : "gap-3 px-3",
                  isActive
                    ? "bg-brand-600 text-white"
                    : "text-ink-300 hover:bg-ink-800 hover:text-white"
                )
              }
            >
              <Icon className="w-5 h-5 shrink-0" />
              <span
                className={clsx(
                  "whitespace-nowrap transition-all duration-300 overflow-hidden",
                  collapsed ? "lg:w-0 lg:opacity-0 lg:pointer-events-none" : "w-auto opacity-100"
                )}
              >
                {label}
              </span>
            </NavLink>
          ))}
        </nav>

        {/* XP bar — desktop only */}
        <SidebarXP collapsed={collapsed} />

        {/* Collapse toggle — desktop only */}
        <div className="hidden lg:flex shrink-0 border-t border-ink-800 p-2 justify-end">
          <button
            onClick={toggleCollapsed}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            className="flex items-center justify-center h-8 w-8 rounded-lg text-ink-400 hover:bg-ink-800 hover:text-white transition-colors"
          >
            {collapsed ? (
              <ChevronRight className="w-4 h-4" />
            ) : (
              <ChevronLeft className="w-4 h-4" />
            )}
          </button>
        </div>
      </aside>

      {/* ── Main ── */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-200 bg-surface px-4 lg:px-8">
          {/* Mobile hamburger */}
          <button
            className="lg:hidden text-slate-700"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open menu"
          >
            <Menu className="w-6 h-6" />
          </button>

          {/* Right-side controls: theme + bell + profile */}
          <div className="ml-auto flex items-center gap-2">

          {/* Theme toggle */}
          <ThemeToggle />

          {/* Notification bell */}
          <NotificationBell />

          {/* Profile dropdown */}
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setDropdownOpen((v) => !v)}
              className="flex items-center gap-2.5 rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
              aria-label="Account menu"
            >
              <span className="text-sm font-medium text-slate-700 hidden sm:block">
                {user?.first_name || user?.username}
              </span>
              <UserAvatar user={user} />
            </button>

            {dropdownOpen && (
              <div className="absolute right-0 mt-2 w-52 rounded-xl border border-slate-200 bg-surface shadow-lg dark:shadow-black/40 py-1 z-50">
                <div className="px-4 py-3 border-b border-slate-100">
                  <p className="text-sm font-semibold text-slate-900 truncate">
                    {user?.first_name
                      ? `${user.first_name} ${user.last_name || ""}`.trim()
                      : user?.username}
                  </p>
                  <p className="text-xs text-slate-500 truncate">{user?.email}</p>
                </div>

                <button
                  onClick={() => { setDropdownOpen(false); navigate("/profile"); }}
                  className="flex w-full items-center gap-3 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition"
                >
                  <UserCircle2 className="w-4 h-4 text-slate-500" />
                  Edit Profile
                </button>

                <button
                  onClick={() => { setDropdownOpen(false); navigate("/profile"); }}
                  className="flex w-full items-center gap-3 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition"
                >
                  <Settings className="w-4 h-4 text-slate-500" />
                  Settings
                </button>

                <div className="border-t border-slate-100 mt-1" />

                <button
                  onClick={handleLogout}
                  className="flex w-full items-center gap-3 px-4 py-2.5 text-sm text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-500/10 transition"
                >
                  <LogOut className="w-4 h-4" />
                  Log Out
                </button>
              </div>
            )}
          </div>
          </div>{/* end right-side controls */}
        </header>

        <main className="flex-1 p-4 lg:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
    </>
  );
}
