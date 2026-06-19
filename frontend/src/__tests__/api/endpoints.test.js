/**
 * Tests for api/endpoints.js
 *
 * Strategy: mock the `api` axios instance from client.js so every test
 * remains a pure unit test — no network, no token logic.  We verify that
 * each endpoint helper calls the correct HTTP method, URL, and parameters.
 */

jest.mock("../../api/client.js", () => ({
  api: {
    get:    jest.fn(),
    post:   jest.fn(),
    put:    jest.fn(),
    patch:  jest.fn(),
    delete: jest.fn(),
    defaults: { baseURL: "/api/v1" },
  },
}));

import { api } from "../../api/client.js";
import {
  authApi,
  exercisesApi,
  workoutsApi,
  achievementsApi,
  remindersApi,
  reportsApi,
  goalsApi,
  notificationsApi,
  measurementsApi,
  socialApi,
} from "../../api/endpoints.js";

const ok = (data) => Promise.resolve({ data });

beforeEach(() => {
  jest.clearAllMocks();
});

// ─────────────────────────────────────────────────────────────────────────────
// Auth
// ─────────────────────────────────────────────────────────────────────────────

describe("authApi", () => {
  it("login POSTs credentials to /auth/login/", async () => {
    api.post.mockReturnValueOnce(ok({ access: "a", refresh: "r" }));
    await authApi.login({ username: "u", password: "p" });
    expect(api.post).toHaveBeenCalledWith("/auth/login/", { username: "u", password: "p" });
  });

  it("register POSTs payload to /auth/register/", async () => {
    api.post.mockReturnValueOnce(ok({}));
    await authApi.register({ username: "u", password: "p", email: "e@e.com" });
    expect(api.post).toHaveBeenCalledWith("/auth/register/", expect.objectContaining({ username: "u" }));
  });

  it("me GETs /auth/me/", async () => {
    api.get.mockReturnValueOnce(ok({ id: 1 }));
    await authApi.me();
    expect(api.get).toHaveBeenCalledWith("/auth/me/");
  });

  it("updateMe PATCHes /auth/me/ with provided data", async () => {
    api.patch.mockReturnValueOnce(ok({}));
    await authApi.updateMe({ profile: { timezone: "Asia/Kathmandu" } });
    expect(api.patch).toHaveBeenCalledWith(
      "/auth/me/",
      { profile: { timezone: "Asia/Kathmandu" } }
    );
  });

  it("forgotPassword POSTs email to /auth/forgot-password/", async () => {
    api.post.mockReturnValueOnce(ok({}));
    await authApi.forgotPassword("user@example.com");
    expect(api.post).toHaveBeenCalledWith("/auth/forgot-password/", { email: "user@example.com" });
  });

  it("changePassword POSTs to /auth/change-password/", async () => {
    api.post.mockReturnValueOnce(ok({}));
    await authApi.changePassword({ current_password: "old", new_password: "new" });
    expect(api.post).toHaveBeenCalledWith("/auth/change-password/", expect.any(Object));
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Exercises
// ─────────────────────────────────────────────────────────────────────────────

describe("exercisesApi", () => {
  it("list GETs /exercises/ and forwards params", async () => {
    api.get.mockReturnValueOnce(ok([]));
    await exercisesApi.list({ search: "squat" });
    expect(api.get).toHaveBeenCalledWith("/exercises/", { params: { search: "squat" } });
  });

  it("retrieve GETs the exercise slug endpoint", async () => {
    api.get.mockReturnValueOnce(ok({}));
    await exercisesApi.retrieve("barbell-squat");
    expect(api.get).toHaveBeenCalledWith("/exercises/barbell-squat/");
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Workouts
// ─────────────────────────────────────────────────────────────────────────────

describe("workoutsApi", () => {
  it("list GETs /workouts/ with page params", async () => {
    api.get.mockReturnValueOnce(ok({ results: [] }));
    await workoutsApi.list({ page: 2 });
    expect(api.get).toHaveBeenCalledWith("/workouts/", { params: { page: 2 } });
  });

  it("stats GETs /workouts/stats/", async () => {
    api.get.mockReturnValueOnce(ok({}));
    await workoutsApi.stats();
    expect(api.get).toHaveBeenCalledWith("/workouts/stats/");
  });

  it("exerciseHistory joins exercise IDs into a comma-separated param", async () => {
    api.get.mockReturnValueOnce(ok({}));
    await workoutsApi.exerciseHistory([1, 2, 3]);
    expect(api.get).toHaveBeenCalledWith("/workouts/exercise-history/", {
      params: { exercise_ids: "1,2,3" },
    });
  });

  it("create POSTs to /workouts/", async () => {
    api.post.mockReturnValueOnce(ok({ id: 99 }));
    await workoutsApi.create({ name: "Leg day" });
    expect(api.post).toHaveBeenCalledWith("/workouts/", { name: "Leg day" });
  });

  it("remove DELETEs the workout by id", async () => {
    api.delete.mockReturnValueOnce(ok(null));
    await workoutsApi.remove(42);
    expect(api.delete).toHaveBeenCalledWith("/workouts/42/");
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Achievements
// ─────────────────────────────────────────────────────────────────────────────

describe("achievementsApi", () => {
  it("catalog GETs /achievements/catalog/", async () => {
    api.get.mockReturnValueOnce(ok([]));
    await achievementsApi.catalog();
    expect(api.get).toHaveBeenCalledWith("/achievements/catalog/");
  });

  it("unlocked GETs /achievements/unlocked/", async () => {
    api.get.mockReturnValueOnce(ok([]));
    await achievementsApi.unlocked();
    expect(api.get).toHaveBeenCalledWith("/achievements/unlocked/");
  });

  it("streak GETs /achievements/streak/", async () => {
    api.get.mockReturnValueOnce(ok({ current_days: 5 }));
    await achievementsApi.streak();
    expect(api.get).toHaveBeenCalledWith("/achievements/streak/");
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Reports
// ─────────────────────────────────────────────────────────────────────────────

describe("reportsApi", () => {
  it("list returns data.results when the response is paginated", async () => {
    api.get.mockReturnValueOnce(ok({ results: [{ id: 1 }], count: 1 }));
    const result = await reportsApi.list();
    expect(result).toEqual([{ id: 1 }]);
  });

  it("list returns data directly when the response is an array", async () => {
    api.get.mockReturnValueOnce(ok([{ id: 2 }]));
    const result = await reportsApi.list();
    expect(result).toEqual([{ id: 2 }]);
  });

  it("trigger POSTs period_type to /reports/trigger/", async () => {
    api.post.mockReturnValueOnce(ok({}));
    await reportsApi.trigger("weekly");
    expect(api.post).toHaveBeenCalledWith("/reports/trigger/", { period_type: "weekly" });
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Goals
// ─────────────────────────────────────────────────────────────────────────────

describe("goalsApi", () => {
  it("list GETs /goals/", async () => {
    api.get.mockReturnValueOnce(ok([]));
    await goalsApi.list();
    expect(api.get).toHaveBeenCalledWith("/goals/");
  });

  it("update PATCHes the goal by id", async () => {
    api.patch.mockReturnValueOnce(ok({}));
    await goalsApi.update(7, { status: "achieved" });
    expect(api.patch).toHaveBeenCalledWith("/goals/7/", { status: "achieved" });
  });

  it("reorder POSTs reorder payload to /goals/reorder/", async () => {
    api.post.mockReturnValueOnce(ok({}));
    await goalsApi.reorder([{ id: 1, order: 0 }]);
    expect(api.post).toHaveBeenCalledWith("/goals/reorder/", [{ id: 1, order: 0 }]);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Notifications
// ─────────────────────────────────────────────────────────────────────────────

describe("notificationsApi", () => {
  it("unreadCount GETs /notifications/unread_count/", async () => {
    api.get.mockReturnValueOnce(ok({ count: 3 }));
    await notificationsApi.unreadCount();
    expect(api.get).toHaveBeenCalledWith("/notifications/unread_count/");
  });

  it("markRead PATCHes the notification with read: true", async () => {
    api.patch.mockReturnValueOnce(ok({}));
    await notificationsApi.markRead(5);
    expect(api.patch).toHaveBeenCalledWith("/notifications/5/", { read: true });
  });

  it("markAllRead POSTs to /notifications/mark_all_read/", async () => {
    api.post.mockReturnValueOnce(ok({}));
    await notificationsApi.markAllRead();
    expect(api.post).toHaveBeenCalledWith("/notifications/mark_all_read/");
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Social
// ─────────────────────────────────────────────────────────────────────────────

describe("socialApi", () => {
  it("commentOnPost POSTs body to the post's comment endpoint", async () => {
    api.post.mockReturnValueOnce(ok({}));
    await socialApi.commentOnPost(10, "Great workout!");
    expect(api.post).toHaveBeenCalledWith(
      "/social/posts/10/comment/",
      { body: "Great workout!" }
    );
  });

  it("searchUsers passes search query as a param", async () => {
    api.get.mockReturnValueOnce(ok([]));
    await socialApi.searchUsers("alice");
    expect(api.get).toHaveBeenCalledWith("/social/users/", {
      params: { search: "alice" },
    });
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Measurements
// ─────────────────────────────────────────────────────────────────────────────

describe("measurementsApi", () => {
  it("weightHistory passes default days=90", async () => {
    api.get.mockReturnValueOnce(ok([]));
    await measurementsApi.weightHistory();
    expect(api.get).toHaveBeenCalledWith("/measurements/weight_history/", {
      params: { days: 90 },
    });
  });

  it("weightHistory accepts a custom days param", async () => {
    api.get.mockReturnValueOnce(ok([]));
    await measurementsApi.weightHistory(30);
    expect(api.get).toHaveBeenCalledWith("/measurements/weight_history/", {
      params: { days: 30 },
    });
  });
});
