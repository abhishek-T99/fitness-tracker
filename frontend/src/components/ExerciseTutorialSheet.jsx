/**
 * ExerciseTutorialSheet
 *
 * Bottom sheet shown during an active workout session.
 * Surfaces:
 *   1. Form cues (parsed from exercise.instructions)
 *   2. Top YouTube tutorial videos fetched from our backend (cached 24 h)
 *      — tapping a thumbnail plays the video inline via YouTube IFrame embed
 *
 * Design principles
 * ─────────────────
 * • Bottom sheet preserves workout context visible above.
 * • Instructions split into numbered bullets — scannable during a 60-s rest.
 * • "First time?" callout gives beginners a clear nudge.
 * • Videos load lazily (only when the sheet opens), shown as a 2-col grid.
 * • Inline player avoids leaving the app entirely.
 * • Graceful degradation: if API key not set or network fails, shows a
 *   "Search on YouTube" link so the user is never stuck.
 */
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Info, X, ExternalLink, Dumbbell, Play, Loader2,
} from "lucide-react";

import { exerciseTutorialsApi } from "../api/endpoints.js";

// ── Helpers ────────────────────────────────────────────────────────────────

function parseBullets(instructions = "") {
  if (!instructions.trim()) return [];
  return instructions
    .split(/(?<=[.!])\s+|;\s*|\n+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 4);
}

function buildFallbackUrl(exercise) {
  if (exercise?.tutorial_url) return exercise.tutorial_url;
  const q = exercise?.youtube_search_query || `${exercise?.name} proper form tutorial`;
  return `https://www.youtube.com/results?search_query=${encodeURIComponent(q)}`;
}

function formatViews(n) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000)     return `${(n / 1_000).toFixed(0)}K`;
  return String(n);
}

const MUSCLE_COLORS = {
  chest:      "bg-rose-50 text-rose-700 dark:bg-rose-500/15 dark:text-rose-300",
  back:       "bg-blue-50 text-blue-700 dark:bg-blue-500/15 dark:text-blue-300",
  shoulders:  "bg-violet-50 text-violet-700 dark:bg-violet-500/15 dark:text-violet-300",
  biceps:     "bg-indigo-50 text-indigo-700 dark:bg-indigo-500/15 dark:text-indigo-300",
  triceps:    "bg-purple-50 text-purple-700 dark:bg-purple-500/15 dark:text-purple-300",
  quads:      "bg-amber-50 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300",
  hamstrings: "bg-orange-50 text-orange-700 dark:bg-orange-500/15 dark:text-orange-300",
  glutes:     "bg-pink-50 text-pink-700 dark:bg-pink-500/15 dark:text-pink-300",
  calves:     "bg-yellow-50 text-yellow-700 dark:bg-yellow-500/15 dark:text-yellow-300",
  core:       "bg-teal-50 text-teal-700 dark:bg-teal-500/15 dark:text-teal-300",
  full_body:  "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300",
  cardio:     "bg-sky-50 text-sky-700 dark:bg-sky-500/15 dark:text-sky-300",
};

// ── Video thumbnail card ───────────────────────────────────────────────────

function VideoCard({ video, isActive, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`relative group w-full text-left rounded-xl overflow-hidden border transition-all ${
        isActive
          ? "border-brand-500 ring-2 ring-brand-500/30"
          : "border-slate-200 hover:border-slate-300"
      }`}
    >
      {/* Thumbnail */}
      <div className="relative aspect-video bg-slate-100 overflow-hidden">
        <img
          src={video.thumbnail}
          alt={video.title}
          className="w-full h-full object-cover"
          loading="lazy"
        />
        {/* Play overlay */}
        <div className={`absolute inset-0 flex items-center justify-center transition-opacity ${
          isActive ? "bg-brand-600/20" : "bg-black/20 group-hover:bg-black/30"
        }`}>
          <div className={`flex h-10 w-10 items-center justify-center rounded-full ${
            isActive ? "bg-brand-600" : "bg-black/60"
          }`}>
            <Play className="w-4 h-4 text-white fill-white" />
          </div>
        </div>
        {/* Duration badge */}
        {video.duration_label && (
          <span className="absolute bottom-1.5 right-1.5 bg-black/80 text-white text-[10px] font-medium px-1.5 py-0.5 rounded">
            {video.duration_label}
          </span>
        )}
      </div>

      {/* Meta */}
      <div className="p-2.5 space-y-0.5">
        <p className="text-xs font-semibold text-slate-900 line-clamp-2 leading-snug">
          {video.title}
        </p>
        <p className="text-[10px] text-slate-400">
          {video.channel} · {formatViews(video.view_count)} views
        </p>
      </div>
    </button>
  );
}

// ── Inline YouTube player ──────────────────────────────────────────────────

function InlinePlayer({ videoId, title }) {
  return (
    <div className="rounded-xl overflow-hidden border border-slate-200 bg-black">
      <div className="relative" style={{ paddingTop: "56.25%" /* 16:9 */ }}>
        <iframe
          className="absolute inset-0 w-full h-full"
          src={`https://www.youtube.com/embed/${videoId}?autoplay=1&rel=0&modestbranding=1`}
          title={title}
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        />
      </div>
    </div>
  );
}

// ── Trigger button ─────────────────────────────────────────────────────────

export function TutorialTrigger({ onClick, isFirstSession }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label="View exercise tutorial"
      className="relative flex items-center justify-center h-8 w-8 rounded-full text-slate-400 hover:text-brand-500 hover:bg-brand-50 dark:hover:bg-brand-500/10 transition-colors"
    >
      <Info className="w-4 h-4" />
      {isFirstSession && (
        <>
          <span className="absolute inset-0 rounded-full border border-brand-400 opacity-60" />
          <span className="absolute inset-0 rounded-full border border-brand-400 animate-ping opacity-40" />
        </>
      )}
    </button>
  );
}

// ── Main sheet ─────────────────────────────────────────────────────────────

export default function ExerciseTutorialSheet({ exercise, isFirstSession, onClose }) {
  const [activeVideoId, setActiveVideoId] = useState(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["exerciseTutorials", exercise?.slug],
    queryFn: () => exerciseTutorialsApi.fetch(exercise.slug),
    enabled: !!exercise?.slug,
    staleTime: 60 * 60 * 1000,  // treat as fresh for 1 h (backend caches 24 h)
    retry: 1,
  });

  if (!exercise) return null;

  const videos   = data?.videos ?? [];
  const bullets  = parseBullets(exercise.instructions);
  const fallback = buildFallbackUrl(exercise);
  const activeVideo = videos.find((v) => v.video_id === activeVideoId);

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Sheet */}
      <div className="fixed bottom-0 left-0 right-0 z-50 max-h-[90vh] overflow-y-auto rounded-t-2xl bg-surface shadow-2xl border-t border-slate-200 animate-slide-up">

        {/* Drag handle */}
        <div className="flex justify-center pt-3 pb-1">
          <span className="h-1 w-10 rounded-full bg-slate-300" />
        </div>

        {/* Header */}
        <div className="flex items-start justify-between gap-3 px-5 py-4 border-b border-slate-100">
          <div className="min-w-0">
            <h2 className="font-bold text-slate-900 text-lg leading-tight">{exercise.name}</h2>
            <div className="flex flex-wrap gap-1.5 mt-2">
              <span className={`badge capitalize text-xs ${MUSCLE_COLORS[exercise.primary_muscle] ?? "bg-slate-100 text-slate-700"}`}>
                {(exercise.primary_muscle || "").replace(/_/g, " ")}
              </span>
              {(exercise.secondary_muscles || []).map((m) => (
                <span key={m} className="badge bg-slate-100 text-slate-600 capitalize text-xs">
                  {m.replace(/_/g, " ")}
                </span>
              ))}
              <span className="badge bg-slate-100 text-slate-600 capitalize text-xs">{exercise.equipment}</span>
              {exercise.is_compound && (
                <span className="badge bg-brand-50 text-brand-700 dark:text-brand-300 text-xs">compound</span>
              )}
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 shrink-0 mt-0.5">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="px-5 py-4 space-y-6">

          {/* First-time callout */}
          {isFirstSession && (
            <div className="flex items-start gap-3 rounded-xl border border-brand-200 dark:border-brand-500/30 bg-brand-50 dark:bg-brand-500/10 p-3.5">
              <Dumbbell className="w-4 h-4 text-brand-600 dark:text-brand-400 shrink-0 mt-0.5" />
              <p className="text-sm text-brand-700 dark:text-brand-300 font-medium">
                First time doing this exercise — review the form cues and watch a tutorial before you start.
              </p>
            </div>
          )}

          {/* Form cues */}
          {bullets.length > 0 && (
            <section>
              <h3 className="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-3">
                Key form cues
              </h3>
              <ul className="space-y-2.5">
                {bullets.map((point, i) => (
                  <li key={i} className="flex items-start gap-2.5">
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand-50 dark:bg-brand-500/15 text-brand-600 dark:text-brand-400 text-[10px] font-bold mt-0.5">
                      {i + 1}
                    </span>
                    <p className="text-sm text-slate-700 leading-relaxed">{point}</p>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* Tutorials section */}
          <section>
            <h3 className="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-3">
              Tutorials
            </h3>

            {/* Loading */}
            {isLoading && (
              <div className="grid grid-cols-2 gap-3">
                {[0, 1, 2, 3].map((i) => (
                  <div key={i} className="rounded-xl border border-slate-200 overflow-hidden animate-pulse">
                    <div className="aspect-video bg-slate-100" />
                    <div className="p-2.5 space-y-1.5">
                      <div className="h-3 bg-slate-100 rounded w-full" />
                      <div className="h-3 bg-slate-100 rounded w-2/3" />
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Videos grid */}
            {!isLoading && videos.length > 0 && (
              <>
                <div className="grid grid-cols-2 gap-3">
                  {videos.map((video) => (
                    <VideoCard
                      key={video.video_id}
                      video={video}
                      isActive={video.video_id === activeVideoId}
                      onClick={() =>
                        setActiveVideoId(
                          activeVideoId === video.video_id ? null : video.video_id
                        )
                      }
                    />
                  ))}
                </div>

                {/* Inline player — shown below the grid when a video is active */}
                {activeVideo && (
                  <div className="mt-3">
                    <InlinePlayer
                      videoId={activeVideo.video_id}
                      title={activeVideo.title}
                    />
                    <p className="mt-2 text-xs text-slate-500 text-center">
                      {activeVideo.title}
                    </p>
                  </div>
                )}
              </>
            )}

            {/* Error / no API key — fallback to YouTube search link */}
            {!isLoading && (isError || videos.length === 0) && (
              <a
                href={fallback}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between gap-3 w-full rounded-xl border border-slate-200 bg-surface px-4 py-3.5 hover:border-rose-300 hover:bg-rose-50 dark:hover:bg-rose-500/10 transition-colors group"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[#FF0000]">
                    <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z"/>
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-900">Search on YouTube</p>
                    <p className="text-xs text-slate-400 mt-0.5">
                      "{exercise.name} proper form tutorial"
                    </p>
                  </div>
                </div>
                <ExternalLink className="w-4 h-4 text-slate-400 group-hover:text-rose-500 shrink-0" />
              </a>
            )}
          </section>
        </div>

        {/* Safe area */}
        <div className="h-6" />
      </div>
    </>
  );
}
