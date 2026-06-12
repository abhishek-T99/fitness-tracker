import { Link, useSearchParams } from "react-router-dom";
import { Dumbbell, Mail } from "lucide-react";
import { useState } from "react";
import toast from "react-hot-toast";

import { authApi } from "../api/endpoints.js";

export default function CheckEmail() {
  const [searchParams] = useSearchParams();
  const type = searchParams.get("type") || "verify";
  const email = searchParams.get("email") || "";
  const [resending, setResending] = useState(false);

  const isReset = type === "reset";

  const handleResend = async () => {
    if (!email) return;
    setResending(true);
    try {
      await authApi.resendVerification(email);
      toast.success("A new verification link is on its way.");
    } catch {
      toast.error("Failed to resend. Please try again.");
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-brand-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-500 text-white mb-3">
            <Dumbbell className="w-7 h-7" />
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-8 text-center space-y-4">
          <div className="inline-flex h-16 w-16 items-center justify-center rounded-full bg-brand-50 mx-auto">
            <Mail className="w-8 h-8 text-brand-500" />
          </div>

          <h1 className="text-2xl font-bold text-slate-900">
            {isReset ? "Check your email" : "Verify your email"}
          </h1>

          <p className="text-slate-500 leading-relaxed">
            {isReset ? (
              <>
                If <strong>{email || "that address"}</strong> is registered, we've sent a
                password-reset link. Check your inbox (and spam folder).
              </>
            ) : (
              <>
                We've sent a verification link to{" "}
                <strong>{email || "your email"}</strong>. Click it to activate your
                account — the link expires in 24 hours.
              </>
            )}
          </p>

          {!isReset && email && (
            <p className="text-sm text-slate-400">
              Didn't receive it?{" "}
              <button
                onClick={handleResend}
                disabled={resending}
                className="text-brand-600 font-semibold hover:underline disabled:opacity-50"
              >
                {resending ? "Sending…" : "Resend verification email"}
              </button>
            </p>
          )}

          <Link
            to="/login"
            className="inline-block mt-2 text-sm text-brand-600 font-semibold hover:underline"
          >
            Back to sign in
          </Link>
        </div>
      </div>
    </div>
  );
}
