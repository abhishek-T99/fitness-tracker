/**
 * Playwright global setup — runs once before all tests.
 *
 * 1. Creates (or resets) the deterministic E2E test user via a Django
 *    management command so no email-verification flow is needed.
 * 2. Logs in via the REST API to obtain JWT tokens.
 * 3. Seeds those tokens into browser localStorage and saves storageState
 *    to .auth/user.json — authenticated projects pick this up automatically.
 */

const { chromium } = require('@playwright/test');
const { execSync }  = require('child_process');
const path          = require('path');
const fs            = require('fs');
const axios         = require('axios');

const BASE_URL = process.env.BASE_URL || 'http://localhost:5173';
const API_URL  = process.env.API_URL  || 'http://localhost:8000/api/v1';
const AUTH_DIR = path.join(__dirname, '.auth');

module.exports = async function globalSetup() {
  // ── 1. Create/reset test user ──────────────────────────────────────────────
  console.log('\n[e2e:setup] Creating Playwright test user...');
  const projectRoot = path.resolve(__dirname, '../..');
  try {
    execSync(
      'docker compose exec -T backend python manage.py create_pw_user',
      { cwd: projectRoot, stdio: 'inherit' }
    );
  } catch (err) {
    console.error(
      '[e2e:setup] Could not create test user.\n' +
      '           Make sure Docker is running: docker compose up -d\n'
    );
    throw err;
  }

  // ── 2. Login via REST API ──────────────────────────────────────────────────
  console.log('[e2e:setup] Authenticating via API...');
  let tokens;
  try {
    const res = await axios.post(`${API_URL}/auth/login/`, {
      username:    'pw_testuser',
      password:    'TestPass123!',
      remember_me: true,        // persist=true → tokens land in localStorage
    });
    tokens = res.data;
  } catch (err) {
    const status = err.response?.status;
    console.error(`[e2e:setup] Login failed (HTTP ${status}).`);
    throw err;
  }

  // ── 3. Seed localStorage and save storageState ─────────────────────────────
  console.log('[e2e:setup] Saving auth state...');
  fs.mkdirSync(AUTH_DIR, { recursive: true });

  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page    = await context.newPage();

  // Navigate to the app first (localStorage is origin-scoped).
  await page.goto(`${BASE_URL}/login`);

  // Replicate what AuthContext does when remember_me=true.
  await page.evaluate(({ access, refresh }) => {
    localStorage.setItem('ft_persist',  'true');
    localStorage.setItem('ft_access',   access);
    localStorage.setItem('ft_refresh',  refresh);
  }, { access: tokens.access, refresh: tokens.refresh });

  // Verify the session actually works before saving.
  await page.goto(`${BASE_URL}/dashboard`);
  await page.waitForURL('**/dashboard', { timeout: 20_000 });

  await context.storageState({ path: path.join(AUTH_DIR, 'user.json') });
  await browser.close();
  console.log('[e2e:setup] Auth state saved to .auth/user.json\n');
};
