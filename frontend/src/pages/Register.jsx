import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { Dumbbell } from "lucide-react";
import toast from "react-hot-toast";

import { useAuth } from "../contexts/AuthContext.jsx";

export default function Register() {
  const { register: registerUser, user } = useAuth();
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const { register, handleSubmit, watch, formState: { errors } } = useForm();
  const password = watch("password");

  if (user) return <Navigate to="/dashboard" replace />;

  const onSubmit = async (data) => {
    setSubmitting(true);
    try {
      await registerUser(data);
      navigate(
        `/check-email?type=verify&email=${encodeURIComponent(data.email)}`,
        { replace: true }
      );
    } catch (err) {
      const body = err?.response?.data;
      const msg = body
        ? Object.entries(body)
            .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : v}`)
            .join(" | ")
        : "Registration failed.";
      toast.error(msg);
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
          <h1 className="text-3xl font-bold text-white">Create your account</h1>
          <p className="text-ink-300 mt-1">Start tracking in under a minute</p>
        </div>
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="bg-surface rounded-2xl shadow-xl p-8 space-y-4"
        >
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">First name</label>
              <input className="input" {...register("first_name")} />
            </div>
            <div>
              <label className="label">Last name</label>
              <input className="input" {...register("last_name")} />
            </div>
          </div>
          <div>
            <label className="label">Username</label>
            <input
              className="input"
              {...register("username", { required: "Required", minLength: 3 })}
            />
            {errors.username && (
              <p className="text-rose-600 text-xs mt-1">{errors.username.message}</p>
            )}
          </div>
          <div>
            <label className="label">Email</label>
            <input
              type="email"
              className="input"
              {...register("email", { required: "Required" })}
            />
            {errors.email && (
              <p className="text-rose-600 text-xs mt-1">{errors.email.message}</p>
            )}
          </div>
          <div>
            <label className="label">Password</label>
            <input
              type="password"
              className="input"
              {...register("password", { required: "Required", minLength: 8 })}
            />
            {errors.password && (
              <p className="text-rose-600 text-xs mt-1">
                {errors.password.message || "At least 8 characters"}
              </p>
            )}
          </div>
          <div>
            <label className="label">Confirm password</label>
            <input
              type="password"
              className="input"
              {...register("password_confirm", {
                required: "Confirm your password",
                validate: (v) => v === password || "Passwords do not match",
              })}
            />
            {errors.password_confirm && (
              <p className="text-rose-600 text-xs mt-1">{errors.password_confirm.message}</p>
            )}
          </div>
          <button type="submit" disabled={submitting} className="btn-primary w-full">
            {submitting ? "Creating…" : "Create account"}
          </button>
          <p className="text-center text-sm text-slate-500">
            Already have an account?{" "}
            <Link to="/login" className="text-brand-600 font-semibold hover:underline">
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
