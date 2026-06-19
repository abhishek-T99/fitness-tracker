const { BasePage } = require('./BasePage');

class WorkoutEditorPage extends BasePage {
  constructor(page) {
    super(page);
    this.nameInput         = page.getByPlaceholder('Push day');
    this.addExerciseButton = page.getByRole('button', { name: /add exercise/i });
    this.saveButton        = page.getByRole('button', { name: /save workout/i });
    this.cancelButton      = page.getByRole('button', { name: /cancel/i });
  }

  async waitForLoad() {
    await this.page.getByRole('heading', { name: /log a workout/i }).waitFor();
  }

  async fillName(name) {
    await this.nameInput.fill(name);
  }

  /**
   * Opens the exercise picker, searches for `searchTerm`, and clicks the first
   * matching result.  Waits for the exercise card to appear in the form before
   * returning.
   */
  async addExercise(searchTerm) {
    await this.addExerciseButton.click();

    // Picker modal
    const picker      = this.page.locator('text=Add exercise').first();
    const searchInput = this.page.getByPlaceholder('Search exercises…');
    await searchInput.waitFor({ timeout: 8_000 });
    await searchInput.fill(searchTerm);

    // Wait for results and click the first one
    const firstAddBtn = this.page.getByText('Add →').first();
    await firstAddBtn.waitFor({ timeout: 8_000 });
    await firstAddBtn.click();

    // Picker should close; wait for the exercise card to appear in the form
    await picker.waitFor({ state: 'detached', timeout: 5_000 }).catch(() => {});
  }

  /**
   * Fill reps + weight for the set at `setIndex` (0-based) of the first
   * exercise block.
   */
  async fillSet(setIndex, { reps, weight }) {
    const row = this.page.locator('tbody tr').nth(setIndex);
    const numInputs = row.locator('input[type="number"]');
    await numInputs.nth(0).fill(String(reps));    // Reps column
    await numInputs.nth(1).fill(String(weight));  // Weight column
  }

  async save() {
    await this.saveButton.click();
  }
}

module.exports = { WorkoutEditorPage };
