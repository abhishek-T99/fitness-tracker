/**
 * Tests for AuthContext / AuthProvider / useAuth
 *
 * Strategy: mock the API layer and token helpers so the context logic is
 * tested in isolation.  TanStack Query's QueryClientProvider is required
 * because AuthProvider calls useQueryClient() on logout.
 */

jest.mock("../../api/endpoints.js", () => ({
  authApi: {
    me:       jest.fn(),
    login:    jest.fn(),
    updateMe: jest.fn(),
    register: jest.fn(),
  },
}));

jest.mock("../../api/client.js", () => ({
  getAccess:   jest.fn(),
  getRefresh:  jest.fn(),
  setTokens:   jest.fn(),
  clearTokens: jest.fn(),
}));

import React from "react";
import { render, screen, act, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { AuthProvider, useAuth } from "../../contexts/AuthContext.jsx";
import { authApi } from "../../api/endpoints.js";
import { getAccess, getRefresh, setTokens, clearTokens } from "../../api/client.js";

// ─── helpers ────────────────────────────────────────────────────────────────

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return function Wrapper({ children }) {
    return (
      <QueryClientProvider client={qc}>
        <AuthProvider>{children}</AuthProvider>
      </QueryClientProvider>
    );
  };
}

/** Small consumer component that exposes context values via data-testid. */
function AuthConsumer() {
  const { user, loading, logout, login, loginWithTokens } = useAuth();
  return (
    <div>
      <span data-testid="loading">{String(loading)}</span>
      <span data-testid="user">{user ? user.username : "none"}</span>
      <button onClick={logout}>logout</button>
      <button onClick={() => login({ username: "u", password: "p" })}>login</button>
      <button onClick={() => loginWithTokens({ access: "a", refresh: "r" })}>
        loginWithTokens
      </button>
    </div>
  );
}

const ME_PAYLOAD = {
  id: 1,
  username: "testuser",
  profile: { timezone: "Asia/Kathmandu" },
};

beforeEach(() => {
  jest.clearAllMocks();
  // Default: no tokens in storage → provider stays logged out
  getAccess.mockReturnValue(null);
  getRefresh.mockReturnValue(null);
});

// ─────────────────────────────────────────────────────────────────────────────
// useAuth hook
// ─────────────────────────────────────────────────────────────────────────────

describe("useAuth", () => {
  it("throws when called outside an AuthProvider", () => {
    // Suppress the expected console.error from React
    const spy = jest.spyOn(console, "error").mockImplementation(() => {});
    expect(() => render(<AuthConsumer />)).toThrow(
      "useAuth must be used inside AuthProvider"
    );
    spy.mockRestore();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Initial loading state
// ─────────────────────────────────────────────────────────────────────────────

describe("loading state", () => {
  it("starts as false and stays false when no tokens are stored", async () => {
    const Wrapper = makeWrapper();
    render(<AuthConsumer />, { wrapper: Wrapper });

    // loading should resolve to false quickly (no fetchMe call)
    await waitFor(() =>
      expect(screen.getByTestId("loading")).toHaveTextContent("false")
    );
    expect(screen.getByTestId("user")).toHaveTextContent("none");
  });

  it("calls fetchMe on mount when an access token exists", async () => {
    getAccess.mockReturnValue("existing_token");
    authApi.me.mockResolvedValueOnce(ME_PAYLOAD);

    const Wrapper = makeWrapper();
    render(<AuthConsumer />, { wrapper: Wrapper });

    await waitFor(() =>
      expect(screen.getByTestId("user")).toHaveTextContent("testuser")
    );
    expect(authApi.me).toHaveBeenCalledTimes(1);
  });

  it("calls fetchMe on mount when only a refresh token exists", async () => {
    getAccess.mockReturnValue(null);
    getRefresh.mockReturnValue("refresh_only");
    authApi.me.mockResolvedValueOnce(ME_PAYLOAD);

    const Wrapper = makeWrapper();
    render(<AuthConsumer />, { wrapper: Wrapper });

    await waitFor(() =>
      expect(screen.getByTestId("user")).toHaveTextContent("testuser")
    );
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// login()
// ─────────────────────────────────────────────────────────────────────────────

describe("login()", () => {
  it("stores tokens then sets user from /auth/me/", async () => {
    authApi.login.mockResolvedValueOnce({ access: "acc", refresh: "ref" });
    authApi.me.mockResolvedValueOnce(ME_PAYLOAD);

    const Wrapper = makeWrapper();
    render(<AuthConsumer />, { wrapper: Wrapper });

    await act(async () => {
      screen.getByRole("button", { name: "login" }).click();
    });

    expect(setTokens).toHaveBeenCalledWith(
      expect.objectContaining({ access: "acc", refresh: "ref" })
    );
    await waitFor(() =>
      expect(screen.getByTestId("user")).toHaveTextContent("testuser")
    );
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// loginWithTokens()
// ─────────────────────────────────────────────────────────────────────────────

describe("loginWithTokens()", () => {
  it("stores tokens without persist flag then fetches user", async () => {
    authApi.me.mockResolvedValueOnce(ME_PAYLOAD);

    const Wrapper = makeWrapper();
    render(<AuthConsumer />, { wrapper: Wrapper });

    await act(async () => {
      screen.getByRole("button", { name: "loginWithTokens" }).click();
    });

    expect(setTokens).toHaveBeenCalledWith({ access: "a", refresh: "r", persist: false });
    await waitFor(() =>
      expect(screen.getByTestId("user")).toHaveTextContent("testuser")
    );
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// logout()
// ─────────────────────────────────────────────────────────────────────────────

describe("logout()", () => {
  it("clears tokens and removes the user from state", async () => {
    // Start logged in
    getAccess.mockReturnValue("tok");
    authApi.me.mockResolvedValueOnce(ME_PAYLOAD);

    const Wrapper = makeWrapper();
    render(<AuthConsumer />, { wrapper: Wrapper });
    await waitFor(() =>
      expect(screen.getByTestId("user")).toHaveTextContent("testuser")
    );

    await act(async () => {
      screen.getByRole("button", { name: "logout" }).click();
    });

    expect(clearTokens).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId("user")).toHaveTextContent("none");
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Browser timezone auto-correction
// ─────────────────────────────────────────────────────────────────────────────

describe("timezone auto-correction", () => {
  beforeEach(() => {
    // Simulate a browser reporting Asia/Kolkata while profile still shows UTC
    jest.spyOn(Intl, "DateTimeFormat").mockReturnValue({
      resolvedOptions: () => ({ timeZone: "Asia/Kolkata" }),
    });
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("PATCHes timezone when profile is still UTC and browser reports something else", async () => {
    getAccess.mockReturnValue("tok");
    authApi.me.mockResolvedValueOnce({
      ...ME_PAYLOAD,
      profile: { timezone: "UTC" },
    });
    authApi.updateMe.mockResolvedValueOnce({});

    const Wrapper = makeWrapper();
    render(<AuthConsumer />, { wrapper: Wrapper });

    await waitFor(() =>
      expect(screen.getByTestId("user")).toHaveTextContent("testuser")
    );

    expect(authApi.updateMe).toHaveBeenCalledWith({
      profile: { timezone: "Asia/Kolkata" },
    });
  });

  it("skips the PATCH when profile timezone is already non-UTC", async () => {
    getAccess.mockReturnValue("tok");
    authApi.me.mockResolvedValueOnce(ME_PAYLOAD); // timezone = Asia/Kathmandu

    const Wrapper = makeWrapper();
    render(<AuthConsumer />, { wrapper: Wrapper });

    await waitFor(() =>
      expect(screen.getByTestId("user")).toHaveTextContent("testuser")
    );

    expect(authApi.updateMe).not.toHaveBeenCalled();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// fetchMe error handling
// ─────────────────────────────────────────────────────────────────────────────

describe("fetchMe error handling", () => {
  it("sets user to null and stops loading when /auth/me/ rejects and refresh is gone", async () => {
    getAccess.mockReturnValue("bad_token");
    getRefresh.mockReturnValue(null);
    authApi.me.mockRejectedValueOnce(new Error("401 Unauthorized"));

    const Wrapper = makeWrapper();
    render(<AuthConsumer />, { wrapper: Wrapper });

    await waitFor(() =>
      expect(screen.getByTestId("loading")).toHaveTextContent("false")
    );
    expect(screen.getByTestId("user")).toHaveTextContent("none");
  });
});
