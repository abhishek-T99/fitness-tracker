const { BasePage } = require('./BasePage');

class AchievementsPage extends BasePage {
  constructor(page) {
    super(page);
    this.heading = page.getByRole('heading', { name: 'Achievements', exact: true });
  }

  async goto() {
    await this.page.goto('/achievements');
    await this.heading.waitFor();
  }

  /** Returns all badge cards (locked and unlocked). */
  badgeCards() {
    return this.page.locator('[class*="rounded-2xl"][class*="flex-col"]');
  }
}

module.exports = { AchievementsPage };
