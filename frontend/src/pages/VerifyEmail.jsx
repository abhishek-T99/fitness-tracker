import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { CheckCircle, Dumbbell, Loader, XCircle } from "lucide-react";

import { authApi } from "../api/endpoints.js";
import { useAuth } from "../contexts/AuthContext.jsx";

export default function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") || "";
  const navigate = useNavigate();
  const { loginWithTokens } = useAuth();

  const [status, setStatus] = useState("verifying"); // verifying | success | error
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setErrorMsg("No verification token found in the link.");
      return;
    }

    let cancelled = false;
    authApi
      .verifyEmail(token)
      .then(async (res) => {
        if (cancelled) return;
        await loginWithTokens(res.tokens);
        setStatus("success");
        setTimeout(() => navigate("/dashboard", { replace: true }), 2000);
      })
      .catch((err) => {
        if (cancelled) return;
        const detail =
          err?.response?.data?.detail || "Verification failed. The link may have expired.";
        setErrorMsg(detail);
        setStatus("error");
      });

    return () => {
      cancelled = true;
    };
  }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="min-h-screen bg-gradient-to-br from-ink-900 via-ink-800 to-brand-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-500 text-white mb-3">
            <Dumbbell className="w-7 h-7" />
          </div>
        </div>

        <div className="bg-surface rounded-2xl shadow-xl p-8 text-center space-y-4">
          {status === "verifying" && (
            <>
              <Loader className="w-12 h-12 text-brand-500 animate-spin mx-auto" />
              <h1 className="text-xl font-bold text-slate-900">Verifying your email…</h1>
              <p className="text-slate-500">Just a moment.</p>
            </>
          )}

          {status === "success" && (
            <>
              <CheckCircle className="w-12 h-12 text-emerald-500 mx-auto" />
              <h1 className="text-xl font-bold text-slate-900">Email verified!</h1>
              <p className="text-slate-500">Your account is active. Redirecting to dashboard…</p>
            </>
          )}

          {status === "error" && (
            <>
              <XCircle className="w-12 h-12 text-rose-500 mx-auto" />
              <h1 className="text-xl font-bold text-slate-900">Verification failed</h1>
              <p className="text-slate-500">{errorMsg}</p>
              <div className="flex flex-col gap-2 pt-2">
                <Link
                  to="/check-email?type=verify"
                  className="text-sm text-brand-600 font-semibold hover:underline"
                >
                  Resend verification email
                </Link>
                <Link
                  to="/login"
                  className="text-sm text-slate-400 hover:underline"
                >
                  Back to sign in
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
