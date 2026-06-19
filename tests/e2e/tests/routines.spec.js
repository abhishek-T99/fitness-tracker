/**
 * Routines spec — authenticated.
 * Covers create → verify in list → delete lifecycle.
 */

const { expect }          = require('@playwright/test');
const { test }            = require('../fixtures/test');
const { RoutinesPage }    = require('../pages/RoutinesPage');
const { WorkoutEditorPage } = require('../pages/WorkoutEditorPage');
const { deleteAllRoutines } = require('../helpers/api');
const data                = require('../helpers/data');

test.beforeEach(async () => {
  await deleteAllRoutines();
});

test.afterEach(async () => {
  await deleteAllRoutines();
});

// ── List page ─────────────────────────────────────────────────────────────────

test.describe('Routines list', () => {
  test('shows heading and "New routine" button', async ({ page }) => {
    const rp = new RoutinesPage(page);
    await rp.goto();
    await expect(rp.heading).toBeVisible();
    await expect(rp.newRoutineButton).toBeVisible();
  });

  test('shows empty state when no routines exist', async ({ page }) => {
    const rp = new RoutinesPage(page);
    await rp.goto();
    await expect(rp.emptyStateText).toBeVisible();
  });

  test('"New routine" button navigates to the editor', async ({ page }) => {
    const rp = new RoutinesPage(page);
    await rp.goto();
    await rp.clickNewRoutine();
    await expect(page).toHaveURL(/\/routines\/new/);
  });
});

// ── Create routine ────────────────────────────────────────────────────────────

test.describe('Create routine', () => {
  test('creates a routine and it appears in the list', async ({ page }) => {
    const routineName = `PW Routine ${data.uid()}`;

    // Navigate to the routine editor
    await page.goto('/routines/new');
    await page.getByRole('heading', { name: /new routine|routine/i }).waitFor({ timeout: 10_000 });

    // The name input has placeholder "Upper body strength"
    const nameInput = page.getByPlaceholder('Upper body strength');
    await nameInput.fill(routineName);

    // Add one exercise
    const addExBtn = page.getByRole('button', { name: /add exercise/i });
    await addExBtn.click();
    const searchInput = page.getByPlaceholder(/search/i);
    await searchInput.waitFor({ timeout: 8_000 });
    await searchInput.fill('squat');
    await page.getByText('Add →').first().waitFor({ timeout: 8_000 });
    await page.getByText('Add →').first().click();

    // Save
    await page.getByRole('button', { name: /save|create/i }).first().click();

    // Should redirect to /routines or /routines/:id
    await expect(page).toHaveURL(/\/routines/, { timeout: 15_000 });

    // Navigate to list and verify
    const rp = new RoutinesPage(page);
    await rp.goto();
    await expect(page.getByText(routineName)).toBeVisible({ timeout: 8_000 });
  });
});

// ── Delete routine ────────────────────────────────────────────────────────────

test.describe('Delete routine', () => {
  test('deletes a routine via API and it disappears from the list', async ({ page, api }) => {
    // Create via API for speed
    const exRes = await api.get('/exercises/', { params: { page_size: 1 } });
    const exId  = exRes.data.results[0].id;

    const name = `PW Del Routine ${data.uid()}`;
    await api.post('/workouts/routines/', {
      name,
      items: [{ exercise: exId, order: 0, target_sets: 3, target_reps: 10 }],
    });

    const rp = new RoutinesPage(page);
    await rp.goto();
    await expect(page.getByText(name)).toBeVisible({ timeout: 8_000 });

    await rp.deleteRoutine(name);

    await expect(page.getByText(name)).not.toBeVisible({ timeout: 8_000 });
  });
});
