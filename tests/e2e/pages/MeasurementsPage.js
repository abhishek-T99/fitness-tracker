const { BasePage } = require('./BasePage');

class MeasurementsPage extends BasePage {
  constructor(page) {
    super(page);
    this.heading        = page.getByRole('heading', { name: 'Measurements', exact: true });
    this.addEntryButton = page.getByRole('button', { name: /add entry/i });
    this.emptyMessage   = page.getByText('No entries yet.');
  }

  async goto() {
    await this.page.goto('/measurements');
    await this.heading.waitFor();
  }

  async openModal() {
    await this.addEntryButton.click();
    await this.page.getByText('New measurement').waitFor({ timeout: 5_000 });
  }

  async addMeasurement({ weight_kg, notes }) {
    await this.openModal();
    if (weight_kg !== undefined)
      await this.page.locator('[name="weight_kg"]').fill(String(weight_kg));
    if (notes)
      await this.page.locator('[name="notes"]').fill(notes);
    await this.page.getByRole('button', { name: /^save$/i }).click();
  }

  /** Returns the table row matching a given weight string (e.g. "75 kg"). */
  rowFor(weightText) {
    return this.page.locator('tbody tr').filter({ hasText: weightText });
  }

  async editRow(weightText, newWeight) {
    const row = this.rowFor(weightText);
    await row.getByTitle('Edit').click();
    await this.page.getByText('Edit measurement').waitFor({ timeout: 5_000 });
    await this.page.locator('[name="weight_kg"]').clear();
    await this.page.locator('[name="weight_kg"]').fill(String(newWeight));
    await this.page.getByRole('button', { name: /update/i }).click();
  }

  async deleteRow(weightText) {
    const row = this.rowFor(weightText);
    await row.getByTitle('Delete').click();
  }
}

module.exports = { MeasurementsPage };
