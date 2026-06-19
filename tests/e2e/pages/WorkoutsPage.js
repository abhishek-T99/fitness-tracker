const { BasePage } = require('./BasePage');

class WorkoutsPage extends BasePage {
  constructor(page) {
    super(page);
    this.heading          = page.getByRole('heading', { name: 'Workouts', exact: true });
    this.logWorkoutButton = page.getByRole('link', { name: /log workout/i });
    this.emptyStateTitle  = page.getByText('No workouts yet');
  }

  async goto() {
    await this.page.goto('/workouts');
    await this.heading.waitFor();
  }

  async clickLogWorkout() {
    await this.logWorkoutButton.click();
    await this.page.waitForURL('**/workouts/new');
  }

  /** Returns all workout card links on the current page. */
  workoutCards() {
    // Each card is a <Link> (renders as <a>) that navigates to /workouts/:id
    return this.page.locator('a[href^="/workouts/"]').filter({
      has: this.page.locator('text=Exercises').or(this.page.locator('text=completed')),
    });
  }
}

module.exports = { WorkoutsPage };
