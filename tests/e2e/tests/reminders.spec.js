/**
 * Reminders spec — authenticated.
 * Covers create, toggle active, delete, and empty state.
 */

const { expect }            = require('@playwright/test');
const { test }              = require('../fixtures/test');
const { RemindersPage }     = require('../pages/RemindersPage');
const { deleteAllReminders } = require('../helpers/api');
const data                  = require('../helpers/data');

test.beforeEach(async () => {
  await deleteAllReminders();
});

test.afterEach(async () => {
  await deleteAllReminders();
});

// ── Empty state ───────────────────────────────────────────────────────────────

test.describe('Reminders empty state', () => {
  test('shows empty state when no reminders exist', async ({ page }) => {
    const rp = new RemindersPage(page);
    await rp.goto();
    await expect(rp.emptyStateText).toBeVisible();
  });

  test('shows "New reminder" button in header and in empty state', async ({ page }) => {
    const rp = new RemindersPage(page);
    await rp.goto();
    await expect(rp.newReminderBtn).toBeVisible();
    await expect(page.getByRole('button', { name: /add reminder/i })).toBeVisible();
  });
});

// ── Create reminder ───────────────────────────────────────────────────────────

test.describe('Create reminder', () => {
  test('opens the modal when "New reminder" is clicked', async ({ page }) => {
    const rp = new RemindersPage(page);
    await rp.goto();
    await rp.openModal();
    await expect(page.getByRole('heading', { name: 'New reminder', exact: true })).toBeVisible();
  });

  test('closes modal when × is clicked', async ({ page }) => {
    const rp = new RemindersPage(page);
    await rp.goto();
    await rp.openModal();
    await page.locator('button:has-text("✕")').click();
    await expect(page.getByRole('heading', { name: 'New reminder', exact: true })).not.toBeVisible({ timeout: 5_000 });
  });

  test('creates a reminder and shows it in the list', async ({ page }) => {
    const rp    = new RemindersPage(page);
    const title = `Hydrate ${data.uid()}`;
    await rp.goto();

    await rp.createReminder({ title, type: 'water', time: '09:00' });

    // Modal should close; reminder card should appear
    await expect(page.getByRole('heading', { name: 'New reminder', exact: true })).not.toBeVisible({ timeout: 5_000 });
    await expect(rp.reminderCard(title)).toBeVisible({ timeout: 8_000 });
  });

  test('new reminder is active by default', async ({ page }) => {
    const rp    = new RemindersPage(page);
    const title = `Morning workout ${data.uid()}`;
    await rp.goto();

    await rp.createReminder({ title, type: 'workout', time: '07:00' });
    const card = rp.reminderCard(title);
    await card.waitFor({ timeout: 8_000 });

    // The active toggle (peer checkbox) should be checked
    const toggle = card.locator('input[type="checkbox"]');
    await expect(toggle).toBeChecked();
  });
});

// ── Toggle active ─────────────────────────────────────────────────────────────

test.describe('Toggle reminder active state', () => {
  test('toggling active deactivates a reminder', async ({ page }) => {
    const rp    = new RemindersPage(page);
    const title = `Toggle test ${data.uid()}`;
    await rp.goto();

    await rp.createReminder({ title, type: 'meal', time: '12:00' });
    const card = rp.reminderCard(title);
    await card.waitFor({ timeout: 8_000 });

    const toggle = card.locator('input[type="checkbox"]');
    await expect(toggle).toBeChecked();

    await rp.toggleReminder(title);
    await expect(toggle).not.toBeChecked({ timeout: 5_000 });
  });
});

// ── Delete reminder ───────────────────────────────────────────────────────────

test.describe('Delete reminder', () => {
  test('deletes a reminder and shows success toast', async ({ page }) => {
    const rp    = new RemindersPage(page);
    const title = `Delete me ${data.uid()}`;
    await rp.goto();

    await rp.createReminder({ title, type: 'custom', time: '18:00' });
    await rp.reminderCard(title).waitFor({ timeout: 8_000 });

    await rp.deleteReminder(title);

    await expect(page.getByText('Reminder deleted')).toBeVisible({ timeout: 8_000 });
    await expect(page.getByText(title)).not.toBeVisible({ timeout: 8_000 });
  });
});
