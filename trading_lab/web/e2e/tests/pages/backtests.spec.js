import { test, expect } from '@playwright/test';
import { BacktestsPage } from '../../pages/backtests.page.js';
import { mockBacktestsApi, mockStrategiesApi } from '../../fixtures/api-mocks.js';
import { TEST_BACKTESTS, EMPTY_BACKTESTS, TEST_STRATEGIES } from '../../fixtures/test-data.js';

test.describe('Backtests Page', () => {
  let backtestsPage;

  test.beforeEach(async ({ page }) => {
    backtestsPage = new BacktestsPage(page);
  });

  test.describe('Page Load', () => {
    test('should display page title', async ({ page }) => {
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await backtestsPage.goto();

      await expect(backtestsPage.pageTitle).toBeVisible();
    });

    test('should display New Backtest button', async ({ page }) => {
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await backtestsPage.goto();

      await expect(backtestsPage.newBacktestButton).toBeVisible();
    });
  });

  test.describe('Table Display', () => {
    test('should display all required columns', async ({ page }) => {
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await backtestsPage.goto();
      await backtestsPage.waitForApi();

      expect(await backtestsPage.hasAllColumns()).toBe(true);
    });

    test('should display correct number of rows', async ({ page }) => {
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await backtestsPage.goto();
      await backtestsPage.waitForApi();

      const count = await backtestsPage.getBacktestCount();
      expect(count).toBe(5);
    });

    test('should show backtest count in subtitle', async ({ page }) => {
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await backtestsPage.goto();
      await backtestsPage.waitForApi();

      const subtitle = await backtestsPage.getSubtitle();
      expect(subtitle).toContain('5');
    });
  });

  test.describe('Return Display', () => {
    test('should show positive return in green', async ({ page }) => {
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await backtestsPage.goto();
      await backtestsPage.waitForApi();

      // First row has positive return
      const isPositive = await backtestsPage.isReturnPositive(0);
      expect(isPositive).toBe(true);
    });

    test('should show negative return in red', async ({ page }) => {
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await backtestsPage.goto();
      await backtestsPage.waitForApi();

      // Row with SOL/USD has negative return (index 4)
      const row = backtestsPage.getRowByStrategy('sentiment').filter({ hasText: 'SOL/USD' });
      const redReturn = row.locator('.text-red-600');
      await expect(redReturn).toBeVisible();
    });

    test('should show dash for null metrics', async ({ page }) => {
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await backtestsPage.goto();
      await backtestsPage.waitForApi();

      // Running backtest has null return
      const runningRow = backtestsPage.getRowByStrategy('sentiment').filter({ hasText: 'running' });
      const nullValue = runningRow.locator('.text-gray-400');
      await expect(nullValue.first()).toBeVisible();
    });
  });

  test.describe('Status Badges', () => {
    test('should show status badges with correct colors', async ({ page }) => {
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await backtestsPage.goto();
      await backtestsPage.waitForApi();

      // Check for various status badges
      await expect(page.locator('.bg-green-100:has-text("completed")').first()).toBeVisible();
      await expect(page.locator('.bg-blue-100:has-text("running")')).toBeVisible();
      await expect(page.locator('.bg-yellow-100:has-text("pending")')).toBeVisible();
      await expect(page.locator('.bg-red-100:has-text("failed")')).toBeVisible();
    });
  });

  test.describe('Navigation', () => {
    test('should have New Backtest button with correct link', async ({ page }) => {
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await backtestsPage.goto();

      const href = await backtestsPage.newBacktestButton.getAttribute('href');
      expect(href).toBe('/backtests/new');
    });

    test('should navigate to new backtest on button click', async ({ page }) => {
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await backtestsPage.goto();

      await backtestsPage.clickNewBacktest();
      await expect(page).toHaveURL('/backtests/new');
    });

    test('should navigate to detail page on row click', async ({ page }) => {
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await backtestsPage.goto();
      await backtestsPage.waitForApi();

      const link = page.locator('tbody a').first();
      await link.click();

      await expect(page).toHaveURL(/\/backtests\/\d+/);
    });
  });

  test.describe('Empty State', () => {
    test('should show empty message when no backtests', async ({ page }) => {
      await mockBacktestsApi(page, EMPTY_BACKTESTS);
      await backtestsPage.goto();
      await backtestsPage.waitForApi();

      await expect(backtestsPage.emptyState).toBeVisible();
    });

    test('should show CTA to run first backtest', async ({ page }) => {
      await mockBacktestsApi(page, EMPTY_BACKTESTS);
      await backtestsPage.goto();
      await backtestsPage.waitForApi();

      await expect(backtestsPage.runFirstBacktestLink).toBeVisible();
    });
  });

  test.describe('Auto-Refresh', () => {
    test('should poll for updates periodically', async ({ page }) => {
      let requestCount = 0;
      await page.route('**/api/backtests*', (route) => {
        requestCount++;
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(TEST_BACKTESTS)
        });
      });

      await backtestsPage.goto();
      await page.waitForTimeout(6000);

      expect(requestCount).toBeGreaterThanOrEqual(2);
    });
  });
});
