import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";

import { authApi } from "../api/endpoints.js";
import { useAuth } from "../contexts/AuthContext.jsx";
import { useTheme } from "../contexts/ThemeContext.jsx";

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;
const FACEBOOK_APP_ID = import.meta.env.VITE_FACEBOOK_APP_ID;

function loadScript(src, id) {
  return new Promise((resolve, reject) => {
    const existing = document.getElementById(id);
    if (existing) {
      // Script tag exists but may still be downloading (StrictMode remount
      // happens before the first mount's script finishes loading).
      if (existing.dataset.loaded) return resolve();
      existing.addEventListener("load", resolve);
      existing.addEventListener("error", reject);
      return;
    }
    const s = document.createElement("script");
    s.src = src;
    s.id = id;
    s.async = true;
    s.defer = true;
    s.onload = () => {
      s.dataset.loaded = "true";
      resolve();
    };
    s.onerror = reject;
    document.head.appendChild(s);
  });
}

export default function SocialLoginButtons() {
  const { loginWithTokens } = useAuth();
  const { theme } = useTheme();
  const navigate = useNavigate();
  const googleBtnRef = useRef(null);
  const [busy, setBusy] = useState(false);

  async function completeLogin(apiCall) {
    setBusy(true);
    try {
      const res = await apiCall();
      await loginWithTokens(res.tokens);
      toast.success("Welcome!");
      navigate("/dashboard", { replace: true });
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Social sign-in failed.");
    } finally {
      setBusy(false);
    }
  }

  // ── Google Identity Services ──
  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) return;
    let cancelled = false;
    loadScript("https://accounts.google.com/gsi/client", "google-gsi").then(() => {
      if (cancelled || !window.google || !googleBtnRef.current) return;
      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: (response) =>
          completeLogin(() => authApi.googleLogin(response.credential)),
      });
      window.google.accounts.id.renderButton(googleBtnRef.current, {
        theme: theme === "dark" ? "filled_black" : "outline",
        size: "large",
        width: 336,
        text: "continue_with",
      });
    }).catch(() => {});
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [theme]);

  // ── Facebook SDK ──
  useEffect(() => {
    if (!FACEBOOK_APP_ID) return;
    loadScript("https://connect.facebook.net/en_US/sdk.js", "facebook-jssdk").then(() => {
      window.FB?.init({
        appId: FACEBOOK_APP_ID,
        cookie: true,
        xfbml: false,
        version: "v19.0",
      });
    }).catch(() => {});
  }, []);

  function handleFacebook() {
    if (!window.FB) {
      toast.error("Facebook SDK not loaded yet — try again in a moment.");
      return;
    }
    window.FB.login(
      (response) => {
        const token = response?.authResponse?.accessToken;
        if (!token) return; // user closed the dialog
        completeLogin(() => authApi.facebookLogin(token));
      },
      { scope: "public_profile,email" }
    );
  }

  if (!GOOGLE_CLIENT_ID && !FACEBOOK_APP_ID) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <div className="h-px flex-1 bg-slate-200" />
        <span className="text-xs text-slate-400 font-medium">or continue with</span>
        <div className="h-px flex-1 bg-slate-200" />
      </div>

      {GOOGLE_CLIENT_ID && (
        <div ref={googleBtnRef} className="flex justify-center" />
      )}

      {FACEBOOK_APP_ID && (
        <button
          type="button"
          onClick={handleFacebook}
          disabled={busy}
          className="w-full flex items-center justify-center gap-2.5 rounded-lg border border-slate-300 bg-[#1877F2] py-2.5 text-sm font-medium text-white hover:bg-[#166FE5] transition disabled:opacity-60"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
          </svg>
          Continue with Facebook
        </button>
      )}
    </div>
  );
}
