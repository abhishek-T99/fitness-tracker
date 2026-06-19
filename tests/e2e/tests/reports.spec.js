/**
 * Fitness Reports spec — authenticated.
 * Covers report preference settings and on-demand report triggering.
 */

const { expect } = require('@playwright/test');
const { test }   = require('../fixtures/test');

// ── Helpers ───────────────────────────────────────────────────────────────────

async function resetReportPrefs(api) {
  await api.patch('/auth/me/', {
    profile: { reports_enabled: false, report_frequency: 'weekly' },
  });
}

// ── Visibility ────────────────────────────────────────────────────────────────

test.describe('Fitness Reports card', () => {
  test('is visible on the profile page', async ({ page }) => {
    await page.goto('/profile');
    await expect(
      page.getByTestId('fitness-reports-card'),
    ).toBeVisible({ timeout: 10_000 });
  });

  test('shows the enable toggle', async ({ page }) => {
    await page.goto('/profile');
    await expect(
      page.getByTestId('reports-enabled-toggle'),
    ).toBeVisible({ timeout: 10_000 });
  });

  test('toggle is unchecked by default for a fresh user', async ({ page, api }) => {
    await resetReportPrefs(api);
    await page.goto('/profile');
    const toggle = page.getByTestId('reports-enabled-toggle');
    await expect(toggle).not.toBeChecked({ timeout: 10_000 });
  });

  test('frequency selector is hidden when reports are disabled', async ({ page, api }) => {
    await resetReportPrefs(api);
    await page.goto('/profile');
    await expect(
      page.getByTestId('report-frequency-select'),
    ).not.toBeVisible({ timeout: 10_000 });
  });
});

// ── Enable + save preferences ─────────────────────────────────────────────────

test.describe('Enable reports and save preferences', () => {
  test.afterEach(async ({ api }) => {
    await resetReportPrefs(api);
  });

  test('enabling toggle shows the frequency selector', async ({ page, api }) => {
    await resetReportPrefs(api);
    await page.goto('/profile');

    await page.getByTestId('reports-toggle-label').click();

    await expect(
      page.getByTestId('report-frequency-select'),
    ).toBeVisible({ timeout: 5_000 });
  });

  test('saving preferences shows success toast', async ({ page, api }) => {
    await resetReportPrefs(api);
    await page.goto('/profile');

    await page.getByTestId('reports-toggle-label').click();
    await page.getByTestId('report-frequency-select').selectOption('monthly');

    await page.getByRole('button', { name: /save preferences/i }).click();

    await expect(
      page.getByText(/report preferences saved/i),
    ).toBeVisible({ timeout: 8_000 });
  });

  test('saved frequency persists after page reload', async ({ page, api }) => {
    await resetReportPrefs(api);
    await page.goto('/profile');

    await page.getByTestId('reports-toggle-label').click();
    await page.getByTestId('report-frequency-select').selectOption('yearly');
    await page.getByRole('button', { name: /save preferences/i }).click();
    await page.getByText(/report preferences saved/i).waitFor({ timeout: 8_000 });

    // Reload and verify the saved value
    await page.reload();
    await expect(
      page.getByTestId('reports-enabled-toggle'),
    ).toBeChecked({ timeout: 10_000 });
    await expect(
      page.getByTestId('report-frequency-select'),
    ).toHaveValue('yearly', { timeout: 5_000 });
  });

  test('frequency hint text updates when option changes', async ({ page, api }) => {
    await resetReportPrefs(api);
    await page.goto('/profile');

    await page.getByTestId('reports-toggle-label').click();
    await page.getByTestId('report-frequency-select').selectOption('monthly');

    await expect(
      page.getByText(/1st of each month/i),
    ).toBeVisible({ timeout: 5_000 });
  });
});

// ── On-demand report trigger ──────────────────────────────────────────────────

test.describe('Send report now', () => {
  test('send weekly button triggers a success toast', async ({ page }) => {
    await page.goto('/profile');

    // Intercept the API call so we don't actually queue a Celery task
    await page.route('**/api/v1/reports/trigger/', async (route) => {
      await route.fulfill({
        status: 202,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Your weekly report is being generated and will be emailed shortly.',
        }),
      });
    });

    await page.getByTestId('trigger-report-weekly').click();

    await expect(
      page.getByText(/weekly report is being generated/i),
    ).toBeVisible({ timeout: 8_000 });
  });

  test('send monthly button sends correct period_type', async ({ page }) => {
    await page.goto('/profile');

    let capturedBody = null;
    await page.route('**/api/v1/reports/trigger/', async (route) => {
      capturedBody = JSON.parse(route.request().postData() || '{}');
      await route.fulfill({
        status: 202,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Your monthly report is being generated and will be emailed shortly.' }),
      });
    });

    await page.getByTestId('trigger-report-monthly').click();
    await page.getByText(/monthly report/i).waitFor({ timeout: 8_000 });
    expect(capturedBody?.period_type).toBe('monthly');
  });

  test('send yearly button sends correct period_type', async ({ page }) => {
    await page.goto('/profile');

    let capturedBody = null;
    await page.route('**/api/v1/reports/trigger/', async (route) => {
      capturedBody = JSON.parse(route.request().postData() || '{}');
      await route.fulfill({
        status: 202,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Your yearly report is being generated and will be emailed shortly.' }),
      });
    });

    await page.getByTestId('trigger-report-yearly').click();
    await page.getByText(/yearly report/i).waitFor({ timeout: 8_000 });
    expect(capturedBody?.period_type).toBe('yearly');
  });
});

// ── Report history ────────────────────────────────────────────────────────────

test.describe('Report history', () => {
  test('report history section appears when reports exist', async ({ page }) => {
    // Route must be registered before navigation so the initial page-load request is mocked.
    await page.route('**/api/v1/reports/', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          count: 1,
          next: null,
          previous: null,
          results: [
            {
              id: 1,
              period_type: 'weekly',
              period_start: '2025-01-01',
              period_end: '2025-01-07',
              generated_at: '2025-01-08T07:00:00Z',
              emailed_at: '2025-01-08T07:01:00Z',
              pdf_url: null,
            },
          ],
        }),
      });
    });

    await page.goto('/profile');

    await expect(
      page.getByTestId('report-history'),
    ).toBeVisible({ timeout: 10_000 });

    await expect(page.getByText(/jan 1/i)).toBeVisible({ timeout: 5_000 });
    await expect(page.getByText(/weekly/i).first()).toBeVisible();
  });

  test('report history is hidden when no reports exist', async ({ page }) => {
    await page.route('**/api/v1/reports/', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ count: 0, next: null, previous: null, results: [] }),
      });
    });

    await page.goto('/profile');

    await expect(
      page.getByTestId('report-history'),
    ).not.toBeVisible({ timeout: 5_000 });
  });

  test('download link appears when pdf_url is present', async ({ page }) => {
    await page.route('**/api/v1/reports/', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          count: 1,
          next: null,
          previous: null,
          results: [
            {
              id: 2,
              period_type: 'monthly',
              period_start: '2025-02-01',
              period_end: '2025-02-28',
              generated_at: '2025-03-01T07:00:00Z',
              emailed_at: '2025-03-01T07:01:00Z',
              pdf_url: 'http://localhost:8000/media/reports/1/fittrack_monthly_2025-02.pdf',
            },
          ],
        }),
      });
    });

    await page.goto('/profile');

    await expect(
      page.getByTestId('report-download-link'),
    ).toBeVisible({ timeout: 10_000 });
    await expect(
      page.getByTestId('report-download-link'),
    ).toHaveAttribute('href', /fittrack_monthly/);
  });
});
