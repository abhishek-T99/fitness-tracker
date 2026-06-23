import { useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Camera, FileText, Loader2, Mail, Zap, Star } from "lucide-react";
import toast from "react-hot-toast";

import PageHeader from "../components/PageHeader.jsx";
import ConnectedApps from "../components/ConnectedApps.jsx";
import LevelBadge from "../components/LevelBadge.jsx";
import { authApi, levelsApi, reportsApi } from "../api/endpoints.js";
import { qk } from "../api/queryKeys.js";
import { useAuth } from "../contexts/AuthContext.jsx";
import { useLevelContext } from "../contexts/LevelContext.jsx";

const ACTIVITY = [
  { value: "sedentary", label: "Sedentary" },
  { value: "light", label: "Lightly active" },
  { value: "moderate", label: "Moderately active" },
  { value: "active", label: "Very active" },
  { value: "athlete", label: "Athlete" },
];

const GENDERS = [
  { value: "unspecified", label: "Prefer not to say" },
  { value: "male", label: "Male" },
  { value: "female", label: "Female" },
  { value: "other", label: "Other" },
];

function AvatarUpload({ user, onUploaded }) {
  const fileRef = useRef(null);
  const [preview, setPreview] = useState(null);

  const upload = useMutation({
    mutationFn: (file) => authApi.uploadAvatar(file),
    onSuccess: async () => {
      toast.success("Profile picture updated");
      await onUploaded();
    },
    onError: () => toast.error("Could not upload picture"),
  });

  function handleFileChange(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setPreview(URL.createObjectURL(file));
    upload.mutate(file);
  }

  const avatarSrc = preview || user?.avatar || null;
  const initials = (user?.first_name?.[0] || user?.username?.[0] || "?").toUpperCase();

  return (
    <div className="card">
      <div className="card-header"><h3 className="font-semibold">Profile picture</h3></div>
      <div className="card-body flex items-center gap-6">
        <div className="relative group shrink-0">
          {avatarSrc ? (
            <img
              src={avatarSrc}
              alt="Avatar"
              className="h-20 w-20 rounded-full object-cover ring-4 ring-slate-100"
            />
          ) : (
            <div className="h-20 w-20 rounded-full bg-brand-600 text-white flex items-center justify-center text-2xl font-semibold ring-4 ring-slate-100">
              {initials}
            </div>
          )}
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            disabled={upload.isPending}
            className="absolute inset-0 rounded-full bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition cursor-pointer disabled:cursor-not-allowed"
            aria-label="Change profile picture"
          >
            <Camera className="w-6 h-6 text-white" />
          </button>
        </div>
        <div>
          <p className="text-sm font-medium text-slate-800">
            {user?.first_name
              ? `${user.first_name} ${user.last_name || ""}`.trim()
              : user?.username}
          </p>
          <p className="text-xs text-slate-500 mb-3">{user?.email}</p>
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            disabled={upload.isPending}
            className="btn-secondary text-sm"
          >
            {upload.isPending ? "Uploading…" : "Change picture"}
          </button>
          <p className="text-xs text-slate-400 mt-1.5">JPG, PNG or GIF · max 5 MB</p>
        </div>
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={handleFileChange}
        />
      </div>
    </div>
  );
}

export default function Profile() {
  const { user, refreshUser } = useAuth();
  const { register, handleSubmit, reset, setValue } = useForm();

  useEffect(() => {
    if (user) {
      reset({
        first_name: user.first_name || "",
        last_name: user.last_name || "",
        email: user.email || "",
        profile: {
          bio: user.profile?.bio || "",
          date_of_birth: user.profile?.date_of_birth || "",
          gender: user.profile?.gender || "unspecified",
          height_cm: user.profile?.height_cm || "",
          activity_level: user.profile?.activity_level || "moderate",
          units: user.profile?.units || "metric",
          daily_calorie_goal: user.profile?.daily_calorie_goal || "",
          weekly_workout_goal: user.profile?.weekly_workout_goal || 3,
          timezone: user.profile?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
        },
      });
    }
  }, [user, reset]);

  const save = useMutation({
    mutationFn: (data) => authApi.updateMe(data),
    onSuccess: async () => {
      toast.success("Profile updated");
      await refreshUser();
    },
    onError: () => toast.error("Could not update profile"),
  });

  const onSubmit = (data) => {
    const cleanProfile = Object.fromEntries(
      Object.entries(data.profile || {}).filter(([, v]) => v !== "")
    );
    save.mutate({ ...data, profile: cleanProfile });
  };

  return (
    <div>
      <PageHeader title="Profile & settings" subtitle="Manage your account" />

      <div className="space-y-6 max-w-3xl">
        <LevelCard />
        <AvatarUpload user={user} onUploaded={refreshUser} />

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <div className="card">
            <div className="card-header"><h3 className="font-semibold">Account</h3></div>
            <div className="card-body grid grid-cols-2 gap-3">
              <div>
                <label className="label">First name</label>
                <input className="input" {...register("first_name")} />
              </div>
              <div>
                <label className="label">Last name</label>
                <input className="input" {...register("last_name")} />
              </div>
              <div className="col-span-2">
                <label className="label">Email</label>
                <input type="email" className="input" {...register("email")} />
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header"><h3 className="font-semibold">Body</h3></div>
            <div className="card-body grid grid-cols-2 gap-3">
              <div>
                <label className="label">Date of birth</label>
                <input type="date" className="input" {...register("profile.date_of_birth")} />
              </div>
              <div>
                <label className="label">Gender</label>
                <select className="input" {...register("profile.gender")}>
                  {GENDERS.map((g) => (
                    <option key={g.value} value={g.value}>{g.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Height (cm)</label>
                <input type="number" step="0.1" className="input" {...register("profile.height_cm")} />
              </div>
              <div>
                <label className="label">Activity level</label>
                <select className="input" {...register("profile.activity_level")}>
                  {ACTIVITY.map((a) => (
                    <option key={a.value} value={a.value}>{a.label}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header"><h3 className="font-semibold">Preferences</h3></div>
            <div className="card-body grid grid-cols-2 gap-3">
              <div>
                <label className="label">Units</label>
                <select className="input" {...register("profile.units")}>
                  <option value="metric">Metric (kg, cm)</option>
                  <option value="imperial">Imperial (lb, in)</option>
                </select>
              </div>
              <div>
                <label className="label">Timezone</label>
                <div className="flex gap-2">
                  <input
                    className="input flex-1"
                    placeholder="e.g. Asia/Kathmandu"
                    {...register("profile.timezone")}
                  />
                  <button
                    type="button"
                    className="btn btn-secondary text-xs px-3 shrink-0"
                    onClick={() =>
                      setValue(
                        "profile.timezone",
                        Intl.DateTimeFormat().resolvedOptions().timeZone,
                      )
                    }
                  >
                    Detect
                  </button>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Used to fire reminders at the correct local time.
                </p>
              </div>
              <div>
                <label className="label">Daily calorie goal</label>
                <input type="number" className="input" {...register("profile.daily_calorie_goal")} />
              </div>
              <div>
                <label className="label">Weekly workout goal</label>
                <input type="number" className="input" {...register("profile.weekly_workout_goal")} />
              </div>
              <div className="col-span-2">
                <label className="label">Bio</label>
                <textarea rows={3} className="input" {...register("profile.bio")} />
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <button type="submit" className="btn-primary" disabled={save.isPending}>
              {save.isPending ? "Saving…" : "Save changes"}
            </button>
          </div>
        </form>

        <FitnessReports user={user} onSaved={refreshUser} />

        <ChangePassword />

        <ConnectedApps />
      </div>
    </div>
  );
}

function LevelCard() {
  const ctx = useLevelContext();
  const profile = ctx?.profile;
  const queryClient = useQueryClient();

  const prestige = useMutation({
    mutationFn: levelsApi.prestige,
    onSuccess: () => {
      toast.success("Prestige unlocked! You're back to Level 1.");
      queryClient.invalidateQueries({ queryKey: qk.levels.profile() });
      ctx?.refetch?.();
    },
    onError: (err) => toast.error(err?.response?.data?.detail || "Prestige failed"),
  });

  if (!profile) return null;

  const pct = Math.min(profile.xp_progress_pct ?? 0, 100);

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="font-semibold flex items-center gap-2">
          <Zap className="w-4 h-4 text-brand-500" /> Level & XP
        </h3>
      </div>
      <div className="card-body">
        <div className="flex items-center gap-5 mb-5">
          <div className="h-16 w-16 rounded-full bg-brand-500/15 ring-4 ring-brand-500/30 flex items-center justify-center shrink-0">
            <span className="text-2xl font-extrabold text-brand-600">{profile.level}</span>
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <LevelBadge tier={profile.tier} level={null} size="lg" />
              <span className="text-sm text-slate-600">{profile.athlete_class_display}</span>
            </div>
            <p className="text-sm text-slate-500">
              {(profile.total_xp ?? 0).toLocaleString()} total XP
            </p>
            {profile.prestige_count > 0 && (
              <p className="text-sm text-yellow-500 font-semibold">
                ✦ Prestige {profile.prestige_count}/5
              </p>
            )}
          </div>
        </div>

        <div className="space-y-1 mb-5">
          <div className="flex justify-between text-xs text-slate-500">
            <span>Level {profile.level}</span>
            <span>Level {profile.level + 1}</span>
          </div>
          <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-brand-500 to-brand-400 rounded-full transition-all duration-700"
              style={{ width: `${pct}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-slate-400">
            <span>{(profile.xp_in_current_level ?? 0).toLocaleString()} XP</span>
            <span>{pct.toFixed(1)}% • {(profile.xp_for_next_level ?? 0).toLocaleString()} to next</span>
          </div>
        </div>

        {profile.level >= 100 && profile.prestige_count < 5 && (
          <button
            className="btn-primary flex items-center gap-2"
            onClick={() => prestige.mutate()}
            disabled={prestige.isPending}
          >
            <Star className="w-4 h-4" />
            {prestige.isPending ? "Prestiging…" : "Prestige Now"}
          </button>
        )}
      </div>
    </div>
  );
}

const FREQ_LABELS = {
  weekly:  "Every Monday — covers the previous week",
  monthly: "1st of each month — covers the previous month",
  yearly:  "January 1st — covers the previous year",
};

function FitnessReports({ user, onSaved }) {
  const { register, handleSubmit, watch, reset } = useForm();
  const queryClient = useQueryClient();

  const enabled    = watch("profile.reports_enabled");
  const frequency  = watch("profile.report_frequency");

  useEffect(() => {
    if (user) {
      reset({
        profile: {
          reports_enabled:  user.profile?.reports_enabled  ?? false,
          report_frequency: user.profile?.report_frequency ?? "weekly",
        },
      });
    }
  }, [user, reset]);

  const save = useMutation({
    mutationFn: (data) => authApi.updateMe(data),
    onSuccess: async () => {
      toast.success("Report preferences saved");
      await onSaved();
    },
    onError: () => toast.error("Could not save report preferences"),
  });

  const trigger = useMutation({
    mutationFn: (period_type) => reportsApi.trigger(period_type),
    onSuccess: (_, period_type) => {
      toast.success(`${period_type.charAt(0).toUpperCase() + period_type.slice(1)} report is being generated — check your email shortly.`);
      queryClient.invalidateQueries({ queryKey: qk.reports.all() });
    },
    onError: (err) =>
      toast.error(err?.response?.data?.detail || "Could not trigger report"),
  });

  const { data: reports = [], isLoading: reportsLoading } = useQuery({
    queryKey: qk.reports.all(),
    queryFn:  reportsApi.list,
  });

  const lastSent = user?.profile?.last_report_sent_at
    ? new Date(user.profile.last_report_sent_at).toLocaleDateString(undefined, {
        year: "numeric", month: "short", day: "numeric",
      })
    : null;

  return (
    <div className="card" data-testid="fitness-reports-card">
      <div className="card-header">
        <h3 className="font-semibold flex items-center gap-2">
          <FileText className="w-4 h-4 text-brand-500" /> Fitness Reports
        </h3>
      </div>
      <form onSubmit={handleSubmit((d) => save.mutate(d))} className="card-body space-y-4">
        {/* Enable toggle */}
        <label className="flex items-center gap-3 cursor-pointer select-none" data-testid="reports-toggle-label">
          <div className="relative">
            <input
              type="checkbox"
              className="sr-only"
              data-testid="reports-enabled-toggle"
              {...register("profile.reports_enabled")}
            />
            <div className={`w-10 h-6 rounded-full transition-colors ${enabled ? "bg-brand-500" : "bg-slate-200"}`} />
            <div className={`absolute top-1 left-1 w-4 h-4 rounded-full bg-white shadow transition-transform ${enabled ? "translate-x-4" : ""}`} />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-800">Enable fitness reports</p>
            <p className="text-xs text-slate-500">Receive a PDF report of your activity by email</p>
          </div>
        </label>

        {/* Frequency selector — only shown when enabled */}
        {enabled && (
          <div>
            <label className="label">Report frequency</label>
            <select
              className="input"
              data-testid="report-frequency-select"
              {...register("profile.report_frequency")}
            >
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
              <option value="yearly">Yearly</option>
            </select>
            {frequency && (
              <p className="text-xs text-slate-400 mt-1">{FREQ_LABELS[frequency]}</p>
            )}
          </div>
        )}

        {lastSent && (
          <p className="text-xs text-slate-500 flex items-center gap-1.5">
            <Mail className="w-3.5 h-3.5" />
            Last report sent: <span className="font-medium">{lastSent}</span>
          </p>
        )}

        <div className="flex items-center justify-between gap-3 pt-1">
          <button type="submit" className="btn-primary" disabled={save.isPending}>
            {save.isPending ? "Saving…" : "Save preferences"}
          </button>

          <div className="flex gap-2">
            {["weekly", "monthly", "yearly"].map((pt) => (
              <button
                key={pt}
                type="button"
                data-testid={`trigger-report-${pt}`}
                className="btn-secondary text-xs"
                disabled={trigger.isPending}
                onClick={() => trigger.mutate(pt)}
                title={`Send a ${pt} report now`}
              >
                {trigger.isPending ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  `Send ${pt}`
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Report history */}
        {reports.length > 0 && (
          <div className="mt-4">
            <p className="text-xs font-semibold text-slate-600 mb-2">Report history</p>
            <div className="divide-y divide-slate-100 border border-slate-100 rounded-lg overflow-hidden" data-testid="report-history">
              {reports.slice(0, 5).map((r) => (
                <div key={r.id} className="flex items-center justify-between px-3 py-2 text-xs bg-white hover:bg-slate-50">
                  <span className="capitalize font-medium text-slate-700">{r.period_type}</span>
                  <span className="text-slate-500">
                    {new Date(r.period_start).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
                    {" – "}
                    {new Date(r.period_end).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}
                  </span>
                  {r.pdf_url ? (
                    <a
                      href={r.pdf_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-brand-600 hover:underline font-medium"
                      data-testid="report-download-link"
                    >
                      Download
                    </a>
                  ) : (
                    <span className="text-slate-400">No file</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {reportsLoading && (
          <div className="flex justify-center py-3">
            <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
          </div>
        )}
      </form>
    </div>
  );
}

function ChangePassword() {
  const { register, handleSubmit, reset, formState: { errors } } = useForm();
  const save = useMutation({
    mutationFn: (data) => authApi.changePassword(data),
    onSuccess: () => {
      toast.success("Password updated");
      reset();
    },
    onError: (err) => {
      const data = err?.response?.data;
      toast.error(data?.old_password || data?.new_password || "Could not change password");
    },
  });

  return (
    <form onSubmit={handleSubmit((d) => save.mutate(d))} className="card">
      <div className="card-header"><h3 className="font-semibold">Change password</h3></div>
      <div className="card-body grid grid-cols-2 gap-3">
        <div className="col-span-2">
          <label className="label">Current password</label>
          <input
            type="password"
            className="input"
            {...register("old_password", { required: true })}
          />
          {errors.old_password && <p className="text-xs text-rose-500 mt-1">Required</p>}
        </div>
        <div className="col-span-2">
          <label className="label">New password</label>
          <input
            type="password"
            className="input"
            {...register("new_password", { required: true, minLength: 8 })}
          />
          {errors.new_password && <p className="text-xs text-rose-500 mt-1">At least 8 chars</p>}
        </div>
        <div className="col-span-2 flex justify-end">
          <button type="submit" className="btn-secondary" disabled={save.isPending}>
            {save.isPending ? "Updating…" : "Update password"}
          </button>
        </div>
      </div>
    </form>
  );
}
