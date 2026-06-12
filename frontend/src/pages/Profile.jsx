import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { useMutation } from "@tanstack/react-query";
import toast from "react-hot-toast";

import PageHeader from "../components/PageHeader.jsx";
import { authApi } from "../api/endpoints.js";
import { useAuth } from "../contexts/AuthContext.jsx";

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

export default function Profile() {
  const { user, refreshUser } = useAuth();
  const { register, handleSubmit, reset } = useForm();

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
          timezone: user.profile?.timezone || "UTC",
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

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 max-w-3xl">
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
              <input className="input" {...register("profile.timezone")} />
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

      <div className="mt-8 max-w-3xl">
        <ChangePassword />
      </div>
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
    <form
      onSubmit={handleSubmit((d) => save.mutate(d))}
      className="card"
    >
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
