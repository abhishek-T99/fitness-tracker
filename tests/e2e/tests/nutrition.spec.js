/**
 * Nutrition spec — authenticated.
 * Covers water logging and meal logging on the Nutrition page.
 */

const { expect }               = require('@playwright/test');
const { test }                 = require('../fixtures/test');
const { NutritionPage }        = require('../pages/NutritionPage');
const { deleteNutritionForDate } = require('../helpers/api');
const data                     = require('../helpers/data');

test.beforeEach(async () => {
  await deleteNutritionForDate(data.today());
});

test.afterEach(async () => {
  await deleteNutritionForDate(data.today());
});

// ── Page structure ────────────────────────────────────────────────────────────

test.describe('Nutrition page structure', () => {
  test('shows page heading and macro cards', async ({ page }) => {
    const nutritionPage = new NutritionPage(page);
    await nutritionPage.goto();

    await expect(nutritionPage.heading).toBeVisible();

    // Five macro summary cards
    for (const label of ['Calories', 'Protein', 'Carbs', 'Fat', 'Water']) {
      await expect(page.getByText(label).first()).toBeVisible();
    }
  });

  test('renders the four meal-type sections', async ({ page }) => {
    const nutritionPage = new NutritionPage(page);
    await nutritionPage.goto();

    for (const section of ['Breakfast', 'Lunch', 'Dinner', 'Snack']) {
      await expect(page.getByRole('heading', { name: section })).toBeVisible();
    }
  });
});

// ── Water logging ─────────────────────────────────────────────────────────────

test.describe('Water logging', () => {
  test('shows the three preset water buttons', async ({ page }) => {
    const nutritionPage = new NutritionPage(page);
    await nutritionPage.goto();

    for (const ml of [250, 500, 750]) {
      await expect(page.getByRole('button', { name: `+${ml} ml` })).toBeVisible();
    }
  });

  test('logs water with a preset button and shows a success toast', async ({ page }) => {
    const nutritionPage = new NutritionPage(page);
    await nutritionPage.goto();

    await nutritionPage.addWater(500);

    await expect(page.getByText('Water logged')).toBeVisible({ timeout: 8_000 });
  });

  test('water log entry appears after logging', async ({ page }) => {
    const nutritionPage = new NutritionPage(page);
    await nutritionPage.goto();

    await nutritionPage.addWater(250);

    // The water log entry span — use exact span to avoid matching the "+250 ml" button
    await expect(page.locator('span').filter({ hasText: /^250 ml$/ })).toBeVisible({ timeout: 8_000 });
  });

  test('logging multiple water presets accumulates in the water log section', async ({ page }) => {
    const nutritionPage = new NutritionPage(page);
    await nutritionPage.goto();

    await nutritionPage.addWater(250);
    await nutritionPage.addWater(500);

    // Both entries should be visible
    await expect(page.getByText('250 ml').first()).toBeVisible({ timeout: 8_000 });
    await expect(page.getByText('500 ml').first()).toBeVisible({ timeout: 8_000 });
  });
});

// ── Meal logging ──────────────────────────────────────────────────────────────

test.describe('Meal logging', () => {
  test('opens the meal modal when "Log meal" is clicked', async ({ page }) => {
    const nutritionPage = new NutritionPage(page);
    await nutritionPage.goto();

    await nutritionPage.logMealButton.click();

    await expect(page.getByText('Log a meal')).toBeVisible({ timeout: 5_000 });
  });

  test('can dismiss the meal modal with the × button', async ({ page }) => {
    const nutritionPage = new NutritionPage(page);
    await nutritionPage.goto();

    await nutritionPage.logMealButton.click();
    await page.getByText('Log a meal').waitFor();

    await page.locator('button:has-text("✕")').click();
    await expect(page.getByText('Log a meal')).not.toBeVisible({ timeout: 5_000 });
  });

  test('shows error toast when saving a meal with no items', async ({ page }) => {
    const nutritionPage = new NutritionPage(page);
    await nutritionPage.goto();

    await nutritionPage.openMealModal();
    await page.getByRole('button', { name: /save meal/i }).click();

    await expect(page.getByText('Add at least one food')).toBeVisible({ timeout: 5_000 });
  });

  test('logs a meal and shows a success toast', async ({ page }) => {
    const nutritionPage = new NutritionPage(page);
    await nutritionPage.goto();

    await nutritionPage.logMeal({ mealType: 'breakfast', foodSearch: 'chicken' });

    await expect(page.getByText('Meal logged')).toBeVisible({ timeout: 10_000 });
  });

  test('edit meal opens pre-filled modal and shows "Meal updated" toast', async ({ page }) => {
    const np = new NutritionPage(page);
    await np.goto();

    // First log a meal so there is something to edit
    await np.logMeal({ mealType: 'breakfast', foodSearch: 'chicken' });
    await page.getByText('Meal logged').waitFor({ timeout: 10_000 });

    // Click the edit (pencil) button on the logged meal card
    await page.getByTitle('Edit meal').first().click();

    // Modal opens in edit mode
    await expect(page.getByText('Edit meal')).toBeVisible({ timeout: 5_000 });

    // Submit without changing anything — server still returns updated
    await page.getByRole('button', { name: /update meal/i }).click();

    await expect(page.getByText('Meal updated')).toBeVisible({ timeout: 8_000 });
  });

  test('delete meal removes the entry and shows "Meal removed" toast', async ({ page }) => {
    const np = new NutritionPage(page);
    await np.goto();

    await np.logMeal({ mealType: 'breakfast', foodSearch: 'chicken' });
    await page.getByText('Meal logged').waitFor({ timeout: 10_000 });

    // Click the delete (trash) button on the logged meal card
    await page.getByTitle('Delete meal').first().click();

    await expect(page.getByText('Meal removed')).toBeVisible({ timeout: 8_000 });
  });
});

// ── Water editing ─────────────────────────────────────────────────────────────

test.describe('Water editing', () => {
  test('edit water entry updates the amount and shows "Water updated" toast', async ({ page }) => {
    const np = new NutritionPage(page);
    await np.goto();

    await np.addWater(250);
    await page.getByText('Water logged').waitFor({ timeout: 8_000 });

    // Click the edit (pencil) button on the water entry row
    await page.getByTitle('Edit').first().click();

    // WaterEditModal opens
    await expect(page.getByText('Edit water entry')).toBeVisible({ timeout: 5_000 });

    // Change the amount
    const amountInput = page.locator('input[type="number"]').last();
    await amountInput.clear();
    await amountInput.fill('500');

    await page.getByRole('button', { name: 'Update' }).click();

    await expect(page.getByText('Water updated')).toBeVisible({ timeout: 8_000 });
  });
});

// ── Date navigation ───────────────────────────────────────────────────────────

test.describe('Date navigation', () => {
  test('changing the date input loads that day\'s data', async ({ page }) => {
    const np = new NutritionPage(page);
    await np.goto();

    const today     = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(today.getDate() - 1);
    const ymd = yesterday.toISOString().slice(0, 10);

    await page.locator('input[type="date"]').fill(ymd);

    // Page should still render without crashing (no new URL, but heading remains)
    await expect(np.heading).toBeVisible({ timeout: 5_000 });
    // Date input should reflect the new value
    await expect(page.locator('input[type="date"]')).toHaveValue(ymd);
  });
});
