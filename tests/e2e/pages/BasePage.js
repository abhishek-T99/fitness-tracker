/**
 * BasePage — shared helpers available on every page object.
 */
class BasePage {
  /** @param {import('@playwright/test').Page} page */
  constructor(page) {
    this.page = page;
  }

  /** Wait for a react-hot-toast notification containing the given text. */
  async waitForToast(text, timeout = 5_000) {
    await this.page.getByText(text).waitFor({ timeout });
  }

  /** Dismiss any open toasts / modals via Escape. */
  async pressEscape() {
    await this.page.keyboard.press('Escape');
  }
}

module.exports = { BasePage };
