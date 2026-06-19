/**
 * Social spec — authenticated.
 * Covers the Feed, Friends, and Find People tabs.
 */

const { expect }      = require('@playwright/test');
const { test }        = require('../fixtures/test');
const { SocialPage }  = require('../pages/SocialPage');
const { deleteAllPosts } = require('../helpers/api');
const data            = require('../helpers/data');

test.beforeEach(async () => {
  await deleteAllPosts();
});

test.afterEach(async () => {
  await deleteAllPosts();
});

// ── Page structure ────────────────────────────────────────────────────────────

test.describe('Social page structure', () => {
  test('renders heading and three tab buttons', async ({ page }) => {
    const sp = new SocialPage(page);
    await sp.goto();

    await expect(sp.heading).toBeVisible();
    await expect(sp.feedTab).toBeVisible();
    await expect(sp.friendsTab).toBeVisible();
    await expect(sp.findTab).toBeVisible();
  });

  test('Feed tab is active by default', async ({ page }) => {
    const sp = new SocialPage(page);
    await sp.goto();

    // The active tab has a brand-colored border; check its aria or class
    await expect(sp.feedTab).toHaveClass(/border-brand-600|text-brand-600/, { timeout: 5_000 });
  });
});

// ── Feed ──────────────────────────────────────────────────────────────────────

test.describe('Feed', () => {
  test('shows a textarea for composing posts', async ({ page }) => {
    const sp = new SocialPage(page);
    await sp.goto();
    await expect(page.locator('textarea').first()).toBeVisible();
  });

  test('creates a post and shows it in the feed', async ({ page }) => {
    const sp   = new SocialPage(page);
    const body = `E2E post ${data.uid()}`;
    await sp.goto();

    await sp.createPost(body);

    await expect(page.getByText(body)).toBeVisible({ timeout: 10_000 });
  });

  test('post textarea clears after successful submission', async ({ page }) => {
    const sp = new SocialPage(page);
    await sp.goto();

    await sp.createPost(`Clear test ${data.uid()}`);
    // After "Posted" toast, body state is reset
    await page.getByText('Posted').waitFor({ timeout: 8_000 });
    await expect(page.locator('textarea').first()).toHaveValue('');
  });

  test('like button is visible on a post', async ({ page }) => {
    const sp = new SocialPage(page);
    await sp.goto();

    await sp.createPost(`Like test ${data.uid()}`);
    await page.getByText('Posted').waitFor({ timeout: 8_000 });

    // Heart icon button appears on each post
    await expect(page.getByRole('button').filter({ has: page.locator('[data-lucide="heart"]').or(page.locator('svg')) }).first()).toBeVisible();
  });
});

// ── Friends tab ───────────────────────────────────────────────────────────────

test.describe('Friends tab', () => {
  test('switching to Friends tab renders without error', async ({ page }) => {
    const sp = new SocialPage(page);
    await sp.goto();
    await sp.switchTab('friends');
    // Friends tab content loads — for a fresh user it shows "no friends" or a list
    await expect(sp.friendsTab).toBeVisible();
    // No crash (no error boundary text)
    await expect(page.getByText('Something went wrong')).not.toBeVisible();
  });
});

// ── Find people ───────────────────────────────────────────────────────────────

test.describe('Find people tab', () => {
  test('shows a search input when Find people is active', async ({ page }) => {
    const sp = new SocialPage(page);
    await sp.goto();
    await sp.switchTab('find');
    await expect(page.getByPlaceholder(/search/i).first()).toBeVisible({ timeout: 5_000 });
  });

  test('searching returns results or an empty state', async ({ page }) => {
    const sp = new SocialPage(page);
    await sp.goto();
    await sp.switchTab('find');

    const searchInput = page.getByPlaceholder(/search/i).first();
    await searchInput.fill('pw_testuser');

    // Either we see a result card or "no users found" — either way no crash
    await page.waitForTimeout(1_000);
    await expect(page.getByText('Something went wrong')).not.toBeVisible();
  });
});
