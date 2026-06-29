/**
 * Misc spec — cross-cutting concerns.
 * Covers dark mode toggle, skeleton loaders, pagination, and notification bell.
 */

const { expect }            = require('@playwright/test');
const { test }              = require('../fixtures/test');
const { deleteAllWorkouts } = require('../helpers/api');
const data                  = require('../helpers/data');

// ── Dark mode ─────────────────────────────────────────────────────────────────

test.describe('Dark mode', () => {
  test('toggle switches the dark class on the html element', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    const isDark = await page.evaluate(() =>
      document.documentElement.classList.contains('dark')
    );

    const label = isDark ? 'Switch to light theme' : 'Switch to dark theme';
    await page.getByRole('button', { name: label }).click();

    if (isDark) {
      await expect(page.locator('html')).not.toHaveClass(/\bdark\b/);
    } else {
      await expect(page.locator('html')).toHaveClass(/\bdark\b/);
    }
  });
});

// ── Skeleton loaders ──────────────────────────────────────────────────────────

test.describe('Skeleton loaders', () => {
  test('shows animated skeleton while workouts are loading', async ({ page }) => {
    let resolveRoute;
    const routeGate = new Promise((r) => { resolveRoute = r; });

    await page.route('**/api/v1/workouts/**', async (route) => {
      await routeGate;
      await route.continue();
    });

    await page.goto('/workouts');

    // Skeletons should be visible while the route is blocked
    await expect(
      page.locator('[class*="animate-pulse"]').first()
    ).toBeVisible({ timeout: 5_000 });

    resolveRoute();
  });
});

// ── Pagination ────────────────────────────────────────────────────────────────

test.describe('Pagination', () => {
  test.afterEach(async () => {
    await deleteAllWorkouts();
  });

  test('pagination bar appears when workout count exceeds page size', async ({ page, api }) => {
    const exRes = await api.get('/exercises/', { params: { page_size: 1 } });
    const exId  = exRes.data.results[0].id;

    // Page size is 12 — create 13 to trigger pagination
    for (let i = 0; i < 13; i++) {
      await api.post('/workouts/', {
        name:       `PW Page ${i} ${Date.now().toString(36)}`,
        started_at: new Date().toISOString(),
        status:     'completed',
        exercises:  [{
          exercise: exId,
          order:    0,
          sets:     [{ set_number: 1, reps: 8, weight: 60, is_warmup: false, completed: true }],
        }],
      });
    }

    await page.goto('/workouts');

    // "Showing 1–12 of 13" label from the Pagination component
    await expect(
      page.getByText(/of 13/i)
    ).toBeVisible({ timeout: 15_000 });
  });
});

// ── Notification bell ─────────────────────────────────────────────────────────

test.describe('Notification bell', () => {
  test('clicking the bell opens the notifications panel', async ({ page }) => {
    await page.goto('/dashboard');

    // Toast notifications (e.g. "Level Up!") can land over the bell and
    // intercept the click. Strip any active toasts before the click so a
    // real user-style click reaches the bell — mousedown + click is needed
    // because the panel uses an outside-mousedown listener to auto-close.
    await page.locator('[role="status"]').evaluateAll((els) => {
      els.forEach((el) => el.remove());
    });
    await page.getByRole('button', { name: 'Notifications' }).click();

    // Dropdown header
    await expect(
      page.getByRole('heading', { name: 'Notifications' })
    ).toBeVisible({ timeout: 5_000 });
  });
});
