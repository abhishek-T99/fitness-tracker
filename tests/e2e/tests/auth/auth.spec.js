/**
 * Auth spec — runs WITHOUT pre-seeded storageState.
 * Tests the login and register flows from an unauthenticated perspective.
 */

const { test, expect } = require('@playwright/test');
const { LoginPage }    = require('../../pages/LoginPage');
const { RegisterPage } = require('../../pages/RegisterPage');
const { TEST_USER }    = require('../../helpers/api');
const data             = require('../../helpers/data');

// ── Login ─────────────────────────────────────────────────────────────────────

test.describe('Login', () => {
  test('redirects unauthenticated user from /dashboard to /login', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login/);
  });

  test('redirects unauthenticated user from / to /login', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/\/login/);
  });

  test('shows validation errors when form is submitted empty', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();

    await loginPage.submitButton.click();

    await expect(page.getByText('Username is required')).toBeVisible();
    await expect(page.getByText('Password is required')).toBeVisible();
  });

  test('shows error toast on wrong credentials', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();

    await loginPage.login('nonexistent_user', 'WrongPassword1!');

    // Django DRF returns a detail message; axios interceptor surfaces it
    await expect(page.getByText(/login failed|no active account|invalid/i)).toBeVisible({
      timeout: 8_000,
    });
    // Should stay on /login
    await expect(page).toHaveURL(/\/login/);
  });

  test('logs in successfully with valid credentials and lands on dashboard', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();

    await loginPage.login(TEST_USER.username, TEST_USER.password);

    await expect(page).toHaveURL(/\/dashboard/, { timeout: 15_000 });
    await expect(page.getByRole('heading', { name: /^Hi,/i })).toBeVisible({ timeout: 10_000 });
  });

  test('remembers the originally requested page and redirects there after login', async ({ page }) => {
    // Try to visit a protected page first
    await page.goto('/goals');
    await expect(page).toHaveURL(/\/login/);

    const loginPage = new LoginPage(page);
    await loginPage.login(TEST_USER.username, TEST_USER.password);

    // Should arrive at /goals, not /dashboard
    await expect(page).toHaveURL(/\/goals/, { timeout: 15_000 });
  });

  test('navigates to register page from login page', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();

    await loginPage.registerLink.click();

    await expect(page).toHaveURL(/\/register/);
    await expect(page.getByRole('heading', { name: /create your account/i })).toBeVisible();
  });
});

// ── Register ─────────────────────────────────────────────────────────────────

test.describe('Register', () => {
  test('shows validation errors when form is submitted empty', async ({ page }) => {
    const registerPage = new RegisterPage(page);
    await registerPage.goto();

    await registerPage.submitButton.click();

    // react-hook-form fires inline errors
    await expect(page.locator('[name="username"]')).toBeVisible();
    // At least one validation error message should appear
    await expect(page.locator('.text-rose-600').first()).toBeVisible();
  });

  test('shows error when passwords do not match', async ({ page }) => {
    const registerPage = new RegisterPage(page);
    await registerPage.goto();

    const u = data.registerUser();
    await registerPage.register({ ...u, password_confirm: 'DifferentPass1!' });

    await expect(page.getByText('Passwords do not match')).toBeVisible();
  });

  test('registers a new user and redirects to check-email page', async ({ page }) => {
    const registerPage = new RegisterPage(page);
    await registerPage.goto();

    const u = data.registerUser();
    await registerPage.register(u);

    // On success the app navigates to /check-email
    await expect(page).toHaveURL(/\/check-email/, { timeout: 15_000 });
  });

  test('shows an error when username is already taken', async ({ page }) => {
    const registerPage = new RegisterPage(page);
    await registerPage.goto();

    // Use the deterministic test user's username
    const u = data.registerUser();
    await registerPage.register({ ...u, username: TEST_USER.username });

    // Backend returns a 400; the frontend shows a toast.error with the server message
    await expect(page.getByText(/already.*exist|duplicate|taken|username/i)).toBeVisible({ timeout: 8_000 });
  });
});

// ── Logout ────────────────────────────────────────────────────────────────────

test.describe('Logout', () => {
  test('clears session and redirects to /login', async ({ page }) => {
    // Auth spec has no storageState — must log in via UI first
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login(TEST_USER.username, TEST_USER.password);
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 15_000 });

    // Wait for the "Welcome back!" toast to disappear
    await page.getByText('Welcome back!').waitFor({ state: 'hidden', timeout: 10_000 }).catch(() => {});

    // Dismiss LevelUpModal if login/first-login XP triggered it
    // (auth spec uses vanilla @playwright/test — no addLocatorHandler registered)
    const keepGoingBtn = page.getByRole('button', { name: 'Keep Going!' });
    await keepGoingBtn.waitFor({ timeout: 4_000 }).then(() => keepGoingBtn.click()).catch(() => {});

    // Open profile dropdown and click Log Out
    await page.getByRole('button', { name: 'Account menu' }).click();
    await page.getByRole('button', { name: 'Log Out' }).click();

    await expect(page).toHaveURL(/\/login/, { timeout: 10_000 });

    // Verify session is gone — protected route should redirect to login
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login/);
  });
});

// ── Forgot password ───────────────────────────────────────────────────────────

test.describe('Forgot password', () => {
  test('shows "Email is required" when form is submitted empty', async ({ page }) => {
    await page.goto('/forgot-password');
    await page.getByRole('button', { name: /send reset link/i }).click();
    await expect(page.getByText('Email is required')).toBeVisible();
  });

  test('redirects to /check-email on valid email submission', async ({ page }) => {
    await page.goto('/forgot-password');
    await page.locator('[type="email"]').fill('test@example.com');
    await page.getByRole('button', { name: /send reset link/i }).click();
    await expect(page).toHaveURL(/\/check-email.*type=reset/, { timeout: 10_000 });
  });
});

// ── Remember me ───────────────────────────────────────────────────────────────

test.describe('Remember me', () => {
  test('"Remember me" checkbox is present on the login page', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await expect(page.getByText('Remember me')).toBeVisible();
    await expect(page.locator('[name="remember_me"]')).toBeAttached();
  });
});
