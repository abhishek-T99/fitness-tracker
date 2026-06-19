const { BasePage } = require('./BasePage');

class ProgressPage extends BasePage {
  constructor(page) {
    super(page);
    this.heading      = page.getByRole('heading', { name: 'Progress', exact: true });
    this.bodyTab      = page.getByRole('button', { name: /body/i });
    this.strengthTab  = page.getByRole('button', { name: /strength/i });
    this.volumeTab    = page.getByRole('button', { name: /volume/i });
  }

  async goto() {
    await this.page.goto('/progress');
    await this.heading.waitFor();
  }

  async switchTab(tab) {
    const tabs = { body: this.bodyTab, strength: this.strengthTab, volume: this.volumeTab };
    await tabs[tab].click();
  }
}

module.exports = { ProgressPage };
