import { useEffect, useRef, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
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
  Settings,
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
];

function UserAvatar({ user, size = "md" }) {
  const sizeClass = size === "sm" ? "h-8 w-8 text-sm" : "h-10 w-10 text-base";
  if (user?.avatar) {
    return (
      <img
        src={user.avatar}
        alt={user.first_name || user.username}
        className={clsx("rounded-full object-cover ring-2 ring-white", sizeClass)}
      />
    );
  }
  return (
    <div
      className={clsx(
        "rounded-full bg-brand-600 text-white flex items-center justify-center font-semibold ring-2 ring-white",
        sizeClass
      )}
    >
      {(user?.first_name?.[0] || user?.username?.[0] || "?").toUpperCase()}
    </div>
  );
}

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function handleEditProfile() {
    setDropdownOpen(false);
    navigate("/profile");
  }

  function handleLogout() {
    setDropdownOpen(false);
    logout();
  }

  return (
    <div className="min-h-screen flex bg-slate-50">
      {/* Sidebar */}
      <aside
        className={clsx(
          "fixed inset-y-0 left-0 z-30 w-64 transform bg-slate-900 text-slate-100 transition-transform lg:static lg:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-16 items-center justify-between px-6 border-b border-slate-800">
          <span className="text-xl font-bold text-white">
            Fit<span className="text-brand-400">Track</span>
          </span>
          <button
            className="lg:hidden text-slate-300"
            onClick={() => setSidebarOpen(false)}
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
              onClick={() => setSidebarOpen(false)}
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
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-200 bg-white px-4 lg:px-8">
          <button
            className="lg:hidden text-slate-700"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open menu"
          >
            <Menu className="w-6 h-6" />
          </button>

          {/* Profile dropdown */}
          <div className="ml-auto" ref={dropdownRef}>
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
              <div className="absolute right-4 lg:right-8 mt-2 w-52 rounded-xl border border-slate-200 bg-white shadow-lg py-1 z-50">
                {/* User info header */}
                <div className="px-4 py-3 border-b border-slate-100">
                  <p className="text-sm font-semibold text-slate-900 truncate">
                    {user?.first_name
                      ? `${user.first_name} ${user.last_name || ""}`.trim()
                      : user?.username}
                  </p>
                  <p className="text-xs text-slate-500 truncate">{user?.email}</p>
                </div>

                <button
                  onClick={handleEditProfile}
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
                  className="flex w-full items-center gap-3 px-4 py-2.5 text-sm text-rose-600 hover:bg-rose-50 transition"
                >
                  <LogOut className="w-4 h-4" />
                  Log Out
                </button>
              </div>
            )}
          </div>
        </header>

        <main className="flex-1 p-4 lg:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
