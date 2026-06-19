const { BasePage } = require('./BasePage');

class RoutinesPage extends BasePage {
  constructor(page) {
    super(page);
    this.heading          = page.getByRole('heading', { name: 'Routines', exact: true });
    this.newRoutineButton = page.getByRole('link', { name: /new routine/i });
    this.emptyStateText   = page.getByText('No routines');
  }

  async goto() {
    await this.page.goto('/routines');
    await this.heading.waitFor();
  }

  async clickNewRoutine() {
    await this.newRoutineButton.click();
    await this.page.waitForURL(/\/routines\/new/);
  }

  /** Card for a routine identified by its name. */
  routineCard(name) {
    return this.page.locator('.card').filter({ hasText: name });
  }

  async deleteRoutine(name) {
    const card = this.routineCard(name);
    // Routines.jsx uses a native confirm() dialog — accept it before the click fires
    this.page.once('dialog', (dialog) => dialog.accept());
    await card.getByTitle('Delete routine').click();
  }
}

module.exports = { RoutinesPage };
