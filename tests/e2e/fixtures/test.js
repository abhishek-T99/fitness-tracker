/**
 * Extended Playwright test fixture that exposes an authenticated Axios client
 * alongside the standard `page` and `expect`.
 *
 * Usage:
 *   const { test, expect } = require('../fixtures/test');
 */

const { test: base, expect } = require('@playwright/test');
const { authedClient }        = require('../helpers/api');

const test = base.extend({
  /**
   * Auto-dismiss the LevelUpModal whenever it appears mid-test.
   * The modal fires when the test user gains enough XP to level up;
   * it blocks all pointer events (z-[100] overlay) until dismissed.
   * addLocatorHandler fires automatically before any blocked action retries.
   */
  page: async ({ page }, use) => {
    await page.addLocatorHandler(
      page.getByText('Level Up!'),
      async () => {
        const keepGoingBtn = page.getByRole('button', { name: 'Keep Going!' });
        if (await keepGoingBtn.isVisible()) {
          await keepGoingBtn.click();
        } else {
          await page.keyboard.press('Escape');
        }
      },
    );
    await use(page);
  },

  /**
   * `api` — a pre-authenticated Axios client scoped to the test user.
   * Use it in beforeEach/afterEach hooks to create or clean up data via
   * the REST API instead of the UI (fast, reliable, no flakiness).
   *
   * Example:
   *   test('...', async ({ page, api }) => {
   *     await api.delete('/goals/123/');
   *   });
   */
  api: async ({}, use) => {
    const client = await authedClient();
    await use(client);
  },
});

module.exports = { test, expect };
