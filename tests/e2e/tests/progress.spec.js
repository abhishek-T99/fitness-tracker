/**
 * Progress spec — authenticated.
 * Verifies the heatmap, tab navigation, and chart container rendering.
 */

const { expect }     = require('@playwright/test');
const { test }       = require('../fixtures/test');
const { ProgressPage } = require('../pages/ProgressPage');

test.describe('Progress page structure', () => {
  test('shows heading', async ({ page }) => {
    const pp = new ProgressPage(page);
    await pp.goto();
    await expect(pp.heading).toBeVisible();
  });

  test('activity heatmap calendar renders', async ({ page }) => {
    const pp = new ProgressPage(page);
    await pp.goto();

    // WorkoutCalendar section is identified by its heading
    await expect(page.getByRole('heading', { name: 'Workout Activity' })).toBeVisible({ timeout: 10_000 });
  });

  test('tab buttons are visible', async ({ page }) => {
    const pp = new ProgressPage(page);
    await pp.goto();

    await expect(pp.bodyTab).toBeVisible();
    await expect(pp.strengthTab).toBeVisible();
    await expect(pp.volumeTab).toBeVisible();
  });
});

test.describe('Progress tabs', () => {
  test('Body tab renders a chart or placeholder', async ({ page }) => {
    const pp = new ProgressPage(page);
    await pp.goto();
    await pp.switchTab('body');

    // Either a recharts wrapper or the placeholder text shown when no measurements exist
    const chartOrEmpty = page
      .locator('.recharts-wrapper')
      .or(page.getByText(/log your weight|record body fat|no data/i));
    await expect(chartOrEmpty.first()).toBeVisible({ timeout: 10_000 });
  });

  test('Strength tab renders an exercise search input', async ({ page }) => {
    const pp = new ProgressPage(page);
    await pp.goto();
    await pp.switchTab('strength');

    // The strength tab has a search/select for exercises
    const exerciseSearch = page
      .getByPlaceholder(/search|exercise/i)
      .or(page.locator('select').first());
    await expect(exerciseSearch.first()).toBeVisible({ timeout: 8_000 });
  });

  test('Volume tab renders a chart or placeholder', async ({ page }) => {
    const pp = new ProgressPage(page);
    await pp.goto();
    await pp.switchTab('volume');

    const chartOrEmpty = page
      .locator('.recharts-wrapper')
      .or(page.getByText(/complete workouts|no data/i));
    await expect(chartOrEmpty.first()).toBeVisible({ timeout: 10_000 });
  });
});
