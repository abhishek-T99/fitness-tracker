/**
 * Navigation spec — authenticated.
 * Verifies that every sidebar link renders the correct page and that global
 * routing (redirects, protected routes) behaves correctly.
 */

const { expect } = require('@playwright/test');
const { test }   = require('../fixtures/test');

// Sidebar links defined in AppLayout.jsx
const NAV_LINKS = [
  { href: '/dashboard',    heading: /^Hi,/i             },
  { href: '/workouts',     heading: 'Workouts'         },
  { href: '/routines',     heading: 'Routines'         },
  { href: '/exercises',    heading: 'Exercise library' },
  { href: '/nutrition',    heading: 'Nutrition'        },
  { href: '/meal-plan',    heading: 'Meal Plan'        },
  { href: '/progress',     heading: 'Progress'         },
  { href: '/measurements', heading: 'Measurements'     },
  { href: '/goals',        heading: 'Goals'            },
  { href: '/social',       heading: 'Social'           },
  { href: '/achievements', heading: 'Achievements'     },
  { href: '/leaderboard',  heading: 'Leaderboard'      },
  { href: '/reminders',    heading: 'Reminders'        },
];

// ── Redirects ─────────────────────────────────────────────────────────────────

test.describe('Routing', () => {
  test('/ redirects to /dashboard', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('unknown route redirects to /dashboard', async ({ page }) => {
    await page.goto('/this-does-not-exist');
    await expect(page).toHaveURL(/\/dashboard/);
  });
});

// ── Sidebar navigation ────────────────────────────────────────────────────────

test.describe('Sidebar navigation', () => {
  test('sidebar is visible on the dashboard', async ({ page }) => {
    await page.goto('/dashboard');
    // AppLayout renders a <nav> with navItems
    await expect(page.getByRole('link', { name: 'Workouts' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Goals' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Nutrition' })).toBeVisible();
  });

  test("displays the logged-in user's avatar / initials in the sidebar", async ({ page }) => {
    await page.goto('/dashboard');
    // The test user has first_name "Playwright" → initials "P"
    // UserAvatar renders an <img> or a div with the initial letter
    const avatarOrInitial = page
      .locator('[class*="rounded-full"]')
      .filter({ hasText: /^P$/i })
      .or(page.locator('img[alt="Playwright"]'));
    await expect(avatarOrInitial.first()).toBeVisible({ timeout: 10_000 });
  });
});

// ── Every page loads ─────────────────────────────────────────────────────────

for (const { href, heading } of NAV_LINKS) {
  test(`navigates to ${href} and renders the "${heading}" heading`, async ({ page }) => {
    await page.goto(href);
    await expect(
      page.getByRole('heading', { name: heading, exact: typeof heading === 'string' })
    ).toBeVisible({ timeout: 15_000 });
  });
}
