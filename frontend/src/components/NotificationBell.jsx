import { useEffect, useRef, useState } from "react";
import {
  Bell,
  CheckCheck,
  Loader2,
  Heart,
  MessageCircle,
  UserPlus,
  Users,
  Trophy,
  Flame,
  Target,
  Clock,
  BarChart2,
} from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { formatDistanceToNow, isToday, isYesterday, format } from "date-fns";
import clsx from "clsx";

import { notificationsApi } from "../api/endpoints.js";

// Icon + colour per notification type
const TYPE_META = {
  like:            { Icon: Heart,         bg: "bg-rose-500" },
  comment:         { Icon: MessageCircle, bg: "bg-blue-500" },
  friend_request:  { Icon: UserPlus,      bg: "bg-violet-500" },
  friend_accepted: { Icon: Users,         bg: "bg-emerald-500" },
  achievement:     { Icon: Trophy,        bg: "bg-amber-500" },
  streak_at_risk:  { Icon: Flame,         bg: "bg-orange-500" },
  goal_milestone:  { Icon: Target,        bg: "bg-green-500" },
  goal_deadline:   { Icon: Clock,         bg: "bg-red-500" },
  reminder:        { Icon: Bell,          bg: "bg-sky-500" },
  weekly_summary:  { Icon: BarChart2,     bg: "bg-indigo-500" },
};

function NotifIcon({ type }) {
  const meta = TYPE_META[type] ?? { Icon: Bell, bg: "bg-slate-500" };
  return (
    <span
      className={clsx(
        "flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-white",
        meta.bg
      )}
    >
      <meta.Icon className="w-4.5 h-4.5 w-[18px] h-[18px]" strokeWidth={2} />
    </span>
  );
}

function groupByDay(notifications) {
  const groups = {};
  for (const n of notifications) {
    const d = new Date(n.created_at);
    let label;
    if (isToday(d)) label = "Today";
    else if (isYesterday(d)) label = "Yesterday";
    else label = format(d, "MMMM d, yyyy");
    (groups[label] ??= []).push(n);
  }
  return Object.entries(groups);
}

export default function NotificationBell() {
  const [open, setOpen]   = useState(false);
  const [tab, setTab]     = useState("all");   // "all" | "unread"
  const ref               = useRef(null);
  const qc                = useQueryClient();

  // Poll unread count every 60 s
  const { data: countData } = useQuery({
    queryKey: ["notifications", "unread_count"],
    queryFn:  notificationsApi.unreadCount,
    refetchInterval: 60_000,
  });
  const unread = countData?.count ?? 0;

  // Fetch list only when open
  const { data: listData, isLoading } = useQuery({
    queryKey: ["notifications", "list"],
    queryFn:  () => notificationsApi.list({ page_size: 30 }),
    enabled:  open,
  });
  const all       = listData?.results ?? [];
  const displayed = tab === "unread" ? all.filter((n) => !n.read) : all;
  const groups    = groupByDay(displayed);

  const markRead = useMutation({
    mutationFn: (id) => notificationsApi.markRead(id),
    onSuccess:  () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const markAll = useMutation({
    mutationFn: notificationsApi.markAllRead,
    onSuccess:  () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });

  // Close on outside click
  useEffect(() => {
    function handler(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  function handleItem(notif) {
    if (!notif.read) markRead.mutate(notif.id);
    setOpen(false);
  }

  return (
    <div className="relative" ref={ref}>
      {/* Bell trigger */}
      <button
        onClick={() => setOpen((v) => !v)}
        aria-label="Notifications"
        className="relative flex items-center justify-center h-9 w-9 rounded-full text-slate-500 hover:bg-slate-100 hover:text-slate-700 transition"
      >
        <Bell className="w-5 h-5" />
        {unread > 0 && (
          <span className="absolute -top-0.5 -right-0.5 flex h-4 min-w-[1rem] items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-bold text-white leading-none">
            {unread > 99 ? "99+" : unread}
          </span>
        )}
      </button>

      {/* Dropdown panel */}
      {open && (
        <div className="absolute right-0 mt-2 w-[400px] rounded-2xl border border-slate-200 bg-surface shadow-2xl z-50 flex flex-col overflow-hidden max-h-[560px]">

          {/* Header */}
          <div className="flex items-center px-5 pt-4 pb-2 shrink-0">
            <h3 className="text-base font-bold text-slate-900">Notifications</h3>
          </div>

          {/* Tabs */}
          <div className="flex items-center justify-between px-5 border-b border-slate-100 shrink-0">
            <div className="flex gap-6">
              {["all", "unread"].map((t) => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className={clsx(
                    "pb-2.5 text-sm font-semibold tracking-wide transition border-b-2",
                    tab === t
                      ? "border-slate-900 text-slate-900"
                      : "border-transparent text-slate-400 hover:text-slate-600"
                  )}
                >
                  {t.toUpperCase()}
                </button>
              ))}
            </div>
            {unread > 0 && (
              <button
                onClick={() => { markAll.mutate(); }}
                className="flex items-center gap-1 pb-2.5 text-xs font-semibold text-emerald-600 hover:text-emerald-700 transition"
              >
                <CheckCheck className="w-3.5 h-3.5" />
                Mark all read
              </button>
            )}
          </div>

          {/* Notification list */}
          <div className="overflow-y-auto flex-1">
            {isLoading && (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
              </div>
            )}

            {!isLoading && displayed.length === 0 && (
              <div className="flex flex-col items-center justify-center py-14 text-slate-400">
                <Bell className="w-9 h-9 mb-3 opacity-30" />
                <p className="text-sm font-medium">
                  {tab === "unread" ? "No unread notifications" : "You're all caught up!"}
                </p>
              </div>
            )}

            {groups.map(([dayLabel, items]) => (
              <div key={dayLabel}>
                {/* Day separator */}
                <p className="px-5 pt-4 pb-1 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  {dayLabel}
                </p>

                {items.map((notif) => (
                  <button
                    key={notif.id}
                    onClick={() => handleItem(notif)}
                    className={clsx(
                      "w-full text-left flex items-start gap-3.5 px-5 py-3.5 transition hover:bg-slate-50",
                      !notif.read && "bg-slate-50/70"
                    )}
                  >
                    {/* Coloured icon */}
                    <NotifIcon type={notif.notif_type} />

                    {/* Text */}
                    <div className="flex-1 min-w-0">
                      <p className={clsx(
                        "text-sm leading-snug",
                        !notif.read ? "font-semibold text-slate-900" : "font-medium text-slate-700"
                      )}>
                        {notif.message}
                      </p>
                      {notif.actor_username && (
                        <p className="text-xs text-slate-400 mt-0.5 truncate">
                          @{notif.actor_username}
                        </p>
                      )}
                    </div>

                    {/* Time + unread dot */}
                    <div className="flex flex-col items-end gap-1.5 shrink-0 ml-1">
                      <span className="text-xs text-slate-400 whitespace-nowrap">
                        {formatDistanceToNow(new Date(notif.created_at), { addSuffix: false })
                          .replace("about ", "")
                          .replace(" minutes", "m")
                          .replace(" minute", "m")
                          .replace(" hours", "h")
                          .replace(" hour", "h")
                          .replace(" days", "d")
                          .replace(" day", "d")} ago
                      </span>
                      {!notif.read && (
                        <span className="h-2 w-2 rounded-full bg-emerald-500" />
                      )}
                    </div>
                  </button>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
