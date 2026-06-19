const { BasePage } = require('./BasePage');

class NutritionPage extends BasePage {
  constructor(page) {
    super(page);
    this.heading       = page.getByRole('heading', { name: 'Nutrition', exact: true });
    this.logMealButton = page.getByRole('button', { name: /log meal/i });
  }

  async goto() {
    await this.page.goto('/nutrition');
    await this.heading.waitFor();
  }

  // ── Water ──────────────────────────────────────────────────────────────────

  /** Click one of the quick-add water preset buttons (+250 ml, +500 ml, +750 ml). */
  async addWater(ml) {
    await this.page.getByRole('button', { name: `+${ml} ml` }).click();
  }

  // ── Meal modal ─────────────────────────────────────────────────────────────

  async openMealModal() {
    await this.logMealButton.click();
    await this.page.getByText('Log a meal').waitFor({ timeout: 5_000 });
  }

  /**
   * In an open MealModal: search for a food, click the first result, then save.
   * `mealType`: 'breakfast' | 'lunch' | 'dinner' | 'snack'
   */
  async logMeal({ mealType = 'breakfast', foodSearch }) {
    await this.openMealModal();

    // Select meal type
    const select = this.page.locator('select').first();
    await select.selectOption(mealType);

    // Search food and pick first result
    const foodInput = this.page.getByPlaceholder('Chicken, banana, oats…');
    await foodInput.fill(foodSearch);
    const firstFood = this.page.locator('[class*="hover:bg-slate-50"]').first();
    await firstFood.waitFor({ timeout: 8_000 });
    await firstFood.click();

    // Save
    await this.page.getByRole('button', { name: /save meal/i }).click();
  }

  /** Returns the displayed calorie total from the macro summary cards. */
  async getCaloriesDisplayed() {
    // Calories card is the first MacroCard
    const card = this.page.locator('.card').filter({ hasText: 'Calories' }).first();
    const text = await card.locator('p.text-xl').textContent();
    return parseInt(text?.trim() ?? '0', 10);
  }
}

module.exports = { NutritionPage };
