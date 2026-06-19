/**
 * Tests for the API client module:
 *   - Token storage / retrieval across localStorage and sessionStorage
 *   - Persist-mode switching (Remember Me)
 *   - Request interceptor: Authorization header injection
 *   - Response interceptor: 401 → token refresh → retry / redirect flows
 */

// jest.mock is hoisted above imports so it runs before client.js is initialised.
// We keep axios.create intact (it builds the `api` instance) but replace
// axios.post with a jest.fn() so we can control the /auth/refresh/ response.
jest.mock("axios", () => {
  const actual = jest.requireActual("axios");
  return { ...actual, post: jest.fn() };
});

import axios from "axios";
import MockAdapter from "axios-mock-adapter";
import {
  api,
  getAccess,
  getRefresh,
  setTokens,
  clearTokens,
} from "../../api/client.js";

// One shared MockAdapter instance; reset after every test.
const mock = new MockAdapter(api);

beforeEach(() => {
  mock.reset();
  localStorage.clear();
  sessionStorage.clear();
  // resetAllMocks clears both call records AND queued mockResolvedValueOnce
  // returns — necessary to prevent mock state bleeding between tests.
  jest.resetAllMocks();
});

afterAll(() => {
  mock.restore();
});

// ─────────────────────────────────────────────────────────────────────────────
// Token storage
// ─────────────────────────────────────────────────────────────────────────────

describe("setTokens / getAccess / getRefresh", () => {
  it("stores tokens in sessionStorage when persist=false", () => {
    setTokens({ access: "acc_session", refresh: "ref_session", persist: false });

    expect(sessionStorage.getItem("ft_access")).toBe("acc_session");
    expect(sessionStorage.getItem("ft_refresh")).toBe("ref_session");
    expect(getAccess()).toBe("acc_session");
    expect(getRefresh()).toBe("ref_session");
  });

  it("stores tokens in localStorage when persist=true", () => {
    setTokens({ access: "acc_local", refresh: "ref_local", persist: true });

    expect(localStorage.getItem("ft_access")).toBe("acc_local");
    expect(localStorage.getItem("ft_refresh")).toBe("ref_local");
    expect(getAccess()).toBe("acc_local");
    expect(getRefresh()).toBe("ref_local");
  });

  it("does not write access when access is falsy", () => {
    setTokens({ refresh: "ref_only", persist: false });

    expect(sessionStorage.getItem("ft_access")).toBeNull();
    expect(sessionStorage.getItem("ft_refresh")).toBe("ref_only");
  });

  it("does not write refresh when refresh is falsy", () => {
    setTokens({ access: "acc_only", persist: false });

    expect(sessionStorage.getItem("ft_access")).toBe("acc_only");
    expect(sessionStorage.getItem("ft_refresh")).toBeNull();
  });

  it("clears the old storage when switching from session → local", () => {
    sessionStorage.setItem("ft_access", "old_acc");
    sessionStorage.setItem("ft_refresh", "old_ref");

    setTokens({ access: "new_acc", refresh: "new_ref", persist: true });

    // Old session tokens must be gone
    expect(sessionStorage.getItem("ft_access")).toBeNull();
    expect(sessionStorage.getItem("ft_refresh")).toBeNull();
    // New tokens land in localStorage
    expect(localStorage.getItem("ft_access")).toBe("new_acc");
  });

  it("clears the old storage when switching from local → session", () => {
    localStorage.setItem("ft_persist", "true");
    localStorage.setItem("ft_access", "old_local");

    setTokens({ access: "new_acc", refresh: "new_ref", persist: false });

    expect(localStorage.getItem("ft_access")).toBeNull();
    expect(sessionStorage.getItem("ft_access")).toBe("new_acc");
  });

  it("respects the existing persist flag when persist is not passed", () => {
    // Previously opted into localStorage
    localStorage.setItem("ft_persist", "true");
    localStorage.setItem("ft_access", "prev_acc");

    setTokens({ access: "updated_acc" });

    expect(localStorage.getItem("ft_access")).toBe("updated_acc");
    expect(sessionStorage.getItem("ft_access")).toBeNull();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// clearTokens
// ─────────────────────────────────────────────────────────────────────────────

describe("clearTokens", () => {
  it("wipes tokens and persist flag from both storages", () => {
    localStorage.setItem("ft_access", "la");
    localStorage.setItem("ft_refresh", "lr");
    localStorage.setItem("ft_persist", "true");
    sessionStorage.setItem("ft_access", "sa");
    sessionStorage.setItem("ft_refresh", "sr");

    clearTokens();

    expect(localStorage.getItem("ft_access")).toBeNull();
    expect(localStorage.getItem("ft_refresh")).toBeNull();
    expect(localStorage.getItem("ft_persist")).toBeNull();
    expect(sessionStorage.getItem("ft_access")).toBeNull();
    expect(sessionStorage.getItem("ft_refresh")).toBeNull();
  });

  it("getAccess and getRefresh return null after clearTokens", () => {
    setTokens({ access: "a", refresh: "r", persist: true });
    clearTokens();

    expect(getAccess()).toBeNull();
    expect(getRefresh()).toBeNull();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Request interceptor
// ─────────────────────────────────────────────────────────────────────────────

describe("request interceptor", () => {
  it("attaches Bearer token when an access token exists", async () => {
    setTokens({ access: "my_token", persist: false });
    mock.onGet("/ping").reply(200);

    await api.get("/ping");

    expect(mock.history.get[0].headers["Authorization"]).toBe("Bearer my_token");
  });

  it("does not attach Authorization header when no token is stored", async () => {
    clearTokens();
    mock.onGet("/ping").reply(200);

    await api.get("/ping");

    expect(mock.history.get[0].headers["Authorization"]).toBeUndefined();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Response interceptor — 401 handling
// ─────────────────────────────────────────────────────────────────────────────

describe("response interceptor — 401 token refresh", () => {
  it("retries the original request with a fresh token after a successful refresh", async () => {
    setTokens({ access: "expired", refresh: "valid_refresh", persist: false });

    let callCount = 0;
    mock.onGet("/protected").reply(() => {
      callCount++;
      return callCount === 1 ? [401, {}] : [200, { ok: true }];
    });

    axios.post.mockResolvedValueOnce({
      data: { access: "fresh_access", refresh: "fresh_refresh" },
    });

    const res = await api.get("/protected");

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining("/auth/refresh/"),
      { refresh: "valid_refresh" }
    );
    expect(getAccess()).toBe("fresh_access");
    expect(res.data).toEqual({ ok: true });
    expect(callCount).toBe(2);
  });

  it("updates both access and refresh tokens after a successful refresh", async () => {
    setTokens({ access: "expired", refresh: "old_refresh", persist: false });

    let callCount = 0;
    mock.onGet("/x").reply(() => {
      callCount++;
      return callCount === 1 ? [401, {}] : [200, {}];
    });

    axios.post.mockResolvedValueOnce({
      data: { access: "new_access", refresh: "new_refresh" },
    });

    await api.get("/x");

    expect(getAccess()).toBe("new_access");
    expect(getRefresh()).toBe("new_refresh");
  });

  it("clears tokens when the refresh request itself fails", async () => {
    setTokens({ access: "expired", refresh: "bad_refresh", persist: false });
    mock.onGet("/protected").reply(401);
    axios.post.mockRejectedValueOnce({ response: { data: {} } });

    await expect(api.get("/protected")).rejects.toBeDefined();

    // Tokens must be wiped so subsequent requests don't loop
    expect(getAccess()).toBeNull();
    expect(getRefresh()).toBeNull();
  });

  it("clears tokens on inactivity_timeout failure", async () => {
    setTokens({ access: "expired", refresh: "bad_refresh", persist: false });
    mock.onGet("/protected").reply(401);
    axios.post.mockRejectedValueOnce({
      response: { data: { code: "inactivity_timeout" } },
    });

    await expect(api.get("/protected")).rejects.toBeDefined();
    expect(getAccess()).toBeNull();
  });

  it("does not attempt refresh when there is no refresh token", async () => {
    clearTokens();
    mock.onGet("/protected").reply(401);

    await expect(api.get("/protected")).rejects.toMatchObject({
      response: { status: 401 },
    });
    expect(axios.post).not.toHaveBeenCalled();
  });

  it("does not retry the refresh endpoint itself on 401", async () => {
    setTokens({ access: "tok", refresh: "ref", persist: false });
    mock.onPost("/auth/refresh/").reply(401);

    await expect(api.post("/auth/refresh/")).rejects.toMatchObject({
      response: { status: 401 },
    });
    // Refresh interceptor must not recurse
    expect(axios.post).not.toHaveBeenCalled();
  });
});
