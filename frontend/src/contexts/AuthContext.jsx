import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { authApi } from "../api/endpoints.js";
import { clearTokens, getAccess, getRefresh, setTokens } from "../api/client.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null);
  const [loading, setLoading] = useState(true);
  const queryClient           = useQueryClient();

  const fetchMe = useCallback(async () => {
    try {
      const me = await authApi.me();
      setUser(me);
    } catch {
      // The axios interceptor already attempted a token refresh before this
      // catch fires. If we're here, both access and refresh tokens are gone.
      if (!getRefresh()) clearTokens();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  // On mount: restore session if any token exists.
  // The refresh interceptor handles the case where only the refresh token is valid.
  useEffect(() => {
    if (getAccess() || getRefresh()) {
      fetchMe();
    } else {
      setLoading(false);
    }
  }, [fetchMe]);

  /**
   * Standard username/password login.
   * remember_me=true → 30-day refresh token stored in localStorage.
   * remember_me=false → 1-day refresh token stored in sessionStorage.
   */
  const login = async ({ username, password, remember_me = false }) => {
    queryClient.clear();
    const res = await authApi.login({ username, password, remember_me });
    setTokens({ access: res.access, refresh: res.refresh, persist: remember_me });
    await fetchMe();
  };

  const register = async (payload) => authApi.register(payload);

  /**
   * Used by email-verification and social-login flows that receive tokens
   * directly from the backend. Not persisted across browser sessions.
   */
  const loginWithTokens = ({ access, refresh }) => {
    queryClient.clear();
    setTokens({ access, refresh, persist: false });
    return fetchMe();
  };

  const logout = () => {
    clearTokens();
    setUser(null);
    queryClient.clear();
  };

  const refreshUser = fetchMe;

  return (
    <AuthContext.Provider
      value={{ user, loading, login, register, loginWithTokens, logout, refreshUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
