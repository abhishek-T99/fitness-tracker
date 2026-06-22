import { api } from "./client.js";

// Auth
export const authApi = {
  login: (data) => api.post("/auth/login/", data).then((r) => r.data),
  googleLogin: (token) => api.post("/auth/google/", { token }).then((r) => r.data),
  facebookLogin: (token) => api.post("/auth/facebook/", { token }).then((r) => r.data),
  register: (data) => api.post("/auth/register/", data).then((r) => r.data),
  verifyEmail: (token) =>
    api.post("/auth/verify-email/", { token }).then((r) => r.data),
  resendVerification: (email) =>
    api.post("/auth/resend-verification/", { email }).then((r) => r.data),
  forgotPassword: (email) =>
    api.post("/auth/forgot-password/", { email }).then((r) => r.data),
  resetPassword: (token, new_password) =>
    api.post("/auth/reset-password/", { token, new_password }).then((r) => r.data),
  me: () => api.get("/auth/me/").then((r) => r.data),
  updateMe: (data) => api.patch("/auth/me/", data).then((r) => r.data),
  uploadAvatar: (file) => {
    const fd = new FormData();
    fd.append("avatar", file);
    return api.patch("/auth/me/", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    }).then((r) => r.data);
  },
  changePassword: (data) =>
    api.post("/auth/change-password/", data).then((r) => r.data),
};

// Exercises
export const exercisesApi = {
  list: (params) =>
    api.get("/exercises/", { params }).then((r) => r.data),
  retrieve: (slug) => api.get(`/exercises/${slug}/`).then((r) => r.data),
};

// Workouts
export const workoutsApi = {
  list: (params) => api.get("/workouts/", { params }).then((r) => r.data),
  exerciseHistory: (exerciseIds) =>
    api.get("/workouts/exercise-history/", {
      params: { exercise_ids: exerciseIds.join(",") },
    }).then((r) => r.data),
  retrieve: (id) => api.get(`/workouts/${id}/`).then((r) => r.data),
  create: (data) => api.post("/workouts/", data).then((r) => r.data),
  update: (id, data) => api.put(`/workouts/${id}/`, data).then((r) => r.data),
  remove: (id) => api.delete(`/workouts/${id}/`).then((r) => r.data),
  stats: () => api.get("/workouts/stats/").then((r) => r.data),
};

// Routines
export const routinesApi = {
  list: () => api.get("/workouts/routines/").then((r) => r.data),
  retrieve: (id) => api.get(`/workouts/routines/${id}/`).then((r) => r.data),
  create: (data) => api.post("/workouts/routines/", data).then((r) => r.data),
  update: (id, data) =>
    api.put(`/workouts/routines/${id}/`, data).then((r) => r.data),
  remove: (id) =>
    api.delete(`/workouts/routines/${id}/`).then((r) => r.data),
  reorder: (items) =>
    api.post("/workouts/routines/reorder/", items).then((r) => r.data),
};

// Nutrition
export const foodsApi = {
  list: (params) => api.get("/nutrition/foods/", { params }).then((r) => r.data),
  create: (data) => api.post("/nutrition/foods/", data).then((r) => r.data),
};
export const mealsApi = {
  list: (params) => api.get("/nutrition/meals/", { params }).then((r) => r.data),
  create: (data) => api.post("/nutrition/meals/", data).then((r) => r.data),
  update: (id, data) => api.put(`/nutrition/meals/${id}/`, data).then((r) => r.data),
  remove: (id) => api.delete(`/nutrition/meals/${id}/`).then((r) => r.data),
  dailySummary: (date) =>
    api
      .get("/nutrition/meals/daily_summary/", { params: { date } })
      .then((r) => r.data),
};
export const waterApi = {
  list: (params) => api.get("/nutrition/water/", { params }).then((r) => r.data),
  create: (data) => api.post("/nutrition/water/", data).then((r) => r.data),
  update: (id, data) => api.patch(`/nutrition/water/${id}/`, data).then((r) => r.data),
  remove: (id) => api.delete(`/nutrition/water/${id}/`).then((r) => r.data),
};

// Measurements
export const exerciseTutorialsApi = {
  fetch: (exerciseSlug) =>
    api.get("/exercises/youtube-tutorials/", {
      params: { exercise_slug: exerciseSlug },
    }).then((r) => r.data),
};

export const wellnessApi = {
  today: () => api.get("/measurements/today_wellness/").then((r) => r.data),
};

export const measurementsApi = {
  list: () => api.get("/measurements/").then((r) => r.data),
  create: (data) => api.post("/measurements/", data).then((r) => r.data),
  update: (id, data) => api.patch(`/measurements/${id}/`, data).then((r) => r.data),
  remove: (id) => api.delete(`/measurements/${id}/`).then((r) => r.data),
  weightHistory: (days = 90) =>
    api
      .get("/measurements/weight_history/", { params: { days } })
      .then((r) => r.data),
  latest: () => api.get("/measurements/latest/").then((r) => r.data),
};

// Goals
export const goalsApi = {
  list: () => api.get("/goals/").then((r) => r.data),
  create: (data) => api.post("/goals/", data).then((r) => r.data),
  update: (id, data) => api.patch(`/goals/${id}/`, data).then((r) => r.data),
  remove: (id) => api.delete(`/goals/${id}/`).then((r) => r.data),
  reorder: (items) => api.post("/goals/reorder/", items).then((r) => r.data),
};

// Social
export const socialApi = {
  feed: () => api.get("/social/posts/").then((r) => r.data),
  createPost: (data) => api.post("/social/posts/", data).then((r) => r.data),
  likePost: (id) => api.post(`/social/posts/${id}/like/`).then((r) => r.data),
  commentOnPost: (id, body) =>
    api.post(`/social/posts/${id}/comment/`, { body }).then((r) => r.data),
  searchUsers: (q) =>
    api.get("/social/users/", { params: { search: q } }).then((r) => r.data),
  friendships: () => api.get("/social/friendships/").then((r) => r.data),
  sendRequest: (addressee) =>
    api.post("/social/friendships/", { addressee }).then((r) => r.data),
  acceptRequest: (id) =>
    api.post(`/social/friendships/${id}/accept/`).then((r) => r.data),
  declineRequest: (id) =>
    api.post(`/social/friendships/${id}/decline/`).then((r) => r.data),
  friends: () => api.get("/social/friendships/friends/").then((r) => r.data),
};

// Achievements
export const achievementsApi = {
  catalog: () => api.get("/achievements/catalog/").then((r) => r.data),
  unlocked: () => api.get("/achievements/unlocked/").then((r) => r.data),
  streak: () => api.get("/achievements/streak/").then((r) => r.data),
};

// Reminders
export const remindersApi = {
  list: () => api.get("/reminders/").then((r) => r.data),
  create: (data) => api.post("/reminders/", data).then((r) => r.data),
  update: (id, data) => api.patch(`/reminders/${id}/`, data).then((r) => r.data),
  remove: (id) => api.delete(`/reminders/${id}/`).then((r) => r.data),
  reorder: (items) => api.post("/reminders/reorder/", items).then((r) => r.data),
};

// Meal Plans
export const mealPlanApi = {
  list:      (params) => api.get("/meal-plans/", { params }).then((r) => r.data),
  create:    (data)   => api.post("/meal-plans/", data).then((r) => r.data),
  retrieve:  (id)     => api.get(`/meal-plans/${id}/`).then((r) => r.data),
  update:    (id, d)  => api.patch(`/meal-plans/${id}/`, d).then((r) => r.data),
  remove:    (id)     => api.delete(`/meal-plans/${id}/`),
  generate:  (id)     => api.post(`/meal-plans/${id}/generate/`).then((r) => r.data),
  logDay:    (id, d)  => api.post(`/meal-plans/${id}/log-day/`, d).then((r) => r.data),
  summary:   (id)     => api.get(`/meal-plans/${id}/summary/`).then((r) => r.data),
  addItem:   (planId, d)  => api.post(`/meal-plans/${planId}/items/`, d).then((r) => r.data),
  updateItem:(itemId, d)  => api.patch(`/meal-plan-items/${itemId}/`, d).then((r) => r.data),
  removeItem:(itemId)     => api.delete(`/meal-plan-items/${itemId}/`),
};

// Progress analytics
export const progressApi = {
  strengthHistory: (exerciseId, days = 90) =>
    api.get("/workouts/strength-history/", { params: { exercise_id: exerciseId, days } }).then((r) => r.data),
  volumeByMuscle: (weeks = 12) =>
    api.get("/workouts/volume-by-muscle/", { params: { weeks } }).then((r) => r.data),
  activityHeatmap: (days = 365) =>
    api.get("/workouts/activity-heatmap/", { params: { days } }).then((r) => r.data),
  bodyComposition: (days = 90) =>
    api.get("/measurements/body-composition/", { params: { days } }).then((r) => r.data),
};

// Integrations
export const integrationsApi = {
  list: () => api.get("/integrations/").then((r) => r.data),
  // Strava (OAuth redirect flow)
  stravaConnectUrl: () => `${api.defaults.baseURL}/integrations/strava/connect/`,
  stravaDisconnect: () => api.delete("/integrations/strava/disconnect/"),
  // Intervals.icu (API key flow)
  intervalsConnect: (data) => api.post("/integrations/intervals/connect/", data).then((r) => r.data),
  intervalsDisconnect: () => api.delete("/integrations/intervals/disconnect/"),
  intervalsSync: (data) => api.post("/integrations/intervals/sync/", data).then((r) => r.data),
};

// Levels / XP
export const levelsApi = {
  profile:      ()       => api.get("/levels/profile/").then((r) => r.data),
  transactions: (params) => api.get("/levels/transactions/", { params }).then((r) => r.data),
  challenges:   ()       => api.get("/levels/challenges/").then((r) => r.data),
  leaderboard:  ()       => api.get("/levels/leaderboard/").then((r) => r.data),
  prestige:     ()       => api.post("/levels/prestige/").then((r) => r.data),
};

// Fitness Reports
export const reportsApi = {
  list: () => api.get("/reports/").then((r) => r.data.results ?? r.data),
  trigger: (period_type) =>
    api.post("/reports/trigger/", { period_type }).then((r) => r.data),
};

// Notifications
export const notificationsApi = {
  list: (params) => api.get("/notifications/", { params }).then((r) => r.data),
  unreadCount: () => api.get("/notifications/unread_count/").then((r) => r.data),
  markRead: (id) => api.patch(`/notifications/${id}/`, { read: true }).then((r) => r.data),
  markAllRead: () => api.post("/notifications/mark_all_read/").then((r) => r.data),
};
