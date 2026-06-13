import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "/api/v1";

export const api = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
});

const ACCESS_KEY  = "ft_access";
const REFRESH_KEY = "ft_refresh";
const PERSIST_KEY = "ft_persist";   // "true" → localStorage, absent → sessionStorage

// Which storage holds the tokens right now.
function storage() {
  return localStorage.getItem(PERSIST_KEY) === "true"
    ? localStorage
    : sessionStorage;
}

export function getAccess()  { return storage().getItem(ACCESS_KEY); }
export function getRefresh() { return storage().getItem(REFRESH_KEY); }

/**
 * Store tokens.
 * @param {object}  opts
 * @param {string}  opts.access
 * @param {string}  [opts.refresh]
 * @param {boolean} [opts.persist]  true → localStorage (Remember Me), false/absent → sessionStorage
 */
export function setTokens({ access, refresh, persist }) {
  if (persist !== undefined) {
    // Persist flag changed — clear the other storage first to avoid orphan tokens.
    const other = persist ? sessionStorage : localStorage;
    other.removeItem(ACCESS_KEY);
    other.removeItem(REFRESH_KEY);

    if (persist) {
      localStorage.setItem(PERSIST_KEY, "true");
    } else {
      localStorage.removeItem(PERSIST_KEY);
    }
  }

  const store = storage();
  if (access)  store.setItem(ACCESS_KEY, access);
  if (refresh) store.setItem(REFRESH_KEY, refresh);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(PERSIST_KEY);
  sessionStorage.removeItem(ACCESS_KEY);
  sessionStorage.removeItem(REFRESH_KEY);
}

// ── Request interceptor: attach access token ─────────────────────────────────

api.interceptors.request.use((config) => {
  const token = getAccess();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ── Response interceptor: auto-refresh on 401 ────────────────────────────────

let isRefreshing = false;
let pending = [];

function flushPending(error, token = null) {
  pending.forEach(({ resolve, reject }) => {
    if (error) reject(error);
    else resolve(token);
  });
  pending = [];
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (
      error.response?.status === 401 &&
      !original._retry &&
      getRefresh() &&
      !original.url?.includes("/auth/refresh")
    ) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          pending.push({
            resolve: (token) => {
              original.headers.Authorization = `Bearer ${token}`;
              resolve(api(original));
            },
            reject,
          });
        });
      }
      original._retry = true;
      isRefreshing = true;
      try {
        const refresh = getRefresh();
        const res = await axios.post(`${BASE_URL}/auth/refresh/`, { refresh });
        const newAccess = res.data.access;
        const newRefresh = res.data.refresh || refresh;
        setTokens({ access: newAccess, refresh: newRefresh });
        flushPending(null, newAccess);
        original.headers.Authorization = `Bearer ${newAccess}`;
        return api(original);
      } catch (refreshErr) {
        flushPending(refreshErr, null);
        clearTokens();
        // If the server rejected the refresh due to inactivity, tell the login
        // page so it can show the right message.
        const code = refreshErr.response?.data?.code;
        const dest = code === "inactivity_timeout" ? "/login?reason=inactivity" : "/login";
        window.location.href = dest;
        return Promise.reject(refreshErr);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);
