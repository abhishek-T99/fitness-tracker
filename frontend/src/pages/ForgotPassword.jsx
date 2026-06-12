import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { Dumbbell } from "lucide-react";
import toast from "react-hot-toast";

import { authApi } from "../api/endpoints.js";

export default function ForgotPassword() {
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const { register, handleSubmit, formState: { errors } } = useForm();

  const onSubmit = async ({ email }) => {
    setSubmitting(true);
    try {
      await authApi.forgotPassword(email);
      navigate(`/check-email?type=reset&email=${encodeURIComponent(email)}`);
    } catch {
      toast.error("Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-ink-900 via-ink-800 to-brand-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-500 text-white mb-3">
            <Dumbbell className="w-7 h-7" />
          </div>
          <h1 className="text-3xl font-bold text-white">Forgot password?</h1>
          <p className="text-ink-300 mt-1">
            Enter your email and we'll send a reset link.
          </p>
        </div>

        <form
          onSubmit={handleSubmit(onSubmit)}
          className="bg-surface rounded-2xl shadow-xl p-8 space-y-4"
        >
          <div>
            <label className="label">Email address</label>
            <input
              type="email"
              autoComplete="email"
              className="input"
              {...register("email", { required: "Email is required" })}
            />
            {errors.email && (
              <p className="text-rose-600 text-xs mt-1">{errors.email.message}</p>
            )}
          </div>

          <button type="submit" disabled={submitting} className="btn-primary w-full">
            {submitting ? "Sending…" : "Send reset link"}
          </button>

          <p className="text-center text-sm text-slate-500">
            Remember your password?{" "}
            <Link to="/login" className="text-brand-600 font-semibold hover:underline">
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
