/**
 * Dashboard spec — authenticated.
 * Verifies stat cards, workout calendar card, and active goals section.
 */

const { expect }        = require('@playwright/test');
const { test }          = require('../fixtures/test');
const { DashboardPage } = require('../pages/DashboardPage');

test.describe('Dashboard', () => {
  test('renders the stat cards', async ({ page }) => {
    const dp = new DashboardPage(page);
    await dp.goto();

    for (const label of ['Workouts this week', 'Minutes this week', 'Current streak']) {
      await expect(page.getByText(label).first()).toBeVisible({ timeout: 10_000 });
    }
  });

  test('workout calendar section renders', async ({ page }) => {
    const dp = new DashboardPage(page);
    await dp.goto();

    await expect(page.getByText('Workouts (last 14 days)')).toBeVisible({ timeout: 10_000 });
  });

  test('active goals section renders', async ({ page }) => {
    const dp = new DashboardPage(page);
    await dp.goto();

    await expect(page.getByRole('heading', { name: 'Active goals', exact: true })).toBeVisible({ timeout: 10_000 });
  });
});
