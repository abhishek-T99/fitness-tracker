import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { authApi } from "../api/endpoints.js";
import { clearTokens, getAccess, setTokens } from "../api/client.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const queryClient = useQueryClient();

  const fetchMe = useCallback(async () => {
    try {
      const me = await authApi.me();
      setUser(me);
    } catch {
      // Clear any stale / invalid tokens so they don't poison future requests.
      clearTokens();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (getAccess()) {
      fetchMe();
    } else {
      setLoading(false);
    }
  }, [fetchMe]);

  const login = async ({ username, password }) => {
    queryClient.clear();   // wipe any previous user's cached data before fetching new user
    const res = await authApi.login({ username, password });
    setTokens({ access: res.access, refresh: res.refresh });
    await fetchMe();
  };

  // register no longer auto-logs the user in — account requires email
  // verification first. Returns the {detail} response for the caller to handle.
  const register = async (payload) => {
    return await authApi.register(payload);
  };

  // Called after the backend returns tokens directly (email verification,
  // social login) instead of via the username/password flow.
  const loginWithTokens = ({ access, refresh }) => {
    queryClient.clear();
    setTokens({ access, refresh });
    return fetchMe();
  };

  const logout = () => {
    clearTokens();
    setUser(null);
    queryClient.clear();   // drop every cached query so the next user starts clean
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
