/**
 * Achievements spec — authenticated.
 * Verifies catalog display, locked badge styling, and streak widget.
 */

const { expect }          = require('@playwright/test');
const { test }            = require('../fixtures/test');
const { AchievementsPage } = require('../pages/AchievementsPage');

test.describe('Achievements catalog', () => {
  test('shows the page heading', async ({ page }) => {
    const ap = new AchievementsPage(page);
    await ap.goto();
    await expect(ap.heading).toBeVisible();
  });

  test('renders achievement category sections from seeded data', async ({ page }) => {
    const ap = new AchievementsPage(page);
    await ap.goto();

    // Seeded achievements have these categories (from CATEGORIES constant)
    for (const label of ['Workout Milestones', 'Streak']) {
      await expect(
        page.getByRole('heading', { name: label, exact: true })
      ).toBeVisible({ timeout: 10_000 });
    }
  });

  test('badge cards are present in the catalog', async ({ page }) => {
    const ap = new AchievementsPage(page);
    await ap.goto();

    // Badges render as rounded-2xl flex-col cards; at least one should exist
    const cards = ap.badgeCards();
    await expect(cards.first()).toBeVisible({ timeout: 10_000 });
    const count = await cards.count();
    expect(count).toBeGreaterThan(0);
  });

  test('locked badges appear with reduced opacity / grayscale class', async ({ page }) => {
    const ap = new AchievementsPage(page);
    await ap.goto();

    // New users have no achievements — all badges are locked
    const lockedBadge = page.locator('[class*="opacity-50"]').first();
    await expect(lockedBadge).toBeVisible({ timeout: 10_000 });
  });
});

test.describe('Streak widget', () => {
  test('streak section is visible', async ({ page }) => {
    const ap = new AchievementsPage(page);
    await ap.goto();

    // The achievements page renders streak info via achievementsApi.streak()
    // For a new user the streak value is 0 but the widget renders
    await expect(page.getByText(/streak|day/i).first()).toBeVisible({ timeout: 10_000 });
  });
});
