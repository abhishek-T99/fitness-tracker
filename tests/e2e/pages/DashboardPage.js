const { BasePage } = require('./BasePage');

class DashboardPage extends BasePage {
  constructor(page) {
    super(page);
    this.heading = page.getByRole('heading', { name: /^Hi,/i });
  }

  async goto() {
    await this.page.goto('/dashboard');
    await this.heading.waitFor({ timeout: 15_000 });
  }

  async isLoaded() {
    await this.heading.waitFor({ timeout: 10_000 });
  }
}

module.exports = { DashboardPage };
