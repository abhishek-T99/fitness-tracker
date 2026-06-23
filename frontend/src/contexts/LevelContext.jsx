import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { levelsApi } from "../api/endpoints.js";
import { useAuth } from "./AuthContext.jsx";
import { qk } from "../api/queryKeys.js";

const LevelContext = createContext(null);
const LS_KEY = "fittrack_level";

export function LevelProvider({ children }) {
  const { user } = useAuth();
  const [levelUp, setLevelUp] = useState(null); // { from, to }

  const { data: profile, refetch } = useQuery({
    queryKey: qk.levels.profile(),
    queryFn: levelsApi.profile,
    enabled: !!user,
    refetchInterval: 30_000,
    staleTime: 10_000,
  });

  useEffect(() => {
    if (!profile) return;
    const prev = parseInt(localStorage.getItem(LS_KEY) || "1", 10);
    if (profile.level > prev) {
      setLevelUp({ from: prev, to: profile.level });
    }
    localStorage.setItem(LS_KEY, String(profile.level));
  }, [profile?.level]);

  const dismissLevelUp = useCallback(() => setLevelUp(null), []);

  return (
    <LevelContext.Provider value={{ profile, levelUp, dismissLevelUp, refetch }}>
      {children}
    </LevelContext.Provider>
  );
}

export function useLevelContext() {
  return useContext(LevelContext);
}
