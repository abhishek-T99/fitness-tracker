/**
 * Node-side API helpers used in global-setup and test beforeEach/afterEach
 * hooks for creating and cleaning up test data without going through the UI.
 */

const axios = require('axios');

const API_URL = process.env.API_URL || 'http://localhost:8000/api/v1';

const TEST_USER = {
  username: 'pw_testuser',
  password: 'TestPass123!',
  email:    'pw_testuser@fittrack.test',
};

/** Returns a fresh access token for the test user. */
async function getToken() {
  const { data } = await axios.post(`${API_URL}/auth/login/`, {
    username: TEST_USER.username,
    password: TEST_USER.password,
  });
  return data.access;
}

/** Returns an axios instance pre-configured with the test user's Bearer token. */
async function authedClient() {
  const token = await getToken();
  return axios.create({
    baseURL: API_URL,
    headers: { Authorization: `Bearer ${token}` },
  });
}

// ── Teardown helpers ──────────────────────────────────────────────────────────

async function deleteAllGoals() {
  const client = await authedClient();
  const { data } = await client.get('/goals/');
  const goals = data.results ?? data;
  await Promise.all(goals.map((g) => client.delete(`/goals/${g.id}/`).catch(() => {})));
}

async function deleteAllWorkouts() {
  const client = await authedClient();
  const { data } = await client.get('/workouts/');
  const workouts = data.results ?? [];
  await Promise.all(workouts.map((w) => client.delete(`/workouts/${w.id}/`).catch(() => {})));
}

/**
 * Delete all meals (and optionally water logs) for a given date.
 * Defaults to today if no date is supplied.
 */
async function deleteAllMeasurements() {
  const client = await authedClient();
  const { data } = await client.get('/measurements/');
  const items = data.results ?? data;
  await Promise.all(items.map((m) => client.delete(`/measurements/${m.id}/`).catch(() => {})));
}

async function deleteAllReminders() {
  const client = await authedClient();
  const { data } = await client.get('/reminders/');
  const items = data.results ?? data;
  await Promise.all(items.map((r) => client.delete(`/reminders/${r.id}/`).catch(() => {})));
}

async function deleteAllRoutines() {
  const client = await authedClient();
  const { data } = await client.get('/workouts/routines/');
  const items = data.results ?? data;
  await Promise.all(items.map((r) => client.delete(`/workouts/routines/${r.id}/`).catch(() => {})));
}

async function deleteAllPosts() {
  const client = await authedClient();
  const { data } = await client.get('/social/posts/');
  const posts = data.results ?? data;
  await Promise.all(posts.map((p) => client.delete(`/social/posts/${p.id}/`).catch(() => {})));
}

async function deleteNutritionForDate(date) {
  const d      = date ?? new Date().toISOString().slice(0, 10);
  const client = await authedClient();

  const [mealsRes, waterRes] = await Promise.all([
    client.get('/nutrition/meals/', { params: { date: d } }),
    client.get('/nutrition/water/', { params: { date: d } }),
  ]);

  const meals = mealsRes.data.results ?? mealsRes.data;
  const water = waterRes.data.results ?? waterRes.data;

  await Promise.all([
    ...meals.map((m) => client.delete(`/nutrition/meals/${m.id}/`).catch(() => {})),
    ...water.map((w) => client.delete(`/nutrition/water/${w.id}/`).catch(() => {})),
  ]);
}

module.exports = {
  TEST_USER,
  authedClient,
  deleteAllGoals,
  deleteAllWorkouts,
  deleteAllMeasurements,
  deleteAllReminders,
  deleteAllRoutines,
  deleteAllPosts,
  deleteNutritionForDate,
};
