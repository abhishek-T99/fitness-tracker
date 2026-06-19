const { BasePage } = require('./BasePage');

class GoalsPage extends BasePage {
  constructor(page) {
    super(page);
    this.heading        = page.getByRole('heading', { name: 'Goals', exact: true });
    this.newGoalButton  = page.getByRole('button', { name: /new goal/i });
    this.emptyStateText = page.getByText('No goals yet');
  }

  async goto() {
    await this.page.goto('/goals');
    await this.heading.waitFor();
  }

  // ── Goal modal ─────────────────────────────────────────────────────────────

  async openNewGoalModal() {
    await this.newGoalButton.click();
    await this.page.getByRole('heading', { name: 'New goal', exact: true }).waitFor({ timeout: 10_000 });
  }

  /**
   * Fill and submit the goal modal.
   * All fields except `title` and `targetValue` are optional.
   */
  async createGoal({ title, goalType = 'custom', targetValue, unit = 'kg' }) {
    await this.openNewGoalModal();

    await this.page.locator('[name="title"]').fill(title);
    await this.page.locator('[name="goal_type"]').selectOption(goalType);
    await this.page.locator('[name="target_value"]').fill(String(targetValue));
    await this.page.locator('[name="unit"]').fill(unit);

    await this.page.getByRole('button', { name: /save goal/i }).click();
  }

  /**
   * Returns the card locator for a goal identified by its title text.
   * Use this to chain further assertions or interactions on the card.
   */
  goalCard(title) {
    return this.page.locator('.card').filter({ hasText: title });
  }

  /** Click the check-mark (mark as achieved) button on a goal card. */
  async markAchieved(title) {
    const card = this.goalCard(title);
    await card.getByTitle('Mark as achieved').click();
  }

  /** Click the trash icon (first click) then confirm deletion. */
  async deleteGoal(title) {
    const card = this.goalCard(title);
    await card.getByTitle('Delete goal').click();
    // Confirmation buttons appear inline
    await card.getByRole('button', { name: 'Delete' }).click();
  }
}

module.exports = { GoalsPage };
