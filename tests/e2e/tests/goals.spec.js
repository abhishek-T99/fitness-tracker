/**
 * Goals spec — authenticated.
 * Covers create → mark-achieved → delete lifecycle for fitness goals.
 */

const { expect }          = require('@playwright/test');
const { test }            = require('../fixtures/test');
const { GoalsPage }       = require('../pages/GoalsPage');
const { deleteAllGoals }  = require('../helpers/api');
const data                = require('../helpers/data');

test.beforeEach(async () => {
  await deleteAllGoals();
});

test.afterEach(async () => {
  await deleteAllGoals();
});

// ── List / empty state ────────────────────────────────────────────────────────

test.describe('Goals list', () => {
  test('shows empty state when there are no goals', async ({ page }) => {
    const goalsPage = new GoalsPage(page);
    await goalsPage.goto();
    await expect(goalsPage.emptyStateText).toBeVisible();
  });

  test('shows "New goal" button', async ({ page }) => {
    const goalsPage = new GoalsPage(page);
    await goalsPage.goto();
    await expect(goalsPage.newGoalButton).toBeVisible();
  });
});

// ── Create goal ───────────────────────────────────────────────────────────────

test.describe('Create goal', () => {
  test('opens the goal modal when "New goal" is clicked', async ({ page }) => {
    const goalsPage = new GoalsPage(page);
    await goalsPage.goto();

    await goalsPage.newGoalButton.click();

    await expect(page.getByRole('heading', { name: 'New goal', exact: true })).toBeVisible({ timeout: 5_000 });
  });

  test('dismisses the modal when Cancel is clicked', async ({ page }) => {
    const goalsPage = new GoalsPage(page);
    await goalsPage.goto();

    await goalsPage.openNewGoalModal();
    await page.getByRole('button', { name: /cancel/i }).click();

    await expect(page.getByRole('heading', { name: 'New goal', exact: true })).not.toBeVisible({ timeout: 5_000 });
  });

  test('shows validation error when Title is empty', async ({ page }) => {
    const goalsPage = new GoalsPage(page);
    await goalsPage.goto();

    await goalsPage.openNewGoalModal();
    await page.locator('[name="target_value"]').fill('80');
    await page.getByRole('button', { name: /save goal/i }).click();

    await expect(page.getByText('Required')).toBeVisible();
  });

  test('creates a goal and shows it in the list', async ({ page }) => {
    const goalsPage = new GoalsPage(page);
    const title     = data.goalTitle();
    await goalsPage.goto();

    await goalsPage.createGoal({ title, targetValue: 80, unit: 'kg' });

    await expect(page.getByText('Goal' + title.replace('PW Goal', '')).or(page.getByText(title))).toBeVisible({
      timeout: 10_000,
    });
    // The modal should be gone
    await expect(page.getByRole('heading', { name: 'New goal', exact: true })).not.toBeVisible();
  });

  test('shows "active" badge on newly created goal', async ({ page }) => {
    const goalsPage = new GoalsPage(page);
    const title     = data.goalTitle();
    await goalsPage.goto();

    await goalsPage.createGoal({ title, targetValue: 100 });

    const card = goalsPage.goalCard(title);
    await card.waitFor({ timeout: 8_000 });
    await expect(card.getByText('active')).toBeVisible();
  });
});

// ── Goal actions ──────────────────────────────────────────────────────────────

test.describe('Goal actions', () => {
  test('marks a goal as achieved', async ({ page }) => {
    const goalsPage = new GoalsPage(page);
    const title     = data.goalTitle();
    await goalsPage.goto();

    await goalsPage.createGoal({ title, targetValue: 50 });
    const card = goalsPage.goalCard(title);
    await card.waitFor({ timeout: 8_000 });

    await goalsPage.markAchieved(title);

    await expect(page.getByText('Goal marked as achieved!')).toBeVisible({ timeout: 8_000 });
    await expect(card.getByText('achieved')).toBeVisible({ timeout: 8_000 });
  });

  test('deletes a goal after confirmation', async ({ page }) => {
    const goalsPage = new GoalsPage(page);
    const title     = data.goalTitle();
    await goalsPage.goto();

    await goalsPage.createGoal({ title, targetValue: 75 });
    const card = goalsPage.goalCard(title);
    await card.waitFor({ timeout: 8_000 });

    await goalsPage.deleteGoal(title);

    await expect(page.getByText('Goal removed')).toBeVisible({ timeout: 8_000 });
    // Card should be gone from the DOM
    await expect(page.getByText(title)).not.toBeVisible({ timeout: 8_000 });
  });

  test('cancels deletion when Cancel is clicked in the confirmation', async ({ page }) => {
    const goalsPage = new GoalsPage(page);
    const title     = data.goalTitle();
    await goalsPage.goto();

    await goalsPage.createGoal({ title, targetValue: 60 });
    const card = goalsPage.goalCard(title);
    await card.waitFor({ timeout: 8_000 });

    // First click shows inline confirm; click Cancel
    await card.getByTitle('Delete goal').click();
    await card.getByRole('button', { name: 'Cancel' }).click();

    // Goal should still be visible
    await expect(page.getByText(title)).toBeVisible();
  });
});

// ── Edit goal ─────────────────────────────────────────────────────────────────

test.describe('Edit goal', () => {
  test('opens the edit modal and updates the goal title', async ({ page }) => {
    const goalsPage = new GoalsPage(page);
    const title     = data.goalTitle();
    await goalsPage.goto();

    await goalsPage.createGoal({ title, targetValue: 50 });
    const card = goalsPage.goalCard(title);
    await card.waitFor({ timeout: 8_000 });

    await card.getByTitle('Edit goal').click();

    // Modal heading changes when editing
    await expect(page.getByText('Edit goal')).toBeVisible({ timeout: 5_000 });

    const updatedTitle = `${title} Updated`;
    await page.locator('[name="title"]').clear();
    await page.locator('[name="title"]').fill(updatedTitle);

    await page.getByRole('button', { name: /update goal/i }).click();

    // Modal should close
    await expect(page.getByText('Edit goal')).not.toBeVisible({ timeout: 5_000 });

    // Updated title should appear in the list
    await expect(page.getByText(updatedTitle)).toBeVisible({ timeout: 8_000 });
  });
});

// ── Reactivate goal ───────────────────────────────────────────────────────────

test.describe('Reactivate goal', () => {
  test('reactivates an achieved goal and shows a toast', async ({ page }) => {
    const goalsPage = new GoalsPage(page);
    const title     = data.goalTitle();
    await goalsPage.goto();

    await goalsPage.createGoal({ title, targetValue: 50 });
    const card = goalsPage.goalCard(title);
    await card.waitFor({ timeout: 8_000 });

    // Mark as achieved first
    await goalsPage.markAchieved(title);
    await expect(card.getByText('achieved')).toBeVisible({ timeout: 8_000 });

    // Reactivate
    await card.getByTitle('Reactivate goal').click();

    await expect(page.getByText('Goal reactivated.')).toBeVisible({ timeout: 8_000 });
    await expect(card.getByText('active')).toBeVisible({ timeout: 8_000 });
  });
});

// ── Update current value ──────────────────────────────────────────────────────

test.describe('Update current value', () => {
  test('blurring the inline value input fires an update without error', async ({ page }) => {
    const goalsPage = new GoalsPage(page);
    const title     = data.goalTitle();
    await goalsPage.goto();

    await goalsPage.createGoal({ title, targetValue: 100, unit: 'kg' });
    const card = goalsPage.goalCard(title);
    await card.waitFor({ timeout: 8_000 });

    // The active goal card renders an inline number input (step="0.1")
    const valueInput = card.locator('input[type="number"][step="0.1"]');
    await valueInput.fill('75');
    await valueInput.press('Tab'); // onBlur triggers the mutation

    // Wait briefly for the mutation to fire — no error toast should appear
    await page.waitForTimeout(1_500);
    await expect(page.getByText(/could not/i)).not.toBeVisible();
  });
});
