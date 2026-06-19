const { BasePage } = require('./BasePage');

class WorkoutDetailPage extends BasePage {
  constructor(page) {
    super(page);
    this.editButton   = page.getByRole('link', { name: /edit/i });
    // Delete uses browser confirm() — caller must set up dialog handler first
    this.deleteButton = page.getByRole('button', { name: /delete/i });
    // Recalculate calories — identified by its title attribute
    this.recalcButton = page.getByTitle('Recalculate from sets');
  }

  async goto(id) {
    await this.page.goto(`/workouts/${id}`);
    // Wait for either the workout name heading or the generic "Workout" heading
    await this.page.getByRole('heading').first().waitFor({ timeout: 10_000 });
  }

  async deleteWithConfirm() {
    this.page.once('dialog', (dialog) => dialog.accept());
    await this.deleteButton.click();
  }
}

module.exports = { WorkoutDetailPage };
