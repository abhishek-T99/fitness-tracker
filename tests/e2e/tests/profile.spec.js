/**
 * Profile spec — authenticated.
 * Covers profile info display, updating fields, and changing password.
 */

const { expect }   = require('@playwright/test');
const { test }     = require('../fixtures/test');
const { TEST_USER } = require('../helpers/api');

// ── Profile page ──────────────────────────────────────────────────────────────

test.describe('Profile page', () => {
  test('renders the profile heading', async ({ page }) => {
    await page.goto('/profile');
    await expect(page.getByRole('heading', { name: 'Profile & settings', exact: true })).toBeVisible();
  });

  test('displays the logged-in user email', async ({ page }) => {
    await page.goto('/profile');
    await expect(page.getByText(TEST_USER.email)).toBeVisible({ timeout: 10_000 });
  });

  test('shows all account form fields', async ({ page }) => {
    await page.goto('/profile');
    await expect(page.locator('[name="first_name"]')).toBeVisible();
    await expect(page.locator('[name="last_name"]')).toBeVisible();
    await expect(page.locator('[name="email"]')).toBeVisible();
  });
});

// ── Update profile ────────────────────────────────────────────────────────────

test.describe('Update profile', () => {
  // Reset first_name back to "Playwright" after each test
  test.afterEach(async ({ api }) => {
    await api.patch('/auth/me/', { first_name: 'Playwright', last_name: 'Tester' });
  });

  test('saves updated name and shows success toast', async ({ page }) => {
    await page.goto('/profile');
    await page.locator('[name="first_name"]').fill('UpdatedName');

    // Find and click the save button (first one in the Account card)
    await page.getByRole('button', { name: /save changes/i }).first().click();

    await expect(page.getByText('Profile updated')).toBeVisible({ timeout: 8_000 });
  });

  test('updated name reflects in the header after save', async ({ page }) => {
    await page.goto('/profile');
    await page.locator('[name="first_name"]').fill('QATester');
    await page.getByRole('button', { name: /save changes/i }).first().click();
    await page.getByText('Profile updated').waitFor({ timeout: 8_000 });

    // The top-right header shows the first name
    await expect(page.getByText('QATester').first()).toBeVisible();
  });
});

// ── Change password ───────────────────────────────────────────────────────────

test.describe('Change password', () => {
  test('change password section is visible on the profile page', async ({ page }) => {
    await page.goto('/profile');
    await expect(page.getByText(/change password/i)).toBeVisible({ timeout: 10_000 });
  });

  test('shows error with wrong current password', async ({ page }) => {
    await page.goto('/profile');

    // Fill the change-password form
    await page.locator('[name="old_password"]').fill('WrongOldPass999!');
    await page.locator('[name="new_password"]').fill('NewPass123!');
    await page.getByRole('button', { name: /update password/i }).click();

    await expect(page.getByText(/incorrect|wrong|invalid/i)).toBeVisible({ timeout: 8_000 });
  });
});
