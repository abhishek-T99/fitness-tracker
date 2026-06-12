import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import { Dumbbell } from "lucide-react";
import toast from "react-hot-toast";

import { authApi } from "../api/endpoints.js";

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") || "";
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const { register, handleSubmit, watch, formState: { errors } } = useForm();
  const password = watch("new_password");

  if (!token) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-brand-900 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 text-center max-w-md w-full space-y-4">
          <h1 className="text-xl font-bold text-slate-900">Invalid link</h1>
          <p className="text-slate-500">This password reset link is missing or malformed.</p>
          <Link to="/forgot-password" className="text-brand-600 font-semibold hover:underline">
            Request a new link
          </Link>
        </div>
      </div>
    );
  }

  const onSubmit = async ({ new_password }) => {
    setSubmitting(true);
    try {
      await authApi.resetPassword(token, new_password);
      toast.success("Password updated! Please sign in.");
      navigate("/login", { replace: true });
    } catch (err) {
      const detail =
        err?.response?.data?.detail ||
        err?.response?.data?.new_password?.[0] ||
        "Failed to reset password.";
      toast.error(detail);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-brand-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-500 text-white mb-3">
            <Dumbbell className="w-7 h-7" />
          </div>
          <h1 className="text-3xl font-bold text-white">Set new password</h1>
          <p className="text-slate-300 mt-1">Choose a strong password for your account.</p>
        </div>

        <form
          onSubmit={handleSubmit(onSubmit)}
          className="bg-white rounded-2xl shadow-xl p-8 space-y-4"
        >
          <div>
            <label className="label">New password</label>
            <input
              type="password"
              autoComplete="new-password"
              className="input"
              {...register("new_password", {
                required: "Required",
                minLength: { value: 8, message: "At least 8 characters" },
              })}
            />
            {errors.new_password && (
              <p className="text-rose-600 text-xs mt-1">{errors.new_password.message}</p>
            )}
          </div>

          <div>
            <label className="label">Confirm new password</label>
            <input
              type="password"
              autoComplete="new-password"
              className="input"
              {...register("confirm_password", {
                required: "Please confirm your password",
                validate: (v) => v === password || "Passwords do not match",
              })}
            />
            {errors.confirm_password && (
              <p className="text-rose-600 text-xs mt-1">{errors.confirm_password.message}</p>
            )}
          </div>

          <button type="submit" disabled={submitting} className="btn-primary w-full">
            {submitting ? "Updating…" : "Update password"}
          </button>

          <p className="text-center text-sm text-slate-500">
            <Link to="/login" className="text-brand-600 font-semibold hover:underline">
              Back to sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
