import { test, expect } from '@playwright/test';
import { mockStrategiesApi, mockBacktestsApi, mockHealthCheck } from '../../fixtures/api-mocks.js';
import { TEST_STRATEGIES, TEST_BACKTESTS } from '../../fixtures/test-data.js';

test.describe('Smoke Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Setup common mocks
    await mockStrategiesApi(page, TEST_STRATEGIES);
    await mockBacktestsApi(page, TEST_BACKTESTS);
    await mockHealthCheck(page);
  });

  test('app loads and shows dashboard', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Dashboard uses h2 for page title
    await expect(page.locator('h2:has-text("Dashboard")')).toBeVisible();
    await expect(page.locator('header')).toBeVisible();
  });

  test('navigation links are visible in header', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Navigation is inside nav element with Link components
    await expect(page.locator('nav >> text=Dashboard')).toBeVisible();
    await expect(page.locator('nav >> text=Strategies')).toBeVisible();
    await expect(page.locator('nav >> text=Backtests')).toBeVisible();
    await expect(page.locator('header >> text=New Backtest')).toBeVisible();
  });

  test('navigation between pages works', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Navigate to Strategies
    await page.locator('nav >> text=Strategies').click();
    await expect(page).toHaveURL('/strategies');
    await expect(page.locator('h2:has-text("Strategies")')).toBeVisible();

    // Navigate to Backtests
    await page.locator('nav >> text=Backtests').click();
    await expect(page).toHaveURL('/backtests');
    await expect(page.locator('h2:has-text("Backtests")')).toBeVisible();

    // Navigate back to Dashboard
    await page.locator('nav >> text=Dashboard').click();
    await expect(page).toHaveURL('/');
    await expect(page.locator('h2:has-text("Dashboard")')).toBeVisible();
  });

  test('new backtest form loads', async ({ page }) => {
    await page.goto('/backtests/new');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('h2:has-text("New Backtest")')).toBeVisible();
    await expect(page.locator('#strategy_name')).toBeVisible();
    await expect(page.locator('#asset')).toBeVisible();
    await expect(page.locator('button:has-text("Start Backtest")')).toBeVisible();
  });

  test('strategies page loads and shows strategy cards', async ({ page }) => {
    await page.goto('/strategies');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('h2:has-text("Strategies")')).toBeVisible();

    // Should have strategy cards with Run Backtest links
    const cards = page.locator('text=Run Backtest');
    await expect(cards.first()).toBeVisible();
  });

  test('backtests page loads and shows table', async ({ page }) => {
    await page.goto('/backtests');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('h2:has-text("Backtests")')).toBeVisible();
    await expect(page.locator('table')).toBeVisible();
  });

  test('header New Backtest button navigates to form', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await page.locator('header >> text=New Backtest').click();

    await expect(page).toHaveURL('/backtests/new');
    await expect(page.locator('h2:has-text("New Backtest")')).toBeVisible();
  });

  test('API health check responds', async ({ page }) => {
    const apiPort = process.env.API_PORT || 8847;
    const response = await page.request.get(`http://localhost:${apiPort}/`);

    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(body.name).toBe('Trading Lab API');
  });
});
