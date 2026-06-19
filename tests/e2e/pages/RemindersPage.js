const { BasePage } = require('./BasePage');

class RemindersPage extends BasePage {
  constructor(page) {
    super(page);
    this.heading          = page.getByRole('heading', { name: 'Reminders', exact: true });
    this.newReminderBtn   = page.getByRole('button', { name: /new reminder/i });
    this.emptyStateText   = page.getByText('No reminders yet');
  }

  async goto() {
    await this.page.goto('/reminders');
    await this.heading.waitFor();
  }

  async openModal() {
    await this.newReminderBtn.click();
    await this.page.getByRole('heading', { name: 'New reminder', exact: true }).waitFor({ timeout: 5_000 });
  }

  /**
   * Create a once-daily reminder.
   * The ReminderModal's type is a radio grid (sr-only inputs); click the label
   * for the desired type, then fill title and save.
   */
  async createReminder({ title, type = 'water', time = '08:00' }) {
    await this.openModal();

    // Radio inputs are sr-only; the SVG icon overlays them — use force:true
    await this.page.locator(`[name="reminder_type"][value="${type}"]`).click({ force: true });

    // Fill title
    await this.page.locator('[name="title"]').fill(title);

    // The modal defaults to "once" recurrence; set time_of_day
    await this.page.locator('[name="time_of_day"]').fill(time);

    // Save
    await this.page.getByRole('button', { name: /save reminder/i }).click();
  }

  /** Returns the card for a reminder identified by its title. */
  reminderCard(title) {
    return this.page.locator('.card').filter({ hasText: title });
  }

  async deleteReminder(title) {
    const card = this.reminderCard(title);
    await card.getByTitle('Delete reminder').click();
  }

  /** Click the toggle switch on a reminder card to flip its active state. */
  async toggleReminder(title) {
    const card = this.reminderCard(title);
    // The toggle is a hidden checkbox inside a <label>; clicking the label works
    await card.locator('label.inline-flex').click();
  }
}

module.exports = { RemindersPage };
