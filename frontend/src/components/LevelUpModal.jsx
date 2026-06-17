import { useEffect } from "react";
import { Zap } from "lucide-react";
import confetti from "canvas-confetti";

import { useLevelContext } from "../contexts/LevelContext.jsx";
import LevelBadge from "./LevelBadge.jsx";

export default function LevelUpModal() {
  const ctx = useLevelContext();
  const levelUp = ctx?.levelUp;
  const dismissLevelUp = ctx?.dismissLevelUp;
  const profile = ctx?.profile;

  useEffect(() => {
    if (!levelUp) return;
    confetti({
      particleCount: 160,
      spread: 90,
      origin: { y: 0.45 },
      colors: ["#6366f1", "#a78bfa", "#f472b6", "#facc15", "#34d399"],
    });
  }, [levelUp]);

  if (!levelUp) return null;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={dismissLevelUp}
    >
      <div
        className="relative bg-surface rounded-2xl shadow-2xl p-8 max-w-sm w-full mx-4 text-center"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-center mb-5">
          <div className="h-20 w-20 rounded-full bg-brand-500/15 ring-4 ring-brand-500/30 flex items-center justify-center">
            <Zap className="w-10 h-10 text-brand-500" />
          </div>
        </div>

        <h2 className="text-3xl font-extrabold text-slate-900 dark:text-white mb-1 tracking-tight">
          Level Up!
        </h2>
        <p className="text-slate-500 mb-5 text-lg">
          <span className="text-slate-400">{levelUp.from}</span>
          {" → "}
          <span className="font-bold text-brand-600">{levelUp.to}</span>
        </p>

        {profile && (
          <div className="mb-6 flex justify-center">
            <LevelBadge tier={profile.tier} level={profile.level} size="lg" />
          </div>
        )}

        <button
          onClick={dismissLevelUp}
          className="btn-primary w-full text-base py-2.5"
        >
          Keep Going!
        </button>
      </div>
    </div>
  );
}
