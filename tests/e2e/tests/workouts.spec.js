/**
 * Workouts spec — authenticated (storageState applied via playwright.config.js).
 * Covers the create → view → delete lifecycle for workout sessions.
 */

const { expect }             = require('@playwright/test');
const { test }               = require('../fixtures/test');
const { WorkoutsPage }       = require('../pages/WorkoutsPage');
const { WorkoutEditorPage }  = require('../pages/WorkoutEditorPage');
const { WorkoutDetailPage }  = require('../pages/WorkoutDetailPage');
const { deleteAllWorkouts }  = require('../helpers/api');
const data                   = require('../helpers/data');

test.beforeEach(async () => {
  // Clean slate — remove any workouts left by a previous test run
  await deleteAllWorkouts();
});

test.afterEach(async () => {
  await deleteAllWorkouts();
});

// ── List page ─────────────────────────────────────────────────────────────────

test.describe('Workouts list', () => {
  test('shows the page heading', async ({ page }) => {
    const workoutsPage = new WorkoutsPage(page);
    await workoutsPage.goto();
    await expect(workoutsPage.heading).toBeVisible();
  });

  test('shows empty state when there are no workouts', async ({ page }) => {
    const workoutsPage = new WorkoutsPage(page);
    await workoutsPage.goto();
    await expect(workoutsPage.emptyStateTitle).toBeVisible();
  });

  test('Log workout button navigates to the editor', async ({ page }) => {
    const workoutsPage = new WorkoutsPage(page);
    await workoutsPage.goto();
    await workoutsPage.clickLogWorkout();
    await expect(page).toHaveURL(/\/workouts\/new/);
  });
});

// ── Create workout ────────────────────────────────────────────────────────────

test.describe('Create workout', () => {
  test('creates a workout and lands on the detail page', async ({ page }) => {
    const workoutsPage = new WorkoutsPage(page);
    const editorPage   = new WorkoutEditorPage(page);
    const name         = data.workoutName();

    await workoutsPage.goto();
    await workoutsPage.clickLogWorkout();
    await editorPage.waitForLoad();

    await editorPage.fillName(name);
    await editorPage.addExercise('bench');   // seeds include "Bench Press"
    await editorPage.save();

    // After save the app redirects to /workouts/:id
    await expect(page).toHaveURL(/\/workouts\/\d+/, { timeout: 15_000 });
  });

  test('shows toast error when trying to save with no exercises', async ({ page }) => {
    const workoutsPage = new WorkoutsPage(page);
    const editorPage   = new WorkoutEditorPage(page);

    await workoutsPage.goto();
    await workoutsPage.clickLogWorkout();
    await editorPage.waitForLoad();

    await editorPage.fillName('Empty workout');
    await editorPage.save();

    await expect(page.getByText(/add at least one exercise/i)).toBeVisible();
    // Should stay on the editor, not navigate away
    await expect(page).toHaveURL(/\/workouts\/new/);
  });

  test('created workout appears in the workouts list', async ({ page }) => {
    const editorPage   = new WorkoutEditorPage(page);
    const workoutsPage = new WorkoutsPage(page);
    const name         = data.workoutName();

    // Create via UI
    await page.goto('/workouts/new');
    await editorPage.waitForLoad();
    await editorPage.fillName(name);
    await editorPage.addExercise('squat');
    await editorPage.save();
    await expect(page).toHaveURL(/\/workouts\/\d+/, { timeout: 15_000 });

    // Navigate back to list and confirm the card is visible
    await workoutsPage.goto();
    await expect(page.getByText(name)).toBeVisible();
  });
});

// ── Workout detail ────────────────────────────────────────────────────────────

test.describe('Workout detail', () => {
  test('clicking a workout card opens its detail page', async ({ page, api }) => {
    // Create workout via API for speed
    const name = data.workoutName();

    // Get an exercise id first
    const exRes  = await api.get('/exercises/', { params: { page_size: 1 } });
    const exId   = exRes.data.results[0].id;

    const { data: workout } = await api.post('/workouts/', {
      name,
      started_at: new Date().toISOString(),
      status:     'completed',
      exercises:  [{
        exercise: exId,
        order:    0,
        sets:     [{ set_number: 1, reps: 8, weight: 60, is_warmup: false, completed: true }],
      }],
    });

    const workoutsPage = new WorkoutsPage(page);
    await workoutsPage.goto();
    await page.getByText(name).click();
    await expect(page).toHaveURL(new RegExp(`/workouts/${workout.id}`));
  });
});

// ── Workout detail page content ───────────────────────────────────────────────

test.describe('Workout detail page content', () => {
  test('shows the workout name, Edit link, and Delete button', async ({ page, api }) => {
    const exRes  = await api.get('/exercises/', { params: { page_size: 1 } });
    const exId   = exRes.data.results[0].id;
    const name   = data.workoutName();

    const { data: workout } = await api.post('/workouts/', {
      name,
      started_at: new Date().toISOString(),
      status:     'completed',
      exercises:  [{
        exercise: exId,
        order:    0,
        sets:     [{ set_number: 1, reps: 8, weight: 60, is_warmup: false, completed: true }],
      }],
    });

    await page.goto(`/workouts/${workout.id}`);
    await expect(page.getByText(name).first()).toBeVisible({ timeout: 10_000 });

    const dp = new WorkoutDetailPage(page);
    await expect(dp.editButton).toBeVisible();
    await expect(dp.deleteButton).toBeVisible();
  });
});

// ── Edit workout ──────────────────────────────────────────────────────────────

test.describe('Edit workout', () => {
  test('opens the editor pre-filled and saves an updated name', async ({ page, api }) => {
    const exRes  = await api.get('/exercises/', { params: { page_size: 1 } });
    const exId   = exRes.data.results[0].id;
    const name   = data.workoutName();

    const { data: workout } = await api.post('/workouts/', {
      name,
      started_at: new Date().toISOString(),
      status:     'completed',
      exercises:  [{
        exercise: exId,
        order:    0,
        sets:     [{ set_number: 1, reps: 8, weight: 60, is_warmup: false, completed: true }],
      }],
    });

    await page.goto(`/workouts/${workout.id}/edit`);
    await page.getByRole('heading', { name: /edit workout/i }).waitFor({ timeout: 10_000 });

    const updatedName = `${name} Edited`;
    await page.getByPlaceholder('Push day').clear();
    await page.getByPlaceholder('Push day').fill(updatedName);

    await page.getByRole('button', { name: /update workout/i }).click();

    await expect(page.getByText('Workout updated')).toBeVisible({ timeout: 8_000 });
  });
});

// ── Delete workout from detail ────────────────────────────────────────────────

test.describe('Delete workout from detail', () => {
  test('deletes a workout and redirects to the list', async ({ page, api }) => {
    const exRes  = await api.get('/exercises/', { params: { page_size: 1 } });
    const exId   = exRes.data.results[0].id;
    const name   = data.workoutName();

    const { data: workout } = await api.post('/workouts/', {
      name,
      started_at: new Date().toISOString(),
      status:     'completed',
      exercises:  [{
        exercise: exId,
        order:    0,
        sets:     [{ set_number: 1, reps: 8, weight: 60, is_warmup: false, completed: true }],
      }],
    });

    await page.goto(`/workouts/${workout.id}`);
    await page.getByText(name).first().waitFor({ timeout: 10_000 });

    const dp = new WorkoutDetailPage(page);
    await dp.deleteWithConfirm();

    await expect(page).toHaveURL(/\/workouts$/, { timeout: 10_000 });
    await expect(page.getByText('Workout deleted')).toBeVisible({ timeout: 8_000 });
  });
});

