import { useEffect, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  CheckCircle2,
  Link2Off,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Loader2,
} from "lucide-react";
import toast from "react-hot-toast";
import { integrationsApi } from "../api/endpoints.js";
import { qk } from "../api/queryKeys.js";

// ── Brand logos ───────────────────────────────────────────────────────────────

function IntervalsLogo({ size = 22 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" aria-hidden="true">
      <rect width="32" height="32" rx="6" fill="#E63946" />
      <path d="M8 22 L13 10 L18 18 L22 13 L26 10" stroke="white" strokeWidth="2.5"
            strokeLinecap="round" strokeLinejoin="round" fill="none" />
    </svg>
  );
}

function StravaLogo({ size = 22 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="#FC4C02" aria-hidden="true">
      <path d="M15.387 17.944l-2.089-4.116h-3.065L15.387 24l5.15-10.172h-3.066m-7.008-5.599l2.836 5.598h4.172L10.463 0l-7 13.828h4.169" />
    </svg>
  );
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatRelative(dateStr) {
  if (!dateStr) return null;
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function ConnectedBadge() {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 dark:bg-emerald-500/15 px-2 py-0.5 text-xs font-medium text-emerald-700 dark:text-emerald-300">
      <CheckCircle2 className="w-3 h-3" />
      Connected
    </span>
  );
}

// ── Reusable provider row shell ───────────────────────────────────────────────

function ProviderRow({ Logo, name, description, meta, actions, children }) {
  return (
    <div className="rounded-xl border border-slate-200 p-4">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-100 dark:bg-slate-100/10">
            <Logo />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-semibold text-slate-900">{name}</span>
              {meta}
            </div>
            <p className="text-xs text-slate-500 mt-0.5">{description}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">{actions}</div>
      </div>
      {children}
    </div>
  );
}

// ── Disconnect + sync button set (shared by both providers) ───────────────────

function DisconnectButton({ onDisconnect, isPending }) {
  return (
    <button
      onClick={onDisconnect}
      disabled={isPending}
      className="btn-ghost text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-500/10 text-sm"
    >
      <Link2Off className="w-4 h-4" />
      Disconnect
    </button>
  );
}

// ── Intervals.icu ─────────────────────────────────────────────────────────────

function IntervalsConnectForm({ onSuccess }) {
  const [athleteId, setAthleteId] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [showHelp, setShowHelp] = useState(false);

  const connect = useMutation({
    mutationFn: () =>
      integrationsApi.intervalsConnect({ athlete_id: athleteId, api_key: apiKey }),
    onSuccess: () => {
      toast.success("Intervals.icu connected! Syncing your last 30 days…");
      onSuccess();
    },
    onError: (err) => {
      toast.error(err?.response?.data?.detail || "Could not connect. Check your credentials.");
    },
  });

  return (
    <div className="mt-3 space-y-3 rounded-xl border border-slate-200 bg-slate-50 dark:bg-slate-100/5 p-4">
      <div>
        <label className="label">Athlete ID</label>
        <input
          className="input"
          placeholder="i12345"
          value={athleteId}
          onChange={(e) => setAthleteId(e.target.value.trim())}
        />
      </div>
      <div>
        <label className="label">API Key</label>
        <input
          className="input"
          type="password"
          placeholder="Your Intervals.icu API key"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value.trim())}
        />
      </div>

      <button
        type="button"
        onClick={() => setShowHelp((v) => !v)}
        className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700"
      >
        {showHelp ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        Where do I find these?
      </button>

      {showHelp && (
        <ol className="text-xs text-slate-500 space-y-1 list-decimal list-inside">
          <li>Open <strong>intervals.icu</strong> and sign in.</li>
          <li>Click your name → <strong>Settings → API</strong>.</li>
          <li>Your <strong>Athlete ID</strong> is shown at the top (e.g. <code>i12345</code>).</li>
          <li>Click <strong>Show API Key</strong> and copy it here.</li>
          <li>
            Make sure your Amazfit watch is linked in Intervals.icu under
            {" "}<strong>Settings → Devices & Integrations → Amazfit / Zepp</strong>.
          </li>
        </ol>
      )}

      <button
        onClick={() => connect.mutate()}
        disabled={!athleteId || !apiKey || connect.isPending}
        className="btn-primary text-sm"
      >
        {connect.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
        Connect
      </button>
    </div>
  );
}

function IntervalsSection({ integration }) {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [syncing, setSyncing] = useState(false);

  const disconnect = useMutation({
    mutationFn: integrationsApi.intervalsDisconnect,
    onSuccess: () => {
      toast.success("Intervals.icu disconnected.");
      queryClient.invalidateQueries({ queryKey: qk.integrations.all() });
    },
    onError: () => toast.error("Could not disconnect."),
  });

  async function handleSync() {
    setSyncing(true);
    try {
      await integrationsApi.intervalsSync({ days_back: 7 });
      toast.success("Sync started — new workouts will appear shortly.");
      setTimeout(() => queryClient.invalidateQueries({ queryKey: qk.integrations.all() }), 3000);
    } catch {
      toast.error("Sync failed. Try again.");
    } finally {
      setSyncing(false);
    }
  }

  if (integration) {
    return (
      <ProviderRow
        Logo={IntervalsLogo}
        name="Intervals.icu"
        description={`Athlete ID: ${integration.token_athlete_id || "—"}${integration.last_synced_at ? " · Last synced " + formatRelative(integration.last_synced_at) : ""}`}
        meta={<ConnectedBadge />}
        actions={
          <>
            <button onClick={handleSync} disabled={syncing} className="btn-ghost text-sm" title="Sync last 7 days">
              <RefreshCw className={`w-4 h-4 ${syncing ? "animate-spin" : ""}`} />
              Sync
            </button>
            <DisconnectButton onDisconnect={() => disconnect.mutate()} isPending={disconnect.isPending} />
          </>
        }
      />
    );
  }

  return (
    <ProviderRow
      Logo={IntervalsLogo}
      name="Intervals.icu"
      description="Free training platform — connects to Amazfit via Zepp."
      actions={
        <>
          <a href="https://intervals.icu" target="_blank" rel="noopener noreferrer" className="btn-ghost text-sm">
            <ExternalLink className="w-4 h-4" />
            Sign up free
          </a>
          <button onClick={() => setShowForm((v) => !v)} className="btn-primary text-sm">
            Connect
          </button>
        </>
      }
    >
      {showForm && (
        <IntervalsConnectForm
          onSuccess={() => {
            setShowForm(false);
            queryClient.invalidateQueries({ queryKey: qk.integrations.all() });
          }}
        />
      )}
    </ProviderRow>
  );
}

// ── Strava ────────────────────────────────────────────────────────────────────

function StravaSection({ integration }) {
  const queryClient = useQueryClient();
  const [showHelp, setShowHelp] = useState(false);

  // Handle redirect back from Strava OAuth
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("strava_connected") === "true") {
      toast.success("Strava connected!");
      window.history.replaceState({}, "", window.location.pathname);
      queryClient.invalidateQueries({ queryKey: qk.integrations.all() });
    }
    if (params.get("strava_error")) {
      toast.error("Could not connect to Strava. Please try again.");
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, [queryClient]);

  const disconnect = useMutation({
    mutationFn: integrationsApi.stravaDisconnect,
    onSuccess: () => {
      toast.success("Strava disconnected.");
      queryClient.invalidateQueries({ queryKey: qk.integrations.all() });
    },
    onError: () => toast.error("Could not disconnect."),
  });

  function handleConnect() {
    const token = localStorage.getItem("ft_access");
    window.location.href = `/api/v1/integrations/strava/connect/?jwt=${token}`;
  }

  if (integration) {
    return (
      <ProviderRow
        Logo={StravaLogo}
        name="Strava"
        description={integration.last_synced_at ? `Last synced ${formatRelative(integration.last_synced_at)}` : "Workouts sync automatically when recorded."}
        meta={<ConnectedBadge />}
        actions={
          <DisconnectButton onDisconnect={() => disconnect.mutate()} isPending={disconnect.isPending} />
        }
      />
    );
  }

  return (
    <ProviderRow
      Logo={StravaLogo}
      name="Strava"
      description="Sync running, cycling, and other activities. Also works as an Amazfit bridge via the Zepp app."
      actions={
        <>
          <button
            type="button"
            onClick={() => setShowHelp((v) => !v)}
            className="btn-ghost text-sm"
          >
            {showHelp ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            How it works
          </button>
          <button onClick={handleConnect} className="btn-primary text-sm" style={{ backgroundColor: "#FC4C02", borderColor: "#FC4C02" }}>
            Connect Strava
          </button>
        </>
      }
    >
      {showHelp && (
        <div className="mt-3 rounded-xl border border-slate-200 bg-slate-50 dark:bg-slate-100/5 p-4 text-xs text-slate-500 space-y-1">
          <p>Clicking <strong>Connect Strava</strong> will open Strava's authorization page.</p>
          <p>Once authorized, your activities will sync automatically via webhook.</p>
          <p className="text-slate-400">
            Note: Strava's developer API requires a paid subscription ($11.99/mo) as of June 2026.
            Intervals.icu is the free alternative for Amazfit users.
          </p>
        </div>
      )}
    </ProviderRow>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function ConnectedApps() {
  const { data: integrations = [], isLoading } = useQuery({
    queryKey: qk.integrations.all(),
    queryFn: integrationsApi.list,
  });

  if (isLoading) return null;

  const intervalsIntegration = integrations.find((i) => i.provider === "intervals" && i.is_active);
  const stravaIntegration = integrations.find((i) => i.provider === "strava" && i.is_active);

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="text-base font-semibold text-slate-900">Connected Apps</h2>
      </div>
      <div className="card-body space-y-3">
        <p className="text-sm text-slate-500">
          Connect a fitness platform to automatically import workouts.
          Amazfit / Zepp users: use <strong>Intervals.icu</strong> (free).
        </p>

        <IntervalsSection integration={intervalsIntegration} />
        <StravaSection integration={stravaIntegration} />

        <p className="text-xs text-slate-400">
          Disconnecting removes the connection but keeps your existing imported workouts.
        </p>
      </div>
    </div>
  );
}
