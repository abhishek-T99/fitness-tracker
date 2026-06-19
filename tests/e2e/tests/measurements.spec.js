/**
 * Measurements spec — authenticated.
 * Covers the full CRUD lifecycle and weight trend chart.
 */

const { expect }               = require('@playwright/test');
const { test }                 = require('../fixtures/test');
const { MeasurementsPage }     = require('../pages/MeasurementsPage');
const { deleteAllMeasurements } = require('../helpers/api');

test.beforeEach(async () => {
  await deleteAllMeasurements();
});

test.afterEach(async () => {
  await deleteAllMeasurements();
});

// ── Page structure ────────────────────────────────────────────────────────────

test.describe('Measurements page structure', () => {
  test('shows heading, "Add entry" button, and chart area', async ({ page }) => {
    const mp = new MeasurementsPage(page);
    await mp.goto();

    await expect(mp.heading).toBeVisible();
    await expect(mp.addEntryButton).toBeVisible();
    await expect(page.getByText('Weight trend')).toBeVisible();
  });

  test('shows empty state in history table when no entries exist', async ({ page }) => {
    const mp = new MeasurementsPage(page);
    await mp.goto();
    await expect(mp.emptyMessage).toBeVisible();
  });
});

// ── Create entry ──────────────────────────────────────────────────────────────

test.describe('Add measurement', () => {
  test('opens the modal when "Add entry" is clicked', async ({ page }) => {
    const mp = new MeasurementsPage(page);
    await mp.goto();
    await mp.openModal();
    await expect(page.getByText('New measurement')).toBeVisible();
  });

  test('closes modal when Cancel is clicked', async ({ page }) => {
    const mp = new MeasurementsPage(page);
    await mp.goto();
    await mp.openModal();
    await page.getByRole('button', { name: /cancel/i }).click();
    await expect(page.getByText('New measurement')).not.toBeVisible({ timeout: 5_000 });
  });

  test('records a measurement and shows success toast', async ({ page }) => {
    const mp = new MeasurementsPage(page);
    await mp.goto();
    await mp.addMeasurement({ weight_kg: 75 });
    await expect(page.getByText('Measurement recorded')).toBeVisible({ timeout: 8_000 });
  });

  test('new entry appears in the history table', async ({ page }) => {
    const mp = new MeasurementsPage(page);
    await mp.goto();
    await mp.addMeasurement({ weight_kg: 80 });
    await expect(page.getByText('80.00 kg')).toBeVisible({ timeout: 8_000 });
  });
});

// ── Edit entry ────────────────────────────────────────────────────────────────

test.describe('Edit measurement', () => {
  test('opens pre-filled edit modal on pencil click', async ({ page }) => {
    const mp = new MeasurementsPage(page);
    await mp.goto();

    // Create one first
    await mp.addMeasurement({ weight_kg: 72 });
    await page.getByText('72.00 kg').waitFor({ timeout: 8_000 });

    // Click edit
    await mp.rowFor('72.00 kg').getByTitle('Edit').click();
    await expect(page.getByText('Edit measurement')).toBeVisible({ timeout: 5_000 });
    // Prefilled value — number inputs strip trailing zeros
    await expect(page.locator('[name="weight_kg"]')).toHaveValue('72.00');
  });

  test('updates a measurement and shows success toast', async ({ page }) => {
    const mp = new MeasurementsPage(page);
    await mp.goto();

    await mp.addMeasurement({ weight_kg: 73 });
    await page.getByText('73.00 kg').waitFor({ timeout: 8_000 });
    await mp.editRow('73.00 kg', 74);

    await expect(page.getByText('Measurement updated')).toBeVisible({ timeout: 8_000 });
    await expect(page.getByText('74.00 kg')).toBeVisible({ timeout: 8_000 });
  });
});

// ── Delete entry ──────────────────────────────────────────────────────────────

test.describe('Delete measurement', () => {
  test('removes entry from table after delete', async ({ page }) => {
    const mp = new MeasurementsPage(page);
    await mp.goto();

    await mp.addMeasurement({ weight_kg: 78 });
    await page.getByText('78.00 kg').waitFor({ timeout: 8_000 });
    await mp.deleteRow('78.00 kg');

    await expect(page.getByText('Deleted')).toBeVisible({ timeout: 8_000 });
    await expect(page.getByText('78.00 kg')).not.toBeVisible({ timeout: 8_000 });
  });
});

// ── Chart ─────────────────────────────────────────────────────────────────────

test.describe('Weight trend chart', () => {
  test('shows placeholder text when no data exists', async ({ page }) => {
    const mp = new MeasurementsPage(page);
    await mp.goto();
    await expect(page.getByText('Log a measurement to see your trend.')).toBeVisible();
  });

  test('renders chart container once a measurement exists', async ({ page }) => {
    const mp = new MeasurementsPage(page);
    await mp.goto();

    await mp.addMeasurement({ weight_kg: 76 });
    await page.getByText('76.00 kg').waitFor({ timeout: 8_000 });

    // Recharts renders an <svg> inside the ResponsiveContainer
    await expect(page.locator('.recharts-wrapper').first()).toBeVisible({ timeout: 8_000 });
  });
});
