// @ts-check
const { defineConfig, devices } = require('@playwright/test');

const BASE_URL = process.env.BASE_URL || 'http://localhost:5173';

module.exports = defineConfig({
  testDir: './tests',

  // Run tests sequentially within each file to avoid data races on shared user.
  // Parallelism across files is still enabled via workers.
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : 2,

  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['list'],
  ],

  use: {
    baseURL:           BASE_URL,
    trace:             'on-first-retry',
    screenshot:        'only-on-failure',
    video:             'retain-on-failure',
    actionTimeout:     10_000,
    navigationTimeout: 30_000,
  },

  globalSetup: require.resolve('./global-setup'),

  projects: [
    // ── Authenticated tests ──────────────────────────────────────────────────
    // Uses stored auth state from global-setup so login is skipped.
    {
      name:       'chromium',
      testIgnore: ['**/auth/**'],
      use: {
        ...devices['Desktop Chrome'],
        storageState: '.auth/user.json',
      },
    },

    // ── Auth / unauthenticated tests ─────────────────────────────────────────
    // Runs WITHOUT any saved session so it can test the login/register flows.
    {
      name:      'auth',
      testMatch: ['**/auth/**'],
      use: {
        ...devices['Desktop Chrome'],
      },
    },
  ],
});
