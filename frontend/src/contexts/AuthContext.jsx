import { createContext, useCallback, useContext, useEffect, useState } from "react";

import { authApi } from "../api/endpoints.js";
import { clearTokens, getAccess, setTokens } from "../api/client.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

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
    const res = await authApi.login({ username, password });
    setTokens({ access: res.access, refresh: res.refresh });
    await fetchMe();
  };

  const register = async (payload) => {
    const res = await authApi.register(payload);
    setTokens(res.tokens);
    setUser(res.user);
  };

  const logout = () => {
    clearTokens();
    setUser(null);
  };

  const refreshUser = fetchMe;

  return (
    <AuthContext.Provider
      value={{ user, loading, login, register, logout, refreshUser }}
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
