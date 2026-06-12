import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { Dumbbell } from "lucide-react";
import toast from "react-hot-toast";

import { useAuth } from "../contexts/AuthContext.jsx";
import SocialLoginButtons from "../components/SocialLoginButtons.jsx";

export default function Login() {
  const { login, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [submitting, setSubmitting] = useState(false);
  const { register, handleSubmit, formState: { errors } } = useForm();

  if (user) {
    const dest = location.state?.from?.pathname || "/dashboard";
    return <Navigate to={dest} replace />;
  }

  const onSubmit = async (data) => {
    setSubmitting(true);
    try {
      await login(data);
      toast.success("Welcome back!");
      navigate(location.state?.from?.pathname || "/dashboard", { replace: true });
    } catch (err) {
      const detail =
        err?.response?.data?.detail || "Login failed. Check credentials.";
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
          <h1 className="text-3xl font-bold text-white">FitTrack</h1>
          <p className="text-slate-300 mt-1">Sign in to your account</p>
        </div>
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="bg-white rounded-2xl shadow-xl p-8 space-y-4"
        >
          <div>
            <label className="label">Username</label>
            <input
              autoComplete="username"
              className="input"
              {...register("username", { required: "Username is required" })}
            />
            {errors.username && (
              <p className="text-rose-600 text-xs mt-1">{errors.username.message}</p>
            )}
          </div>
          <div>
            <label className="label">Password</label>
            <input
              type="password"
              autoComplete="current-password"
              className="input"
              {...register("password", { required: "Password is required" })}
            />
            {errors.password && (
              <p className="text-rose-600 text-xs mt-1">{errors.password.message}</p>
            )}
          </div>
          <div className="text-right">
            <Link
              to="/forgot-password"
              className="text-sm text-brand-600 font-semibold hover:underline"
            >
              Forgot password?
            </Link>
          </div>
          <button type="submit" disabled={submitting} className="btn-primary w-full">
            {submitting ? "Signing in…" : "Sign in"}
          </button>

          <SocialLoginButtons />

          <p className="text-center text-sm text-slate-500">
            Don't have an account?{" "}
            <Link to="/register" className="text-brand-600 font-semibold hover:underline">
              Create one
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
